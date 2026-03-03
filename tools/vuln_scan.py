#!/usr/bin/env python3
"""
Dependency Vulnerability Scanner
=================================
Lightweight, universal tool that auto-detects the project ecosystem
(Python, Node.js, .NET, Ruby, Go) and runs the appropriate vulnerability
audit command.  Outputs structured JSON for agent consumption.

Usage:
    python vuln_scan.py [--path <project_root>] [--format json|markdown] [--severity low|medium|high|critical]

Requirements:
    - Python 3.8+
    - The ecosystem-specific audit tool must be installed:
        Python  -> pip-audit   (pip install pip-audit)
        Node.js -> npm audit   (bundled with npm)
        .NET    -> dotnet CLI
        Ruby    -> bundler-audit (gem install bundler-audit)
        Go      -> govulncheck  (go install golang.org/x/vuln/cmd/govulncheck@latest)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


SEVERITY_ORDER = {"low": 0, "medium": 1, "moderate": 1, "high": 2, "critical": 3}


def detect_ecosystems(project_path: Path) -> list[dict]:
    """Return a list of detected ecosystems with their manifest files."""
    detections = []
    manifests = {
        "python": ["requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "setup.cfg"],
        "node": ["package.json"],
        "dotnet": ["*.csproj", "*.fsproj", "*.sln"],
        "ruby": ["Gemfile"],
        "go": ["go.mod"],
    }

    for eco, patterns in manifests.items():
        for pattern in patterns:
            if "*" in pattern:
                found = list(project_path.glob(pattern))
            else:
                found = [project_path / pattern] if (project_path / pattern).exists() else []
            if found:
                detections.append({"ecosystem": eco, "manifest": str(found[0].relative_to(project_path))})
                break  # one detection per ecosystem is enough

    return detections


def run_command(cmd: list[str], cwd: str, timeout: int = 120) -> tuple[int, str, str]:
    """Run a subprocess and return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True,
            timeout=timeout, shell=(os.name == "nt"),
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return -2, "", f"Command timed out after {timeout}s"


def scan_python(project_path: Path) -> dict:
    """Run pip-audit and parse results."""
    code, stdout, stderr = run_command(["pip-audit", "--format", "json", "--desc"], str(project_path))
    if code == -1:
        return {"tool": "pip-audit", "status": "tool_not_installed",
                "install_hint": "pip install pip-audit", "vulnerabilities": []}

    vulns = []
    try:
        entries = json.loads(stdout) if stdout.strip() else []
        # pip-audit JSON is a flat list of objects
        if isinstance(entries, dict):
            entries = entries.get("dependencies", [])
        for entry in entries:
            for vuln in entry.get("vulns", []):
                vulns.append({
                    "package": entry.get("name", "unknown"),
                    "installed_version": entry.get("version", "unknown"),
                    "vulnerability_id": vuln.get("id", "unknown"),
                    "fix_versions": vuln.get("fix_versions", []),
                    "description": vuln.get("description", ""),
                    "severity": "unknown",
                })
    except json.JSONDecodeError:
        pass

    return {"tool": "pip-audit", "status": "ok" if code != -2 else "timeout", "vulnerabilities": vulns}


def scan_node(project_path: Path) -> dict:
    """Run npm audit and parse results."""
    code, stdout, stderr = run_command(["npm", "audit", "--json"], str(project_path))
    if code == -1:
        return {"tool": "npm audit", "status": "tool_not_installed",
                "install_hint": "npm is bundled with Node.js", "vulnerabilities": []}

    vulns = []
    try:
        data = json.loads(stdout) if stdout.strip() else {}
        advisories = data.get("vulnerabilities", data.get("advisories", {}))
        if isinstance(advisories, dict):
            for _key, adv in advisories.items():
                severity = adv.get("severity", "unknown")
                vulns.append({
                    "package": adv.get("name", _key),
                    "severity": severity,
                    "title": adv.get("title", ""),
                    "url": adv.get("url", ""),
                    "range": adv.get("range", ""),
                    "fix_available": adv.get("fixAvailable", False),
                })
    except json.JSONDecodeError:
        pass

    return {"tool": "npm audit", "status": "ok", "vulnerabilities": vulns}


def scan_dotnet(project_path: Path) -> dict:
    """Run dotnet list package --vulnerable."""
    code, stdout, stderr = run_command(
        ["dotnet", "list", "package", "--vulnerable", "--format", "json"],
        str(project_path),
    )
    if code == -1:
        return {"tool": "dotnet", "status": "tool_not_installed",
                "install_hint": "Install .NET SDK from https://dot.net", "vulnerabilities": []}

    vulns = []
    # dotnet JSON output parsing (available in .NET 8+)
    try:
        data = json.loads(stdout) if stdout.strip() else {}
        for project in data.get("projects", []):
            for framework in project.get("frameworks", []):
                for pkg in framework.get("topLevelPackages", []):
                    for adv in pkg.get("vulnerabilities", []):
                        vulns.append({
                            "package": pkg.get("id", "unknown"),
                            "installed_version": pkg.get("resolvedVersion", "unknown"),
                            "severity": adv.get("severity", "unknown"),
                            "advisory_url": adv.get("advisoryurl", ""),
                        })
    except json.JSONDecodeError:
        # Fall back to text parsing
        for line in stdout.splitlines():
            stripped = line.strip()
            if ">" in stripped and "vulnerability" in stripped.lower():
                vulns.append({"raw": stripped, "severity": "unknown"})

    return {"tool": "dotnet", "status": "ok", "vulnerabilities": vulns}


