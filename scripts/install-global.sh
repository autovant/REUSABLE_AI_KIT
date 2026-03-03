#!/usr/bin/env bash
# =============================================================================
# REUSABLE_AI_KIT — Global Installer (macOS / Linux)
# =============================================================================
# Usage:
#   chmod +x scripts/install-global.sh
#   ./scripts/install-global.sh            # install
#   ./scripts/install-global.sh --uninstall
#
# What it does:
#   - Copies the kit to VS Code (or VS Code Insiders) User directory
#   - Creates a global bootstrap instruction that auto-loads for ALL projects
#   - Installs agents + prompts so they appear in VS Code Copilot
#   - Configures the DuckDB-backed memory system
#
# Supports: macOS, Linux  |  VS Code + VS Code Insiders
# =============================================================================
set -euo pipefail

# ── Resolve paths ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

detect_vscode_user_dir() {
    local candidates=()
    if [[ "$(uname)" == "Darwin" ]]; then
        candidates=(
            "$HOME/Library/Application Support/Code - Insiders/User"
            "$HOME/Library/Application Support/Code/User"
        )
    else
        # Linux
        candidates=(
            "$HOME/.config/Code - Insiders/User"
            "$HOME/.config/Code/User"
        )
    fi

    # Prefer Insiders if installed, otherwise stable
    for d in "${candidates[@]}"; do
        if [[ -d "$d" ]]; then
            echo "$d"
            return
        fi
    done

    # VS Code not found; default to stable location (will be created)
    echo "${candidates[-1]}"
}

VSCODE_USER_DIR="$(detect_vscode_user_dir)"
INSTRUCTIONS_DIR="$VSCODE_USER_DIR/instructions"
PROMPTS_DIR="$VSCODE_USER_DIR/prompts"
GLOBAL_KIT_DIR="$VSCODE_USER_DIR/REUSABLE_AI_KIT"

BOOTSTRAP_FILE="$INSTRUCTIONS_DIR/000-reusable-ai-kit-global.instructions.md"

# ── Helpers ───────────────────────────────────────────────────────────────────
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
GRAY='\033[0;37m'
RESET='\033[0m'

header()  { echo -e "\n${CYAN}$(printf '=%.0s' {1..60})${RESET}"; echo -e "${CYAN} $1${RESET}"; echo -e "${CYAN}$(printf '=%.0s' {1..60})${RESET}\n"; }
step()    { echo -e "${GREEN}[+] $1${RESET}"; }
info()    { echo -e "${GRAY}    $1${RESET}"; }
warn()    { echo -e "${YELLOW}[!] $1${RESET}"; }

# ── Manifest helpers ──────────────────────────────────────────────────────────
MANIFEST_PATH="$GLOBAL_KIT_DIR/.kit-manifest"
MANIFEST_ENTRIES=()

read_manifest() {
    if [[ -f "$MANIFEST_PATH" ]]; then
        mapfile -t PREV_MANIFEST < "$MANIFEST_PATH"
    else
        PREV_MANIFEST=()
    fi
}

manifest_contains() {
    local needle="$1"
    for entry in "${PREV_MANIFEST[@]}"; do
        [[ "$entry" == "$needle" ]] && return 0
    done
    return 1
}

write_manifest() {
    printf '%s\n' "${MANIFEST_ENTRIES[@]}" | sort -u > "$MANIFEST_PATH"
}

