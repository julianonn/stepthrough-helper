# gemini-video

Experiment: send a whole recording to Gemini's video understanding API with the prompt in `prompt.md`.

Run: `../.venv/bin/python gemini-video/run.py <recording file in data_dir> <gemini model name>`

Prints the response and its token usage. Video costs roughly 100 tokens per second at default resolution.
