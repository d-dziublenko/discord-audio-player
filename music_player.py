import discord
from discord.ext import commands
import asyncio
import itertools
import sys
import traceback
import logging
import os
import time
import random
from functools import partial
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import yt_dlp as youtube_dl

# Set up logging for this module
logger = logging.getLogger('discord_bot.music')

# Load configuration from environment variables
DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.5'))
MAX_SONG_DURATION = int(os.getenv('MAX_SONG_DURATION', '0'))  # 0 means no limit
INACTIVITY_TIMEOUT = int(os.getenv('INACTIVITY_TIMEOUT', '300'))  # 5 minutes default
MAX_QUEUE_SIZE = int(os.getenv('MAX_QUEUE_SIZE', '0'))  # 0 means no limit
AUDIO_BITRATE = int(os.getenv('AUDIO_BITRATE', '192'))
FORCE_IPV4 = os.getenv('FORCE_IPV4', 'true').lower() == 'true'

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# Enhanced yt-dlp options with better error handling and quality settings
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
    'default_search': 'ytsearch',  # Use YouTube search by default
    'source_address': '0.0.0.0' if FORCE_IPV4 else None,
    'preferredcodec': 'mp3',
    'preferredquality': str(AUDIO_BITRATE),
    # Additional options for better reliability
    'retries': 3,
    'fragment-retries': 3,
    'skip-unavailable-fragments': True,
    'keepvideo': False,
    'buffersize': 1024,
    # Cookie support for age-restricted videos (if configured)
    'cookiefile': os.getenv('YOUTUBE_COOKIES_FILE') if os.getenv('YOUTUBE_COOKIES_FILE') else None,
}

# Force IPv4 if enabled
if FORCE_IPV4:
    ytdlopts['force-ipv4'] = True

# Enhanced FFmpeg options for better audio quality and stability
ffmpegopts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': f'-vn -ab {AUDIO_BITRATE}k'
}

