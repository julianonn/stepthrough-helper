# stepthrough-helper

Provide: `GEMINI_API_KEY` in `.env`; `cp config.yaml.example config.yaml` and list your recordings under `recordings` (any `defaults` value can be overridden per recording); the GPU box serving the local model, see [seclab-gpu-docker/README.md](seclab-gpu-docker/README.md).

Run all recordings: `../.venv/bin/python pipeline/run.py` · only some: `../.venv/bin/python pipeline/run.py Google_app_settings.mp4`

```
recording ─▶ 1 frames ─▶ 2 OCR ─▶ 3 classify ─▶ 4 pages ─────────▶ 5 describe ─▶ 6 assemble
             ffmpeg+hash  RapidOCR  local GPU     text match +       Gemini Flash   ids, parents,
                                    page/auth/    local GPU picks    1 call/page    paths, validate
                                    junk          the tapped row
```

`output/{recording}/` gets `{page_id}.png` (`{page_id}b.png`, … for scrolls) and `{recording}.jsonl`.
