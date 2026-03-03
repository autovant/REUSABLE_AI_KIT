#!/usr/bin/env python3
"""
Environment Health Validator
==============================
Validates that a developer's environment has all required tools,
correct versions, and proper configuration for a project.

Auto-detects the project ecosystem and checks:
- Required CLI tools (git, node, python, docker, etc.)
- Version constraints (e.g., Node >= 18)
- Environment variables
- Port availability
- Disk space
- Configuration files existence

Usage:
    python env_health.py [--path <project_root>] [--format json|markdown] [--config <config.json>]

The tool auto-detects checks from project manifests, or you can supply
a custom config JSON with explicit checks.

Requirements:
    - Python 3.8+  (stdlib only)
"""

import argparse
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------- Version parsing ----------

def parse_version(version_str: str) -> tuple:
    """Extract numeric version tuple from a string like 'v20.11.0' or 'Python 3.12.1'."""
    match = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", version_str)
    if not match:
        return (0,)
    return tuple(int(x) for x in match.groups() if x is not None)


def version_gte(actual: str, minimum: str) -> bool:
    return parse_version(actual) >= parse_version(minimum)


# ---------- Individual checks ----------

def check_tool(name: str, version_cmd: list[str] | None = None, min_version: str | None = None) -> dict:
    """Check if a CLI tool is installed and optionally meets a version constraint."""
    path = shutil.which(name)
    if not path:
        return {
            "check": f"tool:{name}",
            "status": "fail",
            "message": f"'{name}' not found on PATH",
            "fix_hint": f"Install {name} and ensure it is on your PATH",
        }

    result = {"check": f"tool:{name}", "status": "pass", "path": path, "message": f"Found at {path}"}

    if version_cmd and min_version:
        try:
            proc = subprocess.run(version_cmd, capture_output=True, text=True, timeout=15, shell=(os.name == "nt"))
            actual_version = (proc.stdout + proc.stderr).strip().splitlines()[0] if proc.stdout or proc.stderr else ""
            result["version"] = actual_version
            if not version_gte(actual_version, min_version):
                result["status"] = "warn"
                result["message"] = f"Version {actual_version} < required {min_version}"
                result["fix_hint"] = f"Upgrade {name} to >= {min_version}"
        except (subprocess.TimeoutExpired, FileNotFoundError, IndexError):
            result["version"] = "unknown"

    return result


def check_env_var(name: str, expected: str | None = None) -> dict:
    """Check if an environment variable is set, optionally matching an expected value."""
    value = os.environ.get(name)
    if value is None:
        return {
            "check": f"env:{name}",
            "status": "fail",
            "message": f"Environment variable '{name}' is not set",
            "fix_hint": f"Set {name} in your shell profile or .env file",
        }

    result = {"check": f"env:{name}", "status": "pass", "message": f"'{name}' is set"}

    if expected and value != expected:
        result["status"] = "warn"
        result["message"] = f"'{name}' is set but value does not match expected"

    return result


def check_file_exists(filepath: str, project_path: Path) -> dict:
    """Check if a required file exists."""
    full = project_path / filepath
    exists = full.exists()
    return {
        "check": f"file:{filepath}",
        "status": "pass" if exists else "fail",
        "message": f"{'Found' if exists else 'Missing'}: {filepath}",
        "fix_hint": "" if exists else f"Create {filepath} or run the project setup script",
    }


