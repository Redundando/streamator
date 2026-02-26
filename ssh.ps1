$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''
$key = "$PSScriptRoot\audible-toolkit-key.pem"
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null
ssh -i $key -o ServerAliveInterval=60 -o ServerAliveCountMax=10 ec2-user@$ip
