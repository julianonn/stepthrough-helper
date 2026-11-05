import os
import sys
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv
from google import genai

ROOT = Path(__file__).resolve().parent.parent
PROMPT_PATH = Path(__file__).parent / "prompt.md"


def main():
    load_dotenv(ROOT / ".env")
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    entry = next(entry for entry in config["recordings"] if entry["file"] == sys.argv[1])
    settings = {**config["defaults"], **entry}
    recording = ROOT / config["data_dir"] / settings["file"]
    prompt = PROMPT_PATH.read_text().format(
        stepthrough=settings["stepthrough"],
        device=settings["device"],
        client=settings["client"],
        account=settings["account"],
        start_index=settings["start_index"],
        recording=recording.name,
    )
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    uploaded = client.files.upload(file=recording)
    while uploaded.state.name == "PROCESSING":
        time.sleep(settings["retry_backoff_seconds"])
        uploaded = client.files.get(name=uploaded.name)
    response = client.models.generate_content(model=sys.argv[2], contents=[uploaded, (ROOT / config["schema"]).read_text(), prompt])
    print(response.text)
    print(response.usage_metadata)
    client.files.delete(name=uploaded.name)


main()
