# GitHub Commit Checklist

Before committing to GitHub, ensure you have:

## Security
- [ ] `.env` file is NOT committed (check `.gitignore`)
- [ ] `.env.example` contains only example values
- [ ] `BOT_TOKEN` never appears in any file (except `.env` which is ignored)
- [ ] No credentials or sensitive data in code

## Files to Commit
- [ ] `Dockerfile` - Container image definition
- [ ] `docker-compose.yml` - Compose configuration
- [ ] `docker-compose.prod.yml` - Production configuration
- [ ] `.dockerignore` - Docker build exclusions
- [ ] `.gitignore` - Git exclusions
- [ ] `.env.example` - Environment template
- [ ] `DEPLOYMENT.md` - Deployment guide
- [ ] `deploy.sh` - Linux/Mac deployment script
- [ ] `deploy.bat` - Windows deployment script
- [ ] All original Python files (main.py, handlers.py, etc.)
- [ ] `requirements.txt` - Python dependencies
- [ ] `README.md` - Project documentation

## Files to NOT Commit
- [ ] `.env` - Local environment variables
- [ ] `__pycache__/` - Python cache
- [ ] `*.pyc` - Compiled Python
- [ ] `.vscode/` or `.idea/` - IDE settings
- [ ] `temp/` or `downloads/` - Generated files

## Steps to Commit
1. Verify `.env` is in `.gitignore`: `git check-ignore .env` (should return nothing if ignored)
2. Review files to commit: `git status`
3. Add files: `git add .`
4. Commit with message:
   ```bash
   git commit -m "Add Docker deployment setup for Portainer

   - Add Dockerfile with Python 3.11-slim and FFmpeg
   - Add docker-compose.yml for easy deployment on port 8083
   - Add docker-compose.prod.yml for production use
   - Add deployment guides and scripts
   - Add environment variable template (.env.example)
   - Add security configurations (.gitignore, .dockerignore)"
   ```
5. Push to GitHub: `git push origin main` (or your branch)

## Deployment Verification
After pushing to GitHub:
1. Clone on your home lab: `git clone <repo-url>`
2. Copy environment template: `cp .env.example .env`
3. Add your BOT_TOKEN to `.env`
4. Deploy: `docker-compose up -d`
5. Check health: `curl http://localhost:8083/health`

## GitHub Repository Setup
1. Create repository on GitHub
2. Initialize local repo:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Telegram downloader bot with Docker setup"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/Telegram-downloader.git
   git push -u origin main
   ```

## Important Security Notes
- Never commit `.env` file
- Always use `.env.example` as template
- Rotate your BOT_TOKEN if accidentally exposed
- Use GitHub secrets for CI/CD pipelines (if adding GitHub Actions)
