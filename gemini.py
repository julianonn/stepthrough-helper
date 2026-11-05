import io
import json
import os
import re
import time
from pathlib import Path

from google import genai
from google.genai import errors, types
from PIL import Image

RETRYABLE_STATUS_CODES = {429, 503}
EXCLUDED_MODEL_WORDS = ("image", "tts", "audio", "live", "computer", "embedding", "customtools")


def make_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def newest_pro_model(client):
    candidates = []
    for model in client.models.list():
        match = re.search(r"gemini-(\d+(?:\.\d+)?)-pro", model.name)
        accepts_content = "generateContent" in (model.supported_actions or [])
        if match and accepts_content and not any(word in model.name for word in EXCLUDED_MODEL_WORDS):
            candidates.append((float(match.group(1)), model.name))
    return max(candidates)[1]


def image_part(path, max_side, jpeg_quality):
    image = Image.open(path).convert("RGB")
    image.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality)
    return types.Part.from_bytes(data=buffer.getvalue(), mime_type="image/jpeg")


def ask_json(client, model, parts, config, max_side=None):
    contents = [image_part(part, max_side, config["jpeg_quality"]) if isinstance(part, Path) else part for part in parts]
    config = types.GenerateContentConfig(response_mime_type="application/json")
    for attempt in range(config["max_retry_attempts"]):
        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
            return json.loads(response.text)
        except errors.APIError as error:
            if error.code not in RETRYABLE_STATUS_CODES or attempt == config["max_retry_attempts"] - 1:
                raise
            time.sleep(config["retry_backoff_seconds"] * 2**attempt)
