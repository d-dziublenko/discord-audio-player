# Security Policy

## Supported Versions

I release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

I take the security of our Discord Music Bot seriously. If you have discovered a security vulnerability in this project, please report it to us as described below.

### Reporting Process

1. **Do not report security vulnerabilities through public GitHub issues.**

2. Include the following information:
   - Type of vulnerability
   - Full paths of source file(s) related to the vulnerability
   - The location of the affected source code (tag/branch/commit or direct URL)
   - Any special configuration required to reproduce the issue
   - Step-by-step instructions to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the issue, including how an attacker might exploit it

### What to Expect

- You should receive a response within 48 hours acknowledging your report
- I will work to verify the vulnerability and determine its impact
- I will keep you informed of the progress towards a fix
- I may ask for additional information or guidance
- I will notify you when the vulnerability is fixed

### Disclosure Policy

- I request that you give us reasonable time to address the issue before public disclosure
- I aim to resolve critical issues within 7 days
- Once fixed, I will publish a security advisory detailing the vulnerability

## Security Best Practices for Users

### Protecting Your Bot Token

Your bot token is like a password - keep it secret!

1. **Never commit your token to Git**

   - Always use environment variables
   - Use `.env` files for local development
   - Add `.env` to `.gitignore`

2. **Rotate tokens regularly**

   - If you suspect your token was exposed, regenerate it immediately
   - Change tokens periodically as a precaution

3. **Use environment-specific tokens**
   - Use different tokens for development and production
   - Never use your production token for testing

### Server Security

1. **Limit bot permissions**

   - Only grant permissions the bot actually needs
   - Review permissions regularly
   - Use role hierarchies properly

2. **Monitor bot activity**

   - Check server audit logs regularly
   - Watch for unusual command usage
   - Monitor resource usage

3. **Secure your hosting environment**
   - Keep your server OS and software updated
   - Use firewalls to limit access
   - Enable automatic security updates
   - Use strong passwords for server access

### Code Security

1. **Keep dependencies updated**

   ```bash
   pip list --outdated
   pip install --upgrade [package-name]
   ```

2. **Review code changes**

   - Carefully review any code modifications
   - Be cautious with community contributions
   - Test changes in a safe environment first

3. **Input validation**
   - The bot validates user inputs
   - Be aware of command injection risks
   - Report any input validation issues

## Common Security Issues to Avoid

### 1. Token Exposure

```python
# NEVER DO THIS
TOKEN = "MTE3NjY0ODU2NjQyNDQ0NDk3OA.GH8KPz.fake-token-example"

# DO THIS INSTEAD
import os
from dotenv import load_dotenv
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
```

### 2. Command Injection

The bot uses yt-dlp safely, but always be cautious with user inputs:

```python
# Safe approach used in the bot
search = user_input  # yt-dlp handles sanitization
```

### 3. Rate Limiting

The bot implements cooldowns to prevent abuse:

```python
@commands.cooldown(1, 5, commands.BucketType.user)
async def play(ctx, *, search):
    # Command can only be used once every 5 seconds per user
```

## Security Features

This bot includes several security features:

1. **No eval() or exec() commands** - Prevents arbitrary code execution
2. **Input sanitization** - User inputs are processed safely
3. **Permission checks** - Commands verify user permissions
4. **Error handling** - Errors don't expose sensitive information
5. **Secure dependencies** - Uses maintained, secure libraries

## Vulnerability Rewards

While I don't offer monetary rewards, I will:

- Credit security researchers in our changelog
- Add your name to our security acknowledgments
- Provide a letter of appreciation if needed

## Contact

For general questions and security concerns, use GitHub issues or Discord.

---

Remember: Security is everyone's responsibility. If you see something, say something!
