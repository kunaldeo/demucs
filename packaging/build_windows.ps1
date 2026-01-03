$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")

$Python = $env:PYTHON
if (-not $Python) { $Python = "python" }

$VenvDir = $env:VENV_DIR
if (-not $VenvDir) {
  if (Test-Path ".venv") { $VenvDir = ".venv" } else { $VenvDir = ".venv-build" }
}

$UseExistingVenv = $env:USE_EXISTING_VENV
if (-not $UseExistingVenv) { $UseExistingVenv = "0" }

$PythonVersion = $env:PYTHON_VERSION
if (-not $PythonVersion) { $PythonVersion = "3.9.21" }

$TorchVersion = $env:TORCH_VERSION
if (-not $TorchVersion) { $TorchVersion = "2.0.1" }

$TorchaudioVersion = $env:TORCHAUDIO_VERSION
if (-not $TorchaudioVersion) { $TorchaudioVersion = "2.0.2" }

$PyInstallerOpts = $env:PYINSTALLER_OPTS
if (-not $PyInstallerOpts) { $PyInstallerOpts = "--clean --noconfirm" }

if ($UseExistingVenv -eq "1") {
  $VenvPython = Join-Path $VenvDir "Scripts\python.exe"
  if (-not (Test-Path $VenvPython)) {
    Write-Host "Venv not found at $VenvDir. Set VENV_DIR or create it first."
    exit 1
  }
  $Python = $VenvPython
} else {
  if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv is required to create a pinned Python $PythonVersion venv."
    Write-Host "Install uv, or set USE_EXISTING_VENV=1 to use an existing venv."
    exit 1
  }
  & uv venv --clear --python $PythonVersion $VenvDir
  $Python = Join-Path $VenvDir "Scripts\python.exe"
}

$PyVer = & $Python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($PyVer -notin @("3.8","3.9","3.10","3.11")) {
  Write-Host "Python $PyVer is not compatible with torch $TorchVersion+cpu."
  Write-Host "Set PYTHON to a 3.8-3.11 interpreter (e.g. `$env:PYTHON = 'python3.11')."
  exit 1
}

& "$VenvDir\Scripts\Activate.ps1"

python -m pip --version | Out-Null
if ($LASTEXITCODE -ne 0) {
  python -m ensurepip --upgrade
}

python -m pip install --upgrade pip
python -m pip install `
  "torch==$TorchVersion+cpu" `
  "torchaudio==$TorchaudioVersion+cpu" `
  --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r (Join-Path $RootDir "packaging\requirements_packaging.txt")
python -m pip install $RootDir --no-deps

python (Join-Path $RootDir "packaging\fetch_assets.py") --os windows

$env:DEMUCS_PROJECT_ROOT = $RootDir
$env:DEMUCS_ASSETS_ROOT = (Join-Path $RootDir "packaging\assets")
pyinstaller (Join-Path $RootDir "packaging\demucs_cli.spec") $PyInstallerOpts

Write-Host "`nBuilt CLI at dist\demucs_cli`n"
