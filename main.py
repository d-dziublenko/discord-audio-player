import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up intents - these tell Discord what events your bot needs access to
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content
intents.voice_states = True     # Required for voice channel operations
intents.guilds = True          # Required for guild operations

class MusicBot(commands.Bot):
    """Custom bot class with startup logic"""
    
    def __init__(self):
        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=commands.DefaultHelpCommand(
                no_category='Commands'
            )
        )
    
    async def setup_hook(self):
        """This is called when the bot is starting up"""
        # Load the music cog
        await self.load_extension('music_player')
        print(f"Loaded Music cog")
    
    async def on_ready(self):
        """Called when the bot is fully ready"""
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Connected to {len(self.guilds)} guilds')
        print('------')
        
        # Set the bot's status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name="!help | Music"
            )
        )
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ Unknown command. Use `!help` to see available commands.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param.name}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided.")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"❌ Command on cooldown. Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("❌ This command cannot be used in DMs.")
        else:
            # Log unexpected errors
            print(f'Unexpected error: {error}')
            await ctx.send(f"❌ An unexpected error occurred: {str(error)}")


# Create bot instance
bot = MusicBot()

# Add some basic commands
@bot.command(name='ping', description='Check bot latency')
async def ping(ctx):
    """Check the bot's latency"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: **{latency}ms**",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.command(name='stats', description='Show bot statistics')
async def stats(ctx):
    """Display bot statistics"""
    embed = discord.Embed(
        title="📊 Bot Statistics",
        color=discord.Color.blue()
    )
    embed.add_field(name="Servers", value=len(bot.guilds))
    embed.add_field(name="Users", value=len(set(bot.get_all_members())))
    embed.add_field(name="Commands", value=len(bot.commands))
    
    # Count voice connections
    voice_connections = len(bot.voice_clients)
    embed.add_field(name="Active Voice Connections", value=voice_connections)
    
    await ctx.send(embed=embed)

@bot.command(name='invite', description='Get bot invite link')
async def invite(ctx):
    """Get the bot's invite link"""
    embed = discord.Embed(
        title="🔗 Invite Link",
        description=f"[Click here to invite me!](https://discord.com/api/oauth2/authorize?client_id={bot.user.id}&permissions=8&scope=bot)",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name='support', description='Get support server link')
async def support(ctx):
    """Get support server information"""
    embed = discord.Embed(
        title="💬 Support",
        description="Need help? Join our support server or contact the developer!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Developer", value="YourName#0000")
    embed.add_field(name="GitHub", value="[Source Code](https://github.com/yourusername/music-bot)")
    await ctx.send(embed=embed)


async def main():
    """Main function to run the bot"""
    # Get token from environment variable or use the one provided
    # IMPORTANT: Never hardcode your token in production!
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        # For development only - use environment variables in production!
        token = 'YOUR_BOT_TOKEN_HERE'
        print("⚠️  Warning: Using hardcoded token. Use environment variables in production!")
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Invalid bot token!")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())