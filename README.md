# SubWatch

A Python application that monitors Reddit subreddits for new posts and comments, automatically forwarding them to Discord via webhooks.

## Features

- **Monitor multiple subreddits simultaneously**
- Each subreddit posts to its own Discord channel
- **Keyword monitoring** - Search for specific keywords in posts and comments
- Separate webhooks for regular posts and keyword matches
- Posts updates to Discord with rich formatting
- Includes post metadata (author, score, comments, flair)
- Tracks state independently for each subreddit
- Handles NSFW and spoiler warnings
- Runs continuously with configurable check intervals
- Easy enable/disable individual subreddits or features

## Prerequisites

- Python 3.7 or higher
- A Reddit account to create an app
- A Discord server with webhook access

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Reddit App

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Scroll to the bottom and click "create another app..."
3. Fill in the form:
   - **name**: Choose any name (e.g., "Discord Monitor")
   - **App type**: Select "script"
   - **description**: Optional
   - **about url**: Optional
   - **redirect uri**: Enter `http://localhost:8080` (required but not used)
4. Click "create app"
5. Note down:
   - **client_id**: The string under "personal use script" (14 characters)
   - **client_secret**: The "secret" value shown

### 3. Set Up Discord Webhooks

For each subreddit you want to monitor, create a webhook:

1. In your Discord server, go to Server Settings → Integrations
2. Click "Webhooks" → "New Webhook"
3. Give it a descriptive name (e.g., "r/python Monitor")
4. Choose which channel should receive posts from this subreddit
5. Click "Copy Webhook URL"
6. Repeat for each subreddit you want to monitor

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your Reddit credentials:
   ```
   REDDIT_CLIENT_ID=your-14-char-client-id
   REDDIT_CLIENT_SECRET=your-client-secret
   REDDIT_USER_AGENT=Discord Monitor Bot (by /u/YourUsername)
   CHECK_INTERVAL=300
   ```

   **Note**: Replace `YourUsername` in the user agent with your actual Reddit username.

### 5. Configure Subreddit Subscriptions

Edit `subreddits.json` to define which subreddits to monitor and where to post them:

```json
[
  {
    "subreddit": "python",
    "webhook_url": "https://discord.com/api/webhooks/your-webhook-for-python",
    "enabled": true,
    "monitor_posts": true,
    "monitor_keywords": false,
    "keyword_webhook_url": ""
  },
  {
    "subreddit": "LocalLLaMA",
    "webhook_url": "https://discord.com/api/webhooks/your-webhook-for-localllama",
    "enabled": true,
    "monitor_posts": true,
    "monitor_keywords": true,
    "keyword_webhook_url": "https://discord.com/api/webhooks/your-webhook-for-keywords"
  }
]
```

**Configuration options:**
- `subreddit`: Subreddit name (without "r/" prefix) **(required)**
- `webhook_url`: Discord webhook URL for regular posts **(required)**
- `enabled`: Set to `false` to temporarily disable all monitoring (default: `true`)
- `monitor_posts`: Set to `false` to disable regular post monitoring (default: `true`)
- `monitor_keywords`: Enable keyword monitoring for this subreddit (default: `false`)
- `keyword_webhook_url`: Separate webhook for keyword matches (optional, uses `webhook_url` if empty)

### 6. Configure Keywords (Optional)

If you want to monitor for specific keywords, edit `keywords.json`:

```json
{
  "keywords": [
    "antgear",
    "antgear.com",
    "ant gear"
  ],
  "case_sensitive": false,
  "search_posts": true,
  "search_comments": true
}
```

**Keyword options:**
- `keywords`: Array of keywords/phrases to search for
- `case_sensitive`: Whether matching should be case-sensitive (default: `false`)
- `search_posts`: Search in post titles and bodies (default: `true`)
- `search_comments`: Search in comments (default: `true`)

