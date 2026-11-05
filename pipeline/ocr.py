import json

from rapidocr_onnxruntime import RapidOCR


def detect_text(frames, work_dir):
    cache_path = work_dir / "ocr.json"
    detections_by_file = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    unread_frames = [frame for frame in frames if frame.path.name not in detections_by_file]
    if unread_frames:
        engine = RapidOCR()
        for frame in unread_frames:
            detections, _ = engine(str(frame.path))
            detections_by_file[frame.path.name] = [
                [box[0][1], box[0][0], text, confidence] for box, text, confidence in detections or []
            ]
        cache_path.write_text(json.dumps(detections_by_file))
    return [detections_by_file[frame.path.name] for frame in frames]


def read_lines(frames, work_dir, settings):
    return [
        [
            text.strip() for top, left, text, confidence in sorted(detections)
            if confidence >= settings["ocr_min_confidence"] and len(text.strip()) >= settings["min_line_length"]
        ]
        for detections in detect_text(frames, work_dir)
    ]
