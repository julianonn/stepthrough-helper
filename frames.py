import re
import subprocess
from typing import NamedTuple

import imagehash
import imageio_ffmpeg
from PIL import Image



class Frame(NamedTuple):
    path: object
    seconds: float


def timecode(seconds):
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def extract(recording, work_dir, config):
    video_filter = (
        f"select='eq(n,0)+gt(scene,{config['scene_change_threshold']})',showinfo,"
        f"scale='min({config['max_frame_width']},iw)':-2"
    )
    result = subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-i", str(recording), "-vf", video_filter,
         "-fps_mode", "vfr", str(work_dir / "frame_%05d.png")],
        capture_output=True, text=True, check=True,
    )
    seconds_per_frame = [float(value) for value in re.findall(r"pts_time:([\d.]+)", result.stderr)]
    paths = sorted(work_dir.glob("frame_*.png"))
    frames = [Frame(path, seconds) for path, seconds in zip(paths, seconds_per_frame)]
    return drop_near_duplicates(frames, config['max_duplicate_hash_distance'])


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
