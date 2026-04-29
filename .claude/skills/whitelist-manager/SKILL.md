---
name: whitelist-manager
description: >
  Manage the Gmail automation sender whitelist stored in AWS SSM Parameter Store.
  Use this skill whenever the user wants to: show/list/display the whitelist,
  add an email to the whitelist, remove an email from the whitelist, or check
  who is on the whitelist. Triggers on phrases like "show whitelist", "add to
  whitelist", "remove from whitelist", "who's whitelisted", "update whitelist".
---

# Whitelist Manager

Manages the email whitelist in AWS SSM Parameter Store at `/gmail-automation/whitelist`.
Whitelisted senders receive pricing info in auto-replies (20ft=700 NIS, 40ft=900 NIS).

## Helper script

All SSM operations go through the bundled script. Always use it — never write boto3 directly.

**Script path:** `.claude/skills/whitelist-manager/scripts/whitelist.py`  
**Python:** `C:/Users/Daniel/AppData/Local/Python/bin/python.exe`

```bash
# List
python "C:/projects/gmail-automatization/.claude/skills/whitelist-manager/scripts/whitelist.py" list

# Add
python "C:/projects/gmail-automatization/.claude/skills/whitelist-manager/scripts/whitelist.py" add user@example.com

# Remove
python "C:/projects/gmail-automatization/.claude/skills/whitelist-manager/scripts/whitelist.py" remove user@example.com
```

## Workflow

**"show" / "list" / "who's on the whitelist"**
→ Run `list`, display results clearly.

**"add [email]"**
→ Run `add <email>`, confirm success and show updated count.

**"remove [email]"**
→ Run `remove <email>`, confirm success and show updated count.

**"add multiple" / "remove multiple"**
→ Run the command once per email, report each result.

## Response style

Keep it short. Show the result of the operation and the current state.
For list: show numbered emails or "Whitelist is empty."
For add/remove: confirm what changed and how many emails remain.
