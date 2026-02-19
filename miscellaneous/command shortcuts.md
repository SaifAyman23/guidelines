# PowerShell Command Shortcuts Guide
### For Django, npm, and other CLI-heavy workflows

---

## The Problem

Repeating long commands dozens of times a day is tedious:

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

PowerShell lets you create **persistent shortcuts** that work globally across your system.

---

## How It Works: The PowerShell Profile

PowerShell has a profile file — a script that runs every time a new session starts. Think of it like a startup config where you define your own commands.

**Open or create your profile:**
```powershell
notepad $PROFILE
```

If it doesn't exist yet:
```powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

Anything you add here becomes available in every PowerShell session.

---

## Django Shortcut

Add this to your profile:

```powershell
function pm {
    python manage.py @args
}
```

**Usage:**
```powershell
pm makemigrations
pm makemigrations myapp
pm migrate
pm migrate --fake
pm runserver
pm runserver 0.0.0.0:8000
pm shell
pm createsuperuser
pm collectstatic
pm test myapp
```

`@args` passes everything you type after `pm` directly to `python manage.py`, so all flags and arguments work as expected.

---

## Other Useful Shortcuts

### pip
```powershell
function pip-install { pip install @args }
function pipi { pip install @args }          # even shorter
function pipf { pip freeze }
function pipfr { pip freeze > requirements.txt }
```

### Virtual Environments
```powershell
function venv-create { python -m venv .venv }
function venv-on { .\.venv\Scripts\Activate.ps1 }
function venv-off { deactivate }
```

### Git
```powershell
function gs { git status }
function ga { git add @args }
function gc { git commit -m @args }
function gp { git push }
function gl { git log --oneline --graph --decorate -20 }
function gco { git checkout @args }
function gcb { git checkout -b @args }
```

### npm / Node
```powershell
function ni { npm install @args }
function nr { npm run @args }
function ns { npm start }
function nb { npm run build }
function nt { npm test }
```

### Docker
```powershell
function dcu { docker-compose up @args }
function dcd { docker-compose down }
function dcb { docker-compose build }
function dps { docker ps }
function dlogs { docker-compose logs -f @args }
```

### Navigation
```powershell
function .. { Set-Location .. }
function ... { Set-Location ..\.. }
function proj { Set-Location C:\Users\YourName\Projects }
```

---

## A Full Django Developer Profile

Here's a complete ready-to-use profile for a Django developer:

```powershell
# Django
function pm { python manage.py @args }

# Virtual Environments
function venv-create { python -m venv .venv }
function venv-on { .\.venv\Scripts\Activate.ps1 }
function venv-off { deactivate }

# pip
function pipi { pip install @args }
function pipf { pip freeze }
function pipfr { pip freeze > requirements.txt }

# Git
function gs { git status }
function ga { git add @args }
function gc { git commit -m @args }
function gp { git push }
function gl { git log --oneline --graph --decorate -20 }
function gco { git checkout @args }
function gcb { git checkout -b @args }

# Navigation
function .. { Set-Location .. }
function ... { Set-Location ..\.. }
```

---

## Applying Changes

After editing your profile, reload it in the current session:

```powershell
. $PROFILE
```

Or just open a new PowerShell window — the profile loads automatically.

---

## Tips

**Check your profile location:**
```powershell
echo $PROFILE
```

**See all your custom functions:**
```powershell
Get-Command -CommandType Function
```

**Execution policy** — if PowerShell blocks your profile from running, run this once as Administrator:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Virtual environment note:** The `pm` shortcut uses whichever `python` is currently active in your session. Always activate your virtual environment first with `venv-on` before running `pm`.

---

## Local-only Alternative (no global setup)

If you want a shortcut that only works inside a specific project folder, create a `pm.bat` file in that folder:

```bat
@echo off
python manage.py %*
```

This requires no profile setup, but only works when you're in that directory (and you'll need to call it as `./pm` in PowerShell or Git Bash).
