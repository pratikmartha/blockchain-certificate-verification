# CertChain Deployment Guide 🚀

This document provides complete instructions for deploying the **CertChain: Blockchain Certificate Verification System** in various environments, from single-container Docker setups to cloud platforms and traditional Linux servers.

---

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Quick Deployment with Docker & Docker Compose](#1-docker--docker-compose)
3. [Cloud PaaS Deployment (Render / Railway / Heroku)](#2-cloud-paas-deployment)
4. [Linux VPS Deployment (Ubuntu / Nginx / Systemd)](#3-linux-vps-deployment-ubuntu--nginx)
5. [Windows Server / Local Production (Waitress WSGI)](#4-windows-server--local-production)
6. [Ethereum Network Configuration (Local, Ganache, Sepolia Testnet)](#5-blockchain-network-options)
7. [Environment Variables Reference](#6-environment-variables-reference)

---

## Architecture Overview

```
                      +-----------------------------+
                      |   Cloud / Web Traffic       |
                      +--------------+--------------+
                                     |
                          HTTPS :443 / HTTP :80
                                     v
                      +-----------------------------+
                      |  Reverse Proxy (Nginx/Cloud)|
                      +--------------+--------------+
                                     |
                          Reverse Proxy / Port 5000
                                     v
                      +-----------------------------+
                      | Production WSGI (Gunicorn / |
                      | Waitress with 4 threads)    |
                      +--------------+--------------+
                                     |
                      +--------------v--------------+
                      | Flask Application (app.py)  |
                      +----+-------------------+----+
                           |                   |
            +--------------v---+      +--------v------------------+
            | SQLite Database  |      | Blockchain Provider       |
            | (metadata & txs) |      | - Embedded Py-EVM node OR |
            +------------------+      | - External Ganache / RPC  |
                                      | - Ethereum Sepolia Testnet|
                                      +---------------------------+
```

---

## 1. Docker & Docker Compose

Docker is the recommended and most portable method to deploy CertChain.

### Quick Start with Docker Compose
```bash
# 1. Clone repository
git clone <repo-url>
cd BlockchainCertificate

# 2. Build and launch container in background
docker compose up -d --build

# 3. Check container logs
docker compose logs -f

# 4. Access the portal
open http://localhost:5000
```

### Direct Docker Run
```bash
# Build Docker image
docker build -t certchain:latest .

# Run with persistent volume for database and QR codes
docker run -d \
  -p 5000:5000 \
  -e SECRET_KEY="your-production-secret-key" \
  -v certchain_data:/app/data \
  -v certchain_qr:/app/static/qr_codes \
  --name certchain \
  certchain:latest
```

---

## 2. Cloud PaaS Deployment

### A. Deploy to Render (Render.com)
CertChain includes a pre-configured `render.yaml` blueprint.

1. Push your repository to **GitHub** or **GitLab**.
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New > Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml`.
4. Click **Apply**.
5. Your service will build and deploy automatically at `https://<your-service>.onrender.com`.

### B. Deploy to Railway (Railway.app)
1. In Railway, click **New Project > Deploy from GitHub repo**.
2. Select your repository.
3. Railway automatically detects the `Dockerfile` and `Procfile`.
4. Under **Variables**, add:
   - `SECRET_KEY`: `<generate-a-random-string>`
   - `PORT`: `5000`
5. Railway provides an automatic public domain with SSL.

### C. Deploy to Heroku
```bash
# Login to Heroku
heroku login

# Create app
heroku create certchain-app

# Set production environment variables
heroku config:set SECRET_KEY="secure-random-secret-key"

# Deploy
git push heroku main
```

---

## 3. Linux VPS Deployment (Ubuntu / Nginx)

For full control on DigitalOcean, AWS EC2, Linode, or Hetzner.

### 1. Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git build-essential
```

### 2. Clone & Setup Virtualenv
```bash
cd /var/www
sudo git clone <repo-url> certchain
cd certchain
sudo python3 -m venv venv
sudo ./venv/bin/pip install --upgrade pip
sudo ./venv/bin/pip install -r requirements.txt
sudo chown -R www-data:www-data /var/www/certchain
```

### 3. Create Systemd Service
Create `/etc/systemd/system/certchain.service`:
```ini
[Unit]
Description=CertChain Blockchain Certificate Verification System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/certchain
Environment="PATH=/var/www/certchain/venv/bin"
Environment="PORT=5000"
Environment="HOST=127.0.0.1"
Environment="SECRET_KEY=change-to-a-very-secure-secret-key"
ExecStart=/var/www/certchain/venv/bin/gunicorn --workers 1 --threads 4 --timeout 120 --bind 127.0.0.1:5000 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable certchain
sudo systemctl start certchain
sudo systemctl status certchain
```

### 4. Configure Nginx Reverse Proxy
Create `/etc/nginx/sites-available/certchain`:
```nginx
server {
    server_name certificates.yourdomain.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/certchain/static/;
        expires 30d;
    }
}
```

Enable site and configure SSL:
```bash
sudo ln -s /etc/nginx/sites-available/certchain /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Obtain free SSL certificate
sudo certbot --nginx -d certificates.yourdomain.com
```

---

## 4. Windows Server / Local Production

To run a production-grade WSGI server on Windows without Docker:

```cmd
# Double click or run in terminal:
run_prod.bat
```
Or manually:
```cmd
venv\Scripts\activate.bat
python prod.py
```
This automatically invokes **Waitress** WSGI, providing multi-threaded request processing, timeouts, and resource control.

---

## 5. Blockchain Network Options

CertChain is built with dynamic blockchain provider resolution:

| Scenario | Setup Required | Description |
|---|---|---|
| **Zero-Config (Default)** | None | Runs on embedded **Py-EVM local Ethereum node**. Ideal for instant demo, staging, or self-contained deployments. |
| **Local Ganache Node** | `RPC_URL=http://127.0.0.1:7545` | Connects to Ganache GUI / CLI. Preserves on-chain state between restarts. |
| **Ethereum Sepolia Testnet** | `RPC_URL=https://sepolia.infura.io/v3/...`<br>`PRIVATE_KEY=0x...` | Anchors certificates to Ethereum Sepolia Public Testnet. Signed transactions with cryptographic validation. |
| **Polygon / Base / Arbitrum** | Set corresponding `RPC_URL` & `PRIVATE_KEY` | Ultra-low gas cost production blockchain anchor. |

---

## 6. Environment Variables Reference

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `0.0.0.0` | IP interface to bind WSGI server |
| `PORT` | `5000` | HTTP port for web server |
| `FLASK_DEBUG` | `0` | Debug mode (`1` for development, `0` for production) |
| `SECRET_KEY` | default fallback | Flask session cryptographic signing key |
| `RPC_URL` | None | External Ethereum node HTTP RPC endpoint |
| `PRIVATE_KEY` | None | Hex private key used to sign on-chain transactions |
| `CONTRACT_ADDRESS`| None | Pre-deployed smart contract address (optional) |
| `DATABASE_PATH` | `./database.db` | Custom file path for SQLite database |
| `QR_FOLDER` | `./static/qr_codes` | Custom directory for generated QR codes |

---

## 7. Verification & Health Monitoring

The deployment includes an automated liveness probe for monitoring uptime:

```bash
curl -I http://localhost:5000/health
# Returns HTTP 200 OK
# {"service":"certchain-blockchain-verification","status":"healthy","timestamp":"..."}
```

Diagnostics endpoint:
```bash
curl http://localhost:5000/api/status
# Returns Ethereum node connection, contract address, block number, balance
```
