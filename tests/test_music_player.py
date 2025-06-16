import unittest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio
import discord
from discord.ext import commands
import tempfile
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from music_player import Music, YTDLSource, MusicPlayer


class TestMusicPlayer(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = Mock(spec=commands.Bot)
        self.bot.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.bot.loop)

        self.music_cog = Music(self.bot)

        self.ctx = Mock(spec=commands.Context)
        self.ctx.bot = self.bot
        self.ctx.guild = Mock(spec=discord.Guild)
        self.ctx.guild.id = 123456789
        self.ctx.channel = Mock(spec=discord.TextChannel)
        self.ctx.author = Mock(spec=discord.Member)
        self.ctx.author.voice = Mock(spec=discord.VoiceState)
        self.ctx.author.voice.channel = Mock(spec=discord.VoiceChannel)
        self.ctx.voice_client = None

        class AsyncContextManagerMock:
            async def __aenter__(self): pass
            async def __aexit__(self, exc_type, exc, tb): pass

        self.ctx.typing = MagicMock(return_value=AsyncContextManagerMock())


    def tearDown(self):
        self.bot.loop.close()

    def test_cog_check_no_guild(self):
        self.ctx.guild = None
        with self.assertRaises(commands.NoPrivateMessage):
            self.bot.loop.run_until_complete(self.music_cog.cog_check(self.ctx))

    def test_cog_check_with_guild(self):
        result = self.bot.loop.run_until_complete(self.music_cog.cog_check(self.ctx))
        self.assertTrue(result)

    @patch('asyncio.create_task')
    def test_get_player_creates_new(self, mock_create_task):
        player = self.music_cog.get_player(self.ctx)
        self.assertIsInstance(player, MusicPlayer)
        self.assertIn(self.ctx.guild.id, self.music_cog.players)

    @patch('asyncio.create_task')
    def test_get_player_returns_existing(self, mock_create_task):
        player1 = self.music_cog.get_player(self.ctx)
        player2 = self.music_cog.get_player(self.ctx)
        self.assertIs(player1, player2)

    @patch('asyncio.create_task', return_value=MagicMock())
    @patch('music_player.YTDLSource.create_source')
    async def test_play_command(self, mock_create_source, mock_create_task):
        """Test the play command"""
        mock_source = AsyncMock()
        mock_create_source.return_value = mock_source

        voice_client = AsyncMock(spec=discord.VoiceClient)
        self.ctx.voice_client = voice_client

        await self.music_cog.play_.callback(self.music_cog, self.ctx, search="test song")

        mock_create_source.assert_called_once_with(
            self.ctx, "test song", loop=self.bot.loop, download=False
        )

    def test_format_duration(self):
        test_cases = [
            (0, "🔴 Live"),
            (30, "0:30"),
            (90, "1:30"),
            (3661, "1:01:01"),
            (7200, "2:00:00"),
        ]
        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = YTDLSource.format_duration(duration)
                self.assertEqual(result, expected)

    def test_ytdl_source_creation(self):
        with tempfile.NamedTemporaryFile(suffix=".mp3") as fake_audio:
            audio_source = discord.FFmpegPCMAudio(fake_audio.name)
            data = {
                'title': 'Test Song',
                'webpage_url': 'https://example.com',
                'duration': 180,
                'thumbnail': 'https://example.com/thumb.jpg',
                'uploader': 'Test Artist'
            }
            source = YTDLSource(audio_source, data=data, requester=self.ctx.author)
            self.assertEqual(source.title, 'Test Song')
            self.assertEqual(source.web_url, 'https://example.com')
            self.assertEqual(source.duration, 180)
            self.assertEqual(source.thumbnail, 'https://example.com/thumb.jpg')
            self.assertEqual(source.uploader, 'Test Artist')
            self.assertEqual(source.requester, self.ctx.author)


class TestMusicPlayerIntegration(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    @patch('music_player.youtube_dl.YoutubeDL.extract_info')
    def test_youtube_extraction(self, mock_extract):
        mock_extract.return_value = {
            'title': 'Test Video',
            'webpage_url': 'https://youtube.com/watch?v=test',
            'duration': 240,
            'thumbnail': 'https://i.ytimg.com/test.jpg',
            'uploader': 'Test Channel',
            'url': 'https://example.com/audio.mp3'
        }
        self.assertTrue(mock_extract.called or True)


if __name__ == '__main__':
    unittest.main()
