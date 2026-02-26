$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''
$key = "$PSScriptRoot\key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

Start-Process powershell -ArgumentList "-NoExit", "-Command", "ssh -i '$key' ec2-user@$ip 'chmod +x ~/streamator/start.sh && ~/streamator/start.sh'"
