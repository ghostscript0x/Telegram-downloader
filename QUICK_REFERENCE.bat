@echo off
REM Quick reference commands for deployment (Windows)

echo Telegram Downloader Bot - Quick Commands
echo ========================================
echo.
echo SETUP
echo   copy .env.example .env         # Create environment file
echo   # Edit .env with your BOT_TOKEN
echo.
echo DEPLOYMENT
echo   docker-compose up -d         # Start container
echo   docker-compose down          # Stop container
echo   docker-compose logs -f       # View logs
echo   docker-compose restart       # Restart container
echo.
echo TESTING
echo   curl http://localhost:8083/health
echo.
echo GIT
echo   git add .
echo   git commit -m "Add Docker deployment"
echo   git push origin main
echo.
echo For detailed instructions, see:
echo   - DEPLOYMENT.md (detailed guide)
echo   - DOCKER_SETUP.md (Docker setup)
echo   - GITHUB_CHECKLIST.md (before committing)
