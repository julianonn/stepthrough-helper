import json
import shutil
import string
from pathlib import Path

import gemini
from frames import timecode

DEVICE_CODES = {"iPhone": "IPH", "Samsung": "SAM", "Mac": "MAC", "ThinkPad": "TPD"}
REQUIRED_PAGE_FIELDS = ["page_id", "parent_page_id", "stepthrough", "device", "client", "account",
                        "path", "settings", "auth_required", "media", "llm_notes", "reviewer_notes"]
BREADCRUMB_SEPARATOR = " > "


def screenshot_names(page_id, count):
    suffixes = [""] + list(string.ascii_lowercase[1:count])
    return [f"{page_id}{suffix}.png" for suffix in suffixes]


def validation_problems(line):
    problems = [f"missing field {name}" for name in REQUIRED_PAGE_FIELDS if name not in line]
    for setting in line.get("settings") or []:
        label = setting.get("name", "<unnamed setting>")
        if "name" not in setting or "is_subpage" not in setting:
            problems.append(f"setting '{label}' missing name or is_subpage")
        elif not setting["is_subpage"] and "input_type" not in setting:
            problems.append(f"setting '{label}' missing input_type")
        elif setting.get("input_type") == "multi_option" and "options" not in setting:
            problems.append(f"setting '{label}' missing options")
    return problems


def ask_parent(client, model, line, earlier_lines, config):
    listing = "\n".join(f"{earlier['page_id']}: {earlier.get('path')}" for earlier in earlier_lines)
    prompt = (
        "Pages recorded so far, in navigation order:\n" + listing +
        f"\n\nWhich of them was on screen immediately before the tap that opened the page with path "
        f"'{line.get('path')}'? Return JSON {{\"parent_page_id\": id or null}}."
    )
    return gemini.ask_json(client, model, [prompt], config)["parent_page_id"]


def find_page_opened_by_title(title, earlier_lines):
    for earlier in reversed(earlier_lines):
        for setting in earlier.get("settings") or []:
            if str(setting.get("name", "")).strip().casefold() == title.strip().casefold():
                return earlier, setting


def find_parent_id(client, model, line, title, earlier_lines, config):
    if not earlier_lines:
        return None
    opener = find_page_opened_by_title(title, earlier_lines) if title else None
    if opener:
        parent, setting = opener
        setting["is_subpage"] = True
        setting.pop("input_type", None)
        setting.pop("options", None)
        line["llm_notes"] = f"{line.get('llm_notes', '')} Parent and is_subpage inferred from title matching setting '{setting['name']}' on {parent['page_id']}; tap not checked.".strip()
        return parent["page_id"]
    parent_path = BREADCRUMB_SEPARATOR.join(str(line.get("path", "")).split(BREADCRUMB_SEPARATOR)[:-1])
    matches = [earlier["page_id"] for earlier in earlier_lines if earlier.get("path") == parent_path]
    if len(matches) == 1:
        return matches[0]
    parent_id = ask_parent(client, model, line, earlier_lines, config)
    line["llm_notes"] = f"{line.get('llm_notes', '')} parent_page_id chosen by model from navigation order; path did not identify one parent.".strip()
    return parent_id


def write_output(client, model, pages, records, config, recording, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    device_code = DEVICE_CODES[config["device"]]
    lines = []
    failures = []
    screenshot_count = 0
    for offset, (page, record) in enumerate(zip(pages, records)):
        page_id = f"{config['stepthrough']}-{device_code}-{config['start_index'] + offset:03d}"
        names = screenshot_names(page_id, len(page.frames))
        for frame, name in zip(page.frames, names):
            shutil.copy(frame.path, output_dir / name)
        screenshot_count += len(names)
        notes = record.get("llm_notes", "")
        if page.revisit_seconds:
            times = ", ".join(timecode(seconds) for seconds in page.revisit_seconds)
            notes = f"{notes} Page visited again at {times}.".strip()
        account = record.get("account") if config["account"] == "multiple" else config["account"]
        line = {
            "page_id": page_id,
            "parent_page_id": None,
            "stepthrough": config["stepthrough"],
            "device": config["device"],
            "client": config["client"],
            "account": account,
            "path": record.get("path"),
            "settings": record.get("settings"),
            "auth_required": record.get("auth_required"),
            "media": {"screenshots": names, "recording": recording.name, "timecode": timecode(page.frames[0].seconds)},
            "llm_notes": notes,
            "reviewer_notes": "",
        }
        line["parent_page_id"] = find_parent_id(client, model, line, record.get("title"), lines, config)
        problems = validation_problems(line)
        if problems:
            line["llm_notes"] = f"{line['llm_notes']} Failed validation: {'; '.join(problems)}.".strip()
            failures.append((page_id, problems))
        lines.append(line)
    jsonl_path = output_dir / f"{recording.stem}.jsonl"
    jsonl_path.write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines))
    return len(lines), screenshot_count, failures
