#!/usr/bin/env python3
"""
Jira story creation helper script.

Features:
- Create stories with proper formatting
- Auto-fetch current sprint
- Embed files into descriptions
- Convert Markdown to Jira format
"""

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error


# Configuration - Update these or use environment variables
JIRA_URL = os.environ.get('JIRA_URL', 'https://your-domain.atlassian.net')
JIRA_EMAIL = os.environ.get('JIRA_EMAIL', '')
JIRA_API_TOKEN = os.environ.get('JIRA_API_TOKEN', '')
JIRA_PROJECT = os.environ.get('JIRA_PROJECT', 'PROJ')
JIRA_BOARD_ID = os.environ.get('JIRA_BOARD_ID', '')


def get_auth_header() -> str:
    """Generate Basic auth header."""
    if not JIRA_EMAIL or not JIRA_API_TOKEN:
        print("Error: JIRA_EMAIL and JIRA_API_TOKEN environment variables required")
        sys.exit(1)
    
    credentials = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return f"Basic {encoded}"


def markdown_to_jira(text: str) -> str:
    """Convert Markdown syntax to Jira markup."""
    # Headers
    text = re.sub(r'^#### (.+)$', r'h4. \1', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.+)$', r'h3. \1', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'h2. \1', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'h1. \1', text, flags=re.MULTILINE)
    
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)
    
    # Italic
    text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'_\1_', text)
    
    # Code blocks
    text = re.sub(r'```(\w*)\n(.*?)```', r'{code:\1}\n\2{code}', text, flags=re.DOTALL)
    
    # Inline code
    text = re.sub(r'`([^`]+)`', r'{{\1}}', text)
    
    # Links
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'[\1|\2]', text)
    
    # Checkboxes
    text = re.sub(r'- \[ \]', r'* (x)', text)
    text = re.sub(r'- \[x\]', r'* (/)', text)
    
    # Unordered lists
    text = re.sub(r'^- ', r'* ', text, flags=re.MULTILINE)
    
    return text


def read_and_embed_file(file_path: str) -> str:
    """Read file and format for embedding."""
    path = Path(file_path)
    
    if not path.exists():
        return f"[File not found: {file_path}]"
    
    content = path.read_text(encoding='utf-8')
    
    # Determine file type for code block
    ext = path.suffix.lower()
    lang_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'none',
        '.xml': 'xml',
        '.sql': 'sql',
        '.sh': 'bash',
        '.ps1': 'powershell',
    }
    
    lang = lang_map.get(ext, 'none')
    
    if ext == '.md':
        # Convert embedded Markdown
        content = markdown_to_jira(content)
        return f"\n\nh2. Embedded: {path.name}\n\n{content}"
    else:
        return f"\n\nh2. Embedded: {path.name}\n\n{{code:{lang}}}\n{content}\n{{code}}"


def get_current_sprint(board_id: str) -> Optional[int]:
    """Fetch current active sprint ID."""
    if not board_id:
        return None
    
    url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint?state=active"
    
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': get_auth_header(),
            'Accept': 'application/json'
        }
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data.get('values'):
                return data['values'][0]['id']
    except urllib.error.HTTPError as e:
        print(f"Warning: Could not fetch sprint: {e}")
    
    return None


def create_story(
    title: str,
    description: str,
    epic_key: str,
    story_points: int = 4,
    priority: str = 'High',
    issue_type: str = 'Story',
    sprint_id: Optional[int] = None,
    embed_files: Optional[list[str]] = None,
    assignee: Optional[str] = None,
    team: Optional[str] = None
) -> dict:
    """Create a Jira story."""
    
    # Convert description to Jira format
    jira_description = markdown_to_jira(description)
    
    # Embed files if provided
    if embed_files:
        for file_path in embed_files:
            jira_description += read_and_embed_file(file_path)
    
    # Build payload
    payload = {
        'fields': {
            'project': {'key': JIRA_PROJECT},
            'summary': title,
            'description': jira_description,
            'issuetype': {'name': issue_type},
            'priority': {'name': priority}
        }
    }
    
    # Add epic link (custom field - adjust ID as needed)
    if epic_key:
        payload['fields']['customfield_10014'] = epic_key
    
    # Add story points (custom field - adjust ID as needed)
    if story_points:
        payload['fields']['customfield_10092'] = story_points
    
    # Add sprint (custom field - adjust ID as needed)
    if sprint_id:
        payload['fields']['customfield_10020'] = sprint_id
    
    # Add team (custom field - adjust ID as needed)
    if team:
        payload['fields']['customfield_10175'] = [{'value': team}]
    
    # Add assignee
    if assignee:
        payload['fields']['assignee'] = {'emailAddress': assignee}
    
    # Create the issue
    url = f"{JIRA_URL}/rest/api/2/issue"
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': get_auth_header(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return {
                'success': True,
                'key': data['key'],
                'url': f"{JIRA_URL}/browse/{data['key']}"
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {
            'success': False,
            'error': f"HTTP {e.code}: {error_body}"
        }


def main():
    parser = argparse.ArgumentParser(
        description='Create Jira stories with proper formatting'
    )
    parser.add_argument('--title', required=True, help='Story title')
    parser.add_argument('--description', required=True, help='Story description (Markdown)')
    parser.add_argument('--epic-key', required=True, help='Epic key to link to')
    parser.add_argument('--story-points', type=int, default=4, choices=[2, 4, 8, 12])
    parser.add_argument('--priority', default='High', choices=['Critical', 'High', 'Medium', 'Low'])
    parser.add_argument('--issue-type', default='Story', choices=['Story', 'Task', 'Bug'])
    parser.add_argument('--sprint-id', type=int, help='Sprint ID (auto-fetched if not provided)')
    parser.add_argument('--embed-files', nargs='*', help='Files to embed in description')
    parser.add_argument('--assignee', help='Assignee email')
    parser.add_argument('--team', help='Team name')
    parser.add_argument('--dry-run', action='store_true', help='Print payload without creating')
    
    args = parser.parse_args()
    
    # Auto-fetch sprint if not provided
    sprint_id = args.sprint_id
    if not sprint_id and JIRA_BOARD_ID:
        sprint_id = get_current_sprint(JIRA_BOARD_ID)
        if sprint_id:
            print(f"Using current sprint: {sprint_id}")
    
    if args.dry_run:
        print("Dry run - would create:")
        print(f"  Title: {args.title}")
        print(f"  Epic: {args.epic_key}")
        print(f"  Points: {args.story_points}")
        print(f"  Sprint: {sprint_id}")
        print(f"  Files: {args.embed_files}")
        return 0
    
    result = create_story(
        title=args.title,
        description=args.description,
        epic_key=args.epic_key,
        story_points=args.story_points,
        priority=args.priority,
        issue_type=args.issue_type,
        sprint_id=sprint_id,
        embed_files=args.embed_files,
        assignee=args.assignee,
        team=args.team
    )
    
    if result['success']:
        print(f"Created: {result['key']}")
        print(f"URL: {result['url']}")
        return 0
    else:
        print(f"Error: {result['error']}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
