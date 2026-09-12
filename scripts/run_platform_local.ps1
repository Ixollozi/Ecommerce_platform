$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..

if (-not (Test-Path 'venv\Scripts\python.exe')) {
    python -m venv venv
    .\venv\Scripts\python.exe -m pip install -r requirements.txt
}

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
}

# sites/ is local-only (gitignored). Seed from sites.example/ when missing.
if (-not (Test-Path 'sites\registry.json')) {
    if (-not (Test-Path 'sites.example\registry.json')) {
        throw 'Missing sites.example/registry.json — cannot bootstrap platform sites.'
    }
    Write-Host 'Seeding local sites/ from sites.example/ ...'
    New-Item -ItemType Directory -Force -Path 'sites' | Out-Null
    Copy-Item 'sites.example\registry.json' 'sites\registry.json' -Force
    Get-ChildItem 'sites.example' -Directory | ForEach-Object {
        $dest = Join-Path 'sites' $_.Name
        New-Item -ItemType Directory -Force -Path $dest | Out-Null
        $cfg = Join-Path $_.FullName 'config.json'
        if (Test-Path $cfg) {
            Copy-Item $cfg (Join-Path $dest 'config.json') -Force
        }
    }
}

Write-Host ''
Write-Host '=== themes / domains ==='
Write-Host '  http://127.0.0.1:8000/                 theme=hero (Bahromusta — металл, ножи, ковка)'
Write-Host '  http://localhost:8000/                 theme=hero (Bahromusta — металл, ножи, ковка)'
Write-Host '  http://bahromusta.localhost:8000/      theme=hero (Bahromusta — металл, ножи, ковка)'
Write-Host '  http://demo-main.localhost:8000/       theme=main'
Write-Host '  http://demo-front2.localhost:8000/     theme=front2'
Write-Host '  http://demo-eshop.localhost:8000/       theme=eshop (Apex Goods / ESHOP)'
Write-Host '  http://demo-hero.localhost:8000/       theme=hero (HERO)'

Write-Host '  http://demo-meridian.localhost:8000/    theme=meridian (Meridian Lookbook)'
Write-Host '  http://demo-wood.localhost:8000/       theme=wood'
Write-Host '  http://demo-national.localhost:8000/   theme=national'
Write-Host '  http://demo-ceramics.localhost:8000/   theme=ceramics (React SPA)'
Write-Host ''
Write-Host 'Admin on EVERY domain: /admin  (login: admin / admin)'
Write-Host '  Same admin chrome + CSS for all themes (from store/static).'
Write-Host 'IMPORTANT: use platform_runserver (this script) — not plain runserver.'
Write-Host 'If styles look cached: hard refresh (Ctrl+F5).'
Write-Host 'TG: TELEGRAM_BOT_TOKEN in .env, then Admin -> Telegram settings'
Write-Host ''

.\venv\Scripts\python.exe manage.py platform_bootstrap
.\venv\Scripts\python.exe manage.py platform_runserver 8000
