<#
.SYNOPSIS
    Installs the REUSABLE_AI_KIT globally for VS Code Copilot access.

.DESCRIPTION
    This script installs the AI Kit to your VS Code User directory, making it
    automatically available to GitHub Copilot in ALL projects without needing
    to copy files to each project.

    After installation:
    - Consolidated instruction files are loaded automatically
    - Registered custom agents are available
    - All prompts are accessible via slash commands
    - Memory system is initialized
    - One command integrates into any project: /setup-ai-kit

.PARAMETER Uninstall
    Remove the global installation

.EXAMPLE
    .\install-global.ps1
    # Installs globally

.EXAMPLE
    .\install-global.ps1 -Uninstall
    # Removes global installation

.NOTES
    Requires: VS Code or VS Code Insiders, GitHub Copilot extension
    Location: User directory at %APPDATA%\Code\User\  (or Code - Insiders)
    macOS/Linux: use scripts/install-global.sh
#>

param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

# Paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$KitRoot = Split-Path -Parent $ScriptDir

# Prefer VS Code Insiders if installed, fall back to stable
$VSCodeInsidersDir = "$env:APPDATA\Code - Insiders\User"
$VSCodeStableDir   = "$env:APPDATA\Code\User"
$VSCodeUserDir = if (Test-Path $VSCodeInsidersDir) { $VSCodeInsidersDir } else { $VSCodeStableDir }

$InstructionsDir = "$VSCodeUserDir\Instructions"
$PromptsDir      = "$VSCodeUserDir\prompts"
$GlobalKitDir    = "$VSCodeUserDir\REUSABLE_AI_KIT"

function Write-Header {
    param([string]$Text)
    $line = '=' * 60
    Write-Host ""
    Write-Host $line -ForegroundColor Cyan
    Write-Host " $Text" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
    Write-Host ""
}

function Write-Step {
    param([string]$Text)
    Write-Host "[+] $Text" -ForegroundColor Green
}

function Write-Info {
    param([string]$Text)
    Write-Host "    $Text" -ForegroundColor Gray
}

function Write-Warning {
    param([string]$Text)
    Write-Host "[!] $Text" -ForegroundColor Yellow
}

