import json
from pathlib import Path

import gemini
from frames import timecode

SCHEMA_PATH = Path(__file__).parent / ".instructions" / "stepthrough_schema.md"

PAGE_TASK = """Task: the images below are all frames of ONE settings page in order (scrolling), followed by any auth prompt frames that guard it. The page first appears at {timecode}.
Recording inputs: stepthrough={stepthrough}, device={device}, client={client}, account={account}.
Pages already recorded, in order (use the same labels in `path`):
{earlier_paths}
Return exactly one JSON object with only these keys: "title" (the verbatim screen title), "path", "account", "settings", "auth_required", "llm_notes".
Do not include page_id, parent_page_id, media or reviewer_notes."""


def describe_page(client, model, page, config, earlier_paths):
    task = PAGE_TASK.format(
        timecode=timecode(page.frames[0].seconds),
        stepthrough=config["stepthrough"],
        device=config["device"],
        client=config["client"],
        account=config["account"],
        earlier_paths="\n".join(earlier_paths) or "(none)",
    )
    parts = [SCHEMA_PATH.read_text(), task] + [frame.path for frame in page.frames + page.auth_frames]
    try:
        return gemini.ask_json(client, model, parts, config, config["describe_image_max_side"])
    except json.JSONDecodeError as error:
        return {"llm_notes": f"Model returned invalid JSON: {error}"}
