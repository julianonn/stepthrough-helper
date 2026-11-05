import json
import shutil
import string

from frames import timecode

DEVICE_CODES = {"iPhone": "IPH", "Samsung": "SAM", "Mac": "MAC", "ThinkPad": "TPD"}
REQUIRED_PAGE_FIELDS = ["page_id", "parent_page_id", "stepthrough", "device", "client", "account",
                        "path", "settings", "auth_required", "media", "llm_notes", "reviewer_notes"]


def screenshot_names(page_id, count):
    suffixes = [""] + list(string.ascii_lowercase[1:count])
    return [f"{page_id}{suffix}.png" for suffix in suffixes]


def validation_problems(line):
    problems = [f"missing field {name}" for name in REQUIRED_PAGE_FIELDS if line.get(name) is None and name != "parent_page_id"]
    for setting in line.get("settings") or []:
        label = setting.get("name", "<unnamed setting>")
        if "name" not in setting or "is_subpage" not in setting:
            problems.append(f"setting '{label}' missing name or is_subpage")
        elif not setting["is_subpage"] and "input_type" not in setting:
            problems.append(f"setting '{label}' missing input_type")
        elif setting.get("input_type") == "multi_option" and "options" not in setting:
            problems.append(f"setting '{label}' missing options")
    return problems


def mark_subpage_settings(settings_list, subpage_rows):
    opener_labels = {row.casefold() for row in subpage_rows}
    for setting in settings_list:
        if str(setting.get("name", "")).casefold() in opener_labels:
            setting["is_subpage"] = True
            setting.pop("input_type", None)
            setting.pop("options", None)


def write_output(pages, records, settings, recording, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    page_ids = {}
    paths = {}
    lines = []
    failures = []
    for offset, (page, record) in enumerate(zip(pages, records)):
        page_id = f"{settings['stepthrough']}-{DEVICE_CODES[settings['device']]}-{settings['start_index'] + offset:03d}"
        page_ids[page] = page_id
        names = screenshot_names(page_id, len(page.frames))
        for frame, name in zip(page.frames, names):
            shutil.copy(frame.path, output_dir / name)
        title = record.get("title") or settings["client"]
        paths[page] = f"{paths[page.parent]} > {page.opened_by or title}" if page.parent else title
        settings_list = record.get("settings") or []
        mark_subpage_settings(settings_list, page.subpage_rows)
        line = {
            "page_id": page_id,
            "parent_page_id": page_ids[page.parent] if page.parent else None,
            "stepthrough": settings["stepthrough"],
            "device": settings["device"],
            "client": settings["client"],
            "account": record.get("account") if settings["account"] == "multiple" else settings["account"],
            "path": paths[page],
            "settings": settings_list,
            "auth_required": record.get("auth_required"),
            "media": {"screenshots": names, "recording": recording.name, "timecode": timecode(page.frames[0].seconds)},
            "llm_notes": " ".join([record.get("llm_notes", "")] + page.notes).strip(),
            "reviewer_notes": "",
        }
        problems = validation_problems(line)
        if problems:
            line["llm_notes"] = f"{line['llm_notes']} Failed validation: {'; '.join(problems)}.".strip()
            failures.append((page_id, problems))
        lines.append(line)
    (output_dir / f"{recording.stem}.jsonl").write_text("".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines))
    return sum(len(page.frames) for page in pages), failures
