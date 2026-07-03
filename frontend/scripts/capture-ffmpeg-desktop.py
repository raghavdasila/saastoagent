import os
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg


def _int_env(name: str, fallback: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return fallback
    try:
        return int(raw)
    except ValueError:
        return fallback


def main() -> None:
    output_path = Path(os.environ["DEMO_CAPTURE_OUTPUT"])
    stop_path = Path(os.environ["DEMO_CAPTURE_STOP_FILE"])
    fps = _int_env("DEMO_CAPTURE_FPS", 30)
    left = _int_env("DEMO_CAPTURE_LEFT", 0)
    top = _int_env("DEMO_CAPTURE_TOP", 0)
    width = _int_env("DEMO_CAPTURE_WIDTH", 1920)
    height = _int_env("DEMO_CAPTURE_HEIGHT", 1080)
    encoder = os.environ.get("DEMO_CAPTURE_ENCODER", "libx264")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if stop_path.exists():
        stop_path.unlink()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    command = [
        ffmpeg,
        "-y",
        "-f",
        "gdigrab",
        "-framerate",
        str(fps),
        "-offset_x",
        str(left),
        "-offset_y",
        str(top),
        "-video_size",
        f"{width}x{height}",
        "-draw_mouse",
        "1",
        "-i",
        "desktop",
        "-c:v",
        encoder,
        *(
            ["-quality", "speed", "-usage", "transcoding"]
            if encoder.endswith("_amf")
            else ["-preset", "ultrafast"]
            if encoder == "libx264"
            else []
        ),
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]

    started = time.perf_counter()
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        while process.poll() is None and not stop_path.exists():
            time.sleep(0.2)
        if process.poll() is None and process.stdin:
            process.stdin.write("q\n")
            process.stdin.flush()
        _, stderr = process.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            _, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            _, stderr = process.communicate()

    elapsed = max(time.perf_counter() - started, 0.001)
    print(
        {
            "output": str(output_path),
            "elapsed_sec": round(elapsed, 3),
            "returncode": process.returncode,
            "target_fps": fps,
            "width": width,
            "height": height,
            "ffmpeg_tail": "\n".join((stderr or "").splitlines()[-12:]),
        },
        flush=True,
    )


if __name__ == "__main__":
    main()
