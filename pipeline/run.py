import sys
import tempfile
from collections import Counter
from pathlib import Path

import yaml
from dotenv import find_dotenv, load_dotenv

import assemble
import classify
import describe
import frames
import gemini
import ocr
import pages as page_builder

ROOT = Path(__file__).resolve().parent.parent


def process_recording(settings, config, gemini_client, work_dir):
    recording = ROOT / config["data_dir"] / settings["file"]
    local_client = classify.make_local_client(settings)
    candidate_frames = frames.extract_or_reuse(recording, work_dir, settings)
    lines_per_frame = ocr.read_lines(candidate_frames, work_dir, settings)
    labels = classify.classify_frames(local_client, candidate_frames, settings)
    pages = page_builder.build_pages(candidate_frames, labels, lines_per_frame, local_client, settings)
    model = settings["gemini_model"]
    records, usages = [], []
    for page in pages:
        record, usage = describe.describe_page(gemini_client, model, page, settings)
        records.append(record)
        usages.append(usage)
    screenshot_count, failures = assemble.write_output(
        pages, records, settings, recording, ROOT / config["output_dir"] / recording.stem
    )
    input_tokens = sum(usage.prompt_token_count or 0 for usage in usages if usage)
    output_tokens = sum((usage.candidates_token_count or 0) + (usage.thoughts_token_count or 0) for usage in usages if usage)
    print(f"{settings['file']}: model={model} frames={len(candidate_frames)} labels={dict(Counter(labels))} "
          f"pages={len(pages)} screenshots={screenshot_count} failed_validation={len(failures)} "
          f"gemini_input_tokens={input_tokens} gemini_output_tokens={output_tokens}")
    for page_id, problems in failures:
        print(f"  {page_id}: {'; '.join(problems)}")


def main():
    load_dotenv(find_dotenv(usecwd=True))
    config = yaml.safe_load((ROOT / "config.yaml").read_text())
    selected_files = set(sys.argv[1:])
    gemini_client = gemini.make_client()
    for recording_entry in config["recordings"]:
        settings = {**config["defaults"], **recording_entry}
        if not settings["gemini_model"]:
            sys.exit("Set gemini_model in config.yaml.")
        if selected_files and settings["file"] not in selected_files:
            continue
        with tempfile.TemporaryDirectory() as temporary_dir:
            work_dir = ROOT / config["frames_dir"] / Path(settings["file"]).stem if config.get("frames_dir") else Path(temporary_dir)
            process_recording(settings, config, gemini_client, work_dir)


main()
