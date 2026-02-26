# EC2 Setup Guide

## Launch an EC2 Instance

1. Go to [AWS EC2 Console](https://console.aws.amazon.com/ec2)
2. Click **Launch instance**
3. Settings:
   - **Name:** `audible-toolkit`
   - **AMI:** Amazon Linux 2023
   - **Architecture:** x86
   - **Instance type:** `t3.micro`
   - **Key pair:** Create new → ED25519 → name it `audible-toolkit-key` → download `.pem`
   - **Security group:** Allow SSH
4. Place the `.pem` file in the project root (it's gitignored)

## Automated Setup

Before running, add your EC2's SSH key to GitHub:
```bash
# On EC2 (via browser-based EC2 Instance Connect):
ssh-keygen -t ed25519 -C "ec2-audible-toolkit" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
```
Add the output to [GitHub SSH keys](https://github.com/settings/keys).

Then from PowerShell on your laptop:
```powershell
# 1. Full EC2 setup (Python 3.13, git, Chromium deps, repo clone, pip install)
.\setup_ec2.ps1 -ip 54.234.41.77

# 2. Upload environment variables
.\setup_ec2_env.ps1

# 3. Upload Google credentials
scp -i "audible-toolkit-key.pem" config/google_sheets_credentials.json ec2-user@54.234.41.77:~/audible-toolkit/config/
```

## Daily Use

```powershell
# Deploy latest code
.\deploy.ps1

# SSH into EC2
.\ssh.ps1
```

On EC2:
```bash
cd ~/audible-toolkit
python3.13 generate_genres.py --n 1
```

## Web App (FastAPI)

The toolkit includes a FastAPI web app (`api/main.py`) served by uvicorn on port 8000. It provides JSON endpoints and serves the frontend as static files.

### Port setup

Port 8000 is open in the EC2 security group. However, some home routers block outbound non-standard ports, so traffic is redirected from port 80 → 8000 using iptables. This means the app is reachable at `http://<ip>` (no port number needed) from any network.

The redirect is set up by `start.sh`, which also saves the rule so it persists across reboots.

### Starting the app

```bash
~/audible-toolkit/start.sh
```

This:
1. Flushes and re-applies the iptables rule (80 → 8000)
2. Saves the rule to `/etc/sysconfig/iptables` for persistence
3. Starts uvicorn on port 8000

`deploy.ps1` automatically runs `chmod +x start.sh` after each pull since Git on Windows doesn't preserve the executable bit.

### Security group rules required

| Port | Protocol | Source    | Purpose        |
|------|----------|-----------|----------------|
| 22   | TCP      | 0.0.0.0/0 | SSH            |
| 80   | TCP      | 0.0.0.0/0 | Web app (HTTP) |
| 8000 | TCP      | 0.0.0.0/0 | uvicorn direct |

## Cost Management

- **Stop** the instance when not in use (EC2 Console → Instance State → Stop)
- The IP changes on every stop/start — update `EC2_IP` in `.env` (project root, gitignored)
- 2GB swap file is configured to prevent OOM crashes from parallel Chromium scraping
- Auto-stop after idle: `*/5 * * * * [ $(top -bn1 | grep 'Cpu(s)' | awk '{print int($2)}') -lt 5 ] && sudo shutdown -h now`
- Set shutdown behavior to **Stop** (not Terminate): EC2 Console → Actions → Instance Settings → Change shutdown behavior
