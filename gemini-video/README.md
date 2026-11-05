# gemini-video

Experiment: send a whole recording to Gemini's video understanding API with `prompts/gemini_setting_rules.md` and `prompts/gemini_video_task.md`.

Run: `../.venv/bin/python gemini-video/run.py <recording file in data_dir> <gemini model name>`

Prints the response and its token usage. Video costs roughly 100 tokens per second at default resolution.