**How it works:**
- Keywords use word-boundary matching (won't match "antgear" in "merchantgear")
- Posts and comments that contain ANY of the keywords will be posted to the keyword webhook
- Each match shows which keywords were found and where (title/body/comment)

## Usage

### Run the Monitor

```bash
python main.py
```

The script will:
- Check all enabled subreddits every 5 minutes (configurable)
- Post new Reddit posts to their respective Discord channels
- Track state independently for each subreddit
- Continue running until you stop it with Ctrl+C

### First Run

On the first run, the monitor will check recent posts from each subreddit. After that, it only posts content that appears after the last check for each subreddit.

### Managing Subscriptions

To add a new subreddit:
1. Create a Discord webhook for the new channel
2. Add an entry to `subreddits.json`
3. Restart the monitor

To temporarily disable a subreddit:
- Set `"enabled": false` in `subreddits.json`
- Restart the monitor

To reset state for a specific subreddit:
```bash
# Edit last_check.json and remove the subreddit entry
```

To reset all state:
```bash
rm last_check.json
```

## Configuration

### Environment Variables (`.env`)

- `REDDIT_CLIENT_ID`: Your Reddit app client ID (required)
- `REDDIT_CLIENT_SECRET`: Your Reddit app client secret (required)
- `REDDIT_USER_AGENT`: User agent string (required)
- `CHECK_INTERVAL`: How often to check for new posts (in seconds, default: 300)

### Subreddit Configuration (`subreddits.json`)

Each subreddit entry supports:
- `subreddit`: Name of the subreddit (required)
- `webhook_url`: Discord webhook URL for regular posts (required)
- `enabled`: Whether to monitor this subreddit (default: true)
- `monitor_posts`: Monitor regular posts (default: true)
- `monitor_keywords`: Monitor for keywords (default: false)
- `keyword_webhook_url`: Webhook for keyword matches (optional)

### Keyword Configuration (`keywords.json`)

Global keyword monitoring settings:
- `keywords`: List of keywords/phrases to search for
- `case_sensitive`: Case-sensitive matching (default: false)
- `search_posts`: Search in posts (default: true)
- `search_comments`: Search in comments (default: true)

## Project Structure

```
.
├── main.py              # Main script
├── reddit_monitor.py    # Reddit API integration (posts & comments)
├── discord_poster.py    # Discord webhook integration
├── keyword_matcher.py   # Keyword filtering and matching
├── state_manager.py     # State persistence (per-subreddit)
├── requirements.txt     # Python dependencies
├── .env                 # Reddit API credentials (create from .env.example)
├── .env.example         # Configuration template
├── subreddits.json      # Subreddit-to-webhook mappings
├── keywords.json        # Keyword monitoring configuration
├── last_check.json      # State file (auto-generated, per-subreddit)
└── README.md           # This file
```

## Troubleshooting

### "Error: REDDIT_CLIENT_ID not set"
Make sure you've created a `.env` file and added your Reddit app credentials.

### "Failed to connect to Reddit"
- Verify your client_id and client_secret are correct
- Check that your user agent is properly formatted
- Ensure the subreddit name is correct (without "r/" prefix)

### Posts not appearing in Discord
- Check that the Discord webhook URL is correct
- Verify the webhook hasn't been deleted in Discord

### Rate limiting issues
If you encounter rate limiting errors, increase the `CHECK_INTERVAL` value in your `.env` file to check less frequently.

## Running as a Background Service

### Linux/Mac (using screen or tmux)

```bash
# Using screen
screen -S subwatch
python main.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r subwatch
```

### Using systemd (Linux)

Create `/etc/systemd/system/subwatch.service`:

```ini
[Unit]
Description=SubWatch - Reddit to Discord Monitor
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/subwatch
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable subwatch
sudo systemctl start subwatch
sudo systemctl status subwatch
```

## License

SubWatch is released under the [MIT License](LICENSE). You are free to use, modify, and distribute this software for any purpose, including commercial use.
