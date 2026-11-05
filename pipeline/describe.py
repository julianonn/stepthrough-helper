import json
from pathlib import Path

import gemini

PROMPT_PATH = Path(__file__).parent / "prompts" / "describe_page.md"


def describe_page(client, model, page, settings, schema_text):
    prompt = PROMPT_PATH.read_text().format(
        stepthrough=settings["stepthrough"],
        device=settings["device"],
        client=settings["client"],
        account=settings["account"],
        ocr_text="\n".join(page.text_lines) or "(none)",
        subpage_rows="\n".join(page.subpage_rows) or "(none)",
        auth_context="\n".join(page.auth_context) or "(none)",
    )
    parts = [schema_text, prompt] + [frame.path for frame in page.frames + page.auth_frames]
    try:
        return gemini.ask_json(client, model, parts, settings)
    except json.JSONDecodeError as error:
        return {"llm_notes": f"Model returned invalid JSON: {error}"}, None
