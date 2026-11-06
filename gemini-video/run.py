import json
import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv
from google import genai

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
RESPONSE_SCHEMA_PATH = Path(__file__).parent / "response_schema.json"
UNFINISHED_STATUSES = ("queued", "in_progress")


def main():
    load_dotenv(find_dotenv(usecwd=True))
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    entry = next(entry for entry in config["recordings"] if entry["file"] == sys.argv[1])
    settings = {**config["defaults"], **entry}
    if not settings["gemini_video_model"]:
        sys.exit("Set gemini_video_model in config.yaml.")
    recording = ROOT / config["data_dir"] / settings["file"]
    task = (PROMPTS_DIR / "gemini_video_task.md").read_text().format(
        stepthrough=settings["stepthrough"],
        device=settings["device"],
        client=settings["client"],
        account=settings["account"],
        start_index=settings["start_index"],
        recording=recording.name,
    )
    response_schema = json.loads(RESPONSE_SCHEMA_PATH.read_text())
    page_field_order = response_schema["properties"]["pages"]["items"]["required"]
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    uploaded = client.files.upload(file=recording)
    while uploaded.state.name == "PROCESSING":
        time.sleep(settings["poll_seconds"])
        uploaded = client.files.get(name=uploaded.name)
    if uploaded.state.name != "ACTIVE":
        sys.exit(f"Video upload ended in state {uploaded.state.name}.")
    interaction = client.interactions.create(
        model=settings["gemini_video_model"],
        input=[
            {"type": "video", "uri": uploaded.uri, "mime_type": uploaded.mime_type, "processing": "agentic"},
            {"type": "text", "text": (PROMPTS_DIR / "gemini_setting_rules.md").read_text()},
            {"type": "text", "text": task},
        ],
        response_format={"type": "text", "mime_type": "application/json", "schema": response_schema},
        background=True,
    )
    while interaction.status in UNFINISHED_STATUSES:
        time.sleep(settings["poll_seconds"])
        interaction = client.interactions.get(interaction.id)
    client.files.delete(name=uploaded.name)
    usage = interaction.usage
    if usage:
        print(f"input_tokens={usage.total_input_tokens} output_tokens={usage.total_output_tokens} "
              f"thought_tokens={usage.total_thought_tokens} tool_use_tokens={usage.total_tool_use_tokens}")
    if interaction.status != "completed":
        sys.exit(f"Interaction ended with status {interaction.status}: {interaction.errors}")
    pages = json.loads(interaction.output_text)["pages"]
    output_dir = ROOT / config["output_dir"] / recording.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = output_dir / f"{recording.stem}.gemini-video.jsonl"
    jsonl_path.write_text("".join(
        json.dumps({field: page[field] for field in page_field_order}, ensure_ascii=False) + "\n" for page in pages
    ))
    print(f"pages={len(pages)} written to {jsonl_path}")


main()
