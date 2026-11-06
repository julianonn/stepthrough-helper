import json
import os
import time
from pathlib import Path

from google import genai
from google.genai import errors, types

from frames import jpeg_bytes

RETRYABLE_STATUS_CODES = {429, 503}


def make_client():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])



def ask_json(client, model, parts, settings):
    contents = [
        types.Part.from_bytes(
            data=jpeg_bytes(part, settings["describe_image_max_side"], settings["jpeg_quality"]),
            mime_type="image/jpeg",
        ) if isinstance(part, Path) else part
        for part in parts
    ]
    generation_config = types.GenerateContentConfig(
        response_mime_type="application/json",
        media_resolution=settings["media_resolution"],
        thinking_config=types.ThinkingConfig(thinking_level=settings["thinking_level"]),
    )
    for attempt in range(settings["max_retry_attempts"]):
        try:
            response = client.models.generate_content(model=model, contents=contents, config=generation_config)
            return json.loads(response.text), response.usage_metadata
        except errors.APIError as error:
            if error.code not in RETRYABLE_STATUS_CODES or attempt == settings["max_retry_attempts"] - 1:
                raise
            time.sleep(settings["retry_backoff_seconds"] * 2**attempt)
