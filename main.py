import discord
from discord.ext import commands
import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging based on environment
# This helps us track issues and debug problems more effectively
log_level = os.getenv('LOG_LEVEL', 'INFO')
log_file = os.getenv('LOG_FILE', 'bot.log')

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Set up logging with both file and console output
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/{log_file}'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('discord_bot')

# Bot configuration from environment variables
# Using environment variables makes the bot more flexible and secure
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')
BOT_OWNER_ID = int(os.getenv('BOT_OWNER_ID', '0')) if os.getenv('BOT_OWNER_ID') else None
DEVELOPMENT_MODE = os.getenv('DEVELOPMENT_MODE', 'false').lower() == 'true'

# Set up intents - these tell Discord what events your bot needs access to
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
intents.voice_states = True     # Required for voice channel operations
intents.guilds = True          # Required for guild operations
intents.members = True         # Required for member information

class MusicBot(commands.Bot):
    """Custom bot class with enhanced functionality and error handling"""
    
    def __init__(self):
        super().__init__(
            command_prefix=COMMAND_PREFIX,
            intents=intents,
            help_command=commands.DefaultHelpCommand(
                no_category='Commands',
                dm_help=True  # Allow help command in DMs
            ),
            # Set the bot's status while starting up
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Starting up..."
            ),
            # Prevent the bot from mentioning @everyone or @here
            allowed_mentions=discord.AllowedMentions(
                everyone=False,
                roles=False,
                replied_user=True
            )
        )
        
        # Track bot statistics
        self.start_time = datetime.utcnow()
        self.command_stats = {}
        self.error_count = 0
        
    async def setup_hook(self):
        """This is called when the bot is starting up"""
        logger.info("Bot is starting up...")
        
        try:
            # Load the music cog
            await self.load_extension('music_player')
            logger.info("Successfully loaded Music cog")
        except Exception as e:
            logger.error(f"Failed to load Music cog: {e}")
            raise
        
        # Load any additional cogs here in the future
        # Example: await self.load_extension('moderation')
        
    async def on_ready(self):
        """Called when the bot is fully ready"""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info(f'Connected to {len(self.guilds)} guilds')
        logger.info(f'Total users: {sum(guild.member_count for guild in self.guilds)}')
        logger.info('Bot is ready!')
        print('------')
        
        # Set the bot's final status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name=f"{COMMAND_PREFIX}help | Music"
            ),
            status=discord.Status.online
        )
        
    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id}) with {guild.member_count} members")
        
        # Try to send a welcome message to the system channel
        if guild.system_channel and guild.system_channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="Thanks for inviting me! 🎵",
                description=f"Use `{COMMAND_PREFIX}help` to see all my commands.\n"
                           f"To get started, join a voice channel and use `{COMMAND_PREFIX}play <song>`!",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Need help?",
                value=f"Use `{COMMAND_PREFIX}support` for support information.",
                inline=False
            )
            try:
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Could not send welcome message to {guild.name}")
                
    async def on_guild_remove(self, guild):
        """Called when the bot is removed from a guild"""
        logger.info(f"Removed from guild: {guild.name} (ID: {guild.id})")
        
    async def on_command(self, ctx):
        """Called when a command is successfully invoked"""
        # Track command usage statistics
        command_name = ctx.command.qualified_name
        self.command_stats[command_name] = self.command_stats.get(command_name, 0) + 1
        
        logger.info(f"Command '{command_name}' used by {ctx.author} in {ctx.guild.name if ctx.guild else 'DM'}")
        
    async def on_command_error(self, ctx, error):
        """Global error handler for better error messages and logging"""
        # Don't handle errors that are already handled locally
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Get the original error if it's wrapped
        error = getattr(error, 'original', error)
        
        # Track error count
        self.error_count += 1
        
        # Handle specific error types with user-friendly messages
        if isinstance(error, commands.CommandNotFound):
            # Only respond to command not found in development mode
            if DEVELOPMENT_MODE:
                await ctx.send(f"❌ Unknown command. Use `{COMMAND_PREFIX}help` to see available commands.")
            return
            
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"You're missing a required argument: `{error.param.name}`",
                color=discord.Color.red()
            )
            embed.add_field(
                name="Usage",
                value=f"`{COMMAND_PREFIX}{ctx.command.name} {ctx.command.signature}`",
                inline=False
            )
            await ctx.send(embed=embed)
            
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided. Please check your input and try again.")
            
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
            
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command cannot be used in DMs.")
            
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("❌ You don't have permission to use this command.")
            
        elif isinstance(error, commands.DisabledCommand):
            await ctx.send("❌ This command is currently disabled.")
            
        elif isinstance(error, commands.BotMissingPermissions):
            missing = ', '.join(error.missing_permissions)
            await ctx.send(f"❌ I need the following permissions to run this command: {missing}")
            
        elif isinstance(error, discord.Forbidden):
            await ctx.send("❌ I don't have permission to perform that action.")
            
        elif isinstance(error, discord.HTTPException):
            await ctx.send("❌ An error occurred while communicating with Discord. Please try again.")
            
        else:
            # Log unexpected errors
            logger.error(f'Unexpected error in command {ctx.command}:', exc_info=error)
            
            # Send error message to user
            if DEVELOPMENT_MODE:
                # In development, show the full error
                await ctx.send(f"❌ An unexpected error occurred:\n```python\n{error}\n```")
            else:
                # In production, show a generic message
                await ctx.send("❌ An unexpected error occurred. The issue has been logged.")
            
            # Send error to bot owner if configured
            if BOT_OWNER_ID:
                owner = self.get_user(BOT_OWNER_ID)
                if owner:
                    error_embed = discord.Embed(
                        title="Bot Error",
                        description=f"Error in command `{ctx.command}`",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow()
                    )
                    error_embed.add_field(name="Guild", value=ctx.guild.name if ctx.guild else "DM", inline=True)
                    error_embed.add_field(name="User", value=str(ctx.author), inline=True)
                    error_embed.add_field(name="Error Type", value=type(error).__name__, inline=True)
                    error_embed.add_field(name="Error", value=str(error)[:1024], inline=False)
                    
                    try:
                        await owner.send(embed=error_embed)
                    except discord.Forbidden:
                        pass