# Create yt-dlp instance with our options
ytdl = youtube_dl.YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):
    """Enhanced audio source class with better error handling and metadata"""
    
    def __init__(self, source, *, data, requester):
        self.original = source

        super().__init__(source)
        self.requester = requester
        
        # Extract all available metadata
        self.title = data.get('title', 'Unknown Title')
        self.web_url = data.get('webpage_url', '')
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail', '')
        self.uploader = data.get('uploader', 'Unknown')
        self.uploader_url = data.get('uploader_url', '')
        self.upload_date = data.get('upload_date', '')
        self.description = data.get('description', '')
        self.view_count = data.get('view_count', 0)
        self.like_count = data.get('like_count', 0)
        self.stream_url = data.get('url', '')
        
        # Set initial volume
        self.volume = DEFAULT_VOLUME

    def __del__(self):
        try:
            self.cleanup()
        except Exception:
            pass

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict."""
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        """Create an audio source from search query or URL with enhanced error handling"""
        loop = loop or asyncio.get_event_loop()
        
        # Notify user that we're processing their request
        embed = discord.Embed(
            title="Processing request...",
            description=f"🔍 Searching for: `{search}`",
            color=discord.Color.orange()
        )
        processing_msg = await ctx.send(embed=embed)
        
        try:
            # Extract info from youtube
            to_run = partial(ytdl.extract_info, url=search, download=download)
            data = await loop.run_in_executor(None, to_run)
        except Exception as e:
            await processing_msg.delete()
            
            # Handle specific yt-dlp errors with user-friendly messages
            error_msg = str(e).lower()
            if 'video unavailable' in error_msg:
                raise commands.CommandError('This video is unavailable. It might be private, deleted, or region-locked.')
            elif 'age-restricted' in error_msg or 'sign in' in error_msg:
                raise commands.CommandError('This video is age-restricted. I cannot play age-restricted content.')
            elif 'copyright' in error_msg:
                raise commands.CommandError('This video has been blocked due to copyright claims.')
            elif 'no video formats' in error_msg:
                raise commands.CommandError('No playable audio format found for this video.')
            else:
                logger.error(f"Error extracting video info: {e}")
                raise commands.CommandError(f'An error occurred while searching: {str(e)}')
        
        if 'entries' in data:
            # Take first item from a playlist/search result
            data = data['entries'][0]
        
        # Check duration limit if configured
        if MAX_SONG_DURATION > 0 and data.get('duration', 0) > MAX_SONG_DURATION:
            await processing_msg.delete()
            max_duration_str = cls.format_duration(MAX_SONG_DURATION)
            raise commands.CommandError(f'Song is too long! Maximum duration allowed is {max_duration_str}')
        
        # Delete processing message
        await processing_msg.delete()
        
        # Create detailed embed for queue notification
        embed = discord.Embed(
            title="✅ Added to queue",
            description=f"[{data['title']}]({data['webpage_url']})",
            color=discord.Color.green()
        )
        
        # Add thumbnail if available
        if data.get('thumbnail'):
            embed.set_thumbnail(url=data['thumbnail'])
        
        # Add detailed information
        embed.add_field(name="Duration", value=cls.format_duration(data.get('duration', 0)), inline=True)
        embed.add_field(name="Uploader", value=data.get('uploader', 'Unknown'), inline=True)
        embed.add_field(name="Requested by", value=ctx.author.mention, inline=True)
        
        # Add view count if available
        if data.get('view_count'):
            view_count = f"{data['view_count']:,}"
            embed.add_field(name="Views", value=view_count, inline=True)
        
        # Add upload date if available
        if data.get('upload_date'):
            try:
                upload_date = datetime.strptime(data['upload_date'], '%Y%m%d')
                embed.add_field(name="Uploaded", value=upload_date.strftime('%Y-%m-%d'), inline=True)
            except:
                pass
        
        await ctx.send(embed=embed)
        
        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title'], 
                   'thumbnail': data.get('thumbnail'), 'duration': data.get('duration', 0), 
                   'uploader': data.get('uploader', 'Unknown'), 'data': data}
        
        return cls(discord.FFmpegPCMAudio(source, **ffmpegopts), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream with better error handling"""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']
        
        try:
            to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
            processed_data = await loop.run_in_executor(None, to_run)
        except Exception as e:
            logger.error(f"Error regathering stream: {e}")
            raise commands.CommandError(f'Error loading audio stream: {str(e)}')
        
        return cls(discord.FFmpegPCMAudio(processed_data['url'], **ffmpegopts), 
                  data=processed_data, requester=requester)
    
    @staticmethod
    def format_duration(duration):
        """Format duration in seconds to readable format"""
        if not duration:
            return "🔴 Live"
        
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


