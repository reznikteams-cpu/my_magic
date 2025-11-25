# Deployment Guide for Wise Guide Bot

This guide covers deploying the Wise Guide Bot to production environments.

## Prerequisites

- Linux server (Ubuntu 20.04+ recommended)
- Domain name with SSL certificate
- Robokassa merchant account
- OpenAI API access
- Telegram Bot Token

## Option 1: Manual Deployment on Linux

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx supervisor

# Create application user
sudo useradd -m -s /bin/bash botuser
sudo su - botuser
```

### 2. Clone and Setup Application

```bash
# Clone repository
git clone <your-repo-url> wise_guide_bot
cd wise_guide_bot

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your credentials
nano .env
```

### 3. Configure Supervisor

Create `/etc/supervisor/conf.d/wise-guide-bot.conf`:

```ini
[program:wise-guide-bot]
directory=/home/botuser/wise_guide_bot
command=/home/botuser/wise_guide_bot/venv/bin/python bot.py
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/botuser/wise_guide_bot/logs/bot.log
environment=PATH="/home/botuser/wise_guide_bot/venv/bin"

[program:wise-guide-webhook]
directory=/home/botuser/wise_guide_bot
command=/home/botuser/wise_guide_bot/venv/bin/python webhook_server.py
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/botuser/wise_guide_bot/logs/webhook.log
environment=PATH="/home/botuser/wise_guide_bot/venv/bin"
```

### 4. Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/wise-guide-bot`:

```nginx
upstream webhook_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    
    # Proxy to webhook server
    location /webhook/ {
        proxy_pass http://webhook_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://webhook_backend;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/wise-guide-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. Setup SSL with Let's Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

### 6. Start Services

```bash
# Create logs directory
mkdir -p ~/wise_guide_bot/logs

# Update and restart supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start wise-guide-bot wise-guide-webhook

# Check status
sudo supervisorctl status
```

## Option 2: Docker Deployment

### 1. Install Docker and Docker Compose

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Prepare Docker Environment

```bash
# Create application directory
mkdir -p ~/wise_guide_bot
cd ~/wise_guide_bot

# Copy files
cp docker-compose.yml .
cp Dockerfile.bot .
cp Dockerfile.webhook .
cp requirements.txt .
cp bot.py .
cp database.py .
cp robokassa_handler.py .
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 3. Configure Nginx with Docker

Create `nginx.conf`:

```nginx
upstream webhook {
    server webhook:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location /webhook/ {
        proxy_pass http://webhook;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Update docker-compose.yml

Add Nginx service:

```yaml
  nginx:
    image: nginx:latest
    container_name: wise-guide-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - /etc/letsencrypt:/etc/letsencrypt
    depends_on:
      - webhook
    restart: always
    networks:
      - wise-guide-network
```

### 5. Run Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Option 3: Cloud Deployment (AWS, DigitalOcean, etc.)

### AWS EC2

1. Launch EC2 instance (Ubuntu 20.04, t3.micro)
2. Configure security groups to allow ports 80, 443, 22
3. Follow "Manual Deployment" steps above

### DigitalOcean

1. Create Droplet (Ubuntu 20.04, Basic plan)
2. Configure firewall rules
3. Follow "Manual Deployment" steps above

### Heroku

```bash
# Create Heroku app
heroku create wise-guide-bot

# Set environment variables
heroku config:set TELEGRAM_BOT_TOKEN=your_token
heroku config:set OPENAI_API_KEY=your_key
# ... set other variables

# Deploy
git push heroku main
```

## Monitoring and Maintenance

### Check Service Status

```bash
# Supervisor
sudo supervisorctl status

# Docker
docker-compose ps

# Systemd
sudo systemctl status wise-guide-bot
```

### View Logs

```bash
# Supervisor
tail -f ~/wise_guide_bot/logs/bot.log
tail -f ~/wise_guide_bot/logs/webhook.log

# Docker
docker-compose logs -f bot
docker-compose logs -f webhook

# Systemd
sudo journalctl -u wise-guide-bot -f
```

### Database Backup

```bash
# Backup SQLite database
cp ~/wise_guide_bot/bot_data.db ~/wise_guide_bot/backups/bot_data_$(date +%Y%m%d_%H%M%S).db

# Or use cron for automatic backups
0 2 * * * cp ~/wise_guide_bot/bot_data.db ~/wise_guide_bot/backups/bot_data_$(date +\%Y\%m\%d).db
```

### Update Application

```bash
# Pull latest changes
cd ~/wise_guide_bot
git pull origin main

# Restart services
sudo supervisorctl restart wise-guide-bot wise-guide-webhook

# Or with Docker
docker-compose down
docker-compose up -d
```

## Troubleshooting

### Bot not responding

1. Check service status: `sudo supervisorctl status`
2. Check logs: `tail -f ~/wise_guide_bot/logs/bot.log`
3. Verify token: `curl https://api.telegram.org/bot<TOKEN>/getMe`

### Webhook not receiving payments

1. Check webhook logs: `tail -f ~/wise_guide_bot/logs/webhook.log`
2. Verify Robokassa notification URL is correct
3. Test with curl: `curl -X POST https://your-domain.com/webhook/robokassa/result`

### SSL certificate issues

1. Renew certificate: `sudo certbot renew`
2. Check certificate: `sudo certbot certificates`
3. Restart Nginx: `sudo systemctl restart nginx`

## Security Hardening

1. **Firewall**: Use UFW to restrict access
   ```bash
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Fail2Ban**: Protect against brute force
   ```bash
   sudo apt install fail2ban
   sudo systemctl enable fail2ban
   ```

3. **SSH Keys**: Disable password authentication
   ```bash
   # Edit /etc/ssh/sshd_config
   PasswordAuthentication no
   PubkeyAuthentication yes
   ```

4. **Regular Updates**: Keep system updated
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Performance Tuning

1. **Increase file descriptors**:
   ```bash
   echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
   echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
   ```

2. **Optimize Nginx**:
   ```nginx
   worker_processes auto;
   worker_connections 2048;
   ```

3. **Database optimization**:
   ```sql
   CREATE INDEX idx_user_messages ON messages(user_id, timestamp);
   CREATE INDEX idx_subscriptions ON subscriptions(user_id, expires_at);
   ```

---

**For additional support, refer to the main README.md**