# Create bot instance
bot = MusicBot()

# Basic utility commands
@bot.command(name='ping', description='Check bot latency')
async def ping(ctx):
    """Check the bot's latency to Discord"""
    # Calculate different types of latency
    start_time = datetime.utcnow()
    message = await ctx.send("Pinging...")
    end_time = datetime.utcnow()
    
    # API latency is the websocket latency
    api_latency = round(bot.latency * 1000)
    # Response time is how long it took to send the message
    response_time = (end_time - start_time).total_seconds() * 1000
    
    embed = discord.Embed(
        title="🏓 Pong!",
        color=discord.Color.green() if api_latency < 100 else discord.Color.orange()
    )
    embed.add_field(name="API Latency", value=f"{api_latency}ms", inline=True)
    embed.add_field(name="Response Time", value=f"{response_time:.0f}ms", inline=True)
    
    # Add latency status indicator
    if api_latency < 50:
        status = "Excellent 🟢"
    elif api_latency < 100:
        status = "Good 🟡"
    elif api_latency < 200:
        status = "Fair 🟠"
    else:
        status = "Poor 🔴"
    
    embed.add_field(name="Connection Status", value=status, inline=True)
    
    await message.edit(content=None, embed=embed)

@bot.command(name='stats', description='Show bot statistics')
async def stats(ctx):
    """Display detailed bot statistics"""
    # Calculate uptime
    uptime = datetime.utcnow() - bot.start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    # Get memory usage
    try:
        import psutil
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # Convert to MB
        memory_str = f"{memory_usage:.2f} MB"
    except ImportError:
        memory_str = "N/A (install psutil)"
    
    embed = discord.Embed(
        title="📊 Bot Statistics",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    
    # General stats
    embed.add_field(name="Servers", value=f"{len(bot.guilds):,}", inline=True)
    embed.add_field(name="Users", value=f"{sum(guild.member_count for guild in bot.guilds):,}", inline=True)
    embed.add_field(name="Commands", value=f"{len(bot.commands)}", inline=True)
    
    # Voice connections
    voice_connections = len(bot.voice_clients)
    embed.add_field(name="Voice Connections", value=f"{voice_connections}", inline=True)
    embed.add_field(name="Memory Usage", value=memory_str, inline=True)
    embed.add_field(name="Total Commands Used", value=f"{sum(bot.command_stats.values()):,}", inline=True)
    
    # Uptime
    uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
    embed.add_field(name="Uptime", value=uptime_str, inline=True)
    embed.add_field(name="Errors", value=f"{bot.error_count}", inline=True)
    embed.add_field(name="Python Version", value=f"{sys.version.split()[0]}", inline=True)
    
    # Most used commands
    if bot.command_stats:
        top_commands = sorted(bot.command_stats.items(), key=lambda x: x[1], reverse=True)[:3]
        top_commands_str = '\n'.join([f"`{cmd}`: {count:,}" for cmd, count in top_commands])
        embed.add_field(name="Top Commands", value=top_commands_str or "None yet", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='invite', description='Get bot invite link')
async def invite(ctx):
    """Get the bot's invite link with proper permissions"""
    # Calculate permissions integer for the invite
    permissions = discord.Permissions(
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True,
        add_reactions=True,
        connect=True,
        speak=True,
        use_voice_activation=True,
        change_nickname=True
    )
    
    invite_url = discord.utils.oauth_url(bot.user.id, permissions=permissions)
    
    embed = discord.Embed(
        title="🔗 Invite Links",
        description="Choose the appropriate invite link for your needs:",
        color=discord.Color.blue()
    )
    
    # Recommended permissions link
    embed.add_field(
        name="Recommended Permissions",
        value=f"[**Click here to invite me!**]({invite_url})",
        inline=False
    )
    
    # Admin permissions link (for lazy server owners)
    admin_url = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(administrator=True))
    embed.add_field(
        name="Administrator Permissions",
        value=f"[Invite with admin perms]({admin_url})\n*⚠️ Only use if you trust the bot*",
        inline=False
    )
    
    # No permissions link (user can configure after)
    basic_url = discord.utils.oauth_url(bot.user.id, permissions=discord.Permissions(0))
    embed.add_field(
        name="No Permissions",
        value=f"[Invite without perms]({basic_url})\n*Configure permissions after inviting*",
        inline=False
    )
    
    embed.set_footer(text="Thank you for inviting me to your server! 🎵")
    
    await ctx.send(embed=embed)

