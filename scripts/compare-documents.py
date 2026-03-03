#!/usr/bin/env python3
"""
Document comparison and gap analysis tool.

Compares two documents and identifies:
- Missing sections
- Content differences
- Semantic gaps
- Inconsistencies
"""

import argparse
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime


class GapSeverity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class GapStatus(Enum):
    MISSING = "Missing"
    PARTIAL = "Partial"
    OUTDATED = "Outdated"
    ALIGNED = "Aligned"


@dataclass
class Section:
    """Represents a document section."""
    title: str
    level: int
    content: str
    line_number: int
    subsections: list = field(default_factory=list)


@dataclass
class Gap:
    """Represents an identified gap."""
    id: str
    title: str
    severity: GapSeverity
    status: GapStatus
    source_ref: str
    target_ref: Optional[str]
    description: str
    recommendation: str


def extract_sections(content: str) -> list[Section]:
    """Extract sections from Markdown content."""
    sections = []
    lines = content.split('\n')
    
    current_section = None
    section_content = []
    
    for i, line in enumerate(lines):
        # Check for heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        
        if heading_match:
            # Save previous section
            if current_section:
                current_section.content = '\n'.join(section_content).strip()
                sections.append(current_section)
            
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            current_section = Section(
                title=title,
                level=level,
                content='',
                line_number=i + 1
            )
            section_content = []
        else:
            section_content.append(line)
    
    # Don't forget the last section
    if current_section:
        current_section.content = '\n'.join(section_content).strip()
        sections.append(current_section)
    
    return sections


