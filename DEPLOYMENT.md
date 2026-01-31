# Deployment Guide - Portainer on Home Lab

This guide will help you deploy the Telegram Downloader bot on Portainer running on port 8083.

## Prerequisites

- Portainer running on your home lab
- Docker and Docker Compose installed
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

## Deployment Steps

### Option 1: Using Docker Compose (Recommended)

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd Telegram-downloader
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your Telegram bot token:
   ```
   BOT_TOKEN=your_actual_bot_token_here
   ```

3. **Build and start the container**:
   ```bash
   docker-compose up -d
   ```

4. **Verify it's running**:
   ```bash
   docker-compose ps
   docker-compose logs -f
   ```

### Option 2: Using Portainer Web UI

1. **In Portainer**, go to **Stacks** → **Add Stack**

2. **Paste the docker-compose.yml content** into the editor

3. **Set environment variables**:
   - Click **Add Environment Variable**
   - Name: `BOT_TOKEN`
   - Value: `your_actual_bot_token_here`

4. **Configure port mapping**:
   - Container port: `8000`
   - Host port: `8083`

5. **Deploy** by clicking **Deploy Stack**

6. **Monitor** the container in Containers section

### Option 3: Manual Docker Build

1. **Build the image**:
   ```bash
   docker build -t telegram-downloader .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name telegram-downloader \
     -p 8083:8000 \
     -e BOT_TOKEN=your_bot_token_here \
     --restart unless-stopped \
     telegram-downloader
   ```

3. **Check logs**:
   ```bash
   docker logs -f telegram-downloader
   ```

## Health Checks

The bot includes a health check endpoint:
- **URL**: `http://localhost:8083/health`
- **Status**: Returns "OK" if the bot is running

## Maintenance

### View logs:
```bash
docker-compose logs -f telegram-downloader
```

### Restart the container:
```bash
docker-compose restart telegram-downloader
```

### Stop the container:
```bash
docker-compose stop telegram-downloader
```

### Remove the container:
```bash
docker-compose down
```

### Update the bot:
```bash
git pull
docker-compose up -d --build
```

## Troubleshooting

### Container exits immediately:
- Check logs: `docker-compose logs telegram-downloader`
- Verify `BOT_TOKEN` is set correctly in `.env`

### Health check failing:
- Ensure port 8083 is accessible
- Check firewall settings on your home lab

### Memory/CPU issues:
- Monitor resource usage in Portainer
- Increase limits in docker-compose.yml if needed

### FFmpeg not found:
- The Dockerfile includes FFmpeg installation
- Rebuild the image: `docker-compose up -d --build`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BOT_TOKEN` | Required | Your Telegram bot token |
| `PORT` | 8000 | Port for health checks |
| `LOG_LEVEL` | INFO | Logging verbosity |

## Security Notes

- The container runs as a non-root user (`botuser`)
- No credentials are stored in Docker images
- Use environment variables via `.env` file (not in version control)
- Keep your `BOT_TOKEN` secret and never commit it to Git

## Backup & Recovery

Your bot state and downloads are temporary. To backup configuration:
```bash
cp .env .env.backup
```

## Support

For issues or questions, check:
- Bot logs: `docker-compose logs -f`
- Telegram [@BotFather](https://t.me/botfather) documentation
- yt-dlp documentation: https://github.com/yt-dlp/yt-dlp
