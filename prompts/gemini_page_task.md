# Task: transcribe one page

The images are the screenshots of ONE page, in order (later ones are scrolled further), followed by any authentication prompts that appeared on it.

Recording inputs: stepthrough={stepthrough}, device={device}, client={client}, account={account}.

Text read from the page screenshots by OCR, top to bottom. Use it to spell labels exactly. It also contains the status bar (clock, signal) and may contain misreads, so trust the images for what is actually on the page, and for layout, toggles, and greyed-out state:
{ocr_text}

Settings on this page that the researcher tapped to open another page. These labels were read by OCR and may be truncated or misspelled: match each to the setting on screen, use the on-screen label verbatim, and set is_subpage true. Every other setting has is_subpage false:
{subpage_rows}

Authentication prompts on this page:
{auth_context}

Return only one JSON object with exactly these keys:
- "title": the page's on-screen title, verbatim
- "account": the input account; if the input account is "multiple", the account this page belongs to, from what is on screen
- "settings": list of setting objects
- "auth_required"
- "llm_notes"