def check_port(port: int) -> dict:
    """Check if a port is available (not in use)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result_code = s.connect_ex(("127.0.0.1", port))
        available = result_code != 0
    except OSError:
        available = True

    return {
        "check": f"port:{port}",
        "status": "pass" if available else "warn",
        "message": f"Port {port} is {'available' if available else 'in use'}",
        "fix_hint": "" if available else f"Stop the process using port {port} or use a different port",
    }


def check_disk_space(min_gb: float = 1.0) -> dict:
    """Check available disk space."""
    try:
        if os.name == "nt":
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(str(Path.home().anchor)),
                None, None, ctypes.pointer(free_bytes))
            free_gb = free_bytes.value / (1024 ** 3)
        else:
            stat = os.statvfs("/")
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
    except Exception:
        return {"check": "disk:space", "status": "unknown", "message": "Could not determine free disk space"}

    ok = free_gb >= min_gb
    return {
        "check": "disk:space",
        "status": "pass" if ok else "warn",
        "message": f"{free_gb:.1f} GB free" + ("" if ok else f" (< {min_gb} GB recommended)"),
        "free_gb": round(free_gb, 2),
    }


# ---------- Auto-detection ----------

def auto_detect_checks(project_path: Path) -> list[dict]:
    """Auto-detect which checks to run based on project files."""
    checks = []

    # Always check git
    checks.append({"type": "tool", "name": "git", "version_cmd": ["git", "--version"], "min_version": "2.0"})

    # Python project
    if any((project_path / m).exists() for m in ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"]):
        checks.append({"type": "tool", "name": "python", "version_cmd": ["python", "--version"], "min_version": "3.8"})
        checks.append({"type": "tool", "name": "pip", "version_cmd": ["pip", "--version"]})
        if (project_path / "Pipfile").exists():
            checks.append({"type": "tool", "name": "pipenv"})
        if (project_path / "pyproject.toml").exists():
            toml_text = (project_path / "pyproject.toml").read_text(encoding="utf-8", errors="replace")
            if "poetry" in toml_text:
                checks.append({"type": "tool", "name": "poetry"})
        checks.append({"type": "file", "path": ".env"})

    # Node project
    if (project_path / "package.json").exists():
        checks.append({"type": "tool", "name": "node", "version_cmd": ["node", "--version"], "min_version": "18.0"})
        checks.append({"type": "tool", "name": "npm", "version_cmd": ["npm", "--version"]})
        pkg_json = project_path / "package.json"
        try:
            pkg_data = json.loads(pkg_json.read_text(encoding="utf-8"))
            # Check for lock files implying package manager
            if (project_path / "yarn.lock").exists():
                checks.append({"type": "tool", "name": "yarn"})
            if (project_path / "pnpm-lock.yaml").exists():
                checks.append({"type": "tool", "name": "pnpm"})
            # Check for common port usage in scripts
            scripts = pkg_data.get("scripts", {})
            start_script = scripts.get("start", "") + scripts.get("dev", "")
            port_match = re.search(r"(?:PORT|port)[=: ]*(\d{4,5})", start_script)
            if port_match:
                checks.append({"type": "port", "port": int(port_match.group(1))})
        except (json.JSONDecodeError, OSError):
            pass
        checks.append({"type": "file", "path": ".env"})

    # .NET project
    if any(project_path.glob("*.csproj")) or any(project_path.glob("*.sln")):
        checks.append({"type": "tool", "name": "dotnet", "version_cmd": ["dotnet", "--version"], "min_version": "6.0"})

    # Docker
    if (project_path / "Dockerfile").exists() or (project_path / "docker-compose.yml").exists() \
            or (project_path / "docker-compose.yaml").exists():
        checks.append({"type": "tool", "name": "docker", "version_cmd": ["docker", "--version"]})
        checks.append({"type": "tool", "name": "docker-compose"})

    # Go
    if (project_path / "go.mod").exists():
        checks.append({"type": "tool", "name": "go", "version_cmd": ["go", "version"], "min_version": "1.21"})

    # Rust
    if (project_path / "Cargo.toml").exists():
        checks.append({"type": "tool", "name": "cargo", "version_cmd": ["cargo", "--version"]})
        checks.append({"type": "tool", "name": "rustc", "version_cmd": ["rustc", "--version"]})

    # Terraform
    if any(project_path.glob("*.tf")):
        checks.append({"type": "tool", "name": "terraform", "version_cmd": ["terraform", "--version"]})

    # Always check disk space
    checks.append({"type": "disk", "min_gb": 1.0})

    return checks


# ---------- Run checks ----------

def run_checks(check_specs: list[dict], project_path: Path) -> list[dict]:
    results = []
    for spec in check_specs:
        ctype = spec.get("type")
        if ctype == "tool":
            r = check_tool(
                spec["name"],
                version_cmd=spec.get("version_cmd"),
                min_version=spec.get("min_version"),
            )
        elif ctype == "env":
            r = check_env_var(spec["name"], expected=spec.get("expected"))
        elif ctype == "file":
            r = check_file_exists(spec["path"], project_path)
        elif ctype == "port":
            r = check_port(spec["port"])
        elif ctype == "disk":
            r = check_disk_space(spec.get("min_gb", 1.0))
        else:
            r = {"check": f"unknown:{spec}", "status": "skip", "message": "Unrecognized check type"}
        results.append(r)
    return results


# ---------- Formatting ----------

def format_markdown(report: dict) -> str:
    lines = ["# Environment Health Report",
             f"**Checked**: {report['checked_at']}",
             f"**Path**: {report['project_path']}",
             f"**System**: {report['system']['os']} {report['system']['arch']}", ""]

    s = report["summary"]
    lines.append(f"## Summary: {s['pass']} pass / {s['warn']} warn / {s['fail']} fail\n")

    # Group by status for readability
    for status_label, icon in [("fail", "FAIL"), ("warn", "WARN"), ("pass", "OK")]:
        items = [r for r in report["checks"] if r["status"] == status_label]
        if not items:
            continue
        lines.append(f"### {icon} ({len(items)})")
        for item in items:
            hint = f" - *{item['fix_hint']}*" if item.get("fix_hint") else ""
            lines.append(f"- **{item['check']}**: {item['message']}{hint}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Universal Environment Health Validator")
    parser.add_argument("--path", default=".", help="Project root path")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--config", help="Custom checks config JSON file (overrides auto-detection)")
    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    if not project_path.is_dir():
        print(json.dumps({"error": f"Path not found: {project_path}"}), file=sys.stderr)
        sys.exit(1)

    # Load checks from config or auto-detect
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(json.dumps({"error": f"Config file not found: {args.config}"}), file=sys.stderr)
            sys.exit(1)
        check_specs = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        check_specs = auto_detect_checks(project_path)

    results = run_checks(check_specs, project_path)

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "system": {
            "os": platform.system(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "python": platform.python_version(),
        },
        "checks": results,
        "summary": {
            "total": len(results),
            "pass": sum(1 for r in results if r["status"] == "pass"),
            "warn": sum(1 for r in results if r["status"] == "warn"),
            "fail": sum(1 for r in results if r["status"] == "fail"),
            "unknown": sum(1 for r in results if r["status"] in ("unknown", "skip")),
        },
    }

    if args.format == "markdown":
        print(format_markdown(report))
    else:
        print(json.dumps(report, indent=2))

    # Exit code: 1 if any failures, 0 otherwise
    if report["summary"]["fail"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
