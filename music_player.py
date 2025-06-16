import discord
from discord.ext import commands
import asyncio
import itertools
import sys
import traceback
from functools import partial
import yt_dlp as youtube_dl
from typing import Optional
import datetime

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# Updated options for yt-dlp (youtube-dl successor)
ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    'force-ipv4': True,
    'preferredcodec': 'mp3',
    'preferredquality': '192',
}

# FFmpeg options for better audio quality
ffmpegopts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):
    """Audio source class for youtube-dl"""
    
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester
        
        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')
        self.thumbnail = data.get('thumbnail')
        self.uploader = data.get('uploader')

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict."""
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        """Create an audio source from search query or URL"""
        loop = loop or asyncio.get_event_loop()
        
        # Extract info from youtube
        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)
        
        if 'entries' in data:
            # Take first item from a playlist
            data = data['entries'][0]
        
        # Create embed for queue notification
        embed = discord.Embed(
            title="Added to queue",
            description=f"[{data['title']}]({data['webpage_url']})",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=data.get('thumbnail', ''))
        embed.add_field(name="Duration", value=cls.format_duration(data.get('duration', 0)))
        embed.add_field(name="Requested by", value=ctx.author.mention)
        embed.add_field(name="Uploader", value=data.get('uploader', 'Unknown'))
        
        await ctx.send(embed=embed)
        
        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 
                   'thumbnail': data.get('thumbnail'), 'duration': data.get('duration', 0), 
                   'uploader': data.get('uploader', 'Unknown')}
        
        return cls(discord.FFmpegPCMAudio(source, **ffmpegopts), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']
        
        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)
        
        return cls(discord.FFmpegPCMAudio(data['url'], **ffmpegopts), data=data, requester=requester)
    
    @staticmethod
    def format_duration(duration):
        """Format duration in seconds to readable format"""
        if not duration:
            return "Unknown"
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


class MusicPlayer:
    """Music player class for each guild"""
    
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 
                 'volume', 'repeat_mode', '_task')
    
    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog
        
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        
        self.np = None  # Now playing message
        self.volume = 0.5
        self.current = None
        self.repeat_mode = 'off'  # off, one, all
        
        self._task = ctx.bot.loop.create_task(self.player_loop())
    
    async def player_loop(self):
        """Main player loop."""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.next.clear()
            
            try:
                # Wait for the next song with timeout
                async with asyncio.timeout(300):  # 5 minutes
                    if self.repeat_mode == 'one' and self.current:
                        # Re-create the same source for repeat one
                        source = await YTDLSource.regather_stream(self.current, loop=self.bot.loop)
                    else:
                        source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)
            
            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n```css\n[{e}]\n```')
                    continue
            
            source.volume = self.volume
            self.current = source
            
            # Play the song
            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            
            # Send now playing embed
            embed = discord.Embed(
                title="Now playing",
                description=f"[{source.title}]({source.web_url})",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=source.thumbnail or '')
            embed.add_field(name="Duration", value=YTDLSource.format_duration(source.duration))
            embed.add_field(name="Requested by", value=source.requester.mention)
            embed.add_field(name="Uploader", value=source.uploader)
            
            self.np = await self._channel.send(embed=embed)
            
            # Wait for the song to finish
            await self.next.wait()
            
            # Cleanup
            source.cleanup()
            
            # Handle repeat all mode
            if self.repeat_mode == 'all':
                await self.queue.put(self.current)
            
            self.current = None
    
    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Music related commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
    
    async def cleanup(self, guild):
        """Cleanup player and disconnect"""
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass
        
        try:
            del self.players[guild.id]
        except KeyError:
            pass
    
    async def cog_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True
    
    async def cog_command_error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. Please make sure you are in a valid channel.')
        
        print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
    
    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player
        
        return player
    
    @commands.command(name='join', aliases=['connect', 'j'], description="Connect to voice channel")
    async def connect_(self, ctx, *, channel: discord.VoiceChannel = None):
        """Connect to voice channel"""
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(
                    title="Error",
                    description="No channel to join. Please join a voice channel first.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join.')
        
        vc = ctx.voice_client
        
        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        
        await ctx.send(f'Connected to: **{channel}**')
    
    @commands.command(name='play', aliases=['sing', 'p'], description="Play a song")
    async def play_(self, ctx, *, search: str):
        """Request a song and add it to the queue."""
        async with ctx.typing():
            vc = ctx.voice_client
            
            if not vc:
                await ctx.invoke(self.connect_)
            
            player = self.get_player(ctx)
            
            # Create the source
            source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)
            
            await player.queue.put(source)
    
    @commands.command(name='pause', description="Pause the current song")
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_playing():
            embed = discord.Embed(
                title="Error",
                description="I am not currently playing anything!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return
        
        vc.pause()
        await ctx.send("⏸️ Paused")
    
    @commands.command(name='resume', description="Resume the current song")
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return
        
        vc.resume()
        await ctx.send("▶️ Resumed")
    
    @commands.command(name='skip', aliases=['s'], description="Skip the current song")
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        
        vc.stop()
        await ctx.send("⏭️ Skipped")
    
    @commands.command(name='repeat', aliases=['loop'], description="Set repeat mode")
    async def repeat_(self, ctx, mode: str = None):
        """Set repeat mode (off/one/all)"""
        if mode is None:
            await ctx.send("Usage: !repeat [off/one/all]")
            return
        
        mode = mode.lower()
        if mode not in ['off', 'one', 'all']:
            await ctx.send("Invalid mode! Use: off, one, or all")
            return
        
        player = self.get_player(ctx)
        player.repeat_mode = mode
        
        if mode == 'off':
            await ctx.send("🔁 Repeat mode: OFF")
        elif mode == 'one':
            await ctx.send("🔂 Repeat mode: ONE")
        else:
            await ctx.send("🔁 Repeat mode: ALL")
    
    @commands.command(name='queue', aliases=['q', 'playlist'], description="Show the queue")
    async def queue_info(self, ctx):
        """Display the current queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(
                title="Queue",
                description="The queue is empty.",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        # Get upcoming songs
        upcoming = list(itertools.islice(player.queue._queue, 0, 10))
        
        fmt = '\n'.join(f'**{i+1}.** [{song["title"]}]({song["webpage_url"]}) | `{YTDLSource.format_duration(song.get("duration", 0))}` | {song["requester"].mention}' 
                       for i, song in enumerate(upcoming))
        
        embed = discord.Embed(
            title=f'Queue for {ctx.guild.name}',
            description=fmt,
            color=discord.Color.green()
        )
        
        if player.current:
            embed.add_field(
                name="Now Playing",
                value=f'[{vc.source.title}]({vc.source.web_url}) | `{YTDLSource.format_duration(vc.source.duration)}` | {vc.source.requester.mention}',
                inline=False
            )
        
        embed.set_footer(text=f'{len(upcoming)} songs in queue | Repeat: {player.repeat_mode.upper()}')
        
        await ctx.send(embed=embed)
    
    @commands.command(name='np', aliases=['now', 'current'], description="Show the current song")
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(
                title="Error",
                description="I'm not currently playing anything!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="Now Playing",
            description=f"[{vc.source.title}]({vc.source.web_url})",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=player.current.thumbnail or '')
        embed.add_field(name="Duration", value=YTDLSource.format_duration(player.current.duration))
        embed.add_field(name="Requested by", value=player.current.requester.mention)
        embed.add_field(name="Uploader", value=player.current.uploader)
        embed.add_field(name="Repeat Mode", value=player.repeat_mode.upper())
        
        await ctx.send(embed=embed)
    
    @commands.command(name='volume', aliases=['vol', 'v'], description="Change volume")
    async def change_volume(self, ctx, *, vol: float = None):
        """Change the player volume (1-100)."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if vol is None:
            embed = discord.Embed(
                title="Current Volume",
                description=f"🔊 **{int((vc.source.volume if vc.source else 0.5) * 100)}%**",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        if not 0 < vol < 101:
            embed = discord.Embed(
                title="Error",
                description="Please enter a value between 1 and 100.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        
        if vc.source:
            vc.source.volume = vol / 100
        
        player.volume = vol / 100
        await ctx.send(f'🔊 Volume set to **{vol}%**')
    
    @commands.command(name='clear', aliases=['cl'], description="Clear the queue")
    async def clear_(self, ctx):
        """Clear the entire queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('💥 Queue cleared!')
    
    @commands.command(name='remove', aliases=['rm'], description="Remove a song from queue")
    async def remove_(self, ctx, index: int):
        """Remove a specific song from queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        try:
            if index < 1:
                await ctx.send("Index must be greater than 0!")
                return
            
            removed = player.queue._queue[index - 1]
            del player.queue._queue[index - 1]
            
            embed = discord.Embed(
                title="Removed from queue",
                description=f"[{removed['title']}]({removed['webpage_url']})",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
        except IndexError:
            await ctx.send(f"No song at position {index}!")
    
    @commands.command(name='shuffle', description="Shuffle the queue")
    async def shuffle_(self, ctx):
        """Shuffle the current queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(
                title="Error",
                description="The queue is empty!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Shuffle the queue
        import random
        random.shuffle(player.queue._queue)
        
        await ctx.send('🔀 Queue shuffled!')
    
    @commands.command(name='leave', aliases=['disconnect', 'dc', 'stop'], description="Disconnect from voice")
    async def leave_(self, ctx):
        """Stop the music and disconnect from voice."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Error",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        await self.cleanup(ctx.guild)
        await ctx.send('👋 Disconnected!')


# Helper function to setup the cog
async def setup(bot):
    await bot.add_cog(Music(bot))