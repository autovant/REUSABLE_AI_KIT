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
INSTRUCTIONS_DIR="$VSCODE_USER_DIR/Instructions"
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

# ── Install ───────────────────────────────────────────────────────────────────
install_kit() {
    header "Installing REUSABLE_AI_KIT Globally"

    # Verify source
    if [[ ! -d "$KIT_ROOT" ]]; then
        echo "ERROR: Kit not found at: $KIT_ROOT" >&2
        exit 1
    fi

    # Pick v3 as runtime root when present
    if [[ -f "$KIT_ROOT/v3/README.md" ]]; then
        RUNTIME_ROOT="$KIT_ROOT/v3"
    else
        RUNTIME_ROOT="$KIT_ROOT"
    fi

    step "Using runtime root: $RUNTIME_ROOT"

    # Create directories
    step "Creating VS Code User directories..."
    mkdir -p "$INSTRUCTIONS_DIR" "$PROMPTS_DIR" "$GLOBAL_KIT_DIR"
    info "Instructions: $INSTRUCTIONS_DIR"
    info "Prompts:      $PROMPTS_DIR"
    info "Kit:          $GLOBAL_KIT_DIR"

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
    if [[ -f "$GLOBAL_KIT_DIR/v3/README.md" ]]; then
        INSTALLED_RUNTIME="$GLOBAL_KIT_DIR/v3"
    else
        INSTALLED_RUNTIME="$GLOBAL_KIT_DIR"
    fi

    # ── Bootstrap instruction ─────────────────────────────────────────────────
    step "Creating global bootstrap instruction..."

    TEMPLATE_FILE=""
    for t in "$KIT_ROOT/v3/templates/global-bootstrap.instructions.md" \
              "$KIT_ROOT/templates/global-bootstrap.instructions.md"; do
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

    # ── Prompts ───────────────────────────────────────────────────────────────
    step "Installing global prompts..."

    # setup-ai-kit
    SETUP_SRC="$INSTALLED_RUNTIME/prompts/setup-ai-kit.prompt.md"
    if [[ -f "$SETUP_SRC" ]]; then
        sed "s|\[DETECTED_PATH\]|$GLOBAL_KIT_DIR|g" "$SETUP_SRC" \
            > "$PROMPTS_DIR/setup-ai-kit.prompt.md"
        info "Created: $PROMPTS_DIR/setup-ai-kit.prompt.md"
    fi

    # update-ai-kit, kit-status — copy directly
    for prompt in update-ai-kit kit-status; do
        SRC="$INSTALLED_RUNTIME/prompts/${prompt}.prompt.md"
        if [[ -f "$SRC" ]]; then
            cp "$SRC" "$PROMPTS_DIR/${prompt}.prompt.md"
            info "Created: $PROMPTS_DIR/${prompt}.prompt.md"
        fi
    done

    # ── Agents ────────────────────────────────────────────────────────────────
    step "Installing custom agents..."
    if [[ -d "$INSTALLED_RUNTIME/agents" ]]; then
        for agent in "$INSTALLED_RUNTIME/agents/"*.agent.md; do
            [[ -f "$agent" ]] || continue
            cp "$agent" "$PROMPTS_DIR/$(basename "$agent")"
            info "Installed: $(basename "$agent")"
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
        warn "Then init memory: python v3/tools/global_memory.py init"
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
}

# ── Uninstall ─────────────────────────────────────────────────────────────────
uninstall_kit() {
    header "Uninstalling REUSABLE_AI_KIT"

    local to_remove=(
        "$GLOBAL_KIT_DIR"
        "$BOOTSTRAP_FILE"
        "$PROMPTS_DIR/setup-ai-kit.prompt.md"
        "$PROMPTS_DIR/update-ai-kit.prompt.md"
        "$PROMPTS_DIR/kit-status.prompt.md"
        "$PROMPTS_DIR/verify-ai-kit.prompt.md"
    )

    # Also remove any agent files installed from the kit
    if [[ -d "$GLOBAL_KIT_DIR/v3/agents" ]]; then
        while IFS= read -r -d '' agent; do
            to_remove+=("$PROMPTS_DIR/$(basename "$agent")")
        done < <(find "$GLOBAL_KIT_DIR/v3/agents" -name "*.agent.md" -print0 2>/dev/null)
    fi

    for path in "${to_remove[@]}"; do
        if [[ -e "$path" ]]; then
            rm -rf "$path"
            step "Removed: $path"
        else
            warn "Not found: $path"
        fi
    done

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
