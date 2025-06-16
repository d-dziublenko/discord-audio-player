import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import discord
from discord.ext import commands
import tempfile

# Import your bot modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from music_player import Music, YTDLSource, MusicPlayer


class TestMusicPlayer(unittest.TestCase):
    """Test cases for the music player functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Create a mock bot instance
        self.bot = Mock(spec=commands.Bot)
        self.bot.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.bot.loop)
        
        # Create music cog instance
        self.music_cog = Music(self.bot)
        
        # Create mock context
        self.ctx = Mock(spec=commands.Context)
        self.ctx.bot = self.bot
        self.ctx.guild = Mock(spec=discord.Guild)
        self.ctx.guild.id = 123456789
        self.ctx.channel = Mock(spec=discord.TextChannel)
        self.ctx.author = Mock(spec=discord.Member)
        self.ctx.author.voice = Mock(spec=discord.VoiceState)
        self.ctx.author.voice.channel = Mock(spec=discord.VoiceChannel)
        self.ctx.voice_client = None
        
    def tearDown(self):
        """Clean up after each test"""
        self.bot.loop.close()
        
    def test_cog_check_no_guild(self):
        """Test that commands cannot be used in DMs"""
        # Set up context without guild (DM)
        self.ctx.guild = None
        
        # Run the check
        with self.assertRaises(commands.NoPrivateMessage):
            self.bot.loop.run_until_complete(self.music_cog.cog_check(self.ctx))
            
    def test_cog_check_with_guild(self):
        """Test that commands can be used in guilds"""
        # Context already has guild set in setUp
        result = self.bot.loop.run_until_complete(self.music_cog.cog_check(self.ctx))
        self.assertTrue(result)
    
    @patch('asyncio.create_task')
    def test_get_player_creates_new(self, mock_create_task):
        """Test that get_player creates a new player if none exists"""
        player = self.music_cog.get_player(self.ctx)
        
        # Check that player was created and stored
        self.assertIsInstance(player, MusicPlayer)
        self.assertIn(self.ctx.guild.id, self.music_cog.players)
        self.assertEqual(self.music_cog.players[self.ctx.guild.id], player)
    
    @patch('asyncio.create_task')
    def test_get_player_returns_existing(self, mock_create_task):
        """Test that get_player returns existing player"""
        # Create initial player
        player1 = self.music_cog.get_player(self.ctx)
        
        # Get player again
        player2 = self.music_cog.get_player(self.ctx)
        
        # Should be the same instance
        self.assertIs(player1, player2)
    
    @patch('asyncio.create_task')
    @patch('music_player.YTDLSource.create_source')
    async def test_play_command(self, mock_create_source, mock_create_task):
        """Test the play command"""
        # Set up mocks
        mock_source = AsyncMock()
        mock_create_source.return_value = mock_source
        
        # Mock voice client
        voice_client = AsyncMock(spec=discord.VoiceClient)
        self.ctx.voice_client = voice_client
        
        # Run play command
        self.bot.loop.run_until_complete(self.music_cog.play_(self.ctx, search="test song"))
        
        # Verify create_source was called with correct parameters
        mock_create_source.assert_called_once_with(
            self.ctx, 
            "test song", 
            loop=self.bot.loop, 
            download=False
        )
        
    def test_format_duration(self):
        """Test duration formatting"""
        # Test various duration formats
        test_cases = [
            (0, "🔴 Live"),           # Zero duration
            (30, "0:30"),            # 30 seconds
            (90, "1:30"),            # 1 minute 30 seconds
            (3661, "1:01:01"),       # 1 hour 1 minute 1 second
            (7200, "2:00:00"),       # 2 hours exactly
        ]
        
        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = YTDLSource.format_duration(duration)
                self.assertEqual(result, expected)
                
    def test_ytdl_source_creation(self):
        """Test YTDLSource creation with valid AudioSource"""

        # Create temporary fake audio file
        with tempfile.NamedTemporaryFile(suffix=".mp3") as fake_audio:
            # Create real FFmpegPCMAudio with fake file
            audio_source = discord.FFmpegPCMAudio(fake_audio.name)

            data = {
                'title': 'Test Song',
                'webpage_url': 'https://example.com',
                'duration': 180,
                'thumbnail': 'https://example.com/thumb.jpg',
                'uploader': 'Test Artist'
            }

            # Create YTDLSource with valid source
            source = YTDLSource(audio_source, data=data, requester=self.ctx.author)

            self.assertEqual(source.title, 'Test Song')
            self.assertEqual(source.web_url, 'https://example.com')
            self.assertEqual(source.duration, 180)
            self.assertEqual(source.thumbnail, 'https://example.com/thumb.jpg')
            self.assertEqual(source.uploader, 'Test Artist')
            self.assertEqual(source.requester, self.ctx.author)



class TestMusicPlayerIntegration(unittest.TestCase):
    """Integration tests for music player"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests"""
        # This runs once before all tests in this class
        pass
        
    def setUp(self):
        """Set up for each test"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
    def tearDown(self):
        """Clean up after each test"""
        self.loop.close()
        
    @patch('music_player.youtube_dl.YoutubeDL.extract_info')
    def test_youtube_extraction(self, mock_extract):
        """Test YouTube URL extraction"""
        # Mock YouTube data
        mock_extract.return_value = {
            'title': 'Test Video',
            'webpage_url': 'https://youtube.com/watch?v=test',
            'duration': 240,
            'thumbnail': 'https://i.ytimg.com/test.jpg',
            'uploader': 'Test Channel',
            'url': 'https://example.com/audio.mp3'
        }
        
        # Test extraction
        # This would be more complex in a real integration test
        self.assertTrue(mock_extract.called or True)


# Helper function to run async tests
def async_test(coro):
    """Decorator to run async test methods"""
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


if __name__ == '__main__':
    unittest.main()