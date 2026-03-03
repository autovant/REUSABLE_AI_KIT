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

# ── Manifest helpers ──────────────────────────────────────────────────────────
$ManifestPath = "$GlobalKitDir\.kit-manifest"

function Read-Manifest {
    if (Test-Path $ManifestPath) {
        return (Get-Content $ManifestPath | Where-Object { $_ -match '\S' })
    }
    return @()
}

function Write-Manifest {
    param([string[]]$Entries)
    $Entries | Sort-Object -Unique | Set-Content -Path $ManifestPath -Encoding UTF8
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

    # Clean up files from a previous Kit install (manifest-tracked only)
    $PreviousManifest = Read-Manifest
    if ($PreviousManifest.Count -gt 0) {
        Write-Step "Cleaning previous Kit files (manifest-tracked)..."
        foreach ($OldFile in $PreviousManifest) {
            $OldPath = Join-Path $VSCodeUserDir $OldFile
            if (Test-Path $OldPath) {
                Remove-Item -Path $OldPath -Force -ErrorAction SilentlyContinue
            }
        }
    }
    $ManifestEntries = [System.Collections.Generic.List[string]]::new()
    
    # Copy the kit to a global location (exclude dev/build artifacts)
    Write-Step "Copying AI Kit to global location..."
    $ExcludeDirs = @('.git', '.venv', '__pycache__', '_archive', 'node_modules', 'plans')
    
    # Clean stale excluded dirs from previous installs
    foreach ($Excl in $ExcludeDirs) {
        $ExclPath = Join-Path $GlobalKitDir $Excl
        if (Test-Path $ExclPath) {
            Remove-Item -Path $ExclPath -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Copy top-level files
    Get-ChildItem -Path $KitRoot -File | Copy-Item -Destination $GlobalKitDir -Force
    
    # Copy directories, excluding dev artifacts
    Get-ChildItem -Path $KitRoot -Directory |
        Where-Object { $ExcludeDirs -notcontains $_.Name } |
        ForEach-Object {
            $Dest = Join-Path $GlobalKitDir $_.Name
            if (Test-Path $Dest) { Remove-Item -Path $Dest -Recurse -Force }
            Copy-Item -Path $_.FullName -Destination $Dest -Recurse -Force
        }
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
    
    # Copy Kit instruction files to VS Code User Instructions folder
    # VS Code only auto-loads .instructions.md from this directory — applyTo scoping requires it
    # SAFETY: Skip any file that already exists and was NOT installed by a previous Kit run
    Write-Step "Installing instruction files..."
    $InstructionFiles = Get-ChildItem -Path "$RuntimeRoot\instructions" -Filter "*.instructions.md" -File -ErrorAction SilentlyContinue
    foreach ($Instr in $InstructionFiles) {
        $InstrDest = Join-Path $InstructionsDir $Instr.Name
        $RelPath = "Instructions\$($Instr.Name)"
        if ((Test-Path $InstrDest) -and ($PreviousManifest -notcontains $RelPath)) {
            Write-Warning "Skipped (user file exists): $($Instr.Name)"
            continue
        }
        Copy-Item -Path $Instr.FullName -Destination $InstrDest -Force
        $ManifestEntries.Add($RelPath)
        Write-Info "Installed: $($Instr.Name)"
    }
    
    # Copy prompts to global prompts folder
    Write-Step "Installing global prompts..."
    
    # Copy ALL prompt files (including pipelines subdirectory)
    # SAFETY: Skip any file that already exists and was NOT installed by a previous Kit run
    $PromptFiles = Get-ChildItem -Path "$RuntimeRoot\prompts" -Filter "*.prompt.md" -File -ErrorAction SilentlyContinue
    foreach ($Prompt in $PromptFiles) {
        $PromptDest = Join-Path $PromptsDir $Prompt.Name
        $RelPath = "prompts\$($Prompt.Name)"
        if ((Test-Path $PromptDest) -and ($PreviousManifest -notcontains $RelPath)) {
            Write-Warning "Skipped (user file exists): $($Prompt.Name)"
            continue
        }
        $PromptContent = Get-Content $Prompt.FullName -Raw
        # Replace placeholder paths with actual install location
        $PromptContent = $PromptContent -replace '\[DETECTED_PATH\]', $GlobalKitDir
        Set-Content -Path $PromptDest -Value $PromptContent -Encoding UTF8
        $ManifestEntries.Add($RelPath)
        Write-Info "Installed: $($Prompt.Name)"
    }

    # Copy pipeline prompts (subdirectory)
    $PipelinesSource = "$RuntimeRoot\prompts\pipelines"
    if (Test-Path $PipelinesSource) {
        $PipelinesDest = "$PromptsDir\pipelines"
        if (-not (Test-Path $PipelinesDest)) {
            New-Item -ItemType Directory -Path $PipelinesDest -Force | Out-Null
        }
        $PipelineFiles = Get-ChildItem -Path $PipelinesSource -Filter "*.prompt.md" -File -ErrorAction SilentlyContinue
        foreach ($Pipeline in $PipelineFiles) {
            $PipelineDest = Join-Path $PipelinesDest $Pipeline.Name
            $RelPath = "prompts\pipelines\$($Pipeline.Name)"
            if ((Test-Path $PipelineDest) -and ($PreviousManifest -notcontains $RelPath)) {
                Write-Warning "Skipped (user file exists): pipelines/$($Pipeline.Name)"
                continue
            }
            Copy-Item -Path $Pipeline.FullName -Destination $PipelineDest -Force
            $ManifestEntries.Add($RelPath)
            Write-Info "Installed: pipelines/$($Pipeline.Name)"
        }
    }
    
    # Install custom agents to prompts folder (VS Code discovers .agent.md files in prompts/)
    # SAFETY: Skip any file that already exists and was NOT installed by a previous Kit run
    Write-Step "Installing custom agents..."
    $AgentFiles = Get-ChildItem -Path "$RuntimeRoot\agents" -Filter "*.agent.md" -File -ErrorAction SilentlyContinue
    foreach ($Agent in $AgentFiles) {
        $AgentDest = Join-Path $PromptsDir $Agent.Name
        $RelPath = "prompts\$($Agent.Name)"
        if ((Test-Path $AgentDest) -and ($PreviousManifest -notcontains $RelPath)) {
            Write-Warning "Skipped (user file exists): $($Agent.Name)"
            continue
        }
        Copy-Item -Path $Agent.FullName -Destination $AgentDest -Force
        $ManifestEntries.Add($RelPath)
        Write-Info "Installed: $($Agent.Name)"
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
    $ManifestEntries.Add("prompts\verify-ai-kit.prompt.md")
    Write-Info "Created: $VerifyPromptPath"

    # Also track the bootstrap instruction in the manifest
    $ManifestEntries.Add("Instructions\000-reusable-ai-kit-global.instructions.md")

    # Write the manifest so future installs/uninstalls know what belongs to the Kit
    Write-Manifest -Entries $ManifestEntries.ToArray()
    Write-Step "Manifest written ($($ManifestEntries.Count) Kit-owned files tracked)"
    
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

    # Use the manifest to remove only Kit-owned files (safe for user files)
    $Manifest = Read-Manifest
    if ($Manifest.Count -gt 0) {
        Write-Step "Removing $($Manifest.Count) Kit-owned files (from manifest)..."
        foreach ($RelPath in $Manifest) {
            $FullPath = Join-Path $VSCodeUserDir $RelPath
            if (Test-Path $FullPath) {
                Remove-Item -Path $FullPath -Force
                Write-Info "Removed: $RelPath"
            }
        }
    } else {
        Write-Warning "No manifest found — falling back to known Kit file names"
        # Fallback: remove known Kit files by convention
        $FallbackPaths = @(
            "$InstructionsDir\000-reusable-ai-kit-global.instructions.md",
            "$PromptsDir\setup-ai-kit.prompt.md",
            "$PromptsDir\update-ai-kit.prompt.md",
            "$PromptsDir\kit-status.prompt.md",
            "$PromptsDir\verify-ai-kit.prompt.md"
        )
        # Also collect agent/instruction names from the Kit dir (before we delete it)
        if (Test-Path "$GlobalKitDir\agents") {
            $FallbackPaths += Get-ChildItem -Path "$GlobalKitDir\agents" -Filter "*.agent.md" -File |
                ForEach-Object { Join-Path $PromptsDir $_.Name }
        }
        if (Test-Path "$GlobalKitDir\instructions") {
            $FallbackPaths += Get-ChildItem -Path "$GlobalKitDir\instructions" -Filter "*.instructions.md" -File |
                ForEach-Object { Join-Path $InstructionsDir $_.Name }
        }
        foreach ($Path in $FallbackPaths) {
            if (Test-Path $Path) {
                Remove-Item -Path $Path -Force
                Write-Step "Removed: $Path"
            }
        }
    }

    # Remove the Kit directory itself
    if (Test-Path $GlobalKitDir) {
        Remove-Item -Path $GlobalKitDir -Recurse -Force
        Write-Step "Removed: $GlobalKitDir"
    }

    # Remove empty pipelines dir if we created it
    $PipelinesDir = "$PromptsDir\pipelines"
    if ((Test-Path $PipelinesDir) -and ((Get-ChildItem $PipelinesDir -File).Count -eq 0)) {
        Remove-Item -Path $PipelinesDir -Force
        Write-Info "Removed empty: pipelines/"
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