function Install-GlobalKit {
    Write-Header "Installing REUSABLE_AI_KIT Globally"
    
    # Verify source exists
    if (-not (Test-Path $KitRoot)) {
        throw "Kit not found at: $KitRoot"
    }
    
    # Create VS Code User directories if needed
    Write-Step "Creating VS Code User directories..."
    @($InstructionsDir, $PromptsDir, $GlobalKitDir) | ForEach-Object {
        if (-not (Test-Path $_)) {
            New-Item -ItemType Directory -Path $_ -Force | Out-Null
            Write-Info "Created: $_"
        }
    }
    
    # Copy the entire kit to a global location
    Write-Step "Copying AI Kit to global location..."
    $CopyParams = @{
        Path = "$KitRoot\*"
        Destination = $GlobalKitDir
        Recurse = $true
        Force = $true
    }
    Copy-Item @CopyParams
    Write-Info "Installed to: $GlobalKitDir"

    # Runtime root is the kit root itself (no subfolder needed)
    $RuntimeRoot = $GlobalKitDir
    Write-Info "Runtime root: $RuntimeRoot"
    Write-Info "VS Code User: $VSCodeUserDir"
    
    # Create the global bootstrap instruction
    Write-Step "Creating global bootstrap instruction..."
    
    # Read the template and customize it
    $TemplateCandidates = @(
        "$KitRoot\templates\global-bootstrap.instructions.md"
    )
    $TemplateFile = $TemplateCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (Test-Path $TemplateFile) {
        $BootstrapContent = Get-Content $TemplateFile -Raw
        # Replace placeholder paths with actual paths
        $BootstrapContent = $BootstrapContent -replace '%APPDATA%\\Code\\User\\REUSABLE_AI_KIT', $RuntimeRoot
        $BootstrapContent = $BootstrapContent -replace '%APPDATA%\\Code\\User\\Instructions', $InstructionsDir
        # Add installation timestamp
        $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $BootstrapContent = $BootstrapContent -replace '> It is installed by running:', "> Installed: $Timestamp`n> It is installed by running:"
    } else {
        # Fallback inline template if template file not found
        $BootstrapContent = @"
---
applyTo: '**'
description: 'GLOBAL: Auto-loads REUSABLE_AI_KIT for all projects. Installed by install-global.ps1'
---

# REUSABLE_AI_KIT Global Bootstrap

> **This instruction auto-loads the AI Kit for ALL projects globally.**
> Installed: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
> Kit Location: $GlobalKitDir

## Automatic Loading Requirements

When working on ANY project, the AI agent MUST:

### Step 1: Load Core Rules (CRITICAL)
Read and follow this file FIRST:
$RuntimeRoot\instructions\000-core-rules.instructions.md

### Step 2: Load Orchestration  
Read and follow this file SECOND:
$RuntimeRoot\instructions\orchestration.instructions.md

### Step 3: Load All Other Instructions
Read all remaining instruction files:
$RuntimeRoot\instructions\*.instructions.md

## Quick Access

| Resource | Path |
|----------|------|
| Instructions | $RuntimeRoot\instructions\ |
| Agents | $RuntimeRoot\agents\ |
| Prompts | $RuntimeRoot\prompts\ |
| Memory | $RuntimeRoot\memory\ |
| Tools | $RuntimeRoot\tools\ |
| Scripts | $GlobalKitDir\scripts\ |

## Project-Specific Memory

For project-specific memory that persists:
- Use \`/setup-ai-kit\` prompt to create local memory folder
- Or manually create \`.copilot/memory/\` in project root

## Available Commands

- \`/setup-ai-kit\` - Integrate kit into current project (creates local .copilot folder)
- \`/update-ai-kit\` - Update the global kit installation
- Load any prompt: Reference prompts by name

"@
    }
    
    $BootstrapPath = "$InstructionsDir\000-reusable-ai-kit-global.instructions.md"
    Set-Content -Path $BootstrapPath -Value $BootstrapContent -Encoding UTF8
    Write-Info "Created: $BootstrapPath"
    
    # Copy prompts to global prompts folder
    Write-Step "Installing global prompts..."
    
    # setup-ai-kit prompt
    $SetupPromptSource = "$RuntimeRoot\prompts\setup-ai-kit.prompt.md"
    if (Test-Path $SetupPromptSource) {
        $SetupPromptContent = Get-Content $SetupPromptSource -Raw
        # Customize paths in the prompt
        $SetupPromptContent = $SetupPromptContent -replace '\[DETECTED_PATH\]', $GlobalKitDir
        $SetupPromptPath = "$PromptsDir\setup-ai-kit.prompt.md"
        Set-Content -Path $SetupPromptPath -Value $SetupPromptContent -Encoding UTF8
        Write-Info "Created: $SetupPromptPath"
    } else {
        Write-Warning "setup-ai-kit.prompt.md not found in kit, creating minimal version..."
        $SetupPromptContent = @"
---
agent: agent
description: 'Integrate REUSABLE_AI_KIT into current project. Creates local configuration and memory.'
tools: ["read", "edit", "search"]
---

# Setup AI Kit for This Project

Create .copilot/copilot-instructions.md and .copilot/memory/ structure.
Global kit location: $GlobalKitDir
"@
        $SetupPromptPath = "$PromptsDir\setup-ai-kit.prompt.md"
        Set-Content -Path $SetupPromptPath -Value $SetupPromptContent -Encoding UTF8
    }
    Write-Info "Created: $SetupPromptPath"
    
    # update-ai-kit prompt
    Write-Step "Creating /update-ai-kit prompt..."
    $UpdatePromptContent = @"
---
agent: agent
description: 'Update the globally installed REUSABLE_AI_KIT to the latest version'
tools: ["read", "search", "execute"]
---

# Update AI Kit

You are updating the globally installed REUSABLE_AI_KIT.

## Steps

1. **Check Current Version**
   Read: \`$GlobalKitDir\README.md\`
   Extract the current version number.

2. **Run Update Script**
   If the kit has a git remote configured, pull latest:
   \`\`\`powershell
   cd "$GlobalKitDir"
   git pull
   \`\`\`
   
   Or re-run the installation script if updating from source:
   \`\`\`powershell
   & "$GlobalKitDir\scripts\install-global.ps1"
   \`\`\`

3. **Report Changes**
   Show what changed in the update.
"@

    $UpdatePromptPath = "$PromptsDir\update-ai-kit.prompt.md"
    Set-Content -Path $UpdatePromptPath -Value $UpdatePromptContent -Encoding UTF8
    Write-Info "Created: $UpdatePromptPath"
    
    # kit-status prompt - copy from kit
    Write-Step "Creating /kit-status prompt..."
    $StatusPromptSource = "$RuntimeRoot\prompts\kit-status.prompt.md"
    if (Test-Path $StatusPromptSource) {
        Copy-Item -Path $StatusPromptSource -Destination "$PromptsDir\kit-status.prompt.md" -Force
        Write-Info "Created: $PromptsDir\kit-status.prompt.md"
    }
    
    # Install custom agents to prompts folder (VS Code discovers .agent.md files in prompts/)
    Write-Step "Installing custom agents..."
    $AgentFiles = Get-ChildItem -Path "$RuntimeRoot\agents" -Filter "*.agent.md" -File -ErrorAction SilentlyContinue
    foreach ($Agent in $AgentFiles) {
        $AgentDest = Join-Path $PromptsDir $Agent.Name
        Copy-Item -Path $Agent.FullName -Destination $AgentDest -Force
        Write-Info "Created: $AgentDest"
    }

    # Setup DuckDB (required by global_memory.py)
    Write-Step "Checking DuckDB (required for memory tool)..."
    $PythonBin = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonBin) { $PythonBin = Get-Command python3 -ErrorAction SilentlyContinue }
    if ($PythonBin) {
        $duckOk = & $PythonBin.Source -c "import duckdb" 2>$null; $duckImported = $LASTEXITCODE -eq 0
        if ($duckImported) {
            Write-Info "duckdb already installed v"
        } else {
            Write-Info "Installing duckdb..."
            & $PythonBin.Source -m pip install duckdb --quiet
            if ($LASTEXITCODE -eq 0) { Write-Info "duckdb installed v" }
            else { Write-Warning "Could not install duckdb. Run: pip install duckdb" }
        }
        # Initialize memory DB
        $MemoryDb = "$RuntimeRoot\memory\shared\global-memory.duckdb"
        if (-not (Test-Path $MemoryDb)) {
            & $PythonBin.Source "$RuntimeRoot\tools\global_memory.py" --db $MemoryDb init | Out-Null
            if ($LASTEXITCODE -eq 0) { Write-Info "Memory database initialized v" }
            else { Write-Warning "Memory init failed — run manually: python global_memory.py init" }
        } else {
            Write-Info "Memory database exists v"
        }
    } else {
        Write-Warning "Python not found — install Python 3, then: pip install duckdb"
    }
    Write-Step "Creating /verify-ai-kit prompt..."
    $VerifyPromptContent = @"
---
agent: agent
description: 'Verify the REUSABLE_AI_KIT is working correctly in current project'
tools: ["read", "search", "execute"]
---

# Verify AI Kit Installation

You are verifying that the REUSABLE_AI_KIT is properly installed and functioning.

## Verification Checklist

### 1. Global Installation Check
Verify these files exist:
- \`$GlobalKitDir\README.md\` - Main kit
- \`$InstructionsDir\000-reusable-ai-kit-global.instructions.md\` - Bootstrap

### 2. Agent Availability Check
List available agents by checking:
- \`$PromptsDir\*.agent.md\` files

### 3. Prompt Availability Check
List available prompts by checking:
- \`$PromptsDir\*.prompt.md\` files

### 4. Project Integration Check (if applicable)
If the project has \`.copilot/\` folder:
- Check for \`.copilot/copilot-instructions.md\`
- Check for \`.copilot/memory/\` structure

### 5. Memory System Check
Check if memory directories exist:
- \`$GlobalKitDir\memory\` (global memory)
- \`.copilot/memory/\` (project memory, if integrated)

## Report Format

\`\`\`
=== AI Kit Verification Report ===

Global Installation: [OK/MISSING]
- Kit Location: $GlobalKitDir
- Bootstrap: [OK/MISSING]

Agents Available: [count]
- [list of agent names]

Prompts Available: [count]  
- [list of prompt names]

Project Integration: [INTEGRATED/NOT INTEGRATED]
- .copilot folder: [EXISTS/NOT FOUND]
- Memory structure: [COMPLETE/PARTIAL/MISSING]

Status: [FULLY OPERATIONAL / NEEDS ATTENTION / NOT INSTALLED]
\`\`\`
"@
    $VerifyPromptPath = "$PromptsDir\verify-ai-kit.prompt.md"
    Set-Content -Path $VerifyPromptPath -Value $VerifyPromptContent -Encoding UTF8
    Write-Info "Created: $VerifyPromptPath"
    
    # Success message
    Write-Header "Installation Complete!"
    
    Write-Host "The REUSABLE_AI_KIT is now globally installed." -ForegroundColor Green
    Write-Host ""
    $InstructionCount = (Get-ChildItem -Path "$RuntimeRoot\instructions" -Filter "*.instructions.md" -File | Measure-Object).Count
    $AgentCount = (Get-ChildItem -Path "$RuntimeRoot\agents" -Filter "*.agent.md" -File | Measure-Object).Count
    $PromptCount = (Get-ChildItem -Path "$RuntimeRoot\prompts" -Recurse -Filter "*.prompt.md" -File | Measure-Object).Count
    Write-Host "What's available:" -ForegroundColor White
    Write-Host "  - $InstructionCount instruction files (auto-loaded for all projects)" -ForegroundColor Gray
    Write-Host "  - $AgentCount custom agents" -ForegroundColor Gray
    Write-Host "  - $PromptCount prompts for complex tasks" -ForegroundColor Gray
    Write-Host "  - Memory system for persistent learning" -ForegroundColor Gray
    Write-Host "  - Quality gates, impact analysis, context optimization" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Getting Started:" -ForegroundColor White
    Write-Host "  1. Open any project in VS Code" -ForegroundColor Gray
    Write-Host "  2. Type: /setup-ai-kit" -ForegroundColor Cyan
    Write-Host "  3. The kit is now active for that project!" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or just start working - the kit is already active globally!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Locations:" -ForegroundColor White
    Write-Host "  Kit:          $GlobalKitDir" -ForegroundColor Gray
    Write-Host "  Bootstrap:    $BootstrapPath" -ForegroundColor Gray
    Write-Host "  Setup Prompt: $SetupPromptPath" -ForegroundColor Gray
    Write-Host ""
}

function Uninstall-GlobalKit {
    Write-Header "Uninstalling REUSABLE_AI_KIT"

    $KitAgentPromptPaths = @()
    $AgentSourceDir = if (Test-Path "$GlobalKitDir\v3\agents") { "$GlobalKitDir\v3\agents" } elseif (Test-Path "$GlobalKitDir\agents") { "$GlobalKitDir\agents" } else { $null }
    if ($AgentSourceDir) {
        $KitAgentPromptPaths = Get-ChildItem -Path $AgentSourceDir -Filter "*.agent.md" -File |
            ForEach-Object { Join-Path $PromptsDir $_.Name }
    }
    
    $ToRemove = @(
        "$GlobalKitDir",
        "$InstructionsDir\000-reusable-ai-kit-global.instructions.md",
        "$PromptsDir\setup-ai-kit.prompt.md",
        "$PromptsDir\update-ai-kit.prompt.md",
        "$PromptsDir\kit-status.prompt.md",
        "$PromptsDir\verify-ai-kit.prompt.md"
    )

    if ($KitAgentPromptPaths.Count -gt 0) {
        $ToRemove += $KitAgentPromptPaths
    }
    
    foreach ($Path in $ToRemove) {
        if (Test-Path $Path) {
            Remove-Item -Path $Path -Recurse -Force
            Write-Step "Removed: $Path"
        } else {
            Write-Warning "Not found: $Path"
        }
    }
    
    Write-Header "Uninstall Complete"
    Write-Host "The global AI Kit has been removed." -ForegroundColor Green
    Write-Host "Local project configurations (.copilot folders) were not modified." -ForegroundColor Gray
}

# Main
try {
    if ($Uninstall) {
        Uninstall-GlobalKit
    } else {
        Install-GlobalKit
    }
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    exit 1
}
