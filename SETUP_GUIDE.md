# Complete Setup Guide - No Technical Help Needed

Follow these steps exactly to get SubWatch running on your computer.

## Step 1: Create Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Log in with your Reddit account if needed
3. Scroll to the bottom of the page
4. Click **"create another app..."** or **"are you a developer? create an app..."**
5. Fill in the form:
   - **name**: `Discord Monitor` (or whatever you want)
   - **App type**: Select the **"script"** radio button
   - **description**: Leave blank (optional)
   - **about url**: Leave blank (optional)
   - **redirect uri**: Type `http://localhost:8080` (required but not actually used)
6. Click **"create app"**
7. **COPY these two values** (save them somewhere):
   - **client_id**: The string of characters under "personal use script" (about 14 characters)
   - **secret**: The longer string next to "secret" (about 27 characters)

## Step 2: Choose a Subreddit

Decide which subreddit you want to monitor. Examples:
- `python` (for r/python)
- `news` (for r/news)
- `funny` (for r/funny)
- `LocalLLaMA` (for r/LocalLLaMA)

**Note**: Use just the subreddit name, WITHOUT the "r/" prefix.

You'll need this name in Step 6.

## Step 3: Get Your Discord Webhook URL

1. Open Discord
2. Go to your server → Right-click the server icon → **"Server Settings"**
3. Click **"Integrations"** in the left sidebar
4. Click **"Webhooks"**
5. Click **"New Webhook"**
6. Give it a name (e.g., "Reddit Monitor")
7. Choose which channel should receive the Reddit posts
8. Click **"Copy Webhook URL"**
   - Save this URL, you'll need it in Step 6

## Step 4: Install Python and Dependencies

### On Windows with WSL (Ubuntu/Debian):

