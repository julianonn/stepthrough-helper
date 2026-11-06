# Task: transcribe a whole recording

The video is one screen recording. Return one JSON object, {{"pages": [...]}}, with one page object per page, in the order pages first appear.

Recording inputs: stepthrough={stepthrough}, device={device}, client={client}, account={account}, start_index={start_index}, recording file name={recording}.

## Pages
1. Start a new page whenever new UI with settings appears: a new screen, or a sheet or modal with its own settings. These are not pages: authentication prompts (passcode, password, Face ID, verification code, approval request), loading screens, and scrolling. A long scrolling page is one page.
2. Authentication prompts go in auth_required on the page being reached or changed. If the recording starts with a web sign-in flow, describe every factor asked for in the first settings page's auth_required.
3. The parent of a page is the page on screen immediately before the tap that opened it. Going back doesn't create a page.
4. A page visited twice is recorded once; mention the revisit in llm_notes.

## Page fields
- page_id: "{stepthrough}-DEV-NNN", where DEV is IPH for iPhone, SAM for Samsung, MAC for Mac, TPD for ThinkPad, and NNN counts up from start_index with three digits.
- parent_page_id: the page_id of the parent; null for the first page.
- stepthrough, device, client: copied from the inputs.
- account, settings, auth_required, llm_notes: as described above.
- path: breadcrumb from the first page to this page, joined by " > ", using verbatim labels. Include an on-screen section heading when it groups the setting that was tapped.
- media: {{"screenshots": ["<page_id>.png"], "recording": "<recording file name>", "timecode": "mm:ss"}}, where timecode is when the page first appears.
- reviewer_notes: empty string.

## Example page object
{{"page_id":"ST1-IPH-003","parent_page_id":"ST1-IPH-001","stepthrough":"ST1","device":"iPhone","client":"iPhone Settings","account":"Apple","path":"Settings > Alex Smith > Sign-In & Security","settings":[{{"name":"Email & Phone Numbers","current_value":"alex@icloud.com; +1 (608) •••-••12","is_subpage":false,"input_type":"display"}},{{"name":"Change Password","is_subpage":true}},{{"name":"Two-Factor Authentication","current_value":"On","is_subpage":true}},{{"name":"Account Recovery","is_subpage":false,"input_type":"button"}}],"auth_required":"","media":{{"screenshots":["ST1-IPH-003.png"],"recording":"ST1-IPH-entry01.mp4","timecode":"00:41"}},"llm_notes":"","reviewer_notes":""}}
