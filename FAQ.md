# Frequently Asked Questions (FAQ) ❓

## General Questions

### Q: Is this bot free to use?

**A:** Yes! This bot is completely free and open source under the AGPL-3.0 license. You can host it yourself at no cost (except for any hosting fees if you choose to use a VPS).

### Q: Can I modify the bot for my server?

**A:** Absolutely! The code is open source. Feel free to fork it and customize it to your needs. Just remember to comply with the AGPL-3.0 license.

### Q: How many servers can the bot be in?

**A:** There's no hard limit imposed by the bot itself. The limit depends on your hosting resources and Discord's rate limits. A single instance can easily handle dozens of servers.

### Q: Does the bot store any data?

**A:** No, the bot doesn't store any persistent data. All queue information is kept in memory and is lost when the bot restarts.

## Setup Issues

### Q: I get "discord.errors.LoginFailure: Improper token has been passed"

**A:** This means your bot token is incorrect. Make sure:

- You copied the entire token from Discord Developer Portal
- There are no extra spaces or quotes in your `.env` file
- You're using the bot token, not the client ID or secret

### Q: The bot is online but doesn't respond to commands

**A:** Check these things:

1. Ensure the bot has "Read Messages" and "Send Messages" permissions
2. Make sure you enabled "MESSAGE CONTENT INTENT" in Discord Developer Portal
3. Verify you're using the correct prefix (default is `!`)
4. Check that commands are being sent in a server, not DMs

### Q: I get "No module named 'discord'"

**A:** You need to install the requirements:

```bash
pip install -r requirements.txt
```

### Q: How do I keep the bot running 24/7?

**A:** Several options:

- Use a VPS (Virtual Private Server) like DigitalOcean, Linode, or AWS
- Use a free hosting service like Railway or Fly.io (with limitations)
- Use a Raspberry Pi at home
- Use PM2 or systemd to auto-restart on crashes

## Music Playback Issues

### Q: The bot joins the voice channel but no sound plays

**A:** Common causes:

1. **FFmpeg not installed properly** - Test with `ffmpeg -version` in terminal
2. **Bot doesn't have "Speak" permission** in the voice channel
3. **Volume is set to 0** - Try `!volume 50`
4. **Firewall blocking Discord voice** - Check your server's firewall rules

### Q: "This video is unavailable" error

**A:** This happens when:

- The video is age-restricted (bot can't access these)
- The video is region-locked to a different country than your server
- The video was deleted or made private
- YouTube is blocking the bot's IP (try a VPN on your server)

### Q: Music stops playing after a while

**A:** The bot has a 5-minute inactivity timeout. If nothing is playing and the queue is empty for 5 minutes, it disconnects automatically to save resources.

### Q: Can the bot play Spotify links?

**A:** No, the bot can't directly play Spotify links due to Spotify's restrictions. However, you can:

- Search for the song name instead: `!play song name by artist`
- Copy the song title from Spotify and use it with the play command

### Q: Why is there a delay before music starts?

**A:** The bot needs to:

1. Search YouTube for your query
2. Extract the audio stream URL
3. Connect to Discord voice
4. Start streaming

This usually takes 2-5 seconds depending on your server's internet speed.

## Feature Questions

### Q: Can I change the command prefix?

**A:** Yes! In `main.py`, find this line:

```python
command_prefix='!',
```

Change it to your preferred prefix, like `'?'`, `'.'`, or `'music!'`

### Q: How do I add custom commands?

**A:** Add new commands in `main.py` or create a new cog. Example:

```python
@bot.command(name='hello')
async def hello(ctx):
    await ctx.send(f'Hello {ctx.author.mention}!')
```

### Q: Can the bot play local files?

**A:** Not by default, but you can modify it to play local files by:

1. Uploading files to a specific directory
2. Modifying the play command to check for local files
3. Using `discord.FFmpegPCMAudio('path/to/file.mp3')`

### Q: Is there a song limit for the queue?

**A:** No hard limit, but extremely long queues (1000+ songs) might cause:

- High memory usage
- Slower queue command response
- Longer bot startup time after crashes

### Q: Can multiple people control the bot?

**A:** Yes, by default anyone can use commands. To restrict access:

- Use Discord's role-based permissions
- Add permission checks to commands
- Create DJ-only commands

## Performance & Hosting

### Q: What are the minimum server requirements?

**A:** Minimum specs:

- **RAM:** 512MB (1GB recommended)
- **CPU:** 1 vCPU
- **Storage:** 1GB
- **Network:** Stable connection with at least 1Mbps
- **OS:** Linux (Ubuntu recommended), Windows, or macOS

### Q: Why does the bot use so much CPU?

**A:** Audio processing is CPU-intensive. To reduce usage:

- Use a server closer to Discord's servers
- Limit the number of concurrent voice connections
- Use a more powerful server
- Optimize FFmpeg settings

### Q: Can I run multiple bot instances?

**A:** Yes, but:

- Each needs a unique bot token
- Use different prefixes to avoid confusion
- Consider using one instance with multiple guild support instead

## Troubleshooting Commands

### Q: How do I debug issues?

**A:** Enable debug logging by adding to `main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Q: The bot crashes with no error

**A:** Common causes:

1. **Out of memory** - Check with `free -m` on Linux
2. **FFmpeg crash** - Update FFmpeg to latest version
3. **Network issues** - Check your internet connection
4. **Discord API issues** - Check Discord's status page

### Q: How do I see what version I'm running?

**A:** Add a version command:

```python
@bot.command(name='version')
async def version(ctx):
    await ctx.send('Bot Version: 1.0.0')
```

## Advanced Questions

### Q: Can I add a web dashboard?

**A:** Yes, you could add a web dashboard using:

- Flask/FastAPI for the backend
- discord.py's IPC for communication
- React/Vue for the frontend

### Q: How do I add playlist support?

**A:** You can modify the `play` command to:

1. Detect playlist URLs
2. Extract all video IDs
3. Add each to the queue
4. Be careful of rate limits

### Q: Can the bot stream live content?

**A:** Yes, but with limitations:

- Live streams work but can't be seeked
- No duration information available
- May cut out if stream has issues
- Higher bandwidth usage

## Community & Support

### Q: Where can I get help?

**A:** Several places:

1. Open an issue on GitHub
2. Check existing issues for solutions
3. Read the documentation thoroughly
4. Ask in Discord.py community

### Q: How can I contribute?

**A:** Welcome contributions!

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request
5. See [CONTRIBUTING.md](CONTRIBUTING.md) for details

### Q: I found a security vulnerability

**A:** Please don't post it publicly! Instead:

1. Email us at [security email]
2. Include details and steps to reproduce
3. Wait for our response before disclosure
4. See [SECURITY.md](SECURITY.md) for more info

---

**Still have questions?** Open an issue on GitHub and we'll add it to this FAQ!
