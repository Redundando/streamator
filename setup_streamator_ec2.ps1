$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''
$key = "$PSScriptRoot\key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

$setup = @"
set -e
mkdir -p ~/streamator/python

cd ~/streamator/python
python3.13 -m pip install -e ".[fastapi]"
python3.13 -m pip install uvicorn
echo "Streamator setup complete."
"@

# Upload package files first
scp -i $key -r "$PSScriptRoot\python\streamator" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\python\main.py" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\python\pyproject.toml" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\python\requirements.txt" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\start.sh" ec2-user@${ip}:~/streamator/start.sh

ssh -i $key ec2-user@$ip $setup
