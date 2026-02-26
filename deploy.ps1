$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''
$key = "$PSScriptRoot\key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null

ssh -i $key ec2-user@$ip "cd ~/streamator && git pull && chmod +x start.sh && ~/streamator/start.sh"
