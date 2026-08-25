[CmdletBinding()]
param([switch]$E2E)

$ErrorActionPreference = 'Stop'
$repoRoot = (Get-Location).Path

function Write-Status([string]$kind, [string]$message) { Write-Host "[$kind] $message" }
function Fail([string]$message, [int]$code = 1) { Write-Status 'FAIL' $message; exit $code }
function Require-Command([string]$name) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $command) { Fail "No se encontró $name." }
    try { $version = (& $name --version 2>&1 | Select-Object -First 1); Write-Status 'OK' "$name disponible: $version" }
    catch { Write-Status 'WARN' "No se pudo obtener la versión de $name." }
}

if (-not (Test-Path (Join-Path $repoRoot 'requirements.txt')) -or
    -not (Test-Path (Join-Path $repoRoot 'frontend/package.json')) -or
    -not (Test-Path (Join-Path $repoRoot 'AGENTS.md'))) {
    Fail 'El directorio actual no parece ser la raiz valida de Turnelia.' 2
}

Write-Status 'OK' "Raiz valida: $repoRoot"
Write-Status 'OK' "PowerShell disponible: $($PSVersionTable.PSVersion)"
Require-Command 'python'
Require-Command 'node'
Require-Command 'npm'
if (Get-Command docker -ErrorAction SilentlyContinue) { Require-Command 'docker' } else { Write-Status 'SKIP' 'Docker no esta disponible; no es obligatorio para setup.' }

$venvPython = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path $venvPython)) {
    Write-Status 'OK' 'Creando .venv...'
    & python -m venv (Join-Path $repoRoot '.venv')
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) { Fail 'No se pudo crear .venv.' }
} else {
    try { & $venvPython --version | Out-Host; if ($LASTEXITCODE -ne 0) { throw 'invalid' }; Write-Status 'OK' '.venv existente reutilizado.' }
    catch { Fail '.venv existe pero su Python no es utilizable. No se elimino; revisar o reparar manualmente.' }
}

Write-Status 'OK' 'Instalando dependencias backend desde requirements.txt...'
& $venvPython -m pip install -r (Join-Path $repoRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { Fail 'pip falló al instalar dependencias backend.' }

$frontend = Join-Path $repoRoot 'frontend'
if (-not (Test-Path (Join-Path $frontend 'package.json')) -or -not (Test-Path (Join-Path $frontend 'package-lock.json'))) {
    Fail 'Faltan package.json o package-lock.json en frontend.'
}
Push-Location $frontend
try {
    Write-Status 'OK' 'Instalando dependencias frontend con npm ci...'
    & npm ci
    if ($LASTEXITCODE -ne 0) { Fail 'npm ci falló; no se ejecutó npm install como fallback.' }
} finally { Pop-Location }

$envFile = Join-Path $repoRoot '.env'
if (Test-Path $envFile) { Write-Status 'OK' '.env existe; no se modifico ni se mostro su contenido.' }
elseif (Test-Path (Join-Path $repoRoot '.env.example')) { Write-Status 'WARN' '.env no existe. Consultar .env.example y la documentacion; no se creo automaticamente.' }
else { Write-Status 'WARN' '.env y .env.example no existen; revisar configuracion manualmente.' }

Write-Status 'OK' 'Setup finalizado. No se ejecutaron Docker Compose, migraciones ni seed.'
if ($E2E) {
    Push-Location $frontend
    try {
        Write-Status 'OK' 'Instalando Chromium de Playwright...'
        & npx playwright install chromium
        if ($LASTEXITCODE -ne 0) { Fail 'No se pudo instalar Chromium de Playwright.' }
    } finally { Pop-Location }
}
exit 0
