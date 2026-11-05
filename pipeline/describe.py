import json
from pathlib import Path

import gemini

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


def describe_page(client, model, page, settings):
    task = (PROMPTS_DIR / "gemini_page_task.md").read_text().format(
        stepthrough=settings["stepthrough"],
        device=settings["device"],
        client=settings["client"],
        account=settings["account"],
        ocr_text="\n".join(page.text_lines) or "(none)",
        subpage_rows="\n".join(page.subpage_rows) or "(none)",
        auth_context="\n".join(page.auth_context) or "(none)",
    )
    parts = [(PROMPTS_DIR / "gemini_setting_rules.md").read_text(), task] + [frame.path for frame in page.frames + page.auth_frames]
    try:
        return gemini.ask_json(client, model, parts, settings)
    except json.JSONDecodeError as error:
        return {"llm_notes": f"Model returned invalid JSON: {error}"}, None