# ── Install ───────────────────────────────────────────────────────────────────
install_kit() {
    header "Installing REUSABLE_AI_KIT Globally"

    # Verify source
    if [[ ! -d "$KIT_ROOT" ]]; then
        echo "ERROR: Kit not found at: $KIT_ROOT" >&2
        exit 1
    fi

    # Runtime root is the kit root itself (no subfolder needed)
    RUNTIME_ROOT="$KIT_ROOT"
    step "Using runtime root: $RUNTIME_ROOT"

    # Create directories
    step "Creating VS Code User directories..."
    mkdir -p "$INSTRUCTIONS_DIR" "$PROMPTS_DIR" "$GLOBAL_KIT_DIR"
    info "Instructions: $INSTRUCTIONS_DIR"
    info "Prompts:      $PROMPTS_DIR"
    info "Kit:          $GLOBAL_KIT_DIR"

    # Read manifest from any prior install (for collision checks and cleanup)
    read_manifest

    # Clean up files from a previous Kit install (manifest-tracked only)
    if [[ ${#PREV_MANIFEST[@]} -gt 0 ]]; then
        step "Cleaning previous Kit files (manifest-tracked)..."
        for old_rel in "${PREV_MANIFEST[@]}"; do
            [[ -z "$old_rel" ]] && continue
            local old_path="$VSCODE_USER_DIR/$old_rel"
            if [[ -f "$old_path" ]]; then
                rm -f "$old_path"
            fi
        done
    fi

    # Copy kit
    step "Copying AI Kit to global location..."
    rsync -a --delete \
        --exclude='.git' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='*.duckdb' \
        --exclude='*.db' \
        "$KIT_ROOT/" "$GLOBAL_KIT_DIR/"
    info "Installed: $GLOBAL_KIT_DIR"

    # Resolve runtime root inside the installed copy
    INSTALLED_RUNTIME="$GLOBAL_KIT_DIR"

    # ── Bootstrap instruction ─────────────────────────────────────────────────
    step "Creating global bootstrap instruction..."

    TEMPLATE_FILE=""
    for t in "$KIT_ROOT/templates/global-bootstrap.instructions.md"; do
        if [[ -f "$t" ]]; then
            TEMPLATE_FILE="$t"
            break
        fi
    done

    TIMESTAMP="$(date '+%Y-%m-%d %H:%M:%S')"

    if [[ -n "$TEMPLATE_FILE" ]]; then
        sed \
            -e "s|%APPDATA%\\\\Code\\\\User\\\\REUSABLE_AI_KIT|$INSTALLED_RUNTIME|g" \
            -e "s|%APPDATA%/Code/User/REUSABLE_AI_KIT|$INSTALLED_RUNTIME|g" \
            -e "s|> It is installed by running:|> Installed: $TIMESTAMP\n> It is installed by running:|" \
            "$TEMPLATE_FILE" > "$BOOTSTRAP_FILE"
    else
        cat > "$BOOTSTRAP_FILE" << EOF
---
applyTo: '**'
description: 'GLOBAL: Auto-loads REUSABLE_AI_KIT for all projects'
---

# REUSABLE_AI_KIT Global Bootstrap

> **This instruction auto-loads the AI Kit for ALL projects globally.**
> Installed: $TIMESTAMP
> Kit Location: $GLOBAL_KIT_DIR

## Automatic Loading Requirements

When working on ANY project, the AI agent MUST:

### Step 1: Load Core Rules (CRITICAL)
Read and follow: \`$INSTALLED_RUNTIME/instructions/000-core-rules.instructions.md\`

### Step 2: Load Orchestration
Read and follow: \`$INSTALLED_RUNTIME/instructions/orchestration.instructions.md\`

### Step 3: Load All Other Instructions
Read remaining: \`$INSTALLED_RUNTIME/instructions/*.instructions.md\`

## Quick Access

| Resource | Path |
|----------|------|
| Instructions | $INSTALLED_RUNTIME/instructions/ |
| Agents       | $INSTALLED_RUNTIME/agents/ |
| Prompts      | $INSTALLED_RUNTIME/prompts/ |
| Memory       | $INSTALLED_RUNTIME/memory/ |
| Tools        | $INSTALLED_RUNTIME/tools/ |

## Available Commands
- \`/setup-ai-kit\`  — Integrate kit into current project
- \`/update-ai-kit\` — Re-run installer to update
- \`/kit-status\`    — Check kit health
EOF
    fi
    info "Created: $BOOTSTRAP_FILE"

    # ── Instruction files ─────────────────────────────────────────────────────
    # VS Code only auto-loads .instructions.md from the User Instructions dir.
    # SAFETY: Skip any file that already exists and was NOT installed by a previous Kit run.
    step "Installing instruction files..."
    if [[ -d "$INSTALLED_RUNTIME/instructions" ]]; then
        for instr in "$INSTALLED_RUNTIME/instructions/"*.instructions.md; do
            [[ -f "$instr" ]] || continue
            local base; base="$(basename "$instr")"
            local rel="instructions/$base"
            local dest="$INSTRUCTIONS_DIR/$base"
            if [[ -f "$dest" ]] && ! manifest_contains "$rel"; then
                warn "Skipped (user file exists): $base"
                continue
            fi
            cp "$instr" "$dest"
            MANIFEST_ENTRIES+=("$rel")
            info "Installed: $base"
        done
    fi

    # ── Prompts ───────────────────────────────────────────────────────────────
    # SAFETY: Skip any file that already exists and was NOT installed by a previous Kit run.
    step "Installing global prompts..."

    # Copy ALL prompt files
    if [[ -d "$INSTALLED_RUNTIME/prompts" ]]; then
        for prompt in "$INSTALLED_RUNTIME/prompts/"*.prompt.md; do
            [[ -f "$prompt" ]] || continue
            local base; base="$(basename "$prompt")"
            local rel="prompts/$base"
            local dest="$PROMPTS_DIR/$base"
            if [[ -f "$dest" ]] && ! manifest_contains "$rel"; then
                warn "Skipped (user file exists): $base"
                continue
            fi
            sed "s|\[DETECTED_PATH\]|$GLOBAL_KIT_DIR|g" "$prompt" > "$dest"
            MANIFEST_ENTRIES+=("$rel")
            info "Installed: $base"
        done
    fi

    # Copy pipeline prompts (subdirectory)
    if [[ -d "$INSTALLED_RUNTIME/prompts/pipelines" ]]; then
        mkdir -p "$PROMPTS_DIR/pipelines"
        for pipeline in "$INSTALLED_RUNTIME/prompts/pipelines/"*.prompt.md; do
            [[ -f "$pipeline" ]] || continue
            local base; base="$(basename "$pipeline")"
            local rel="prompts/pipelines/$base"
            local dest="$PROMPTS_DIR/pipelines/$base"
            if [[ -f "$dest" ]] && ! manifest_contains "$rel"; then
                warn "Skipped (user file exists): pipelines/$base"
                continue
            fi
            cp "$pipeline" "$dest"
            MANIFEST_ENTRIES+=("$rel")
            info "Installed: pipelines/$base"
        done
    fi

    # ── Agents ────────────────────────────────────────────────────────────────
    # SAFETY: Skip any file that already exists and was NOT installed by a previous Kit run.
    step "Installing custom agents..."
    if [[ -d "$INSTALLED_RUNTIME/agents" ]]; then
        for agent in "$INSTALLED_RUNTIME/agents/"*.agent.md; do
            [[ -f "$agent" ]] || continue
            local base; base="$(basename "$agent")"
            local rel="prompts/$base"
            local dest="$PROMPTS_DIR/$base"
            if [[ -f "$dest" ]] && ! manifest_contains "$rel"; then
                warn "Skipped (user file exists): $base"
                continue
            fi
            cp "$agent" "$dest"
            MANIFEST_ENTRIES+=("$rel")
            info "Installed: $base"
        done
    fi

    # ── DuckDB setup ──────────────────────────────────────────────────────────
    step "Checking DuckDB (required for memory tool)..."
    PYTHON_BIN=""
    for py in python3 python; do
        if command -v "$py" &>/dev/null; then
            PYTHON_BIN="$py"
            break
        fi
    done

    if [[ -n "$PYTHON_BIN" ]]; then
        if "$PYTHON_BIN" -c "import duckdb" 2>/dev/null; then
            info "duckdb already installed ✓"
        else
            info "Installing duckdb..."
            "$PYTHON_BIN" -m pip install duckdb --quiet && info "duckdb installed ✓" || \
                warn "Could not install duckdb. Run: pip install duckdb"
        fi

        # Initialize memory DB
        MEMORY_DB="$INSTALLED_RUNTIME/memory/shared/global-memory.duckdb"
        if [[ ! -f "$MEMORY_DB" ]]; then
            "$PYTHON_BIN" "$INSTALLED_RUNTIME/tools/global_memory.py" --db "$MEMORY_DB" init \
                && info "Memory database initialized ✓" \
                || warn "Memory init failed — run manually: python global_memory.py init"
        else
            info "Memory database exists ✓"
        fi
    else
        warn "Python not found — install Python 3 and run: pip install duckdb"
        warn "Then init memory: python tools/global_memory.py init"
    fi

    # ── Summary ───────────────────────────────────────────────────────────────
    header "Installation Complete!"

    INSTR_COUNT=$(find "$INSTALLED_RUNTIME/instructions" -name "*.instructions.md" 2>/dev/null | wc -l | tr -d ' ')
    AGENT_COUNT=$(find "$INSTALLED_RUNTIME/agents" -name "*.agent.md" 2>/dev/null | wc -l | tr -d ' ')
    PROMPT_COUNT=$(find "$INSTALLED_RUNTIME/prompts" -name "*.prompt.md" 2>/dev/null | wc -l | tr -d ' ')

    echo -e "${GREEN}The REUSABLE_AI_KIT is now globally installed.${RESET}"
    echo ""
    echo -e "What's available:"
    echo -e "${GRAY}  - $INSTR_COUNT instruction files (auto-loaded for all projects)${RESET}"
    echo -e "${GRAY}  - $AGENT_COUNT custom agents${RESET}"
    echo -e "${GRAY}  - $PROMPT_COUNT prompts for complex tasks${RESET}"
    echo -e "${GRAY}  - DuckDB memory system for persistent learning${RESET}"
    echo ""
    echo -e "Getting Started:"
    echo -e "${GRAY}  1. Open any project in VS Code${RESET}"
    echo -e "${CYAN}  2. Type: /setup-ai-kit${RESET}"
    echo -e "${GRAY}  3. The kit is active for that project!${RESET}"
    echo ""
    echo -e "${YELLOW}Or just start working — the kit is already active globally!${RESET}"
    echo ""
    echo -e "Locations:"
    echo -e "${GRAY}  Kit:       $GLOBAL_KIT_DIR${RESET}"
    echo -e "${GRAY}  Bootstrap: $BOOTSTRAP_FILE${RESET}"

    # Track bootstrap in manifest and write it
    MANIFEST_ENTRIES+=("instructions/000-reusable-ai-kit-global.instructions.md")
    write_manifest
    step "Manifest written (${#MANIFEST_ENTRIES[@]} Kit-owned files tracked)"
}

# ── Uninstall ─────────────────────────────────────────────────────────────────
uninstall_kit() {
    header "Uninstalling REUSABLE_AI_KIT"

    # Use the manifest to remove only Kit-owned files (safe for user files)
    read_manifest
    if [[ ${#PREV_MANIFEST[@]} -gt 0 ]]; then
        step "Removing ${#PREV_MANIFEST[@]} Kit-owned files (from manifest)..."
        for rel in "${PREV_MANIFEST[@]}"; do
            [[ -z "$rel" ]] && continue
            local full="$VSCODE_USER_DIR/$rel"
            if [[ -f "$full" ]]; then
                rm -f "$full"
                info "Removed: $rel"
            fi
        done
    else
        warn "No manifest found — falling back to known Kit file names"
        local fallback=(
            "$BOOTSTRAP_FILE"
            "$PROMPTS_DIR/setup-ai-kit.prompt.md"
            "$PROMPTS_DIR/update-ai-kit.prompt.md"
            "$PROMPTS_DIR/kit-status.prompt.md"
            "$PROMPTS_DIR/verify-ai-kit.prompt.md"
        )
        # Collect agent/instruction names from Kit dir before deleting
        if [[ -d "$GLOBAL_KIT_DIR/agents" ]]; then
            while IFS= read -r -d '' agent; do
                fallback+=("$PROMPTS_DIR/$(basename "$agent")")
            done < <(find "$GLOBAL_KIT_DIR/agents" -name "*.agent.md" -print0 2>/dev/null)
        fi
        if [[ -d "$GLOBAL_KIT_DIR/instructions" ]]; then
            while IFS= read -r -d '' instr; do
                fallback+=("$INSTRUCTIONS_DIR/$(basename "$instr")")
            done < <(find "$GLOBAL_KIT_DIR/instructions" -name "*.instructions.md" -print0 2>/dev/null)
        fi
        for path in "${fallback[@]}"; do
            if [[ -e "$path" ]]; then
                rm -rf "$path"
                step "Removed: $path"
            fi
        done
    fi

    # Remove the Kit directory itself
    if [[ -d "$GLOBAL_KIT_DIR" ]]; then
        rm -rf "$GLOBAL_KIT_DIR"
        step "Removed: $GLOBAL_KIT_DIR"
    fi

    # Remove empty pipelines dir if we created it
    if [[ -d "$PROMPTS_DIR/pipelines" ]] && [[ -z "$(ls -A "$PROMPTS_DIR/pipelines" 2>/dev/null)" ]]; then
        rmdir "$PROMPTS_DIR/pipelines"
        info "Removed empty: pipelines/"
    fi

    header "Uninstall Complete"
    echo -e "${GREEN}The global AI Kit has been removed.${RESET}"
    echo -e "${GRAY}Local project configurations (.copilot folders) were not modified.${RESET}"
}

# ── Main ──────────────────────────────────────────────────────────────────────
case "${1:-}" in
    --uninstall|-u) uninstall_kit ;;
    --help|-h)
        echo "Usage: $0 [--uninstall]"
        echo "  (no args)    Install REUSABLE_AI_KIT globally"
        echo "  --uninstall  Remove global installation"
        ;;
    *) install_kit ;;
esac
