# Reads Windows env vars and uploads them to EC2 ~/.bashrc
$key = "$PSScriptRoot\audible-toolkit-key.pem"
$tmpScript = "$PSScriptRoot\set_env.sh"
$ip = (Get-Content "$PSScriptRoot\.env" | Where-Object { $_ -match '^EC2_IP=' }) -replace '^EC2_IP=', ''

$varNames = @("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "BRAVE_API_KEY", "OPENAI_API_KEY", "TOOLKIT_PASSWORD")

$lines = @("#!/bin/bash")
foreach ($name in $varNames) {
    $value = [System.Environment]::GetEnvironmentVariable($name, "User")
    if (-not $value) { $value = [System.Environment]::GetEnvironmentVariable($name, "Machine") }
    if ($value) { $lines += "export $name=$value" }
    else { Write-Warning "$name not found in Windows environment" }
}
$lines += "echo 'Environment variables set.'"
$content = $lines -join "`n"
[System.IO.File]::WriteAllText($tmpScript, $content, [System.Text.UTF8Encoding]::new($false))

# Upload and run on EC2
icacls $key /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null
scp -i $key $tmpScript ec2-user@${ip}:~/set_env.sh
ssh -i $key ec2-user@$ip "bash ~/set_env.sh && cat ~/set_env.sh >> ~/.bashrc && source ~/.bashrc && rm ~/set_env.sh"

Remove-Item $tmpScript
Write-Host "Done. Environment variables added to EC2 ~/.bashrc"
