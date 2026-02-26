param(
    [string]$ip = "34.228.36.29"
)

$key = "$PSScriptRoot\audible-toolkit-key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

$setup = @"
set -e

# Python 3.13
sudo dnf install -y gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget
wget -q https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz
tar xzf Python-3.13.0.tgz
cd Python-3.13.0 && ./configure --enable-optimizations -q && sudo make altinstall -j2
cd .. && rm -rf Python-3.13.0 Python-3.13.0.tgz

# Aliases
echo "alias python=python3.13" >> ~/.bashrc
echo "alias pip='python3.13 -m pip'" >> ~/.bashrc

# Git
sudo dnf install -y git

# Chromium system dependencies
sudo dnf install -y atk at-spi2-atk cups-libs libdrm libXcomposite libXdamage libXrandr mesa-libgbm pango alsa-lib libxkbcommon

# Clone repo
git clone git@github.com:Redundando/audible-toolkit.git ~/audible-toolkit

# Install Python dependencies
cd ~/audible-toolkit
python3.13 -m pip install -r requirements.txt

# Swap file (2GB)
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab

# Create config dir for credentials
mkdir -p ~/audible-toolkit/config

echo "Setup complete. Upload google_sheets_credentials.json to ~/audible-toolkit/config/ and run setup_ec2_env.ps1."
"@

ssh -i $key ec2-user@$ip $setup
