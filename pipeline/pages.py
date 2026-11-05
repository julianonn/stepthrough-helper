from dataclasses import dataclass, field

import classify
from frames import timecode


@dataclass(eq=False)
class Page:
    frames: list
    seen_lines: set
    text_lines: list
    parent: "Page | None" = None
    opened_by: str | None = None
    subpage_rows: list = field(default_factory=list)
    auth_frames: list = field(default_factory=list)
    auth_context: list = field(default_factory=list)
    notes: list = field(default_factory=list)


def normalized(lines):
    return {line.casefold() for line in lines}


def share_already_on_page(lines, page):
    texts = normalized(lines)
    return len(texts & page.seen_lines) / len(texts) if texts else 0


def best_matching_page(lines, current_page, pages, settings):
    if current_page and share_already_on_page(lines, current_page) >= settings["same_page_overlap"]:
        return current_page
    earlier_pages = [page for page in pages if page is not current_page]
    if not earlier_pages:
        return None
    best_page = max(earlier_pages, key=lambda page: share_already_on_page(lines, page))
    if share_already_on_page(lines, best_page) >= settings["revisit_overlap"]:
        return best_page
    return None


def add_frame(page, frame, lines, settings):
    if len(normalized(lines) - page.seen_lines) >= settings["min_new_lines_for_screenshot"]:
        page.frames.append(frame)
        page.text_lines += [line for line in lines if line not in page.text_lines]
    page.seen_lines |= normalized(lines)


def attach_auth(page, auth_frames, when):
    page.auth_frames += auth_frames
    page.auth_context += [f"Auth prompt at {timecode(frame.seconds)} appeared {when}." for frame in auth_frames]


def build_pages(frames, labels, lines_per_frame, local_client, settings):
    pages = []
    current_page = None
    previous_frame, previous_lines = None, []
    pending_auth_frames = []
    for frame, label, lines in zip(frames, labels, lines_per_frame):
        if label == "junk":
            continue
        if label == "auth":
            pending_auth_frames.append(frame)
            continue
        matched_page = best_matching_page(lines, current_page, pages, settings)
        if matched_page:
            if matched_page is not current_page:
                matched_page.notes.append(f"Visited again at {timecode(frame.seconds)}.")
            attach_auth(matched_page, pending_auth_frames, "while this page was on screen")
            add_frame(matched_page, frame, lines, settings)
            current_page = matched_page
        else:
            page = Page(frames=[frame], seen_lines=normalized(lines), text_lines=list(lines), parent=current_page)
            if current_page:
                page.opened_by = classify.pick_opener(local_client, previous_frame, previous_lines, frame, settings)
                if page.opened_by:
                    current_page.subpage_rows.append(page.opened_by)
                else:
                    page.notes.append("Could not tell which setting on the parent page opened this page.")
            attach_auth(page, pending_auth_frames, "when opening this page")
            pages.append(page)
            current_page = page
        pending_auth_frames = []
        previous_frame, previous_lines = frame, lines
    if current_page:
        attach_auth(current_page, pending_auth_frames, "while this page was on screen")
    return pages
