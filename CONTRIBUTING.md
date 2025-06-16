# Contributing to Discord Music Bot

First off, thank you for considering contributing to this Discord Music Bot! It's people like you that make this bot better for everyone.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive criticism
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your environment details (Python version, OS, etc.)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Why this enhancement would be useful
- Possible implementation approaches

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. Ensure your code follows the existing code style
4. Update documentation as needed
5. Issue that pull request!

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a test Discord server and bot for development
5. Set up your `.env` file with your test bot token

## Code Style Guidelines

- Follow PEP 8 Python style guide
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions small and focused
- Comment complex logic
- Use type hints where appropriate

### Example Code Style

```python
from typing import Optional

async def play_song(ctx, song_url: str, volume: Optional[float] = None):
    """
    Play a song in the voice channel.

    Args:
        ctx: Discord context object
        song_url: URL of the song to play
        volume: Optional volume level (0.0 to 1.0)

    Returns:
        bool: True if song started playing successfully
    """
    # Implementation here
    pass
```

## Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

### Commit Message Format

```
<type>: <subject>

<body>

<footer>
```

Types:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **test**: Adding missing tests
- **chore**: Changes to build process or auxiliary tools

Example:

```
feat: add shuffle command to music player

Added ability to shuffle the current queue using Fisher-Yates algorithm.
This helps users randomize their playlist order.

Closes #123
```

## Testing

- Test your changes locally before submitting
- Include tests for new features
- Ensure all existing tests pass
- Test edge cases and error conditions

## Documentation

- Update README.md if you change functionality
- Add docstrings to new functions/classes
- Update command descriptions in the code
- Include examples where helpful

## Questions?

Feel free to open an issue with your question.

Thank you for contributing! 🎉