def scan_ruby(project_path: Path) -> dict:
    """Run bundler-audit."""
    code, stdout, stderr = run_command(["bundler-audit", "check", "--format", "json"], str(project_path))
    if code == -1:
        return {"tool": "bundler-audit", "status": "tool_not_installed",
                "install_hint": "gem install bundler-audit", "vulnerabilities": []}

    vulns = []
    try:
        data = json.loads(stdout) if stdout.strip() else {}
        for result in data.get("results", []):
            adv = result.get("advisory", {})
            vulns.append({
                "package": result.get("gem", {}).get("name", "unknown"),
                "installed_version": result.get("gem", {}).get("version", "unknown"),
                "vulnerability_id": adv.get("id", "unknown"),
                "title": adv.get("title", ""),
                "severity": adv.get("criticality", "unknown"),
                "url": adv.get("url", ""),
            })
    except json.JSONDecodeError:
        for line in stdout.splitlines():
            if line.strip().startswith("Name:") or line.strip().startswith("Advisory:"):
                vulns.append({"raw": line.strip(), "severity": "unknown"})

    return {"tool": "bundler-audit", "status": "ok", "vulnerabilities": vulns}


def scan_go(project_path: Path) -> dict:
    """Run govulncheck."""
    code, stdout, stderr = run_command(["govulncheck", "-json", "./..."], str(project_path))
    if code == -1:
        return {"tool": "govulncheck", "status": "tool_not_installed",
                "install_hint": "go install golang.org/x/vuln/cmd/govulncheck@latest", "vulnerabilities": []}

    vulns = []
    try:
        data = json.loads(stdout) if stdout.strip() else {}
        for vuln in data.get("vulns", []):
            osv = vuln.get("osv", {})
            vulns.append({
                "vulnerability_id": osv.get("id", "unknown"),
                "summary": osv.get("summary", ""),
                "severity": osv.get("database_specific", {}).get("severity", "unknown"),
                "affected_packages": [a.get("package", {}).get("name", "") for a in osv.get("affected", [])],
            })
    except json.JSONDecodeError:
        pass

    return {"tool": "govulncheck", "status": "ok", "vulnerabilities": vulns}


SCANNERS = {
    "python": scan_python,
    "node": scan_node,
    "dotnet": scan_dotnet,
    "ruby": scan_ruby,
    "go": scan_go,
}


def filter_by_severity(vulns: list[dict], min_severity: str) -> list[dict]:
    """Filter vulnerabilities to only include those at or above min_severity."""
    threshold = SEVERITY_ORDER.get(min_severity, 0)
    return [v for v in vulns if SEVERITY_ORDER.get(v.get("severity", "unknown"), 0) >= threshold]


def format_markdown(report: dict) -> str:
    """Convert JSON report to markdown."""
    lines = [f"# Vulnerability Scan Report", f"**Scanned**: {report['scanned_at']}", f"**Path**: {report['project_path']}", ""]
    total = report["summary"]["total_vulnerabilities"]
    lines.append(f"## Summary: {total} vulnerabilit{'y' if total == 1 else 'ies'} found\n")

    for eco_report in report["ecosystems"]:
        eco = eco_report["ecosystem"]
        tool = eco_report["tool"]
        vulns = eco_report["vulnerabilities"]
        lines.append(f"### {eco.title()} ({tool})")

        if eco_report["status"] == "tool_not_installed":
            lines.append(f"> Tool not installed. Install with: `{eco_report.get('install_hint', 'N/A')}`\n")
            continue

        if not vulns:
            lines.append("No vulnerabilities found.\n")
            continue

        lines.append(f"| Package | Severity | Details |")
        lines.append(f"|---------|----------|---------|")
        for v in vulns:
            pkg = v.get("package", v.get("raw", "unknown"))
            sev = v.get("severity", "unknown")
            detail = v.get("vulnerability_id", v.get("title", v.get("summary", "")))
            lines.append(f"| {pkg} | {sev} | {detail} |")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Universal Dependency Vulnerability Scanner")
    parser.add_argument("--path", default=".", help="Project root path (default: current directory)")
    parser.add_argument("--format", choices=["json", "markdown"], default="json", help="Output format")
    parser.add_argument("--severity", choices=["low", "medium", "high", "critical"], default="low",
                        help="Minimum severity to report (default: low = show all)")
    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    if not project_path.is_dir():
        print(json.dumps({"error": f"Path not found: {project_path}"}), file=sys.stderr)
        sys.exit(1)

    ecosystems = detect_ecosystems(project_path)
    if not ecosystems:
        result = {"error": "No recognized project manifests found", "scanned_path": str(project_path),
                  "hint": "Ensure the path contains requirements.txt, package.json, *.csproj, Gemfile, or go.mod"}
        print(json.dumps(result, indent=2))
        sys.exit(0)

    report = {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "detected_ecosystems": [e["ecosystem"] for e in ecosystems],
        "ecosystems": [],
        "summary": {"total_vulnerabilities": 0, "by_severity": {}},
    }

    for eco in ecosystems:
        scanner = SCANNERS.get(eco["ecosystem"])
        if not scanner:
            continue
        result = scanner(project_path)
        result["ecosystem"] = eco["ecosystem"]
        result["manifest"] = eco["manifest"]

        # Apply severity filter
        if "vulnerabilities" in result:
            result["vulnerabilities"] = filter_by_severity(result["vulnerabilities"], args.severity)

        report["ecosystems"].append(result)
        count = len(result.get("vulnerabilities", []))
        report["summary"]["total_vulnerabilities"] += count

        for v in result.get("vulnerabilities", []):
            sev = v.get("severity", "unknown")
            report["summary"]["by_severity"][sev] = report["summary"]["by_severity"].get(sev, 0) + 1

    if args.format == "markdown":
        print(format_markdown(report))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
