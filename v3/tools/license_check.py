#!/usr/bin/env python3
"""
License Compliance Checker
===========================
Scans project dependencies and reports their licenses.  Flags packages
whose licenses conflict with a configurable allow/deny list.

Supports: Python (pip), Node.js (npm), Go (go.mod)

Usage:
    python license_check.py [--path <project_root>] [--format json|markdown]
                            [--policy permissive|copyleft|custom]
                            [--allow "MIT,Apache-2.0,..."]
                            [--deny "GPL-3.0,..."]

Requirements:
    - Python 3.8+
    - For Python deps: pip (used via subprocess)
    - For Node deps: npm must be on PATH
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------- License policy presets ----------

PERMISSIVE_ALLOWED = {
    "MIT", "MIT License",
    "Apache-2.0", "Apache License 2.0", "Apache Software License",
    "BSD-2-Clause", "BSD-3-Clause", "BSD License",
    "ISC", "ISC License",
    "0BSD",
    "Unlicense", "The Unlicense",
    "CC0-1.0",
    "Python-2.0", "PSF", "Python Software Foundation License",
    "WTFPL",
    "Zlib", "zlib/libpng License",
    "BSL-1.0", "Boost Software License",
}

COPYLEFT_DENIED = {
    "GPL-2.0", "GPL-3.0", "GPLv2", "GPLv3",
    "GNU General Public License v2", "GNU General Public License v3",
    "AGPL-3.0", "GNU Affero General Public License v3",
    "LGPL-2.1", "LGPL-3.0",
    "SSPL-1.0", "Server Side Public License",
    "EUPL-1.2",
}


def detect_ecosystem(project_path: Path) -> list[str]:
    ecosystems = []
    if any((project_path / m).exists() for m in ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py"]):
        ecosystems.append("python")
    if (project_path / "package.json").exists():
        ecosystems.append("node")
    if (project_path / "go.mod").exists():
        ecosystems.append("go")
    return ecosystems


def run_cmd(cmd: list[str], cwd: str, timeout: int = 90) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                           timeout=timeout, shell=(os.name == "nt"))
        return r.returncode, r.stdout, r.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", "timeout"


# ---------- Python license extraction ----------

def get_python_licenses(project_path: Path) -> list[dict]:
    """Use pip show to extract license metadata for installed packages."""
    # First get list of packages from requirements
    req_file = project_path / "requirements.txt"
    packages = []

    if req_file.exists():
        for line in req_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("-"):
                pkg = re.split(r"[>=<!\[\];]", line)[0].strip()
                if pkg:
                    packages.append(pkg)
    else:
        # Try pip list as fallback
        code, stdout, _ = run_cmd(["pip", "list", "--format", "json"], str(project_path))
        if code == 0:
            try:
                for item in json.loads(stdout):
                    packages.append(item["name"])
            except (json.JSONDecodeError, KeyError):
                pass

    if not packages:
        return []

    results = []
    # Batch pip show
    code, stdout, _ = run_cmd(["pip", "show"] + packages[:50], str(project_path), timeout=60)
    if code != 0 and code != -1:
        return results

    current = {}
    for line in (stdout or "").splitlines():
        if line.startswith("Name:"):
            if current:
                results.append(current)
            current = {"package": line.split(":", 1)[1].strip(), "version": "", "license": "UNKNOWN"}
        elif line.startswith("Version:"):
            current["version"] = line.split(":", 1)[1].strip()
        elif line.startswith("License:"):
            lic = line.split(":", 1)[1].strip()
            current["license"] = lic if lic and lic != "UNKNOWN" else "UNKNOWN"
    if current:
        results.append(current)

    return results


# ---------- Node license extraction ----------

def get_node_licenses(project_path: Path) -> list[dict]:
    """Parse node_modules/*/package.json for license info."""
    results = []
    nm = project_path / "node_modules"

    if not nm.exists():
        # Try npm ls
        code, stdout, _ = run_cmd(["npm", "ls", "--json", "--all"], str(project_path))
        if code == -1:
            return [{"package": "npm", "license": "TOOL_NOT_FOUND", "version": ""}]
        try:
            data = json.loads(stdout)
            deps = data.get("dependencies", {})
            for name, info in deps.items():
                results.append({
                    "package": name,
                    "version": info.get("version", ""),
                    "license": "CHECK_MANUALLY",
                })
        except json.JSONDecodeError:
            pass
        return results

    for pkg_dir in nm.iterdir():
        if not pkg_dir.is_dir():
            continue
        # Handle scoped packages
        if pkg_dir.name.startswith("@"):
            for sub in pkg_dir.iterdir():
                if sub.is_dir() and (sub / "package.json").exists():
                    info = _parse_node_pkg(sub, f"{pkg_dir.name}/{sub.name}")
                    if info:
                        results.append(info)
        else:
            if (pkg_dir / "package.json").exists():
                info = _parse_node_pkg(pkg_dir, pkg_dir.name)
                if info:
                    results.append(info)

    return results


def _parse_node_pkg(pkg_dir: Path, name: str) -> dict | None:
    try:
        data = json.loads((pkg_dir / "package.json").read_text(encoding="utf-8", errors="replace"))
        lic = data.get("license", "")
        if isinstance(lic, dict):
            lic = lic.get("type", "UNKNOWN")
        return {"package": name, "version": data.get("version", ""), "license": lic or "UNKNOWN"}
    except (json.JSONDecodeError, OSError):
        return None


# ---------- Go license extraction ----------

def get_go_licenses(project_path: Path) -> list[dict]:
    """Parse go.sum or go.mod for modules, then check for LICENSE files in GOPATH."""
    results = []
    gomod = project_path / "go.mod"

    if not gomod.exists():
        return results

    for line in gomod.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        # Lines like: github.com/pkg/errors v0.9.1
        if line and not line.startswith("//") and not line.startswith("module") \
                and not line.startswith("go ") and not line.startswith("require") \
                and line != "(" and line != ")":
            parts = line.split()
            if parts:
                mod = parts[0]
                ver = parts[1] if len(parts) > 1 else ""
                results.append({"package": mod, "version": ver, "license": "CHECK_MANUALLY"})

    return results


# ---------- Policy evaluation ----------

def evaluate_policy(packages: list[dict], allowed: set[str] | None, denied: set[str] | None) -> list[dict]:
    """Tag each package as ok, flagged, or unknown."""
    for pkg in packages:
        lic = pkg.get("license", "UNKNOWN")
        if lic in ("UNKNOWN", "CHECK_MANUALLY", "TOOL_NOT_FOUND"):
            pkg["status"] = "unknown"
            pkg["reason"] = "License could not be determined"
            continue

        # Normalize for matching
        lic_upper = lic.upper().strip()

        if denied:
            for d in denied:
                if d.upper() in lic_upper:
                    pkg["status"] = "denied"
                    pkg["reason"] = f"License '{lic}' matches deny-list entry '{d}'"
                    break
            else:
                if allowed:
                    matched = any(a.upper() in lic_upper for a in allowed)
                    pkg["status"] = "ok" if matched else "review"
                    pkg["reason"] = "" if matched else f"License '{lic}' not in allow-list"
                else:
                    pkg["status"] = "ok"
                    pkg["reason"] = ""
        elif allowed:
            matched = any(a.upper() in lic_upper for a in allowed)
            pkg["status"] = "ok" if matched else "review"
            pkg["reason"] = "" if matched else f"License '{lic}' not in allow-list"
        else:
            pkg["status"] = "ok"
            pkg["reason"] = ""

    return packages


def format_markdown(report: dict) -> str:
    lines = ["# License Compliance Report",
             f"**Scanned**: {report['scanned_at']}",
             f"**Path**: {report['project_path']}",
             f"**Policy**: {report['policy']}", ""]

    s = report["summary"]
    lines.append(f"## Summary")
    lines.append(f"- Total packages: {s['total']}")
    lines.append(f"- OK: {s['ok']}  |  Review: {s['review']}  |  Denied: {s['denied']}  |  Unknown: {s['unknown']}")
    lines.append("")

    for eco_report in report["ecosystems"]:
        eco = eco_report["ecosystem"]
        pkgs = eco_report["packages"]
        lines.append(f"### {eco.title()} ({len(pkgs)} packages)")

        if not pkgs:
            lines.append("No packages found.\n")
            continue

        lines.append("| Package | Version | License | Status | Reason |")
        lines.append("|---------|---------|---------|--------|--------|")
        for p in pkgs:
            status_icon = {"ok": "pass", "review": "REVIEW", "denied": "DENIED", "unknown": "?"}.get(p["status"], "?")
            lines.append(f"| {p['package']} | {p.get('version', '')} | {p.get('license', 'UNKNOWN')} | {status_icon} | {p.get('reason', '')} |")
        lines.append("")

    return "\n".join(lines)


ECOSYSTEM_SCANNERS = {
    "python": get_python_licenses,
    "node": get_node_licenses,
    "go": get_go_licenses,
}


def main():
    parser = argparse.ArgumentParser(description="Universal License Compliance Checker")
    parser.add_argument("--path", default=".", help="Project root path")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--policy", choices=["permissive", "copyleft", "custom", "none"], default="permissive",
                        help="License policy preset (default: permissive)")
    parser.add_argument("--allow", default="", help="Comma-separated allowed licenses (use with --policy custom)")
    parser.add_argument("--deny", default="", help="Comma-separated denied licenses (use with --policy custom)")
    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    if not project_path.is_dir():
        print(json.dumps({"error": f"Path not found: {project_path}"}), file=sys.stderr)
        sys.exit(1)

    # Build policy sets
    allowed, denied = None, None
    if args.policy == "permissive":
        allowed = PERMISSIVE_ALLOWED
        denied = COPYLEFT_DENIED
    elif args.policy == "copyleft":
        denied = COPYLEFT_DENIED
    elif args.policy == "custom":
        if args.allow:
            allowed = {s.strip() for s in args.allow.split(",")}
        if args.deny:
            denied = {s.strip() for s in args.deny.split(",")}

    ecosystems = detect_ecosystem(project_path)
    if not ecosystems:
        print(json.dumps({"error": "No recognized project found", "path": str(project_path)}))
        sys.exit(0)

    report = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "policy": args.policy,
        "detected_ecosystems": ecosystems,
        "ecosystems": [],
        "summary": {"total": 0, "ok": 0, "review": 0, "denied": 0, "unknown": 0},
    }

    for eco in ecosystems:
        scanner = ECOSYSTEM_SCANNERS.get(eco)
        if not scanner:
            continue

        packages = scanner(project_path)
        packages = evaluate_policy(packages, allowed, denied)

        report["ecosystems"].append({"ecosystem": eco, "packages": packages})
        for p in packages:
            report["summary"]["total"] += 1
            status = p.get("status", "unknown")
            if status in report["summary"]:
                report["summary"][status] += 1

    if args.format == "markdown":
        print(format_markdown(report))
    else:
        print(json.dumps(report, indent=2))

    # Exit code: 1 if any denied, 0 otherwise
    if report["summary"]["denied"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
