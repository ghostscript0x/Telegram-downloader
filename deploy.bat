@echo off
REM Quick deployment script for Windows

echo 🚀 Telegram Downloader - Docker Deployment Setup
echo ==================================================

REM Check if .env file exists
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ⚠️  Please edit .env and add your BOT_TOKEN before deploying!
    exit /b 1
) else (
    echo ✅ .env file already exists
)

echo.
echo Building Docker image...
docker-compose build

echo.
echo Starting container...
docker-compose up -d

echo.
echo ✅ Deployment complete!
echo.
echo Container Info:
docker-compose ps
echo.
echo Bot will be accessible at: http://localhost:8083/health
echo View logs with: docker-compose logs -f
echo.
echo To deploy on Portainer:
echo   1. Go to Stacks in Portainer
echo   2. Click 'Add Stack'
echo   3. Copy content from docker-compose.yml
echo   4. Add BOT_TOKEN environment variable
echo   5. Set port mapping 8083:8000
echo   6. Deploy!
