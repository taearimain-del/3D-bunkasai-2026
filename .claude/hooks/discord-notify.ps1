param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("start","stop")]
  [string]$Phase
)

$ErrorActionPreference = "SilentlyContinue"
[Console]::InputEncoding = [System.Text.Encoding]::UTF8

$envPath = Join-Path $PSScriptRoot "..\..\.env"
if (-not (Test-Path $envPath)) { exit 0 }

$webhookLine = Get-Content $envPath | Where-Object { $_ -match "^DISCORD_WEBHOOK_URL=" } | Select-Object -First 1
if (-not $webhookLine) { exit 0 }
$webhookUrl = $webhookLine -replace "^DISCORD_WEBHOOK_URL=", ""
$webhookUrl = $webhookUrl.Trim()
if (-not $webhookUrl) { exit 0 }

$stdin = [Console]::In.ReadToEnd()
$agentType = $null
$resultMsg = $null
try {
  $json = $stdin | ConvertFrom-Json
  if ($json.agent_type) { $agentType = $json.agent_type }
  if ($json.last_assistant_message) { $resultMsg = $json.last_assistant_message }
} catch {}

if ($resultMsg -and $resultMsg.Length -gt 300) { $resultMsg = $resultMsg.Substring(0, 297) + "..." }

$rocket = [System.Char]::ConvertFromUtf32(0x1F680)
$check = [System.Char]::ConvertFromUtf32(0x2705)

if ($Phase -eq "start") {
  if ($agentType) { $content = "Subagent started ($agentType)" } else { $content = "Subagent started" }
  $content = "$rocket " + $content
} else {
  if ($resultMsg) { $content = "Done: $resultMsg" } else { $content = "Done" }
  if ($agentType) { $content = "($agentType) " + $content }
  $content = "$check " + $content
}

$body = @{ content = $content } | ConvertTo-Json -Compress
$bodyBytes = [System.Text.Encoding]::UTF8.GetBytes($body)
try {
  Invoke-RestMethod -Uri $webhookUrl -Method Post -Body $bodyBytes -ContentType "application/json; charset=utf-8" | Out-Null
} catch {}
exit 0
