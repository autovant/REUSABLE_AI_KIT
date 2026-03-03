#!/usr/bin/env python3
"""
Code and documentation synchronization checker.

Detects when code changes require documentation updates or vice versa.

Features:
- Monitors code changes and identifies affected docs
- Monitors doc changes and identifies affected code
- Generates sync reports
- Integration with git for change detection
"""

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class SyncRule:
    """Defines a sync relationship between code and docs."""
    code_pattern: str
    doc_pattern: str
    description: str


@dataclass
class SyncIssue:
    """Represents a detected sync issue."""
    source_file: str
    target_file: str
    source_type: str  # 'code' or 'doc'
    change_type: str  # 'modified', 'added', 'deleted'
    description: str
    recommendation: str


# Default sync rules - customize per project
DEFAULT_RULES = [
    SyncRule(
        code_pattern=r"backend/src/api/.*\.py",
        doc_pattern="docs/api-reference.md",
        description="API endpoints"
    ),
    SyncRule(
        code_pattern=r"agents/.*/manifest\.json",
        doc_pattern="docs/agents/*.md",
        description="Agent manifests"
    ),
    SyncRule(
        code_pattern=r".*requirements\.txt",
        doc_pattern="docs/installation.md",
        description="Dependencies"
    ),
    SyncRule(
        code_pattern=r"docker-compose.*\.yml",
        doc_pattern="docs/deployment.md",
        description="Docker configuration"
    ),
    SyncRule(
        code_pattern=r"\.env\.example",
        doc_pattern="docs/configuration.md",
        description="Environment variables"
    ),
]


def run_git_command(cmd: list[str], cwd: Optional[str] = None) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ['git'] + cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return ""


def get_changed_files(since: str = 'HEAD~1', cwd: Optional[str] = None) -> list[tuple[str, str]]:
    """Get list of changed files with their status."""
    output = run_git_command(['diff', '--name-status', since], cwd)
    
    changes = []
    for line in output.split('\n'):
        if line:
            parts = line.split('\t')
            if len(parts) >= 2:
                status = parts[0][0]  # M, A, D, R, etc.
                filename = parts[-1]  # Use last part for renames
                
                status_map = {
                    'M': 'modified',
                    'A': 'added',
                    'D': 'deleted',
                    'R': 'renamed'
                }
                changes.append((filename, status_map.get(status, 'modified')))
    
    return changes


def match_pattern(filepath: str, pattern: str) -> bool:
    """Check if filepath matches the given pattern."""
    # Convert glob-like pattern to regex
    regex_pattern = pattern.replace('.', r'\.').replace('*', '.*')
    return bool(re.match(regex_pattern, filepath))


def find_related_docs(code_file: str, rules: list[SyncRule]) -> list[str]:
    """Find documentation files related to a code file."""
    related = []
    for rule in rules:
        if match_pattern(code_file, rule.code_pattern):
            related.append(rule.doc_pattern)
    return related


def find_related_code(doc_file: str, rules: list[SyncRule]) -> list[str]:
    """Find code files related to a documentation file."""
    related = []
    for rule in rules:
        if match_pattern(doc_file, rule.doc_pattern):
            related.append(rule.code_pattern)
    return related


def is_code_file(filepath: str) -> bool:
    """Determine if a file is a code file."""
    code_extensions = {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cs',
        '.go', '.rb', '.php', '.rs', '.cpp', '.c', '.h',
        '.json', '.yaml', '.yml', '.xml', '.sql'
    }
    return Path(filepath).suffix.lower() in code_extensions


def is_doc_file(filepath: str) -> bool:
    """Determine if a file is a documentation file."""
    doc_extensions = {'.md', '.rst', '.txt', '.adoc'}
    doc_paths = {'docs/', 'documentation/', 'doc/', 'README'}
    
    filepath_lower = filepath.lower()
    
    if Path(filepath).suffix.lower() in doc_extensions:
        return True
    
    for doc_path in doc_paths:
        if doc_path.lower() in filepath_lower:
            return True
    
    return False