def extract_key_terms(content: str) -> set[str]:
    """Extract important terms from content."""
    # Remove code blocks
    content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
    
    # Extract capitalized terms (likely important)
    caps_terms = set(re.findall(r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\b', content))
    
    # Extract quoted terms
    quoted_terms = set(re.findall(r'["\']([^"\']+)["\']', content))
    
    # Extract code-style terms
    code_terms = set(re.findall(r'`([^`]+)`', content))
    
    return caps_terms | quoted_terms | code_terms


def normalize_title(title: str) -> str:
    """Normalize a section title for comparison."""
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def find_matching_section(section: Section, candidates: list[Section], threshold: float = 0.7) -> Optional[Section]:
    """Find a matching section in candidates based on title similarity."""
    source_norm = normalize_title(section.title)
    
    for candidate in candidates:
        target_norm = normalize_title(candidate.title)
        
        # Exact match
        if source_norm == target_norm:
            return candidate
        
        # Check for substring match
        if source_norm in target_norm or target_norm in source_norm:
            return candidate
        
        # Simple word overlap
        source_words = set(source_norm.split())
        target_words = set(target_norm.split())
        overlap = len(source_words & target_words)
        total = len(source_words | target_words)
        
        if total > 0 and overlap / total >= threshold:
            return candidate
    
    return None


def compare_content(source_content: str, target_content: str) -> GapStatus:
    """Compare content of two sections."""
    source_terms = extract_key_terms(source_content)
    target_terms = extract_key_terms(target_content)
    
    if not source_terms:
        return GapStatus.ALIGNED
    
    overlap = len(source_terms & target_terms)
    coverage = overlap / len(source_terms) if source_terms else 1.0
    
    if coverage >= 0.8:
        return GapStatus.ALIGNED
    elif coverage >= 0.5:
        return GapStatus.PARTIAL
    else:
        return GapStatus.OUTDATED


def analyze_gaps(source_path: Path, target_path: Path) -> list[Gap]:
    """Analyze gaps between source and target documents."""
    with open(source_path, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    with open(target_path, 'r', encoding='utf-8') as f:
        target_content = f.read()
    
    source_sections = extract_sections(source_content)
    target_sections = extract_sections(target_content)
    
    gaps = []
    gap_counter = 1
    
    for source_section in source_sections:
        matching_target = find_matching_section(source_section, target_sections)
        
        if matching_target is None:
            # Section completely missing
            severity = GapSeverity.HIGH if source_section.level <= 2 else GapSeverity.MEDIUM
            gaps.append(Gap(
                id=f"GAP-{gap_counter:03d}",
                title=f"Missing: {source_section.title}",
                severity=severity,
                status=GapStatus.MISSING,
                source_ref=f"Section: {source_section.title} (Line {source_section.line_number})",
                target_ref=None,
                description=f"Section '{source_section.title}' from source is not present in target document.",
                recommendation=f"Add section covering: {source_section.title}"
            ))
            gap_counter += 1
        else:
            # Section exists, compare content
            status = compare_content(source_section.content, matching_target.content)
            
            if status == GapStatus.PARTIAL:
                gaps.append(Gap(
                    id=f"GAP-{gap_counter:03d}",
                    title=f"Partial: {source_section.title}",
                    severity=GapSeverity.MEDIUM,
                    status=GapStatus.PARTIAL,
                    source_ref=f"Section: {source_section.title} (Line {source_section.line_number})",
                    target_ref=f"Section: {matching_target.title} (Line {matching_target.line_number})",
                    description=f"Section '{source_section.title}' has partial coverage in target.",
                    recommendation="Review and expand target section to cover all source content."
                ))
                gap_counter += 1
            elif status == GapStatus.OUTDATED:
                gaps.append(Gap(
                    id=f"GAP-{gap_counter:03d}",
                    title=f"Outdated: {source_section.title}",
                    severity=GapSeverity.HIGH,
                    status=GapStatus.OUTDATED,
                    source_ref=f"Section: {source_section.title} (Line {source_section.line_number})",
                    target_ref=f"Section: {matching_target.title} (Line {matching_target.line_number})",
                    description=f"Section '{source_section.title}' content differs significantly from source.",
                    recommendation="Update target section to align with source content."
                ))
                gap_counter += 1
    
    return gaps


def generate_report(gaps: list[Gap], source_path: Path, target_path: Path, output_path: Path):
    """Generate a gap analysis report."""
    # Count by status
    missing = len([g for g in gaps if g.status == GapStatus.MISSING])
    partial = len([g for g in gaps if g.status == GapStatus.PARTIAL])
    outdated = len([g for g in gaps if g.status == GapStatus.OUTDATED])
    total = len(gaps)
    
    # Count by severity
    critical = len([g for g in gaps if g.severity == GapSeverity.CRITICAL])
    high = len([g for g in gaps if g.severity == GapSeverity.HIGH])
    medium = len([g for g in gaps if g.severity == GapSeverity.MEDIUM])
    low = len([g for g in gaps if g.severity == GapSeverity.LOW])
    
    report = f"""# Gap Analysis Report

**Source**: {source_path.name}
**Target**: {target_path.name}
**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Executive Summary

- **Total Gaps**: {total}
- **Missing Sections**: {missing}
- **Partial Coverage**: {partial}
- **Outdated Content**: {outdated}

### By Severity

| Severity | Count |
|----------|-------|
| Critical | {critical} |
| High | {high} |
| Medium | {medium} |
| Low | {low} |

## Coverage Matrix

| Status | Count | Percentage |
|--------|-------|------------|
| Missing | {missing} | {missing/total*100:.1f}% |
| Partial | {partial} | {partial/total*100:.1f}% |
| Outdated | {outdated} | {outdated/total*100:.1f}% |

## Detailed Findings

"""

    # Group by severity
    for severity in [GapSeverity.CRITICAL, GapSeverity.HIGH, GapSeverity.MEDIUM, GapSeverity.LOW]:
        severity_gaps = [g for g in gaps if g.severity == severity]
        if severity_gaps:
            report += f"### {severity.value} Priority\n\n"
            
            for gap in severity_gaps:
                report += f"""#### {gap.id}: {gap.title}

**Status**: {gap.status.value}
**Source Reference**: {gap.source_ref}
"""
                if gap.target_ref:
                    report += f"**Target Reference**: {gap.target_ref}\n"
                
                report += f"""
**Description**:
{gap.description}

**Recommendation**:
{gap.recommendation}

---

"""

    # Recommendations summary
    report += """## Recommendations Summary

### Priority 1 (Critical/High)
"""
    for gap in [g for g in gaps if g.severity in [GapSeverity.CRITICAL, GapSeverity.HIGH]]:
        report += f"- {gap.id}: {gap.recommendation}\n"
    
    report += """
### Priority 2 (Medium)
"""
    for gap in [g for g in gaps if g.severity == GapSeverity.MEDIUM]:
        report += f"- {gap.id}: {gap.recommendation}\n"
    
    report += """
### Priority 3 (Low)
"""
    for gap in [g for g in gaps if g.severity == GapSeverity.LOW]:
        report += f"- {gap.id}: {gap.recommendation}\n"
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Gap analysis report generated: {output_path}")
    print(f"Found {total} gaps ({critical} critical, {high} high, {medium} medium, {low} low)")


def main():
    parser = argparse.ArgumentParser(
        description='Compare documents and generate gap analysis'
    )
    parser.add_argument(
        '--source', '-s',
        required=True,
        help='Source/reference document path'
    )
    parser.add_argument(
        '--target', '-t',
        required=True,
        help='Target document to compare'
    )
    parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output report path'
    )
    parser.add_argument(
        '--type',
        choices=['requirements', 'specifications', 'documentation', 'code_comments'],
        default='documentation',
        help='Type of comparison'
    )
    
    args = parser.parse_args()
    
    source_path = Path(args.source)
    target_path = Path(args.target)
    output_path = Path(args.output)
    
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}")
        return 1
    
    if not target_path.exists():
        print(f"Error: Target file not found: {target_path}")
        return 1
    
    gaps = analyze_gaps(source_path, target_path)
    generate_report(gaps, source_path, target_path, output_path)
    
    return 0


if __name__ == '__main__':
    exit(main())