@bot.command(name='support', description='Get support server link')
async def support(ctx):
    """Get support server information and helpful links"""
    embed = discord.Embed(
        title="💬 Support & Information",
        description="Need help? Found a bug? Want to suggest a feature?",
        color=discord.Color.blue()
    )
    
    # GitHub repository
    github_url = "https://github.com/d-dziublenko/discord-audio-player.git"
    embed.add_field(
        name="GitHub",
        value=f"[Source Code]({github_url})",
        inline=True
    )
    
    # Documentation
    embed.add_field(
        name="Documentation",
        value=f"[Read the Docs]({github_url}/wiki)",
        inline=True
    )
    
    # Bug reports
    embed.add_field(
        name="Bug Reports",
        value=f"[Report an Issue]({github_url}/issues)",
        inline=True
    )
    
    # Feature requests
    embed.add_field(
        name="Feature Requests",
        value=f"[Suggest a Feature]({github_url}/issues/new)",
        inline=True
    )
    
    # Bot information
    embed.set_footer(
        text=f"Version 1.0.0 | Made with discord.py",
        icon_url=bot.user.display_avatar.url
    )
    
    await ctx.send(embed=embed)

@bot.command(name='about', description='Information about the bot')
async def about(ctx):
    """Display detailed information about the bot"""
    embed = discord.Embed(
        title=f"About {bot.user.name}",
        description="A feature-rich music bot for Discord servers!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="Features",
        value="• High-quality music streaming\n"
              "• Queue management\n"
              "• Playback controls\n"
              "• Volume control\n"
              "• Repeat modes\n"
              "• Auto-disconnect\n"
              "• And much more!",
        inline=False
    )
    
    embed.add_field(
        name="Technology",
        value="• **Language:** Python 3.8+\n"
              "• **Library:** discord.py\n"
              "• **Audio:** yt-dlp & FFmpeg\n"
              "• **Hosting:** Your choice!",
        inline=True
    )
    
    embed.add_field(
        name="Links",
        value=f"• [Invite Bot]({discord.utils.oauth_url(bot.user.id)})\n"
              "• [GitHub](https://github.com/d-dziublenko/discord-audio-player.git)\n",
        inline=True
    )
    
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(
        text=f"Serving {len(bot.guilds)} servers | {sum(g.member_count for g in bot.guilds):,} users",
        icon_url=bot.user.display_avatar.url
    )
    
    await ctx.send(embed=embed)

