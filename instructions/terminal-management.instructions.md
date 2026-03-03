---
applyTo: '**'
description: 'Terminal management - external windows, server startup, port handling, service protection'
---

# Terminal Management

## Critical Rule: Never Block the VS Code Terminal

All servers and long-running processes MUST start in external terminal windows or with `isBackground: true`.

> **Note**: Examples below use PowerShell (Windows). On macOS/Linux, substitute: `Start-Process` → background `&` or `nohup`, `Get-NetTCPConnection` → `lsof -i :PORT` or `ss -tlnp`, `Stop-Process` → `kill`.

## Starting Servers - Preferred Method

```powershell
# Backend server in named external window
Start-Process powershell -ArgumentList "-NoExit -Command `"
    `$Host.UI.RawUI.WindowTitle = 'Backend: uvicorn :8001';
    cd backend;
    ..\venv\Scripts\Activate.ps1;
    uvicorn src.main:app --port 8001
`""

# Frontend dev server in named external window
Start-Process powershell -ArgumentList "-NoExit -Command `"
    `$Host.UI.RawUI.WindowTitle = 'Frontend: vite :5173';
    cd web;
    npm run dev
`""
```

## Port Management

```powershell
# Check if port is in use
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue

# Kill process on port
Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess |
    Get-Process | Stop-Process -Force

# Wait for server readiness
while (-not (Test-NetConnection -ComputerName localhost -Port 8001 -InformationLevel Quiet -WarningAction SilentlyContinue)) {
    Start-Sleep -Seconds 1
}
```

## Terminal Protection - CRITICAL

AI agents frequently kill running services by sending commands to the wrong terminal. Prevention is mandatory.

### Before EVERY Terminal Command
1. Is there a service running in the current terminal? Check `get_terminal_output` first.
2. Would this command interrupt a running process? If yes, use a different terminal.
3. Am I about to `cd` into a terminal running a server? STOP. Open a new terminal.

### Anti-Patterns - NEVER Do These
- Running `npm install` in a terminal that has `npm run dev` active
- Running `cd backend && pip install ...` in a terminal running uvicorn
- Sending Ctrl+C to a service terminal "just to run a quick command"
- Using `run_in_terminal` with isBackground=false when a service is running
- Killing all node/python processes to "clean up" without checking what they are

### Correct Patterns
- Use `isBackground: true` for ALL server/watch processes
- Use Start-Process to launch servers in separate windows (preferred)
- Create a NEW terminal for build/install/test commands
- Check `get_terminal_output` before reusing any terminal
- Name external windows so they're identifiable

### Recovery: Service Was Accidentally Killed
1. Immediately restart it in an external window (not the same terminal)
2. Log the incident in `memory/shared/session-log.md`
3. Wait for health check to pass before continuing other work
