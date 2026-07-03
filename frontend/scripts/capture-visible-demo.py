import os
import time
from pathlib import Path

import cv2
import dxcam
import mss
import numpy as np
from PIL import ImageGrab


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
    width = _int_env("DEMO_CAPTURE_WIDTH", 1440)
    height = _int_env("DEMO_CAPTURE_HEIGHT", 900)
    region = (left, top, left + width, top + height)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if stop_path.exists():
        stop_path.unlink()

    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not open video writer for {output_path}")

    backend = os.environ.get("DEMO_CAPTURE_BACKEND", "dxcam").lower()
    camera = dxcam.create(output_color="BGR") if backend == "dxcam" else None
    sct = mss.mss() if backend == "mss" else None
    started = time.perf_counter()
    frames = 0
    next_frame_at = started

    try:
        while not stop_path.exists():
            if camera is not None:
                frame = camera.grab(region=region)
            elif sct is not None:
                raw = sct.grab({"left": left, "top": top, "width": width, "height": height})
                frame = cv2.cvtColor(np.asarray(raw), cv2.COLOR_BGRA2BGR)
            else:
                image = ImageGrab.grab(bbox=region)
                frame = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
            if frame is None:
                time.sleep(0.005)
                continue
            writer.write(frame)
            frames += 1
            next_frame_at += 1 / fps
            delay = next_frame_at - time.perf_counter()
            if delay > 0:
                time.sleep(delay)
    finally:
        elapsed = max(time.perf_counter() - started, 0.001)
        writer.release()
        print(
            {
                "output": str(output_path),
                "frames": frames,
                "elapsed_sec": round(elapsed, 3),
                "capture_fps": round(frames / elapsed, 3),
                "target_fps": fps,
                "width": width,
                "height": height,
            },
            flush=True,
        )


if __name__ == "__main__":
    main()
