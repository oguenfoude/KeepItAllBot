# 🐳 Docker Deployment for VPS

Deploy KeepItAllBot to any VPS (Ubuntu, Debian, etc.)

**Supports 2GB uploads with Pyrogram!**

---

## 🤔 How It Works on VPS

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Your VPS    │     │   Docker     │     │  Telegram    │
│  (Ubuntu)    │ ──► │  Container   │ ──► │   Servers    │
│              │     │  (the bot)   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

- Docker runs the bot in an isolated container
- Container restarts automatically if it crashes
- Logs are saved and rotated automatically
- VPS has fast internet = fast downloads!

---

## 📋 What You Need

1. **A VPS** (Contabo, DigitalOcean, Hetzner, etc.)
2. **SSH access** to your VPS
3. **Telegram credentials** (see main README.md)

---

## 🚀 Quick Setup (Copy-Paste)

### Step 1: Upload project to VPS

From your Windows PowerShell:
```powershell
scp -r D:\MVP\KeepItAllBot root@YOUR_VPS_IP:/opt/
```

Or use FileZilla/WinSCP to upload the folder.

### Step 2: SSH into your VPS

```bash
ssh root@YOUR_VPS_IP
```

### Step 3: Install Docker (if not installed)

```bash
curl -fsSL https://get.docker.com | sh
```

### Step 4: Go to project folder

```bash
cd /opt/KeepItAllBot
```

### Step 5: Create .env file

```bash
cp .env.example .env
nano .env
```

Fill in these 3 values (get them from my.telegram.org and @BotFather):
```env
API_ID=32757195
API_HASH=95d3469e61380761284461d93eed7995
BOT_TOKEN=7216622938:AAF8VCZTVoZcdmqJcN4dlqSxknRWohADVBo
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 6: Build and run

```bash
cd docker
docker compose up -d --build
```

### Step 7: Check if it's running

```bash
docker compose logs -f
```

You should see:
```
Starting KeepItAllBot (Pyrogram - 2GB uploads!)
Bot started successfully!
Bot is running...
```

Press `Ctrl+C` to exit logs (bot keeps running).

---

## 📋 Useful Commands

```bash
# Go to docker folder first
cd /opt/KeepItAllBot/docker

# Check status
docker compose ps

# View logs (live)
docker compose logs -f

# View last 100 log lines
docker compose logs --tail 100

# Stop bot
docker compose down

# Restart bot
docker compose restart

# Rebuild after code changes
docker compose up -d --build

# Full reset (removes container)
docker compose down
docker compose up -d --build
```

---

## ⚙️ Configuration

Settings are in `.env` file AND can be overridden in `docker-compose.yml`:

### In docker-compose.yml (production settings):

```yaml
environment:
  - CONCURRENT_DOWNLOADS=5          # 5 parallel downloads
  - MAX_VIDEO_RESOLUTION=1080       # Up to 1080p
  - DOWNLOAD_TIMEOUT=1800           # 30 min max
  - CLEANUP_AFTER_MINUTES=10        # Quick cleanup
  - MAX_DOWNLOADS_PER_USER=50       # 50 per hour
```

| Setting | Default | Description |
|---------|---------|-------------|
| `MAX_VIDEO_RESOLUTION` | 1080 | Max quality (360, 480, 720, 1080, 1440, 2160) |
| `CONCURRENT_DOWNLOADS` | 5 | How many videos to download at once |
| `MAX_DOWNLOADS_PER_USER` | 50 | Limit per user per hour |
| `DOWNLOAD_TIMEOUT` | 1800 | Max seconds to wait for download (30 min) |
| `CLEANUP_AFTER_MINUTES` | 10 | Delete old files after this |

---

## 🔍 Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker compose logs

# Check if .env exists and has values
cat /opt/KeepItAllBot/.env
```

### "permission denied"
```bash
# Run as root or use sudo
sudo docker compose up -d --build
```

### Bot not responding
```bash
# Check if container is running
docker compose ps

# Should show "Up" status
# If not, check logs:
docker compose logs --tail 50
```

### Out of disk space
```bash
# Check disk usage
df -h

# Clean old docker images
docker system prune -a
```

---

## 🔄 Updating the Bot

When you make changes to the code:

```bash
# 1. Upload new files to VPS (from Windows)
scp -r D:\MVP\KeepItAllBot root@YOUR_VPS_IP:/opt/

# 2. SSH in and rebuild
ssh root@YOUR_VPS_IP
cd /opt/KeepItAllBot/docker
docker compose up -d --build
```

---

## 📊 Why VPS is Better

| | Home PC | VPS |
|---|---------|-----|
| **Download speed** | 1-10 MB/s | 100+ MB/s |
| **Upload to Telegram** | Slow | Fast |
| **Always online** | No | Yes ✅ |
| **Electricity cost** | You pay | Included |
| **Price** | Free | ~$5/month |
- **Faster uploads** with MTProto protocol
- **Upload progress** shown in chat
