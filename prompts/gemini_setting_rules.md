# Transcribing security settings from screen recordings

## Background
These screenshots come from screen recordings made for a research study of how consumer accounts and devices authenticate one another. One persona, "Alex Smith", owns seven accounts (Apple, Google, Microsoft, Samsung, Facebook, WhatsApp, Bitwarden) used across four devices (iPhone, Samsung Galaxy phone, Mac, ThinkPad running Windows). A researcher walks through security-related settings without saving any change. To see what a change would require, they open the change flow and cancel before submitting.

## Which settings to record
Record a setting only if it meets at least one of these criteria:
- Credentials: it adds, changes, copies or backs up, or removes a sign-in or recovery credential (password, phone, email, passkey, 2FA, recovery code, key, or contact, password or passkey sync, credential backups, SMS forwarding).
- Devices: it shows or changes which devices or sessions are signed in or trusted, or can approve, lock, locate, or erase them (device lists, Find My).
- Security conditions: it changes when or where a credential or device works (Stolen Device Protection, security delays, lockout settings).

Always record a setting that was tapped to open another page, even if it meets no criterion. If you are unsure whether a setting meets a criterion, record it and say so in llm_notes. Record settings top to bottom as shown, including those revealed by scrolling.

## Setting fields
Each setting is a JSON object:
- name (always): the label, verbatim.
- account (only if different from the page's account): which account the setting belongs to, when one page mixes accounts (e.g. a list of mail accounts).
- explanation (if shown): the description shown with the setting, verbatim. Omit if none.
- current_value (if shown): the displayed value or state, verbatim (e.g. "On", "2 devices", "•••• 1234"). If the setting is greyed out or unavailable, add that and any reason shown, e.g. "Off (greyed out: Managed by Screen Time)". Omit if none.
- is_subpage (always): true if the recording shows the setting being tapped and a new page opening. Otherwise false.
- input_type (only if is_subpage is false): toggle, text, password, multi_option, button, or display. Free text if none fits.
- options (only for multi_option): the list of choices, verbatim.

## Page fields you fill
- account: the account the page belongs to.
- auth_required: empty string if nothing was asked. Otherwise: what was asked, on which device, and when (on opening this page, when signing in, or when starting a change to a named setting). E.g. "Tapping 'Turn On' for Recovery Key asked for the device passcode (cancelled)."
- llm_notes: anything uncertain or notable (unreadable text, unclear page boundary, guessed values). Empty string if none.

## Rules
1. Verbatim: copy labels, explanations, and values exactly. Don't paraphrase, translate, or correct.
2. Lists: when a page lists several devices, sessions, passkeys, phone numbers, or similar, record each one as its own setting: the item's label as name, the details shown (location, last used, etc.) as current_value, and input_type "display" unless it can be tapped.
3. Banners and warnings: an in-scope message not attached to one setting (e.g. "You can't change this for 7 days") is recorded as a setting with the message text as name and input_type "display".
4. Leaving the app: if tapping a setting opens a different app or the browser, set is_subpage false and describe the destination in llm_notes.
5. Secrets: replace one-time codes, full passwords, and recovery keys with "[redacted]". Masked values may be copied as shown.
6. No inference: record only what is on screen. Give your best reading of unclear text and explain in llm_notes. Prompts on other devices (approvals, SMS) are not in this recording: draft auth_required from what is visible, and say in llm_notes that the reviewer must check the other devices.
