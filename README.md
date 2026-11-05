# stepthrough-helper

Provide: `GEMINI_API_KEY` in `.env`; `recording`, `stepthrough`, `device`, `client`, `account`, `start_index`, `scene_change_threshold` (optional `model`, `frames_dir` to keep the extracted frames as `frame_00001.png`, …) in `config.yaml`.

Run: `../.venv/bin/python run.py`

```
recording → [1 frames] → [2 pages] → [3 JSON per page] → [4 assemble]
            ffmpeg+hash   Gemini      Gemini               ids, parents, validate
```

`output/{recording_name}/` gets `{page_id}.png` (`{page_id}b.png`, … for scrolls) and `{recording_name}.jsonl`.
