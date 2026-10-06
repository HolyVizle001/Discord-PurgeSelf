# Discord-PurgeSelf
Bulk delete your own Discord messages from DMs or servers. Self-bot tool with strict rate-limiting.


> **NOTE**: This uses self-bot automation which violates Discord's Terms of Service. Your account may be banned. Use only on accounts you are willing to lose. The tool will not delete all your messages from your DMs with a user, or a server, from running it once. For safety, it stops deleting after around 30-60 messages. Just run it again. Read the license.

## Features
- Delete all your messages from a specific DM conversation
- Delete all your messages from all channels in a server
- Strict rate limiting (1.2-2.5s delays + batch pauses) to minimize detection
- Progress tracking with timestamps
- Confirmation prompts to prevent accidents

## What is the safest way to use this?
- Currently, the limits are set to:

        self.min_delay = 0.9
        self.max_delay = 2.2
        self.batch_delay = 4.7
- The safest, would probably be:

        self.min_delay = 1.5      
        self.max_delay = 3.0      
        self.batch_delay = 6     



## Requirements
- Python 3.7+
- `requests` library

## Install & Run
```bash
git clone https://github.com/HolyVizle001/Discord-PurgeSelf.git
pip install requests
cd Discord-purgeself
python purgeself.py
