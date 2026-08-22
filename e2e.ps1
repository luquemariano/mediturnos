[CmdletBinding()]
param([switch]$Headed)

$ErrorActionPreference = 'Stop'
$repoRoot = (Get-Location).Path
$composeFile = Join-Path $repoRoot 'docker-compose.e2e.yml'
$projectName = 'turnelia-e2e'
$python = Join-Path $repoRoot '.venv/Scripts/python.exe'
$frontend = Join-Path $repoRoot 'frontend'
$apiProcess = $null
$frontendProcess = $null
$composePhaseStarted = $false
$exitCode = 0
$failurePhase = $null
$logDirectory = Join-Path ([IO.Path]::GetTempPath()) "turnelia-e2e-$PID"
$frontendStdout = Join-Path $logDirectory 'frontend.stdout.log'
$frontendStderr = Join-Path $logDirectory 'frontend.stderr.log'

function Fail([string]$phase, [string]$message) {
    $script:failurePhase = $phase
    throw "[$phase] $message"
}
function Assert-Root {
    if (-not (Test-Path (Join-Path $repoRoot 'AGENTS.md')) -or -not (Test-Path $composeFile)) { Fail 'Precondiciones' 'El directorio actual no parece ser la raíz E2E de Turnelia.' }
    if (-not (Test-Path $python)) { Fail 'Precondiciones' 'Falta .venv/Scripts/python.exe.' }
}
function Assert-E2eSecrets {
    if (-not $env:E2E_ADMIN_PASSWORD) { Fail 'Precondiciones E2E' 'Falta E2E_ADMIN_PASSWORD.' }
    if (-not $env:E2E_JWT_SECRET) { Fail 'Precondiciones E2E' 'Falta E2E_JWT_SECRET.' }
    if (-not $env:E2E_DB_PASSWORD) { Fail 'Precondiciones E2E' 'Falta E2E_DB_PASSWORD.' }
    if ($env:E2E_JWT_SECRET.Length -lt 32) { Fail 'Precondiciones E2E' 'E2E_JWT_SECRET debe tener al menos 32 caracteres.' }
}
function Assert-CleanupTarget {
    $expected = [IO.Path]::GetFullPath((Join-Path $repoRoot 'docker-compose.e2e.yml'))
    $actual = [IO.Path]::GetFullPath($composeFile)
    if ($projectName -ne 'turnelia-e2e' -or $actual -ne $expected) {
        throw '[Seguridad cleanup] El proyecto o archivo Compose E2E no coincide; no se ejecutó cleanup destructivo.'
    }
}
function Test-PortFree([int]$port) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return $null -eq $listener
}
function Wait-Http([string]$url, [int]$timeoutSeconds = 60, $process = $null, [string]$stderrPath = '') {
    $deadline = (Get-Date).AddSeconds($timeoutSeconds)
    do {
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 500) { return }
        } catch { }
        if ($null -ne $process -and $process.HasExited) {
            $detail = if ($stderrPath -and (Test-Path $stderrPath)) { (Get-Content $stderrPath -Tail 12 -ErrorAction SilentlyContinue) -join ' ' } else { 'sin stderr disponible' }
            throw "El proceso terminó antes de readiness. stderr: $detail"
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    throw "No llegó a readiness: $url"
}
function Wait-Db {
    $deadline = (Get-Date).AddSeconds(90)
    do {
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & docker compose -p $projectName -f $composeFile exec -T db psql -U turnelia_e2e -d turnelia_e2e -c 'SELECT 1' *> $null
        $probeExit = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        if ($probeExit -eq 0) { return }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    throw 'PostgreSQL E2E no llegó a healthy.'
}
function Stop-Child($process) {
    if ($null -ne $process -and -not $process.HasExited) {
        & taskkill.exe /PID $process.Id /T /F *> $null
    }
}
function Invoke-E2eCleanup {
    Stop-Child $frontendProcess
    Stop-Child $apiProcess
    if ($composePhaseStarted) {
        try { Assert-CleanupTarget } catch { Write-Host "[FAIL] Cleanup E2E: $($_.Exception.Message)"; $script:exitCode = 1; return }
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $cleanupOutput = @(& docker compose -p $projectName -f $composeFile down -v --remove-orphans 2>&1)
        $cleanupExit = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        if ($cleanupExit -eq 0) { Write-Host '[OK] Cleanup E2E completado.' }
        else {
            Write-Host "[FAIL] Cleanup E2E: docker compose down devolvió exit $cleanupExit."
            $script:exitCode = 1
        }
    }
    if (Test-Path $logDirectory) {
        Remove-Item $logDirectory -Recurse -Force -ErrorAction SilentlyContinue
    }
}

try {
    Assert-Root
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { Fail 'Precondiciones' 'Docker no está disponible.' }
    if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Fail 'Precondiciones' 'npm no está disponible.' }
    Assert-E2eSecrets
    New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
    Push-Location $frontend
    try { & npx playwright --version *> $null; if ($LASTEXITCODE -ne 0) { Fail 'Precondiciones' 'Playwright no está instalado en frontend.' } } finally { Pop-Location }

    foreach ($port in @(55432, 8001, 5174)) { if (-not (Test-PortFree $port)) { Fail 'Precondiciones' "El puerto E2E $port ya está ocupado." } }

    & docker info *> $null
    if ($LASTEXITCODE -ne 0) { Fail 'Precondiciones' 'Docker daemon no está disponible.' }
    Assert-CleanupTarget
    $composePhaseStarted = $true
    & docker compose -p $projectName -f $composeFile down -v --remove-orphans *> $null
    & docker compose -p $projectName -f $composeFile up -d db
    if ($LASTEXITCODE -ne 0) { Fail 'PostgreSQL E2E' 'No se pudo iniciar PostgreSQL E2E.' }
    Wait-Db

    $env:APP_ENV = 'test'
    $env:E2E_DATABASE_NAME = 'turnelia_e2e'
    $encodedDbPassword = [Uri]::EscapeDataString($env:E2E_DB_PASSWORD)
    $env:DATABASE_URL = "postgresql+psycopg://turnelia_e2e:$encodedDbPassword@127.0.0.1:55432/turnelia_e2e"
    $env:JWT_SECRET_KEY = $env:E2E_JWT_SECRET
    $env:JWT_ALGORITHM = 'HS256'
    $env:JWT_EXPIRE_MINUTES = '60'
    $env:CORS_ALLOWED_ORIGINS = '["http://127.0.0.1:5174"]'
    $env:FRONTEND_URL = 'http://127.0.0.1:5174'
    $env:VITE_API_URL = 'http://127.0.0.1:8001'
    $env:EMAIL_PROVIDER = 'in_memory'
    $env:OBJECT_STORAGE_PROVIDER = 'fake'
    $env:MERCADOPAGO_ACCESS_TOKEN = ''
    $env:MERCADOPAGO_PUBLIC_KEY = ''
    $env:RESEND_API_KEY = ''

    & $python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { Fail 'Migraciones E2E' 'Fallaron las migraciones de la base E2E.' }
    & $python -m app.scripts.seed_e2e
    if ($LASTEXITCODE -ne 0) { Fail 'Fixture E2E' 'Falló el fixture E2E.' }

    $apiProcess = Start-Process -FilePath $python -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8001' -WorkingDirectory $repoRoot -PassThru -NoNewWindow
    Wait-Http 'http://127.0.0.1:8001/health/ready' 60 $apiProcess
    $npmCommand = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
    if (-not $npmCommand) { Fail 'Frontend E2E' 'No se encontró npm.cmd para iniciar Vite.' }
    $frontendProcess = Start-Process -FilePath $npmCommand -ArgumentList 'run','dev','--','--host','127.0.0.1','--port','5174' -WorkingDirectory $frontend -RedirectStandardOutput $frontendStdout -RedirectStandardError $frontendStderr -PassThru -WindowStyle Hidden
    try { Wait-Http 'http://127.0.0.1:5174' 60 $frontendProcess $frontendStderr }
    catch {
        $frontendDetail = if (Test-Path $frontendStderr) { (Get-Content $frontendStderr -Tail 20 -ErrorAction SilentlyContinue) -join ' ' } else { 'sin stderr disponible' }
        Fail 'Frontend E2E' "no pudo iniciarse: $($_.Exception.Message). stderr: $frontendDetail"
    }

    Push-Location $frontend
    try {
        $playwrightArgs = @('run', 'test:e2e')
        if ($Headed) { $playwrightArgs += '--', '--headed' }
        & npm @playwrightArgs
        $suiteExit = $LASTEXITCODE
    } finally { Pop-Location }
    if ($suiteExit -ne 0) { Fail 'Playwright' "La suite terminó con exit $suiteExit." }
} catch {
    $exitCode = 1
    $message = $_.Exception.Message -replace '[\r\n]+', ' '
    if ($message -match '^\[(.+?)\]') { Write-Host "[FAIL] $message" }
    else {
        $phase = if ($failurePhase) { $failurePhase } else { 'E2E' }
        Write-Host "[FAIL] $phase`: $message"
    }
} finally {
    Invoke-E2eCleanup
}
exit $exitCode
