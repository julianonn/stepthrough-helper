from dataclasses import dataclass, field

import gemini
from frames import Frame, timecode

INSTRUCTIONS = """These are frames from a screen recording of a read-only walk through settings pages, in order.
Label every frame with exactly one of:
- new_page: new UI with settings appeared (a new screen, or a sheet/modal with its own settings)
- same_page_scrolled: the page already on screen, scrolled or slightly changed
- auth_prompt: passcode, password, Face ID, verification code or approval request
- noise: keyboard, loading, transition, or anything else that is not a settings page
If a new_page frame shows a page that an earlier frame already showed (e.g. after going back), set revisit_of to the index of that earlier frame; otherwise null.
Return a JSON list with one object per frame: {"index": int, "label": str, "revisit_of": int or null}."""


@dataclass
class Page:
    frames: list[Frame]
    auth_frames: list[Frame] = field(default_factory=list)
    revisit_seconds: list[float] = field(default_factory=list)


def label_frames(client, model, frames, config):
    parts = [INSTRUCTIONS]
    for index, frame in enumerate(frames):
        parts += [f"Frame {index} (t={timecode(frame.seconds)}):", frame.path]
    return gemini.ask_json(client, model, parts, config, config["classify_image_max_side"])


def group_into_pages(client, model, frames, config):
    labels = sorted(label_frames(client, model, frames, config), key=lambda entry: entry["index"])
    pages = []
    page_of_frame_index = {}
    current_page = None
    pending_auth_frames = []
    for entry in labels:
        frame = frames[entry["index"]]
        if entry["label"] == "noise":
            continue
        if entry["label"] == "auth_prompt":
            pending_auth_frames.append(frame)
            continue
        revisited_page = page_of_frame_index.get(entry.get("revisit_of"))
        if revisited_page:
            revisited_page.revisit_seconds.append(frame.seconds)
            revisited_page.auth_frames += pending_auth_frames
            current_page = revisited_page
        elif entry["label"] == "new_page" or current_page is None:
            current_page = Page(frames=[frame], auth_frames=pending_auth_frames)
            pages.append(current_page)
        else:
            current_page.frames.append(frame)
            current_page.auth_frames += pending_auth_frames
        pending_auth_frames = []
        page_of_frame_index[entry["index"]] = current_page
    if current_page:
        current_page.auth_frames += pending_auth_frames
    return pages
