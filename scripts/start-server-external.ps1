<#
.SYNOPSIS
    Start a server or long-running process in an external PowerShell window.

.DESCRIPTION
    Launches commands in a separate PowerShell window to prevent blocking the VS Code terminal.
    Optionally waits for a port to become available before returning.

.PARAMETER Command
    The command to execute in the external window.

.PARAMETER WorkingDir
    The working directory for the command. Defaults to current directory.

.PARAMETER Port
    Port number to wait for (optional). Script will wait until port is listening.

.PARAMETER Name
    Friendly name for the server (shown in window title).

.PARAMETER NoWait
    Don't wait for port to be ready, return immediately after starting.

.PARAMETER Timeout
    Timeout in seconds when waiting for port. Default 120.

.EXAMPLE
    .\start-server-external.ps1 -Command "npm run dev" -Port 5173 -Name "Frontend"

.EXAMPLE
    .\start-server-external.ps1 -Command "uvicorn main:app --port 8001" -WorkingDir "backend" -Port 8001

.EXAMPLE
    .\start-server-external.ps1 -Command "docker-compose up" -NoWait
#>

param(
    [Parameter(Mandatory)]
    [string]$Command,
    
    [string]$WorkingDir = (Get-Location).Path,
    
    [int]$Port = 0,
    
    [string]$Name = "Server",
    
    [switch]$NoWait,
    
    [int]$Timeout = 120
)

# Validate working directory
if (-not (Test-Path $WorkingDir)) {
    Write-Error "Working directory does not exist: $WorkingDir"
    exit 1
}

# Build the command to run in external window
$windowTitle = "$Name - $Port"
$escapedWorkingDir = $WorkingDir -replace "'", "''"
$escapedCommand = $Command -replace "'", "''"

$fullCommand = @"
`$Host.UI.RawUI.WindowTitle = '$windowTitle'
Set-Location '$escapedWorkingDir'
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  $Name' -ForegroundColor Cyan
Write-Host '  Port: $Port' -ForegroundColor Cyan
Write-Host '  Directory: $escapedWorkingDir' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
$escapedCommand
"@

# Check if port is already in use
if ($Port -gt 0) {
    $existingConnection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($existingConnection) {
        $process = Get-Process -Id $existingConnection.OwningProcess -ErrorAction SilentlyContinue
        Write-Warning "Port $Port is already in use by process: $($process.ProcessName) (PID: $($process.Id))"
        $kill = Read-Host "Kill existing process? (y/n)"
        if ($kill -eq 'y') {
            Stop-Process -Id $existingConnection.OwningProcess -Force
            Start-Sleep -Seconds 2
        } else {
            Write-Host "Aborted. Free the port manually and try again."
            exit 1
        }
    }
}

# Start the external PowerShell window
Write-Host "Starting $Name in external window..." -ForegroundColor Green
$processArgs = "-NoExit", "-Command", $fullCommand

Start-Process -FilePath "powershell.exe" -ArgumentList $processArgs

# Wait for port if specified
if ($Port -gt 0 -and -not $NoWait) {
    Write-Host "Waiting for port $Port to be available..." -ForegroundColor Yellow
    
    $elapsed = 0
    $ready = $false
    
    while ($elapsed -lt $Timeout) {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($connection) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
        $elapsed += 2
        Write-Host "." -NoNewline
    }
    
    Write-Host ""
    
    if ($ready) {
        Write-Host "$Name is ready on port $Port" -ForegroundColor Green
    } else {
        Write-Warning "$Name did not become ready within $Timeout seconds"
        Write-Host "Check the external window for errors."
    }
} elseif ($NoWait) {
    Write-Host "$Name started (not waiting for port)" -ForegroundColor Green
}

# Return success
exit 0
