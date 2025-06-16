# Discord Music Bot 🎵

A feature-rich Discord music bot built with discord.py and yt-dlp that can play music from YouTube and other sources directly in your Discord server.

## Features ✨

- **Music Playback**: Stream music from YouTube and other supported platforms
- **Queue System**: Add multiple songs to queue with automatic playback
- **Playback Controls**: Play, pause, resume, skip, and stop functionality
- **Volume Control**: Adjust playback volume (1-100%)
- **Repeat Modes**: Support for repeat off, repeat one, and repeat all
- **Queue Management**: View, clear, remove, and shuffle the queue
- **Now Playing**: Display current song information with thumbnails
- **Auto-disconnect**: Leaves voice channel after 5 minutes of inactivity
- **Rich Embeds**: Beautiful embed messages for better user experience

## Commands 🎮

### Music Commands

- `!play <song/URL>` or `!p` - Play a song or add it to queue
- `!pause` - Pause the current song
- `!resume` - Resume the paused song
- `!skip` or `!s` - Skip the current song
- `!stop` or `!leave` or `!dc` - Stop playback and disconnect
- `!queue` or `!q` - Display the current queue
- `!np` or `!now` - Show currently playing song
- `!volume <1-100>` or `!vol` - Set playback volume
- `!repeat <off/one/all>` or `!loop` - Set repeat mode
- `!shuffle` - Shuffle the queue
- `!clear` - Clear the entire queue
- `!remove <position>` - Remove a song from queue

### Utility Commands

- `!join` or `!connect` - Connect bot to your voice channel
- `!ping` - Check bot latency
- `!stats` - Display bot statistics
- `!help` - Show all available commands
- `!invite` - Get bot invite link
- `!support` - Get support information

## Prerequisites 📋

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord Bot Token

## Installation 🚀

1. **Clone the repository**

   ```bash
   git clone https://github.com/d-dziublenko/discord-audio-player.git
   cd discord-audio-player
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install FFmpeg**

   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt update && sudo apt install ffmpeg`

5. **Set up your bot token**

   - Copy `.env.example` to `.env`
   - Replace `your_actual_bot_token_here` with your Discord bot token

   ```bash
   cp .env.example .env
   ```

6. **Run the bot**
   ```bash
   python main.py
   ```

## Creating a Discord Bot 🤖

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token and save it in your `.env` file
6. Under "Privileged Gateway Intents", enable:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
7. Go to OAuth2 → URL Generator
8. Select "bot" scope and these permissions:
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Connect
   - Speak
   - Use Voice Activity
9. Use the generated URL to invite your bot to servers

## Configuration ⚙️

The bot uses environment variables for configuration. Create a `.env` file based on `.env.example`:

```env
DISCORD_TOKEN=your_actual_bot_token_here
```

## Project Structure 📁

```
discord-audio-player/
├── main.py           # Bot initialization and basic commands
├── music_player.py   # Music functionality cog
├── requirements.txt  # Python dependencies
├── .env.example     # Environment variables template
├── .env             # Your environment variables (not in git)
├── .gitignore       # Git ignore file
└── README.md        # This file
```

## Troubleshooting 🔧

### Bot not playing music

- Ensure FFmpeg is properly installed and in PATH
- Check if the bot has proper permissions in the voice channel
- Verify your internet connection

### "This video is unavailable"

- The video might be age-restricted or region-locked
- Try a different video or URL

### Bot disconnecting randomly

- The bot auto-disconnects after 5 minutes of inactivity
- Check your internet connection stability

### High latency or stuttering

- Check your VPS/hosting server location
- Ensure sufficient bandwidth
- Try adjusting FFmpeg options in `music_player.py`

## Contributing 🤝

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- [discord.py](https://github.com/Rapptz/discord.py) - The Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FFmpeg](https://ffmpeg.org/) - Audio processing

## Support 💬

If you need help or have questions:

- Open an issue on GitHub

---

Made with ❤️ by DmytroDziublenko
