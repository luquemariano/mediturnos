[CmdletBinding()]
param(
    [switch]$Quick,
    [switch]$Full,
    [switch]$LocalServices
)

$ErrorActionPreference = 'Continue'
$repoRoot = (Get-Location).Path
$failures = 0

function Write-Status([string]$kind, [string]$message) { Write-Host "[$kind] $message" }
function Required-Fail([string]$message) { Write-Status 'FAIL' $message; $script:failures++ }
function Run-Required([string]$label, [scriptblock]$command) {
    Write-Status 'OK' "$label..."
    & $command
    if ($LASTEXITCODE -ne 0) { Required-Fail "$label falló (exit $LASTEXITCODE)."; return $false }
    return $true
}
function Test-Command([string]$name, [bool]$required) {
    if (Get-Command $name -ErrorAction SilentlyContinue) { Write-Status 'OK' "$name disponible."; return $true }
    if ($required) { Required-Fail "No se encontró $name." } else { Write-Status 'WARN' "$name no está disponible." }
    return $false
}
function Get-Tracked([string]$path) {
    $tracked = @(git ls-files -- $path 2>$null)
    return ($tracked.Count -gt 0)
}
function Test-LocalTcp([string]$hostName, [int]$port) {
    if (Get-Command Test-NetConnection -ErrorAction SilentlyContinue) {
        return (Test-NetConnection -ComputerName $hostName -Port $port -InformationLevel Quiet -WarningAction SilentlyContinue)
    }
    try {
        $client = [Net.Sockets.TcpClient]::new()
        $task = $client.ConnectAsync($hostName, $port)
        if (-not $task.Wait(1500)) { $client.Dispose(); return $false }
        $ok = $client.Connected
        $client.Dispose()
        return $ok
    } catch { return $false }
}

if (-not (Test-Path (Join-Path $repoRoot 'requirements.txt')) -or
    -not (Test-Path (Join-Path $repoRoot 'frontend/package.json')) -or
    -not (Test-Path (Join-Path $repoRoot 'AGENTS.md'))) {
    Write-Status 'FAIL' 'El directorio actual no parece ser la raiz valida de Turnelia.'; exit 2
}

if ($Quick -and $Full) { Write-Status 'FAIL' '-Quick y -Full son mutuamente excluyentes.'; exit 2 }
$mode = if ($Full) { 'Full' } else { 'Quick' }
Write-Status 'OK' "Raiz valida; modo $mode."

if (-not (Test-Command 'git' $true)) { exit 1 }
$status = @(git status --short 2>$null)
if ($LASTEXITCODE -ne 0) { Required-Fail 'No se pudo consultar git status.' }
elseif ($status.Count -gt 0) { Write-Status 'WARN' "Working tree con $($status.Count) entrada(s); no se modifico." }
else { Write-Status 'OK' 'Working tree limpio.' }
if (@(git ls-files --others --exclude-standard 2>$null).Count -gt 0) { Write-Status 'WARN' 'Existen archivos untracked; no se modificaron.' }

$null = Test-Command 'python' $true
$null = Test-Command 'node' $true
$null = Test-Command 'npm' $true
$venvPython = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path $venvPython)) { Required-Fail '.venv no existe o no contiene Scripts/python.exe.' }
else { Run-Required 'Python del entorno virtual' { & $venvPython --version } | Out-Null }

if (-not (Test-Path (Join-Path $repoRoot 'frontend/package-lock.json'))) { Required-Fail 'Falta frontend/package-lock.json.' }
else { Write-Status 'OK' 'Archivos frontend esenciales presentes.' }

$envPath = Join-Path $repoRoot '.env'
if (Get-Tracked '.env') { Required-Fail '.env esta trackeado por Git; no se mostro su contenido.' }
elseif (Test-Path $envPath) { Write-Status 'WARN' '.env local existe y no esta trackeado; no se mostro su contenido.' }
else { Write-Status 'SKIP' '.env ausente; Quick continua porque este check no lo requiere.' }

foreach ($sensitive in @('.env', '*.pem', '*.key', '*.p12', '*.pfx', '*.dump')) {
    $tracked = @(git ls-files -- $sensitive 2>$null)
    if ($tracked.Count -gt 0) { Required-Fail "Archivo potencialmente sensible trackeado: categoria $sensitive." }
    $local = @(Get-ChildItem -Path $repoRoot -Filter $sensitive -File -ErrorAction SilentlyContinue)
    foreach ($file in $local) { if (-not (Get-Tracked $file.Name)) { Write-Status 'WARN' "Archivo potencialmente sensible local no trackeado: $($file.Name)." } }
}

Run-Required 'Import basico backend' { & $venvPython -c "import app.main" } | Out-Null

if ($LocalServices) {
    if (-not (Test-Command 'docker' $true)) { Required-Fail 'Docker es obligatorio con -LocalServices.' }
    else {
        Write-Status 'OK' 'Docker daemon...'
        & docker info *> $null
        $daemonExit = $LASTEXITCODE
        if ($daemonExit -ne 0) {
            Required-Fail "Docker daemon fallo (exit $daemonExit)."
            Write-Status 'SKIP' 'PostgreSQL y health locales omitidos porque Docker daemon no esta disponible.'
        } else {
            Write-Status 'OK' 'Docker daemon disponible.'
            & docker compose ps *> $null
            $composeExit = $LASTEXITCODE
            if ($composeExit -ne 0) { Required-Fail "Estado read-only de Docker Compose fallo (exit $composeExit)." }
        $composeDb = @(docker compose ps --services --filter status=running 2>$null)
        if ($composeDb -notcontains 'db') { Required-Fail 'El servicio PostgreSQL local db no está activo.' }
        else { Write-Status 'OK' 'El servicio PostgreSQL local db está activo.' }
        if (Test-LocalTcp '127.0.0.1' 5432) { Write-Status 'OK' 'PostgreSQL local accesible en 127.0.0.1:5432.' }
        else { Required-Fail 'PostgreSQL local no es accesible en 127.0.0.1:5432.' }
        $healthUrl = 'http://127.0.0.1:8000/health/ready'
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 5
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) { Write-Status 'OK' 'Health local /health/ready respondió correctamente.' }
            else { Required-Fail "Health local respondió HTTP $($response.StatusCode)." }
        } catch { Required-Fail 'La API local no respondió correctamente en 127.0.0.1:8000/health/ready.' }
        }
    }
} else { Write-Status 'SKIP' 'Servicios locales omitidos; usar -LocalServices para solicitarlos explicitamente.' }

if ($Full) {
    Run-Required 'pytest backend' { & $venvPython -m pytest } | Out-Null
    Push-Location (Join-Path $repoRoot 'frontend')
    try {
        Run-Required 'tests frontend' { & npm test } | Out-Null
        Run-Required 'lint frontend' { & npm run lint } | Out-Null
        Run-Required 'build frontend' { & npm run build } | Out-Null
    } finally { Pop-Location }
    Write-Status 'SKIP' 'Playwright/E2E no incorporado.'
} else { Write-Status 'SKIP' 'Full no solicitado; no se ejecutaron pytest, Vitest, lint ni build.' }

if ($failures -gt 0) { Write-Status 'FAIL' "$failures verificacion(es) obligatoria(s) fallaron."; exit 1 }
Write-Status 'OK' "Verificacion $mode finalizada con warnings permitidos."; exit 0
