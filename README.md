# Discord Audio Player 🎵

A powerful Discord music bot built with discord.py that streams high-quality audio from YouTube and other platforms directly to your Discord server. This bot features a robust queue system, playback controls, and an intuitive command interface.

## ✨ Features

### Core Functionality

- **High-Quality Audio Streaming**: Stream music from YouTube and other supported platforms
- **Advanced Queue System**: Add multiple songs with automatic playback progression
- **Full Playback Control**: Play, pause, resume, skip, and stop functionality
- **Volume Management**: Precise volume control (1-100%)
- **Repeat Modes**: Support for off, single track, and queue repeat
- **Auto-disconnect**: Automatically leaves after 5 minutes of inactivity to save resources

### Queue Management

- View current queue with pagination
- Clear entire queue
- Remove specific songs
- Shuffle queue order
- Move songs within queue

### User Experience

- Rich embed messages with thumbnails and detailed information
- Now playing display with progress tracking
- Search functionality with interactive selection
- Save favorite songs to DMs
- Comprehensive help system

## 🎮 Commands

### Music Commands

| Command                 | Aliases             | Description                     | Example                         |
| ----------------------- | ------------------- | ------------------------------- | ------------------------------- |
| `!play <song/URL>`      | `!p`                | Play a song or add to queue     | `!play never gonna give you up` |
| `!pause`                | -                   | Pause current playback          | `!pause`                        |
| `!resume`               | -                   | Resume paused playback          | `!resume`                       |
| `!skip`                 | `!s`, `!next`       | Skip current song (with voting) | `!skip`                         |
| `!stop`                 | `!leave`, `!dc`     | Stop playback and disconnect    | `!stop`                         |
| `!queue`                | `!q`, `!playlist`   | Display current queue           | `!queue` or `!queue 2`          |
| `!np`                   | `!now`, `!current`  | Show now playing info           | `!np`                           |
| `!volume <1-100>`       | `!vol`, `!v`        | Adjust volume                   | `!volume 75`                    |
| `!repeat <off/one/all>` | `!loop`             | Set repeat mode                 | `!repeat all`                   |
| `!shuffle`              | `!mix`              | Shuffle the queue               | `!shuffle`                      |
| `!clear`                | `!cl`, `!empty`     | Clear entire queue              | `!clear`                        |
| `!remove <position>`    | `!rm`, `!delete`    | Remove song from queue          | `!remove 3`                     |
| `!move <from> <to>`     | `!mv`               | Move song in queue              | `!move 5 2`                     |
| `!search <query>`       | -                   | Search and select songs         | `!search lofi hip hop`          |
| `!save`                 | `!favorite`, `!fav` | Save current song to DMs        | `!save`                         |

### Utility Commands

| Command    | Description                       |
| ---------- | --------------------------------- |
| `!join`    | Connect bot to your voice channel |
| `!ping`    | Check bot latency                 |
| `!stats`   | Display bot statistics            |
| `!help`    | Show all commands                 |
| `!invite`  | Get bot invite link               |
| `!support` | Get support information           |
| `!about`   | About the bot                     |

## 📋 Prerequisites

Before installation, ensure you have:

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord bot token
- Basic command line knowledge

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/d-dziublenko/discord-audio-player.git
cd discord-audio-player
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install FFmpeg

- **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
- **Fedora**: `sudo dnf install ffmpeg`

### 4. Configure Bot Token

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your bot token
# DISCORD_TOKEN=your_actual_bot_token_here
```

### 5. Create Discord Application

1. Visit [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it
3. Navigate to "Bot" section
4. Click "Add Bot"
5. Enable these Privileged Gateway Intents:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT
6. Copy the bot token and add to `.env` file

### 6. Invite Bot to Server

1. In Discord Developer Portal, go to OAuth2 → URL Generator
2. Select scopes: `bot`
3. Select permissions:
   - View Channels
   - Send Messages
   - Embed Links
   - Connect
   - Speak
   - Use Voice Activity
4. Use generated URL to invite bot

### 7. Run the Bot

```bash
python main.py
```

## 🐳 Docker Deployment

For containerized deployment:

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ⚙️ Configuration

The bot can be configured through environment variables in the `.env` file:

```env
# Required
DISCORD_TOKEN=your_bot_token_here

# Optional
COMMAND_PREFIX=!              # Default command prefix
DEFAULT_VOLUME=0.5           # Default volume (0.0-1.0)
INACTIVITY_TIMEOUT=300       # Auto-disconnect timeout in seconds
MAX_SONG_DURATION=0          # Maximum song duration (0 = unlimited)
MAX_QUEUE_SIZE=0             # Maximum queue size (0 = unlimited)
AUDIO_BITRATE=192            # Audio quality in kbps
```

## 📁 Project Structure

```
discord-audio-player/
├── main.py                  # Bot initialization and core commands
├── music_player.py          # Music functionality and queue management
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development dependencies
├── .env.example            # Environment configuration template
├── .env                    # Your configuration (not in git)
├── .gitignore              # Git ignore rules
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker compose configuration
├── .dockerignore           # Docker ignore rules
├── setup.sh                # Automated setup script
├── README.md               # This file (main documentation)
├── QUICKSTART.md           # Quick start guide
├── CONTRIBUTING.md         # Contribution guidelines
├── FAQ.md                  # Frequently asked questions
├── SECURITY.md             # Security policy and guidelines
├── LICENSE                 # AGPL-3.0 license file
├── tests/                  # Test suite
│   └── test_music_player.py    # Unit tests for music functionality
├── .github/                # GitHub specific files
│   ├── workflows/              # GitHub Actions
│   │   └── ci.yml                 # CI/CD pipeline configuration
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   │   ├── bug_report.md          # Bug report template
│   │   └── feature_request.md     # Feature request template
│   └── pull_request_template.md   # PR template
├── logs/                   # Log files directory (created at runtime)
├── downloads/              # Temporary download cache (created at runtime)
└── venv/                   # Virtual environment (not in git)
```

## 🔧 Troubleshooting

### Bot Not Playing Music

- Ensure FFmpeg is installed and in PATH
- Check bot has proper voice channel permissions
- Verify internet connection stability

### "Video Unavailable" Error

- Video may be age-restricted or region-locked
- Try a different video or search query
- Check if video is private/deleted

### High CPU Usage

- Audio processing is CPU-intensive
- Consider using a server closer to Discord
- Limit concurrent voice connections

### Bot Disconnecting

- Check the inactivity timeout setting
- Ensure stable internet connection
- Verify bot has proper permissions

For more detailed troubleshooting, see [FAQ.md](FAQ.md).

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Get running in 5 minutes
- [FAQ](FAQ.md) - Frequently asked questions
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Security Policy](SECURITY.md) - Security guidelines

## 🔒 Security

For security concerns, please review our [Security Policy](SECURITY.md). Never commit tokens or sensitive data.

## 📄 License

This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Media extractor
- [FFmpeg](https://ffmpeg.org/) - Audio processing
- All contributors and users of this bot

## 💬 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/d-dziublenko/discord-audio-player/issues)
- **Documentation**: Check the [FAQ](FAQ.md) and other docs
- **Discord**: Join our community (link in bot's `!support` command)

## 👨‍💻 Author

**Dmytro Dziublenko**

- GitHub: [@d-dziublenko](https://github.com/d-dziublenko)
- Repository: [discord-audio-player](https://github.com/d-dziublenko/discord-audio-player)

---

<div align="center">
  
**If you find this bot useful, please consider giving it a ⭐ star on GitHub!**

Made with ❤️ by Dmytro Dziublenko

</div>
