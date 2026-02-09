# Babblefish Setup Script (Windows PowerShell)
# Quick setup for development environment

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  Babblefish Setup Script" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Check Python
Write-Host "`nChecking Python..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion found" -ForegroundColor Green
} else {
    Write-Host "✗ Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}

# Check Node.js
Write-Host "`nChecking Node.js..." -ForegroundColor Yellow
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node --version
    Write-Host "✓ Node.js $nodeVersion found" -ForegroundColor Green
} else {
    Write-Host "✗ Node.js not found. Please install Node.js 20+" -ForegroundColor Red
    exit 1
}

# Server setup
Write-Host "`nSetting up server..." -ForegroundColor Yellow
Set-Location server

if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
}

Write-Host "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

Write-Host "Installing Python dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "✓ Server setup complete" -ForegroundColor Green

Set-Location ..

# Client setup
Write-Host "`nSetting up client..." -ForegroundColor Yellow
Set-Location client

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..."
    npm install
} else {
    Write-Host "node_modules already exists, skipping npm install"
}

Write-Host "✓ Client setup complete" -ForegroundColor Green

Set-Location ..

# Model download
Write-Host "`nModel setup..." -ForegroundColor Yellow
Write-Host "Models need to be downloaded (~3GB)"
$response = Read-Host "Download models now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Set-Location models
    python download_server_models.py
    Set-Location ..
} else {
    Write-Host "Skipping model download. Run 'cd models; python download_server_models.py' later."
}

# Environment file
Write-Host "`nEnvironment configuration..." -ForegroundColor Yellow
if (-not (Test-Path "server\.env")) {
    Write-Host "Creating .env file from template..."
    Copy-Item ".env.example" "server\.env"
    Write-Host "✓ Created server\.env" -ForegroundColor Green
    Write-Host "You can edit server\.env to customize configuration"
} else {
    Write-Host ".env already exists"
}

# Done
Write-Host "`n==================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start the server:"
Write-Host "  cd server"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "  python main.py"
Write-Host ""
Write-Host "To start the client (in another terminal):"
Write-Host "  cd client"
Write-Host "  npm run dev"
Write-Host ""
Write-Host "Then open http://localhost:3000 in your browser"
Write-Host ""
Write-Host "See docs\DEPLOYMENT.md for detailed instructions"
