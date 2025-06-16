2. **Copy and Use the Link**
   - Copy the generated URL
   - Paste it in your browser
   - Select your server
   - Click "Authorize"

## Step 5: Run Your Bot! 🎉

```bash
# Make sure you're in the project directory with virtual environment activated
python main.py
```

You should see:

```
Loaded Music cog
Logged in as YourBot#1234 (ID: 123456789)
Connected to 1 guilds
------
```

## Step 6: Test Your Bot 🎵

1. **Join a voice channel** in your Discord server

2. **Try these commands in any text channel:**
   ```
   !help              # See all commands
   !ping              # Check if bot is responsive
   !play never gonna give you up    # Play a song
   !skip              # Skip current song
   !queue             # View the queue
   !volume 50         # Set volume to 50%
   ```

## Common Issues & Solutions 🔍

### Bot is offline

- Check your token is correct in `.env`
- Ensure you're running `python main.py`
- Check your internet connection

### "FFmpeg not found" error

- **Windows**: Download from https://ffmpeg.org and add to PATH
- **macOS**: Run `brew install ffmpeg`
- **Linux**: Run `sudo apt install ffmpeg`

### Bot can't join voice channel

- Ensure bot has voice permissions
- Check you're in a voice channel
- Re-invite bot with correct permissions

### No sound when playing

- Check bot has "Speak" permission
- Verify FFmpeg is installed correctly
- Try a different YouTube video

## Quick Command Reference 📝

| Command   | Description        | Example              |
| --------- | ------------------ | -------------------- |
| `!play`   | Play a song        | `!play shape of you` |
| `!pause`  | Pause playback     | `!pause`             |
| `!resume` | Resume playback    | `!resume`            |
| `!skip`   | Skip current song  | `!skip`              |
| `!queue`  | Show queue         | `!queue`             |
| `!volume` | Set volume (1-100) | `!volume 75`         |
| `!np`     | Now playing info   | `!np`                |
| `!clear`  | Clear the queue    | `!clear`             |
| `!leave`  | Disconnect bot     | `!leave`             |

## Next Steps 🚶‍♂️

- Read the full [README.md](README.md) for detailed features
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- Star the repository if you find it useful! ⭐

## Running with Docker (Optional) 🐳

If you prefer Docker:

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

---

**Congratulations!** 🎊 Your Discord Music Bot is now running. Enjoy the music!# Quick Start Guide 🚀

This guide will get you up and running with the Discord Music Bot in under 5 minutes!

## Prerequisites Checklist ✅

Before starting, ensure you have:

- [ ] Python 3.8 or higher installed
- [ ] FFmpeg installed on your system
- [ ] A Discord account
- [ ] Basic command line knowledge

## Step 1: Create Your Discord Bot 🤖

1. **Visit Discord Developer Portal**

   - Go to https://discord.com/developers/applications
   - Log in with your Discord account

2. **Create New Application**

   - Click "New Application"
   - Name it (e.g., "My Music Bot")
   - Click "Create"

3. **Create Bot User**

   - Navigate to "Bot" in the left sidebar
   - Click "Add Bot"
   - Click "Yes, do it!"

4. **Configure Bot Settings**

   - Under "Privileged Gateway Intents", enable:
     - ✅ MESSAGE CONTENT INTENT
     - ✅ SERVER MEMBERS INTENT
   - Click "Save Changes"

5. **Copy Your Token**
   - Click "Reset Token"
   - Click "Copy" to copy your bot token
   - **Keep this token secret!**

## Step 2: Set Up the Bot Code 💻

### Option A: Using the Setup Script (Recommended)

```bash
# Clone the repository
git clone https://github.com/d-dziublenko/discord-audio-player.git
cd discord-audio-player

# Make setup script executable
chmod +x setup.sh

# Run setup script
./setup.sh
```

### Option B: Manual Setup

```bash
# Clone the repository
git clone https://github.com/d-dziublenko/discord-audio-player.git
cd discord-audio-player

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

## Step 3: Configure Your Bot 🔧

1. **Open `.env` file in a text editor**

   ```bash
   # Linux/macOS
   nano .env

   # Windows
   notepad .env
   ```

2. **Replace the placeholder with your bot token**

   ```
   DISCORD_TOKEN=your_actual_bot_token_here
   ```

3. **Save and close the file**

## Step 4: Invite Bot to Your Server 📨

1. **Generate Invite Link**

   - Go back to Discord Developer Portal
   - Select your application
   - Go to "OAuth2" → "URL Generator"
   - Select these scopes:
     - ✅ bot
   - Select these bot permissions:
     - ✅ View Channels
     - ✅ Send Messages
     - ✅ Embed Links
     - ✅ Connect
     - ✅ Speak
     - ✅ Use Voice Activity

2. **Copy and Use the Link**
   - Copy the generated URL
   - Paste it in your browser
   - Select your server
   - Click "Authorize"
