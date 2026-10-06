# Discord-PurgeSelf
Bulk delete your own Discord messages from DMs or servers. Self-bot tool with strict rate-limiting.


> **NOTE**: This uses self-bot automation which violates Discord's Terms of Service. Your account may be banned. Use only on accounts you are willing to lose.

## Features
- Delete all your messages from a specific DM conversation
- Delete all your messages from all channels in a server
- Strict rate limiting (1.2-2.5s delays + batch pauses) to minimize detection
- Progress tracking with timestamps
- Confirmation prompts to prevent accidents

## Requirements
- Python 3.7+
- `requests` library

## Install & Run
```bash
pip install requests
python purgeself.py
