$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''
$key = "$PSScriptRoot\key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

$setup = @"
set -e
git clone git@github.com:Redundando/streamator.git ~/streamator
cd ~/streamator/python
python3.13 -m pip install -e ".[fastapi]"
python3.13 -m pip install uvicorn
echo "Streamator setup complete."
"@

ssh -i $key ec2-user@$ip $setup
