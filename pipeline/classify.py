import base64
import re
from pathlib import Path

from openai import OpenAI

from frames import jpeg_bytes

PROMPTS_DIR = Path(__file__).parent / "prompts"
FRAME_LABELS = ("page", "auth", "junk")


def make_local_client(settings):
    return OpenAI(base_url=settings["local_model_url"], api_key="unused")


def ask_local_model(client, settings, prompt, image_paths):
    images = [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(
            jpeg_bytes(path, settings["classify_image_max_side"], settings["jpeg_quality"])).decode()}}
        for path in image_paths
    ]
    response = client.chat.completions.create(
        model=settings["local_model"],
        messages=[{"role": "user", "content": images + [{"type": "text", "text": prompt}]}],
        temperature=0,
    )
    return response.choices[0].message.content.strip().lower()


def read_prompt(name):
    return (PROMPTS_DIR / "study_context.md").read_text() + "\n" + (PROMPTS_DIR / name).read_text()


def classify_frames(client, frames, settings):
    prompt = read_prompt("classify_frame.md")
    labels = []
    for frame in frames:
        answer = ask_local_model(client, settings, prompt, [frame.path])
        labels.append(next((label for label in FRAME_LABELS if label in answer), "page"))
    return labels


def pick_opener(client, parent_frame, parent_lines, child_frame, settings):
    numbered_rows = "\n".join(f"{number}. {line}" for number, line in enumerate(parent_lines, 1))
    prompt = read_prompt("pick_opener.md").format(rows=numbered_rows)
    answer = ask_local_model(client, settings, prompt, [parent_frame.path, child_frame.path])
    number = re.search(r"\d+", answer)
    if number and 1 <= int(number.group()) <= len(parent_lines):
        return parent_lines[int(number.group()) - 1]
    return None
