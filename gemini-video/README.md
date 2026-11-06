# gemini-video

Experiment: send a whole recording to Gemini's video understanding API in agentic mode (Interactions API, background task) with `prompts/gemini_setting_rules.md` and `prompts/gemini_video_task.md`.

Run: `../.venv/bin/python gemini-video/run.py <recording file>`. The model is `gemini_video_model` in `config.yaml`.

Gemini returns one JSON object, `{"pages": [...]}`, forced to match `response_schema.json`. The script writes one page per line to `output/{recording}/{recording}.gemini-video.jsonl`, next to the pipeline's `{recording}.jsonl`, and prints token usage. In agentic mode, navigation is billed as thought tokens and the frames it loads as tool-use tokens. Supported models: Gemini 4 Argon, 3.8 Flash, 3.6 Flash, 3.5 Flash Lite.
