# Docker Setup for Telegram Downloader

Complete Docker and Portainer deployment setup for the Telegram Media Downloader Bot.

## 📦 What's Included

### Docker Files
- **Dockerfile** - Multi-stage optimized container image
  - Python 3.11-slim base image
  - FFmpeg for video processing
  - Non-root user security
  - Health checks enabled

- **docker-compose.yml** - Standard deployment configuration
  - Port mapping: 8083 → 8000
  - Automatic restart policy
  - Environment variable support

- **docker-compose.prod.yml** - Production-grade configuration
  - Resource limits (CPU & memory)
  - Enhanced logging
  - Health monitoring

### Configuration Files
- **.env.example** - Template for environment variables
- **.dockerignore** - Optimized Docker build context
- **.gitignore** - Prevents committing sensitive files

### Deployment Scripts
- **deploy.sh** - Linux/Mac one-command deployment
- **deploy.bat** - Windows one-command deployment
- **DEPLOYMENT.md** - Detailed deployment guide
- **GITHUB_CHECKLIST.md** - Pre-commit verification checklist

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Telegram Bot Token from [@BotFather](https://t.me/botfather)

### 1. Local Testing (Linux/Mac)
```bash
cp .env.example .env
# Edit .env and add your BOT_TOKEN
chmod +x deploy.sh
./deploy.sh
```

### 1. Local Testing (Windows)
```bash
copy .env.example .env
# Edit .env and add your BOT_TOKEN
deploy.bat
```

### 2. Deployment to Portainer

**Option A: Via Docker Compose**
```bash
docker-compose up -d
```

**Option B: Via Portainer UI**
1. Login to Portainer
2. Stacks → Add Stack
3. Paste content from `docker-compose.yml`
4. Add environment variable `BOT_TOKEN`
5. Deploy

**Option C: Via Git Integration (Advanced)**
1. Push this repo to GitHub
2. In Portainer: Stacks → Add Stack → Git Repository
3. Configure GitHub webhook for auto-deployment

## 📋 Port Mapping

- **Internal Port**: 8000 (health checks and bot)
- **External Port**: 8083 (what you access from your home lab)
- **Health Check**: `http://localhost:8083/health`

## 🔒 Security Features

✅ Container runs as non-root user  
✅ No credentials in image  
✅ Environment variables for secrets  
✅ `.env` file automatically excluded from Git  
✅ Small image footprint  
✅ Health check monitoring  

## 📊 Container Management

### View logs
```bash
docker-compose logs -f
```

### Stop container
```bash
docker-compose stop
```

### Restart container
```bash
docker-compose restart
```

### Update and redeploy
```bash
git pull
docker-compose up -d --build
```

### Remove container (keep data)
```bash
docker-compose down
```

### Full cleanup
```bash
docker-compose down -v
docker image rm telegram-downloader
```

## 🔧 Environment Variables

| Variable | Required | Default | Notes |
|----------|----------|---------|-------|
| `BOT_TOKEN` | Yes | - | Your Telegram bot token |
| `PORT` | No | 8000 | Health check port |
| `LOG_LEVEL` | No | INFO | DEBUG/INFO/WARNING/ERROR |

## 📈 Resource Usage

By default:
- **CPU Limit**: 1 core
- **Memory Limit**: 512 MB
- **Memory Reserve**: 256 MB

Adjust in `docker-compose.prod.yml` if needed.

## 🐛 Troubleshooting

### Container exits immediately
```bash
docker-compose logs telegram-downloader
# Check BOT_TOKEN is set in .env
```

### Port already in use
```bash
# Change port in docker-compose.yml
ports:
  - "8084:8000"  # Use 8084 instead
```

### Health check failing
```bash
# Verify access
curl http://localhost:8083/health
# Should return: OK
```

### Permission denied errors
```bash
# Fix permissions on deploy scripts
chmod +x deploy.sh
```

## 🔄 CI/CD Integration

For automated deployments, see [GitHub Actions examples](#) (optional setup).

## 📚 Related Documentation

- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide
- [GITHUB_CHECKLIST.md](GITHUB_CHECKLIST.md) - Pre-commit checklist
- [README.md](README.md) - Main project documentation
- [Docker Documentation](https://docs.docker.com/)
- [Portainer Documentation](https://docs.portainer.io/)

## 💡 Best Practices

1. **Always backup .env**: `cp .env .env.backup`
2. **Use .env.example**: Keep template updated
3. **Monitor logs**: `docker-compose logs -f`
4. **Regular updates**: `git pull && docker-compose up -d --build`
5. **Health checks**: Monitor `http://localhost:8083/health`

## 📝 Version Info

- **Base Image**: python:3.11-slim
- **FFmpeg**: Latest from apt
- **Non-root User**: botuser (UID: 1000)
- **Health Check**: Every 30s with 3 retries

## ⚠️ Important Notes

- **Telegram Bot Token**: Keep your token SECRET
- **No data persistence**: Downloads are temporary (by design)
- **Home Lab Security**: Ensure Portainer is only accessible on trusted network
- **Firewall**: Only expose port 8083 if needed

---

**Ready to deploy?** Start with [DEPLOYMENT.md](DEPLOYMENT.md)
