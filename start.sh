#!/bin/bash
set -e

# Kill anything on 8001
fuser -k 8001/tcp 2>/dev/null || true
sleep 2

# Port forwarding: 80 → 8001
sudo iptables -t nat -F PREROUTING
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8001
sudo iptables-save | sudo tee /etc/sysconfig/iptables > /dev/null

# Start app
cd ~/streamator/python
source ~/.bashrc
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