Open WSL terminal and run:
```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

### On Linux:

Open terminal and run:
```bash
sudo apt update
sudo apt install python3 python3-pip -y
```

### On Mac:

Python 3 should be pre-installed. If not:
```bash
brew install python3
```

## Step 5: Set Up the Application

1. Copy all the files from this folder to your target computer
2. Put them in a folder like `C:\subwatch\` (Windows) or `~/subwatch/` (Linux/Mac)
3. Open terminal/WSL and navigate to the folder:
   ```bash
   cd /mnt/c/subwatch    # Windows with WSL
   # OR
   cd ~/subwatch         # Linux/Mac
   ```

4. Install Python packages:
   ```bash
   pip3 install -r requirements.txt
   ```

5. Create your configuration file:
   ```bash
   cp .env.example .env
   ```

6. Edit the .env file with your actual values:
   ```bash
   nano .env
   ```

   Replace the placeholder values with what you saved earlier:
   ```
   REDDIT_CLIENT_ID=paste-your-14-char-client-id-here
   REDDIT_CLIENT_SECRET=paste-your-27-char-secret-here
   REDDIT_USER_AGENT=Discord Monitor Bot (by /u/YourRedditUsername)
   SUBREDDIT_NAME=python
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/paste-your-webhook-url-here
   CHECK_INTERVAL=300
   ```

   **Important Notes**:
   - Replace `YourRedditUsername` with your actual Reddit username
   - Replace `python` with the subreddit you chose in Step 2
   - No quotes needed around the values
   - No spaces around the `=` signs

   Press `Ctrl+X`, then `Y`, then `Enter` to save and exit

## Step 6: Test It

Run the monitor:
```bash
python3 main.py
```

You should see:
```
Monitoring subreddit: r/python
Check interval: 300 seconds
Press Ctrl+C to stop
```

Within a few minutes, new posts from that subreddit should start appearing in your Discord channel!

Press `Ctrl+C` to stop it when you're done testing.

## Step 7: Run It 24/7

### Option A: Using Screen (Easiest)

1. Start screen:
   ```bash
   screen -S subwatch
   ```

2. Start the monitor:
   ```bash
   cd /mnt/c/subwatch    # or wherever you put the files
   python3 main.py
   ```

3. Detach from screen (leave it running):
   - Press `Ctrl+A`, then press `D`

4. To check on it later:
   ```bash
   screen -r subwatch
   ```

5. To stop it:
   - Reattach with `screen -r subwatch`
   - Press `Ctrl+C`

### Option B: Using nohup (Alternative)

```bash
cd /mnt/c/subwatch
nohup python3 main.py > monitor.log 2>&1 &
```

To stop it:
```bash
pkill -f main.py
```

To view logs:
```bash
tail -f monitor.log
```

### Option C: Auto-Start on Boot (Best for 24/7 - Windows with WSL)

This makes the monitor start automatically whenever you boot your computer.

1. First, create a startup script. In WSL terminal:
   ```bash
   cd /mnt/c/subwatch
   nano start_monitor.sh
   ```

2. Paste this content (adjust the path if yours is different):
   ```bash
   #!/bin/bash
   cd /mnt/c/subwatch
   python3 main.py >> monitor.log 2>&1
   ```

3. Press `Ctrl+X`, then `Y`, then `Enter` to save

4. Make it executable:
   ```bash
   chmod +x start_monitor.sh
   ```

5. Now set up Windows Task Scheduler:
   - Press `Windows + R`
   - Type: `taskschd.msc` and press Enter
   - Click **"Create Task"** (not "Create Basic Task") in the right sidebar

6. In the **General** tab:
   - Name: `SubWatch`
   - Check **"Run whether user is logged on or not"**
   - Check **"Run with highest privileges"**

7. In the **Triggers** tab:
   - Click **"New"**
   - Begin the task: **"At startup"**
   - Click **"OK"**

8. In the **Actions** tab:
   - Click **"New"**
   - Action: **"Start a program"**
   - Program/script: `wsl.exe`
   - Add arguments: `-d Ubuntu bash /mnt/c/subwatch/start_monitor.sh`
     - If you use a different WSL distro (like Debian), replace `Ubuntu` with your distro name
   - Click **"OK"**

9. In the **Conditions** tab:
   - **UNCHECK** "Start the task only if the computer is on AC power"
   - This ensures it runs even on battery

10. In the **Settings** tab:
    - Check **"Allow task to be run on demand"**
    - Check **"If the task fails, restart every: 1 minute"**
    - Set **"Attempt to restart up to: 3 times"**

11. Click **"OK"** to save the task
    - You may need to enter your Windows password

12. Test it by right-clicking the task and choosing **"Run"**

13. Check if it's working:
    ```bash
    tail -f /mnt/c/subwatch/monitor.log
    ```

Now the monitor will start automatically every time your computer boots!

To stop it:
```bash
pkill -f main.py
```

To check the log:
```bash
tail -f /mnt/c/subwatch/monitor.log
```

## Troubleshooting

### "Error: REDDIT_CLIENT_ID not set"
- Make sure you created the `.env` file (not `.env.example`)
- Check that you pasted your credentials correctly (no extra spaces)

### "Failed to connect to Reddit"
- Your client_id or client_secret is wrong
- Go back to Step 1 and double-check the values
- Make sure there are no extra spaces or quotes in your .env file

### "Forbidden" or "401 Unauthorized" errors
- Check that your REDDIT_USER_AGENT is properly formatted
- It should include your Reddit username: `Something (by /u/YourActualUsername)`

### No posts appearing
- The subreddit might not have new posts yet
- Try a busier subreddit like `python` or `news` for testing
- Check that the subreddit name is correct (no "r/" prefix)

### Posts not appearing in Discord
- Check the webhook URL is correct
- Make sure the webhook wasn't deleted in Discord settings
- Look for error messages in the terminal

### pip3 not found
- Try `pip` instead of `pip3`
- Reinstall Python: `sudo apt install python3-pip`

### Rate limiting
- Reddit has rate limits to prevent spam
- If you get rate limited, increase CHECK_INTERVAL to 600 (10 minutes) or more
- Don't set CHECK_INTERVAL below 60 seconds

## That's It!

The monitor is now running and will:
- Check every 5 minutes for new Reddit posts
- Post them to Discord with rich formatting
- Show score, comments, author, and flair
- Mark NSFW and spoiler posts with warnings
- Keep track of what it's already posted

To change the check interval, edit the `CHECK_INTERVAL` value in `.env` (in seconds).

To monitor a different subreddit, just change the `SUBREDDIT_NAME` in `.env` and restart the monitor.
