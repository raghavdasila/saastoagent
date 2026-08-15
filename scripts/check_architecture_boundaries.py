from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


PUBLIC_BACKEND_ROOTS = frozenset({"corpus.credentials", "corpus.jobs"})
PUBLIC_BACKEND_NAMESPACES = frozenset({"corpus.persistence", "corpus.shared"})
IMPORT_PATTERN = re.compile(
    r"(?:import|export)\s+(?:type\s+)?(?:[^;]*?\s+from\s+)?[\"']([^\"']+)[\"']"
)


@dataclass(frozen=True, order=True)
class ArchitectureViolation:
    path: str
    line: int
    message: str


def find_architecture_violations(repository: Path) -> list[ArchitectureViolation]:
    return sorted(
        [
            *_backend_feature_violations(repository),
            *_backend_provider_identity_violations(repository),
            *_backend_shared_violations(repository),
            *_frontend_feature_violations(repository),
            *_frontend_auth_violations(repository),
        ]
    )


def _backend_feature_violations(
    repository: Path,
) -> list[ArchitectureViolation]:
    root = repository / "backend" / "src" / "corpus" / "features"
    violations: list[ArchitectureViolation] = []
    for feature in _feature_directories(root):
        feature_root = root / feature
        if not feature_root.exists():
            continue
        for path in feature_root.rglob("*.py"):
            for module, line in _python_imports(path):
                if not module.startswith("corpus."):
                    continue
                if _backend_feature_import_allowed(feature, module):
                    continue
                violations.append(
                    ArchitectureViolation(
                        _relative(repository, path),
                        line,
                        f"feature '{feature}' cannot import '{module}'",
                    )
                )
    return violations


def _backend_provider_identity_violations(
    repository: Path,
) -> list[ArchitectureViolation]:
    root = repository / "backend" / "src" / "corpus" / "features"
    violations: list[ArchitectureViolation] = []
    if not root.exists():
        return violations
    for path in root.rglob("providers.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            method = node.func
            if (
                not isinstance(method, ast.Attribute)
                or method.attr != "get_secret_value"
                or not isinstance(method.value, ast.Attribute)
                or method.value.attr != "private_id"
            ):
                continue
            violations.append(
                ArchitectureViolation(
                    _relative(repository, path),
                    node.lineno,
                    (
                        "context-provider persisted private_id is already a "
                        "string; do not apply execution-time SecretStr handling"
                    ),
                )
            )
    return violations


def _backend_feature_import_allowed(feature: str, module: str) -> bool:
    if module == f"corpus.features.{feature}" or module.startswith(
        f"corpus.features.{feature}."
    ):
        return True
    if module in PUBLIC_BACKEND_ROOTS:
        return True
    if any(
        module == namespace or module.startswith(f"{namespace}.")
        for namespace in PUBLIC_BACKEND_NAMESPACES
    ):
        return True
    if module == "corpus.auth.contracts":
        return True
    parts = module.split(".")
    return (
        len(parts) == 4
        and parts[:2] == ["corpus", "features"]
        and parts[2] != feature
        and parts[3] == "contracts"
    )


def _backend_shared_violations(
    repository: Path,
) -> list[ArchitectureViolation]:
    root = repository / "backend" / "src" / "corpus" / "shared"
    violations: list[ArchitectureViolation] = []
    if not root.exists():
        return violations
    for path in root.rglob("*.py"):
        for module, line in _python_imports(path):
            if module.startswith("corpus.") and not (
                module == "corpus.shared" or module.startswith("corpus.shared.")
            ):
                violations.append(
                    ArchitectureViolation(
                        _relative(repository, path),
                        line,
                        f"shared backend code cannot import '{module}'",
                    )
                )
    return violations


def _frontend_feature_violations(
    repository: Path,
) -> list[ArchitectureViolation]:
    source_root = repository / "frontend" / "src"
    features_root = source_root / "features"
    violations: list[ArchitectureViolation] = []
    for feature in _feature_directories(features_root):
        feature_root = features_root / feature
        if not feature_root.exists():
            continue
        for path in _typescript_files(feature_root):
            for specifier, line in _typescript_imports(path):
                target = _resolve_frontend_import(source_root, path, specifier)
                if target is None:
                    continue
                if _is_within(target, source_root / "app"):
                    violations.append(
                        ArchitectureViolation(
                            _relative(repository, path),
                            line,
                            f"frontend feature '{feature}' cannot import app composition '{specifier}'",
                        )
                    )
                    continue
                if not _is_within(target, features_root):
                    continue
                relative = target.relative_to(features_root)
                target_feature = relative.parts[0]
                if target_feature == feature:
                    continue
                contract_path = relative.parts[1:]
                if contract_path and contract_path[0] == "contracts":
                    continue
                violations.append(
                    ArchitectureViolation(
                        _relative(repository, path),
                        line,
                        f"frontend feature '{feature}' can import feature '{target_feature}' only through contracts",
                    )
                )
    return violations


def _frontend_auth_violations(
    repository: Path,
) -> list[ArchitectureViolation]:
    source_root = repository / "frontend" / "src"
    auth_root = source_root / "auth"
    violations: list[ArchitectureViolation] = []
    if not auth_root.exists():
        return violations
    for path in _typescript_files(auth_root):
        for specifier, line in _typescript_imports(path):
            target = _resolve_frontend_import(source_root, path, specifier)
            if target is None:
                continue
            if _is_within(target, source_root / "app") or _is_within(
                target, source_root / "features"
            ):
                violations.append(
                    ArchitectureViolation(
                        _relative(repository, path),
                        line,
                        f"frontend auth cannot import '{specifier}'",
                    )
                )
    return violations


def _python_imports(path: Path) -> list[tuple[str, int]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.append((node.module, node.lineno))
    return imports


def _typescript_files(root: Path):
    for pattern in ("*.ts", "*.tsx"):
        yield from root.rglob(pattern)


def _feature_directories(root: Path) -> tuple[str, ...]:
    if not root.is_dir():
        return ()
    return tuple(
        sorted(
            path.name
            for path in root.iterdir()
            if path.is_dir() and not path.name.startswith((".", "_"))
        )
    )


def _typescript_imports(path: Path) -> list[tuple[str, int]]:
    content = path.read_text(encoding="utf-8")
    return [
        (match.group(1), content.count("\n", 0, match.start()) + 1)
        for match in IMPORT_PATTERN.finditer(content)
    ]


def _resolve_frontend_import(
    source_root: Path,
    importer: Path,
    specifier: str,
) -> Path | None:
    if specifier.startswith("@/"):
        return (source_root / specifier[2:]).resolve()
    if specifier.startswith("."):
        return (importer.parent / specifier).resolve()
    return None


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _relative(repository: Path, path: Path) -> str:
    return path.relative_to(repository).as_posix()


def main() -> int:
    repository = Path(__file__).resolve().parents[1]
    violations = find_architecture_violations(repository)
    if not violations:
        print("Corpus architecture boundaries passed.")
        return 0
    for violation in violations:
        print(f"{violation.path}:{violation.line}: {violation.message}")
    print(f"Corpus architecture boundaries failed: {len(violations)} violation(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