class MusicPlayer:
    """Enhanced music player class with better queue management and features"""
    
    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 
                 'volume', 'repeat_mode', '_task', 'skip_votes', 'audio_player', 
                 'start_time', 'pause_time', 'total_paused')
    
    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog
        
        self.queue = asyncio.Queue()
        self.next = asyncio.Event()
        
        self.np = None  # Now playing message
        self.volume = DEFAULT_VOLUME
        self.current = None
        self.repeat_mode = 'off'  # off, one, all
        self.skip_votes = set()  # Track skip votes
        
        # Timing tracking for current position
        self.start_time = None
        self.pause_time = None
        self.total_paused = 0
        
        self._task = ctx.bot.loop.create_task(self.player_loop())
    
    async def player_loop(self):
        """Main player loop with enhanced error handling and logging"""
        await self.bot.wait_until_ready()
        
        while not self.bot.is_closed():
            self.next.clear()
            self.skip_votes.clear()  # Clear skip votes for new song
            
            try:
                # Wait for the next song with timeout
                async with asyncio.timeout(INACTIVITY_TIMEOUT):
                    if self.repeat_mode == 'one' and self.current:
                        # Re-create the same source for repeat one
                        source = await YTDLSource.regather_stream(self.current, loop=self.bot.loop)
                    else:
                        source = await self.queue.get()
            except asyncio.TimeoutError:
                logger.info(f"Player timeout in guild {self._guild.name}")
                return self.destroy(self._guild)
            except Exception as e:
                logger.error(f"Error in player loop: {e}")
                await self._channel.send(f'An error occurred in the player: {str(e)}')
                continue
            
            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    logger.error(f"Error processing song: {e}")
                    await self._channel.send(f'There was an error processing your song.\n```css\n[{e}]\n```')
                    continue
            
            source.volume = self.volume
            self.current = source
            
            # Track timing
            self.start_time = time.time()
            self.pause_time = None
            self.total_paused = 0
            
            # Play the song
            self._guild.voice_client.play(
                source, 
                after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set)
            )
            
            # Send now playing embed with enhanced information
            embed = discord.Embed(
                title="🎵 Now playing",
                description=f"[{source.title}]({source.web_url})",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=source.thumbnail or '')
            
            # Add fields
            fields = [
                ("Duration", YTDLSource.format_duration(source.duration), True),
                ("Requested by", source.requester.mention, True),
                ("Uploader", f"[{source.uploader}]({source.uploader_url})" if source.uploader_url else source.uploader, True),
                ("Volume", f"{int(source.volume * 100)}%", True),
                ("Repeat", self.repeat_mode.upper(), True),
                ("Queue", f"{self.queue.qsize()} songs", True)
            ]
            
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)
            
            # Add progress bar (placeholder for live updates)
            if source.duration:
                embed.add_field(
                    name="Progress",
                    value=f"```[{'─' * 30}] 0:00 / {YTDLSource.format_duration(source.duration)}```",
                    inline=False
                )
            
            self.np = await self._channel.send(embed=embed)
            
            # Wait for the song to finish
            await self.next.wait()
            
            # Cleanup
            source.cleanup()
            
            # Delete now playing message
            try:
                await self.np.delete()
            except discord.HTTPException:
                pass
            
            # Handle repeat all mode
            if self.repeat_mode == 'all':
                await self.queue.put(self.current)
            
            self.current = None
    
    def get_current_position(self):
        """Get current playback position in seconds"""
        if not self.start_time or not self.current:
            return 0
        
        if self.pause_time:
            # Currently paused
            return self.pause_time - self.start_time - self.total_paused
        else:
            # Currently playing
            return time.time() - self.start_time - self.total_paused
    
    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Enhanced music cog with more features and better error handling"""
    
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
        
        # Track statistics
        self.songs_played = 0
        self.total_duration = 0
    
    async def cleanup(self, guild):
        """Enhanced cleanup with logging"""
        logger.info(f"Cleaning up player in guild {guild.name}")
        
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
    
    async def cog_before_invoke(self, ctx):
        """Called before any command in this cog"""
        # Ensure the user is in a voice channel for voice commands
        voice_commands = ['play', 'join', 'pause', 'resume', 'skip', 'stop', 'volume']
        if ctx.command.name in voice_commands and not ctx.author.voice:
            raise commands.CommandError('You need to be in a voice channel to use this command!')
    
    async def cog_command_error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. Please make sure you are in a valid channel.')
        elif isinstance(error, commands.CommandError):
            await ctx.send(str(error))
        else:
            logger.error(f'Error in music command {ctx.command}: {error}', exc_info=error)
    
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
                    title="No channel to join",
                    description="Please join a voice channel or specify one.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join.')
        
        vc = ctx.voice_client
        
        if vc:
            if vc.channel.id == channel.id:
                embed = discord.Embed(
                    title="Already connected",
                    description=f"I'm already in {channel.mention}!",
                    color=discord.Color.orange()
                )
                return await ctx.send(embed=embed)
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        
        embed = discord.Embed(
            title="Connected",
            description=f"Connected to {channel.mention}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='play', aliases=['sing', 'p'], description="Play a song")
    @commands.cooldown(1, 3, commands.BucketType.user)  # Prevent spam
    async def play_(self, ctx, *, search: str):
        """Request a song and add it to the queue."""
        async with ctx.typing():
            vc = ctx.voice_client
            
            if not vc:
                await ctx.invoke(self.connect_)
            
            player = self.get_player(ctx)
            
            # Check queue size limit
            if MAX_QUEUE_SIZE > 0 and player.queue.qsize() >= MAX_QUEUE_SIZE:
                embed = discord.Embed(
                    title="Queue Full",
                    description=f"The queue is full! Maximum size is {MAX_QUEUE_SIZE} songs.",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            # Create the source
            try:
                source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)
            except commands.CommandError as e:
                await ctx.send(f"❌ {str(e)}")
                return
            
            # Add to queue
            await player.queue.put(source)
            
            # Update statistics
            self.songs_played += 1
            if source.get('duration'):
                self.total_duration += source['duration']
    
    @commands.command(name='pause', description="Pause the current song")
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_playing():
            embed = discord.Embed(
                title="Nothing playing",
                description="I am not currently playing anything!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            embed = discord.Embed(
                title="Already paused",
                description="The player is already paused!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        vc.pause()
        player = self.get_player(ctx)
        if player:
            player.pause_time = time.time()
        
        embed = discord.Embed(
            title="Paused",
            description="⏸️ Playback paused",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='resume', description="Resume the current song")
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            embed = discord.Embed(
                title="Not paused",
                description="The player is not paused!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        vc.resume()
        player = self.get_player(ctx)
        if player and player.pause_time:
            player.total_paused += time.time() - player.pause_time
            player.pause_time = None
        
        embed = discord.Embed(
            title="Resumed",
            description="▶️ Playback resumed",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='skip', aliases=['s', 'next'], description="Skip the current song")
    async def skip_(self, ctx):
        """Skip the song with voting system for non-admins"""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return
        
        player = self.get_player(ctx)
        
        # Check if user has DJ permissions or is alone with bot
        voter = ctx.message.author
        voice_members = len([m for m in voter.voice.channel.members if not m.bot])
        
        # If user is alone with bot or has manage_channels permission, skip immediately
        if voice_members <= 1 or ctx.author.guild_permissions.manage_channels:
            vc.stop()
            embed = discord.Embed(
                title="Skipped",
                description=f"⏭️ Skipped by {ctx.author.mention}",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            # Voting system
            player.skip_votes.add(voter.id)
            total_votes = len(player.skip_votes)
            
            # Calculate required votes (50% of voice members)
            required_votes = voice_members // 2 + 1
            
            if total_votes >= required_votes:
                vc.stop()
                embed = discord.Embed(
                    title="Skipped",
                    description=f"⏭️ Vote skip passed! ({total_votes}/{required_votes})",
                    color=discord.Color.green()
                )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Vote Skip",
                    description=f"Skip vote added: **{total_votes}/{required_votes}**",
                    color=discord.Color.orange()
                )
                embed.add_field(
                    name="Already voted",
                    value=', '.join([f"<@{user_id}>" for user_id in player.skip_votes]),
                    inline=False
                )
                await ctx.send(embed=embed)
    
    @commands.command(name='repeat', aliases=['loop'], description="Set repeat mode")
    async def repeat_(self, ctx, mode: str = None):
        """Set repeat mode (off/one/all)"""
        if mode is None:
            player = self.get_player(ctx)
            embed = discord.Embed(
                title="Repeat Mode",
                description=f"Current repeat mode: **{player.repeat_mode.upper()}**\n"
                           f"Usage: `{ctx.prefix}repeat [off/one/all]`",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        mode = mode.lower()
        if mode not in ['off', 'one', 'all']:
            embed = discord.Embed(
                title="Invalid Mode",
                description="Please use: `off`, `one`, or `all`",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        player.repeat_mode = mode
        
        # Emoji based on mode
        emoji = {'off': '➡️', 'one': '🔂', 'all': '🔁'}[mode]
        
        embed = discord.Embed(
            title="Repeat Mode Changed",
            description=f"{emoji} Repeat mode set to: **{mode.upper()}**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='queue', aliases=['q', 'playlist'], description="Show the queue")
    async def queue_info(self, ctx, page: int = 1):
        """Display the current queue with pagination"""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(
                title="📋 Queue",
                description="The queue is empty.",
                color=discord.Color.orange()
            )
            
            # Add currently playing if exists
            if player.current:
                embed.add_field(
                    name="Now Playing",
                    value=f'[{vc.source.title}]({vc.source.web_url}) | `{YTDLSource.format_duration(vc.source.duration)}` | {vc.source.requester.mention}',
                    inline=False
                )
            
            return await ctx.send(embed=embed)
        
        # Calculate pagination
        items_per_page = 10
        pages = (player.queue.qsize() - 1) // items_per_page + 1
        
        if page < 1:
            page = 1
        elif page > pages:
            page = pages
        
        start = (page - 1) * items_per_page
        end = start + items_per_page
        
        # Get queue items
        queue_list = list(itertools.islice(player.queue._queue, 0, player.queue.qsize()))
        current_page_items = queue_list[start:end]
        
        # Format queue items
        queue_text = []
        for idx, song in enumerate(current_page_items, start=start+1):
            duration = YTDLSource.format_duration(song.get('duration', 0))
            queue_text.append(f'**{idx}.** [{song["title"]}]({song["webpage_url"]}) | `{duration}` | {song["requester"].mention}')
        
        embed = discord.Embed(
            title=f'📋 Queue for {ctx.guild.name}',
            description='\n'.join(queue_text),
            color=discord.Color.green()
        )
        
        # Add currently playing
        if player.current:
            current_pos = player.get_current_position()
            progress = f"{YTDLSource.format_duration(int(current_pos))}/{YTDLSource.format_duration(vc.source.duration)}"
            embed.add_field(
                name="Now Playing",
                value=f'[{vc.source.title}]({vc.source.web_url}) | `{progress}` | {vc.source.requester.mention}',
                inline=False
            )
        
        # Add footer with page info and stats
        total_duration = sum(song.get('duration', 0) for song in queue_list)
        embed.set_footer(
            text=f'Page {page}/{pages} | {player.queue.qsize()} songs | '
                 f'Total duration: {YTDLSource.format_duration(total_duration)} | '
                 f'Repeat: {player.repeat_mode.upper()}'
        )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='np', aliases=['now', 'current', 'nowplaying'], description="Show the current song")
    async def now_playing_(self, ctx):
        """Display detailed information about the currently playing song"""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(
                title="Nothing playing",
                description="I'm not currently playing anything!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Calculate progress
        current_pos = player.get_current_position()
        duration = player.current.duration
        
        # Create progress bar
        if duration > 0:
            progress_percent = current_pos / duration
            filled_blocks = int(progress_percent * 30)
            empty_blocks = 30 - filled_blocks
            progress_bar = f"{'█' * filled_blocks}{'░' * empty_blocks}"
            time_display = f"{YTDLSource.format_duration(int(current_pos))} / {YTDLSource.format_duration(duration)}"
        else:
            progress_bar = "🔴 LIVE STREAM"
            time_display = "N/A"
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"[{vc.source.title}]({vc.source.web_url})",
            color=discord.Color.green()
        )
        
        # Set thumbnail
        if player.current.thumbnail:
            embed.set_thumbnail(url=player.current.thumbnail)
        
        # Add fields
        embed.add_field(name="Progress", value=f"```{progress_bar}```{time_display}", inline=False)
        embed.add_field(name="Requested by", value=player.current.requester.mention, inline=True)
        embed.add_field(name="Uploader", value=player.current.uploader, inline=True)
        embed.add_field(name="Volume", value=f"{int(player.volume * 100)}%", inline=True)
        embed.add_field(name="Repeat Mode", value=player.repeat_mode.upper(), inline=True)
        embed.add_field(name="Queue Length", value=f"{player.queue.qsize()} songs", inline=True)
        
        # Add view count if available
        if hasattr(player.current, 'view_count') and player.current.view_count:
            embed.add_field(name="Views", value=f"{player.current.view_count:,}", inline=True)
        
        # Add controls hint
        embed.set_footer(text=f"Use {ctx.prefix}help music for all commands")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='volume', aliases=['vol', 'v'], description="Change volume")
    async def change_volume(self, ctx, *, vol: float = None):
        """Change the player volume (1-100)."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        
        if vol is None:
            # Show current volume
            embed = discord.Embed(
                title="Current Volume",
                description=f"🔊 Volume is set to **{int(player.volume * 100)}%**",
                color=discord.Color.blue()
            )
            return await ctx.send(embed=embed)
        
        if not 0 < vol <= 100:
            embed = discord.Embed(
                title="Invalid Volume",
                description="Please enter a value between 1 and 100.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if vc.source:
            vc.source.volume = vol / 100
        
        player.volume = vol / 100
        
        # Volume indicator
        volume_emoji = "🔇" if vol == 0 else "🔈" if vol < 30 else "🔉" if vol < 70 else "🔊"
        
        embed = discord.Embed(
            title="Volume Changed",
            description=f"{volume_emoji} Volume set to **{int(vol)}%**",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=['cl', 'empty'], description="Clear the queue")
    async def clear_(self, ctx):
        """Clear the entire queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        
        if player.queue.empty():
            embed = discord.Embed(
                title="Queue already empty",
                description="The queue is already empty!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        # Count songs before clearing
        song_count = player.queue.qsize()
        
        # Clear the queue
        player.queue._queue.clear()
        
        embed = discord.Embed(
            title="Queue Cleared",
            description=f"💥 Removed {song_count} songs from the queue!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='remove', aliases=['rm', 'delete'], description="Remove a song from queue")
    async def remove_(self, ctx, index: int):
        """Remove a specific song from queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        
        if player.queue.empty():
            embed = discord.Embed(
                title="Queue is empty",
                description="There are no songs in the queue to remove!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        try:
            if index < 1 or index > player.queue.qsize():
                embed = discord.Embed(
                    title="Invalid Index",
                    description=f"Please provide a number between 1 and {player.queue.qsize()}",
                    color=discord.Color.red()
                )
                return await ctx.send(embed=embed)
            
            # Convert queue to list, remove item, recreate queue
            queue_list = list(player.queue._queue)
            removed_song = queue_list.pop(index - 1)
            
            # Clear and refill queue
            player.queue._queue.clear()
            for song in queue_list:
                player.queue._queue.append(song)
            
            embed = discord.Embed(
                title="Song Removed",
                description=f"✅ Removed: [{removed_song['title']}]({removed_song['webpage_url']})",
                color=discord.Color.green()
            )
            embed.add_field(
                name="Requested by",
                value=removed_song['requester'].mention,
                inline=True
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error removing song: {e}")
            embed = discord.Embed(
                title="Error",
                description="An error occurred while removing the song.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed)
    
    @commands.command(name='shuffle', aliases=['mix'], description="Shuffle the queue")
    async def shuffle_(self, ctx):
        """Shuffle the current queue."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        
        if player.queue.qsize() < 2:
            embed = discord.Embed(
                title="Not enough songs",
                description="Need at least 2 songs in the queue to shuffle!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        # Convert queue to list, shuffle, recreate queue
        queue_list = list(player.queue._queue)
        random.shuffle(queue_list)
        
        # Clear and refill queue
        player.queue._queue.clear()
        for song in queue_list:
            player.queue._queue.append(song)
        
        embed = discord.Embed(
            title="Queue Shuffled",
            description=f"🔀 Successfully shuffled {len(queue_list)} songs!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='seek', description="Seek to a specific position in the song")
    async def seek_(self, ctx, position: str):
        """Seek to a specific position in the current song (format: MM:SS)"""
        vc = ctx.voice_client
        
        if not vc or not vc.is_playing():
            embed = discord.Embed(
                title="Nothing playing",
                description="I'm not currently playing anything!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # For now, seeking isn't supported with streaming
        # This is a placeholder for future implementation
        embed = discord.Embed(
            title="Not Supported",
            description="Seeking is not currently supported for streamed audio.\n"
                       "This feature may be added in a future update!",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='lyrics', description="Get lyrics for the current song")
    async def lyrics_(self, ctx, *, song_name: str = None):
        """Get lyrics for a song (current song if no name provided)"""
        # This is a placeholder for future implementation
        # You would need to integrate with a lyrics API like Genius
        embed = discord.Embed(
            title="Coming Soon",
            description="Lyrics feature is not yet implemented.\n"
                       "This feature will be added in a future update!",
            color=discord.Color.orange()
        )
        embed.set_footer(text="Tip: You can search for lyrics on Google or Genius.com")
        await ctx.send(embed=embed)
    
    @commands.command(name='move', aliases=['mv'], description="Move a song in the queue")
    async def move_(self, ctx, from_index: int, to_index: int):
        """Move a song from one position to another in the queue"""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        queue_size = player.queue.qsize()
        
        # Validate indices
        if not (1 <= from_index <= queue_size and 1 <= to_index <= queue_size):
            embed = discord.Embed(
                title="Invalid Position",
                description=f"Please provide positions between 1 and {queue_size}",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        if from_index == to_index:
            embed = discord.Embed(
                title="Same Position",
                description="The song is already at that position!",
                color=discord.Color.orange()
            )
            return await ctx.send(embed=embed)
        
        # Convert queue to list, move item, recreate queue
        queue_list = list(player.queue._queue)
        song_to_move = queue_list.pop(from_index - 1)
        queue_list.insert(to_index - 1, song_to_move)
        
        # Clear and refill queue
        player.queue._queue.clear()
        for song in queue_list:
            player.queue._queue.append(song)
        
        embed = discord.Embed(
            title="Song Moved",
            description=f"✅ Moved **{song_to_move['title']}** from position {from_index} to {to_index}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='leave', aliases=['disconnect', 'dc', 'stop', 'bye'], description="Disconnect from voice")
    async def leave_(self, ctx):
        """Stop the music and disconnect from voice."""
        vc = ctx.voice_client
        
        if not vc or not vc.is_connected():
            embed = discord.Embed(
                title="Not connected",
                description="I'm not connected to a voice channel!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Check if user is in the same voice channel
        if ctx.author.voice and ctx.author.voice.channel != vc.channel:
            embed = discord.Embed(
                title="Different Channel",
                description="You need to be in the same voice channel as me!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        # Clear the queue and stop playback
        player = self.get_player(ctx)
        player.queue._queue.clear()
        
        await self.cleanup(ctx.guild)
        
        embed = discord.Embed(
            title="Disconnected",
            description="👋 Thanks for listening! See you next time!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    
    @commands.command(name='save', aliases=['favorite', 'fav'], description="Save the current song")
    async def save_(self, ctx):
        """Save the current song to your DMs"""
        vc = ctx.voice_client
        
        if not vc or not vc.is_playing():
            embed = discord.Embed(
                title="Nothing playing",
                description="I'm not currently playing anything to save!",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed)
        
        player = self.get_player(ctx)
        if not player.current:
            return
        
        # Create embed with song info
        embed = discord.Embed(
            title="🎵 Saved Song",
            description=f"[{player.current.title}]({player.current.web_url})",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        
        if player.current.thumbnail:
            embed.set_thumbnail(url=player.current.thumbnail)
        
        embed.add_field(name="Duration", value=YTDLSource.format_duration(player.current.duration), inline=True)
        embed.add_field(name="Uploader", value=player.current.uploader, inline=True)
        embed.add_field(name="Saved from", value=ctx.guild.name, inline=True)
        
        # Try to send to user's DM
        try:
            await ctx.author.send(embed=embed)
            
            # Confirm in channel
            confirm_embed = discord.Embed(
                title="Song Saved",
                description=f"✅ I've sent you the song details in a DM!",
                color=discord.Color.green()
            )
            await ctx.send(embed=confirm_embed)
        except discord.Forbidden:
            error_embed = discord.Embed(
                title="Cannot Send DM",
                description="❌ I couldn't send you a DM. Please check your privacy settings!",
                color=discord.Color.red()
            )
            await ctx.send(error_embed)
    
    @commands.command(name='search', description="Search for songs")
    async def search_(self, ctx, *, query: str):
        """Search for songs and let user choose"""
        async with ctx.typing():
            # Search for multiple results
            search_msg = await ctx.send("🔍 Searching...")
            
            try:
                # Configure for search results
                search_opts = ytdlopts.copy()
                search_opts['extract_flat'] = True
                search_opts['force_generic_extractor'] = False
                
                ytdl_search = youtube_dl.YoutubeDL(search_opts)
                
                # Search for 5 results
                search_query = f"ytsearch5:{query}"
                data = await self.bot.loop.run_in_executor(
                    None, 
                    lambda: ytdl_search.extract_info(search_query, download=False)
                )
                
                if not data or 'entries' not in data:
                    await search_msg.delete()
                    embed = discord.Embed(
                        title="No Results",
                        description="No results found for your search.",
                        color=discord.Color.red()
                    )
                    return await ctx.send(embed=embed)
                
                # Create embed with results
                entries = data['entries'][:5]
                embed = discord.Embed(
                    title="🔍 Search Results",
                    description=f"Results for: **{query}**\n\nReact with a number to play:",
                    color=discord.Color.blue()
                )
                
                # Add results to embed
                emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣']
                for idx, entry in enumerate(entries):
                    title = entry.get('title', 'Unknown Title')
                    duration = YTDLSource.format_duration(entry.get('duration', 0))
                    uploader = entry.get('uploader', 'Unknown')
                    
                    embed.add_field(
                        name=f"{emojis[idx]} {title}",
                        value=f"**Duration:** {duration} | **Channel:** {uploader}",
                        inline=False
                    )
                
                await search_msg.delete()
                search_message = await ctx.send(embed=embed)
                
                # Add reactions
                for i in range(len(entries)):
                    await search_message.add_reaction(emojis[i])
                
                # Wait for user reaction
                def check(reaction, user):
                    return (user == ctx.author and 
                            str(reaction.emoji) in emojis[:len(entries)] and
                            reaction.message.id == search_message.id)
                
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
                except asyncio.TimeoutError:
                    await search_message.clear_reactions()
                    timeout_embed = discord.Embed(
                        title="Search Timed Out",
                        description="You didn't select a song in time.",
                        color=discord.Color.orange()
                    )
                    await search_message.edit(embed=timeout_embed)
                    return
                
                # Get selected song
                selected_index = emojis.index(str(reaction.emoji))
                selected_entry = entries[selected_index]
                
                # Clear reactions and update message
                await search_message.clear_reactions()
                selected_embed = discord.Embed(
                    title="Song Selected",
                    description=f"Selected: **{selected_entry['title']}**",
                    color=discord.Color.green()
                )
                await search_message.edit(embed=selected_embed)
                
                # Play the selected song
                url = f"https://youtube.com/watch?v={selected_entry['id']}"
                await ctx.invoke(self.play_, search=url)
                
            except Exception as e:
                logger.error(f"Error in search command: {e}")
                await search_msg.delete()
                embed = discord.Embed(
                    title="Search Error",
                    description="An error occurred while searching.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=embed)


# Setup function for the cog
async def setup(bot):
    await bot.add_cog(Music(bot))