def analyze_changes(
    changes: list[tuple[str, str]],
    rules: list[SyncRule],
    workspace: Optional[str] = None
) -> list[SyncIssue]:
    """Analyze changes and identify sync issues."""
    issues = []
    
    for filepath, change_type in changes:
        if is_code_file(filepath):
            # Code changed - check if docs need updating
            related_docs = find_related_docs(filepath, rules)
            
            for doc_pattern in related_docs:
                # Check if doc was also changed
                doc_changed = any(
                    match_pattern(f, doc_pattern)
                    for f, _ in changes
                    if is_doc_file(f)
                )
                
                if not doc_changed:
                    issues.append(SyncIssue(
                        source_file=filepath,
                        target_file=doc_pattern,
                        source_type='code',
                        change_type=change_type,
                        description=f"Code file '{filepath}' was {change_type} but related documentation may be outdated.",
                        recommendation=f"Review and update documentation matching '{doc_pattern}'."
                    ))
        
        elif is_doc_file(filepath):
            # Doc changed - check if it reflects code changes
            related_code = find_related_code(filepath, rules)
            
            for code_pattern in related_code:
                # Check if related code was also changed
                code_changed = any(
                    match_pattern(f, code_pattern)
                    for f, _ in changes
                    if is_code_file(f)
                )
                
                if not code_changed:
                    issues.append(SyncIssue(
                        source_file=filepath,
                        target_file=code_pattern,
                        source_type='doc',
                        change_type=change_type,
                        description=f"Documentation '{filepath}' was {change_type} without corresponding code changes.",
                        recommendation=f"Verify documentation matches current code in '{code_pattern}'."
                    ))
    
    return issues


def generate_report(issues: list[SyncIssue], output_path: Optional[Path] = None) -> str:
    """Generate a sync report."""
    report = f"""# Code-Documentation Sync Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Total Issues**: {len(issues)}

## Summary

| Source Type | Count |
|-------------|-------|
| Code changes needing doc updates | {len([i for i in issues if i.source_type == 'code'])} |
| Doc changes needing verification | {len([i for i in issues if i.source_type == 'doc'])} |

## Issues

"""
    
    if not issues:
        report += "*No sync issues detected.*\n"
    else:
        for i, issue in enumerate(issues, 1):
            report += f"""### Issue {i}

**Source**: `{issue.source_file}` ({issue.change_type})
**Target**: `{issue.target_file}`
**Type**: {issue.source_type.upper()} -> DOC sync

**Description**:
{issue.description}

**Recommendation**:
{issue.recommendation}

---

"""
    
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
    
    return report


def load_rules(config_path: Optional[Path] = None) -> list[SyncRule]:
    """Load sync rules from config file or use defaults."""
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [
                SyncRule(
                    code_pattern=rule['code_pattern'],
                    doc_pattern=rule['doc_pattern'],
                    description=rule.get('description', '')
                )
                for rule in data.get('rules', [])
            ]
    
    return DEFAULT_RULES


def main():
    parser = argparse.ArgumentParser(
        description='Check code and documentation synchronization'
    )
    parser.add_argument(
        '--since',
        default='HEAD~1',
        help='Git ref to compare against (default: HEAD~1)'
    )
    parser.add_argument(
        '--output', '-o',
        help='Output report file path'
    )
    parser.add_argument(
        '--config', '-c',
        help='Path to sync rules config file'
    )
    parser.add_argument(
        '--workspace', '-w',
        default='.',
        help='Workspace directory'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Exit with error code if issues found'
    )
    
    args = parser.parse_args()
    
    # Load rules
    config_path = Path(args.config) if args.config else None
    rules = load_rules(config_path)
    
    # Get changes
    changes = get_changed_files(args.since, args.workspace)
    
    if not changes:
        print("No changes detected.")
        return 0
    
    print(f"Analyzing {len(changes)} changed files...")
    
    # Analyze
    issues = analyze_changes(changes, rules, args.workspace)
    
    # Output
    if args.json:
        output = {
            'timestamp': datetime.now().isoformat(),
            'changes_analyzed': len(changes),
            'issues_found': len(issues),
            'issues': [
                {
                    'source_file': i.source_file,
                    'target_file': i.target_file,
                    'source_type': i.source_type,
                    'change_type': i.change_type,
                    'description': i.description,
                    'recommendation': i.recommendation
                }
                for i in issues
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        output_path = Path(args.output) if args.output else None
        report = generate_report(issues, output_path)
        
        if not args.output:
            print(report)
        else:
            print(f"Report written to: {args.output}")
    
    # Summary
    print(f"\nSync Check Complete:")
    print(f"  Files analyzed: {len(changes)}")
    print(f"  Issues found: {len(issues)}")
    
    if args.strict and issues:
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
