#!/usr/bin/env python3
"""
Issue tracker management for cross-agent learning.

Features:
- Add new issues
- Update existing issues
- Generate reports
- Search issues
"""

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class Category(Enum):
    BUILD = "Build"
    RUNTIME = "Runtime"
    CONFIG = "Config"
    INTEGRATION = "Integration"
    PERFORMANCE = "Performance"
    SECURITY = "Security"
    TESTING = "Testing"
    DEPLOYMENT = "Deployment"


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Issue:
    id: str
    title: str
    category: str
    severity: str
    date: str
    symptoms: list[str]
    root_cause: str
    solution: str
    prevention: str
    files_changed: list[str]
    related_issues: list[str] = None
    
    def to_markdown(self) -> str:
        """Convert issue to Markdown format."""
        md = f"""### {self.id}: {self.title}

**Category**: {self.category}
**Date**: {self.date}
**Severity**: {self.severity}

**Symptoms**:
"""
        for symptom in self.symptoms:
            md += f"- {symptom}\n"
        
        md += f"""
**Root Cause**:
{self.root_cause}

**Solution**:
```
{self.solution}
```

**Prevention**:
{self.prevention}

**Files Changed**:
"""
        for file in self.files_changed:
            md += f"- `{file}`\n"
        
        if self.related_issues:
            md += "\n**Related Issues**: " + ", ".join(self.related_issues)
        
        md += "\n\n---\n"
        return md


class IssueTracker:
    """Manages the issue tracker file."""
    
    def __init__(self, tracker_path: Path):
        self.tracker_path = tracker_path
        self.issues: list[Issue] = []
        self._load()
    
    def _load(self):
        """Load issues from the tracker file."""
        if not self.tracker_path.exists():
            self._create_new_tracker()
            return
        
        content = self.tracker_path.read_text(encoding='utf-8')
        
        # Parse existing issues
        issue_pattern = r'### (ISS-\d+): (.+?)\n'
        matches = re.finditer(issue_pattern, content)
        
        for match in matches:
            issue_id = match.group(1)
            title = match.group(2)
            # Note: Full parsing would be more complex
            # This is a simplified version
    
    def _create_new_tracker(self):
        """Create a new issue tracker file."""
        template = """# Issue Tracker

Central log of resolved issues for cross-agent reference.

## Quick Reference

| ID | Category | Summary | Solution |
|----|----------|---------|----------|

---

## Detailed Issues

"""
        self.tracker_path.parent.mkdir(parents=True, exist_ok=True)
        self.tracker_path.write_text(template, encoding='utf-8')
    
    def _get_next_id(self) -> str:
        """Get the next issue ID."""
        content = self.tracker_path.read_text(encoding='utf-8')
        existing_ids = re.findall(r'ISS-(\d+)', content)
        
        if existing_ids:
            max_id = max(int(id) for id in existing_ids)
            return f"ISS-{max_id + 1:03d}"
        return "ISS-001"
    
    def add_issue(self, issue: Issue) -> str:
        """Add a new issue to the tracker."""
        content = self.tracker_path.read_text(encoding='utf-8')
        
        # Assign ID if not provided
        if not issue.id:
            issue.id = self._get_next_id()
        
        # Add to quick reference
        quick_ref_row = f"| {issue.id} | {issue.category} | {issue.title} | {issue.solution[:50]}... |\n"
        
        # Find the end of quick reference table
        table_end = content.find("---\n\n## Detailed Issues")
        if table_end != -1:
            content = content[:table_end] + quick_ref_row + content[table_end:]
        
        # Add detailed issue at the end
        content += issue.to_markdown()
        
        self.tracker_path.write_text(content, encoding='utf-8')
        return issue.id
    
    def search(self, query: str) -> list[dict]:
        """Search issues by keyword."""
        content = self.tracker_path.read_text(encoding='utf-8')
        results = []
        
        # Simple search in content
        issue_blocks = content.split('### ISS-')
        
        for block in issue_blocks[1:]:  # Skip header
            if query.lower() in block.lower():
                # Extract ID and title
                first_line = block.split('\n')[0]
                match = re.match(r'(\d+): (.+)', first_line)
                if match:
                    results.append({
                        'id': f"ISS-{match.group(1)}",
                        'title': match.group(2),
                        'preview': block[:200] + '...'
                    })
        
        return results
    
    def get_stats(self) -> dict:
        """Get statistics about tracked issues."""
        content = self.tracker_path.read_text(encoding='utf-8')
        
        categories = {}
        severities = {}
        
        for cat in Category:
            count = len(re.findall(rf'\*\*Category\*\*: {cat.value}', content))
            if count > 0:
                categories[cat.value] = count
        
        for sev in Severity:
            count = len(re.findall(rf'\*\*Severity\*\*: {sev.value}', content))
            if count > 0:
                severities[sev.value] = count
        
        total = len(re.findall(r'### ISS-\d+', content))
        
        return {
            'total': total,
            'by_category': categories,
            'by_severity': severities
        }


def main():
    parser = argparse.ArgumentParser(
        description='Issue tracker management'
    )
    parser.add_argument(
        '--tracker', '-t',
        default='issue-tracker.md',
        help='Path to issue tracker file'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new issue')
    add_parser.add_argument('--title', required=True, help='Issue title')
    add_parser.add_argument('--category', required=True, choices=[c.value for c in Category])
    add_parser.add_argument('--severity', required=True, choices=[s.value for s in Severity])
    add_parser.add_argument('--symptoms', required=True, nargs='+', help='Symptoms list')
    add_parser.add_argument('--root-cause', required=True, help='Root cause description')
    add_parser.add_argument('--solution', required=True, help='Solution')
    add_parser.add_argument('--prevention', required=True, help='Prevention steps')
    add_parser.add_argument('--files', nargs='+', default=[], help='Changed files')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search issues')
    search_parser.add_argument('query', help='Search query')
    
    # Stats command
    subparsers.add_parser('stats', help='Show statistics')
    
    # Init command
    subparsers.add_parser('init', help='Initialize new tracker')
    
    args = parser.parse_args()
    
    tracker = IssueTracker(Path(args.tracker))
    
    if args.command == 'add':
        issue = Issue(
            id='',  # Will be assigned
            title=args.title,
            category=args.category,
            severity=args.severity,
            date=datetime.now().strftime('%Y-%m-%d'),
            symptoms=args.symptoms,
            root_cause=args.root_cause,
            solution=args.solution,
            prevention=args.prevention,
            files_changed=args.files
        )
        issue_id = tracker.add_issue(issue)
        print(f"Added issue: {issue_id}")
    
    elif args.command == 'search':
        results = tracker.search(args.query)
        if results:
            print(f"Found {len(results)} results:\n")
            for r in results:
                print(f"  {r['id']}: {r['title']}")
        else:
            print("No matching issues found.")
    
    elif args.command == 'stats':
        stats = tracker.get_stats()
        print(f"Total Issues: {stats['total']}")
        print("\nBy Category:")
        for cat, count in stats['by_category'].items():
            print(f"  {cat}: {count}")
        print("\nBy Severity:")
        for sev, count in stats['by_severity'].items():
            print(f"  {sev}: {count}")
    
    elif args.command == 'init':
        if not tracker.tracker_path.exists():
            tracker._create_new_tracker()
            print(f"Created new tracker: {args.tracker}")
        else:
            print(f"Tracker already exists: {args.tracker}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
