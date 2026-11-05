import io
import json
import re
import shutil
import subprocess
from typing import NamedTuple

import imagehash
import imageio_ffmpeg
from PIL import Image


FRAME_SETTING_KEYS = ("scene_change_threshold", "max_duplicate_hash_distance", "max_frame_width")


class Frame(NamedTuple):
    path: object
    seconds: float


def timecode(seconds):
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def jpeg_bytes(path, max_side, jpeg_quality):
    image = Image.open(path).convert("RGB")
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality)
    return buffer.getvalue()


def extract_or_reuse(recording, work_dir, settings):
    manifest_path = work_dir / "frames.json"
    frame_settings = {key: settings[key] for key in FRAME_SETTING_KEYS}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["settings"] == frame_settings:
            return [Frame(work_dir / name, seconds) for name, seconds in manifest["frames"]]
    shutil.rmtree(work_dir, ignore_errors=True)
    work_dir.mkdir(parents=True)
    frames = extract(recording, work_dir, settings)
    manifest_path.write_text(json.dumps({"settings": frame_settings, "frames": [[frame.path.name, frame.seconds] for frame in frames]}))
    return frames


def extract(recording, work_dir, settings):
    video_filter = (
        f"select='eq(n,0)+gt(scene,{settings['scene_change_threshold']})',showinfo,"
        f"scale='min({settings['max_frame_width']},iw)':-2"
    )
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(recording), "-vf", video_filter,
         "-fps_mode", "vfr", str(work_dir / "frame_%05d.png")],
        capture_output=True, text=True, check=True,
    )
    seconds_per_frame = [float(value) for value in re.findall(r"pts_time:([\d.]+)", result.stderr)]
    paths = sorted(work_dir.glob("frame_*.png"))
    frames = [Frame(path, seconds) for path, seconds in zip(paths, seconds_per_frame)]
    return drop_near_duplicates(frames, settings["max_duplicate_hash_distance"])


def drop_near_duplicates(frames, max_hash_distance):
    kept = []
    last_hash = None
    for frame in frames:
        frame_hash = imagehash.phash(Image.open(frame.path))
        if last_hash is not None and frame_hash - last_hash <= max_hash_distance:
            frame.path.unlink()
            continue
        renumbered_path = frame.path.with_name(f"frame_{len(kept) + 1:05d}.png")
        frame.path.rename(renumbered_path)
        kept.append(Frame(renumbered_path, frame.seconds))
        last_hash = frame_hash
    return kept
