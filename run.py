import tempfile
from pathlib import Path

import yaml
from dotenv import load_dotenv

import assemble
import classify
import describe
import frames
import gemini

ROOT = Path(__file__).parent


def main():
    load_dotenv(ROOT / ".env")
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    recording = ROOT / config["recording"]
    client = gemini.make_client()
    model = config.get("model") or gemini.newest_pro_model(client)
    with tempfile.TemporaryDirectory() as temporary_dir:
        work_dir = ROOT / config["frames_dir"] if config.get("frames_dir") else Path(temporary_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        candidate_frames = frames.extract(recording, work_dir, config)
        pages = classify.group_into_pages(client, model, candidate_frames, config)
        records = []
        for page in pages:
            earlier_paths = [record.get("path", "") for record in records]
            records.append(describe.describe_page(client, model, page, config, earlier_paths))
        page_count, screenshot_count, failures = assemble.write_output(
            client, model, pages, records, config, recording, ROOT / "output" / recording.stem
        )
    print(f"model={model} pages={page_count} screenshots={screenshot_count} failed_validation={len(failures)}")
    for page_id, problems in failures:
        print(f"{page_id}: {'; '.join(problems)}")


main()