# Owner-only commands
@bot.command(name='shutdown', hidden=True)
@commands.is_owner()
async def shutdown(ctx):
    """Gracefully shutdown the bot (owner only)"""
    embed = discord.Embed(
        title="Shutting Down",
        description="Bot is shutting down gracefully...",
        color=discord.Color.red()
    )
    await ctx.send(embed=embed)
    
    logger.info(f"Shutdown command issued by {ctx.author}")
    
    # Disconnect from all voice channels
    for vc in bot.voice_clients:
        await vc.disconnect()
    
    # Close the bot
    await bot.close()

@bot.command(name='reload', hidden=True)
@commands.is_owner()
async def reload(ctx, extension: str = 'music_player'):
    """Reload a cog without restarting the bot (owner only)"""
    try:
        await bot.reload_extension(extension)
        await ctx.send(f"✅ Successfully reloaded `{extension}`")
        logger.info(f"Reloaded extension: {extension}")
    except Exception as e:
        await ctx.send(f"❌ Failed to reload `{extension}`: {str(e)}")
        logger.error(f"Failed to reload {extension}: {e}")

@bot.command(name='debug', hidden=True)
@commands.is_owner()
async def debug(ctx):
    """Show debug information (owner only)"""
    # Get system information
    try:
        import platform
        system_info = f"{platform.system()} {platform.release()}"
    except:
        system_info = "Unknown"
    
    embed = discord.Embed(
        title="🔧 Debug Information",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )
    
    embed.add_field(name="Bot User", value=f"{bot.user} ({bot.user.id})", inline=False)
    embed.add_field(name="Discord.py Version", value=discord.__version__, inline=True)
    embed.add_field(name="Python Version", value=sys.version.split()[0], inline=True)
    embed.add_field(name="System", value=system_info, inline=True)
    embed.add_field(name="Shards", value=f"{bot.shard_count or 1}", inline=True)
    embed.add_field(name="Command Prefix", value=f"`{COMMAND_PREFIX}`", inline=True)
    embed.add_field(name="Development Mode", value=str(DEVELOPMENT_MODE), inline=True)
    
    # Show cogs status
    cogs_status = []
    for cog_name in ['music_player']:  # Add more cog names as you add them
        if cog_name in bot.extensions:
            cogs_status.append(f"✅ {cog_name}")
        else:
            cogs_status.append(f"❌ {cog_name}")
    
    embed.add_field(name="Cogs Status", value='\n'.join(cogs_status) or "No cogs", inline=False)
    
    await ctx.send(embed=embed)


async def main():
    """Main function to run the bot with proper error handling"""
    # Get token from environment variable
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error("No Discord token found! Please set DISCORD_TOKEN in your .env file")
        print("\n❌ ERROR: No Discord token found!")
        print("Please make sure you have:")
        print("1. Created a .env file")
        print("2. Added DISCORD_TOKEN=your_token_here to the file")
        print("3. Saved the file\n")
        return
    
    try:
        logger.info("Starting bot...")
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token!")
        print("\n❌ ERROR: Invalid bot token!")
        print("Please check that your token is correct in the .env file")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        print(f"\n❌ An unexpected error occurred: {e}")
    finally:
        # Ensure proper cleanup
        if not bot.is_closed():
            await bot.close()
        logger.info("Bot has shut down")


if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by keyboard interrupt")
        print("\n👋 Bot shutdown by user")