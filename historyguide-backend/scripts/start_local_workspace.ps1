param(
    [ValidateRange(1024, 65535)]
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
$taskRoot = Split-Path -Parent $PSScriptRoot
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw 'Create the Python 3.11+ .venv and install requirements-dev.txt first.'
}

$taskVariables = @(
    'HISTORYGUIDE_DATABASE_URL', 'HISTORYGUIDE_SCHEMA_MODE',
    'HISTORYGUIDE_API_KEY', 'HISTORYGUIDE_API_KEY_FILE',
    'HISTORYGUIDE_API_KEY_NEXT', 'HISTORYGUIDE_API_KEY_NEXT_FILE',
    'HISTORYGUIDE_OPERATOR_API_KEY', 'HISTORYGUIDE_OPERATOR_API_KEY_FILE',
    'HISTORYGUIDE_CORS_ORIGINS'
)
$taskPrevious = @{}
foreach ($taskName in $taskVariables) {
    $taskPrevious[$taskName] = [Environment]::GetEnvironmentVariable($taskName, 'Process')
}

Push-Location -LiteralPath $taskRoot
try {
    $taskSecret = Read-Host 'Choose a fresh LOCAL operator key (hidden input; use it in the workspace)' -AsSecureString
    $taskCredential = [System.Net.NetworkCredential]::new('', $taskSecret)
    $taskPlainSecret = $taskCredential.Password
    if ([string]::IsNullOrWhiteSpace($taskPlainSecret)) { throw 'A local operator key is required.' }
    if ($taskPlainSecret.Trim() -notmatch '^[\x21-\x7e]+$') { throw 'Use a local key with printable ASCII characters and no spaces.' }
    foreach ($taskName in $taskVariables) { [Environment]::SetEnvironmentVariable($taskName, $null, 'Process') }
    $env:HISTORYGUIDE_OPERATOR_API_KEY = $taskPlainSecret.Trim()
    $env:HISTORYGUIDE_API_KEY = [Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N')
    $taskDataDirectory = Join-Path $taskRoot '.local'
    New-Item -ItemType Directory -Path $taskDataDirectory -Force | Out-Null
    $taskDatabase = Join-Path $taskDataDirectory 'workspace.db'
    $env:HISTORYGUIDE_DATABASE_URL = 'sqlite:///' + $taskDatabase.Replace('\', '/')
    $env:HISTORYGUIDE_SCHEMA_MODE = 'migrated'
    if (-not (Test-Path -LiteralPath $taskDatabase)) {
        & $taskPython -m alembic upgrade head
        if ($LASTEXITCODE -ne 0) { throw 'Local database initialization failed.' }
    }
    Write-Host "Local workspace: http://127.0.0.1:$Port/operator"
    Write-Host 'Only the isolated .local/workspace.db is used. Press Ctrl+C to stop.'
    & $taskPython -m uvicorn app.main:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'The local workspace stopped with an error.' }
}
finally {
    $taskPlainSecret = $null
    $taskCredential = $null
    if ($taskSecret) { $taskSecret.Dispose() }
    foreach ($taskName in $taskVariables) {
        [Environment]::SetEnvironmentVariable($taskName, $taskPrevious[$taskName], 'Process')
    }
    Pop-Location
}
