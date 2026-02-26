$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''
$key = "$PSScriptRoot\key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

# Sync python package
scp -i $key -r "$PSScriptRoot\python\streamator" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\python\main.py" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\python\pyproject.toml" ec2-user@${ip}:~/streamator/python/
scp -i $key "$PSScriptRoot\python\requirements.txt" ec2-user@${ip}:~/streamator/python/

# Fix start.sh permissions and restart
ssh -i $key ec2-user@$ip "chmod +x ~/streamator/start.sh && ~/streamator/start.sh"
