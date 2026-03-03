#!/usr/bin/env python3
"""
Code Metrics Collector
========================
Collects code metrics for any project:
- Lines of code (LOC) by language
- File count and size distribution
- Cyclomatic complexity (Python files)
- Duplicate/near-duplicate detection
- Large file identification
- TODO/FIXME/HACK density

Auto-detects languages from file extensions.  Zero external dependencies.

Usage:
    python code_metrics.py [--path <project_root>] [--format json|markdown]
                           [--exclude ".git,node_modules,__pycache__,dist,build,.venv,venv"]
                           [--top N]  (top N largest files, default 10)

Requirements:
    - Python 3.8+  (stdlib only)
"""

import argparse
import ast
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ---------- Language detection ----------

EXTENSION_MAP = {
    ".py": "Python", ".pyw": "Python",
    ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".ts": "TypeScript", ".tsx": "TypeScript",
    ".jsx": "React JSX",
    ".java": "Java",
    ".cs": "C#",
    ".cpp": "C++", ".cc": "C++", ".cxx": "C++", ".hpp": "C++", ".h": "C/C++ Header",
    ".c": "C",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin", ".kts": "Kotlin",
    ".scala": "Scala",
    ".r": "R", ".R": "R",
    ".sql": "SQL",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".psm1": "PowerShell",
    ".html": "HTML", ".htm": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".less": "Less",
    ".json": "JSON",
    ".yaml": "YAML", ".yml": "YAML",
    ".xml": "XML",
    ".md": "Markdown", ".mdx": "Markdown",
    ".toml": "TOML",
    ".ini": "INI", ".cfg": "INI",
    ".tf": "Terraform", ".tfvars": "Terraform",
    ".proto": "Protocol Buffers",
    ".graphql": "GraphQL", ".gql": "GraphQL",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".dart": "Dart",
    ".lua": "Lua",
    ".ex": "Elixir", ".exs": "Elixir",
    ".erl": "Erlang",
    ".hs": "Haskell",
    ".ml": "OCaml", ".mli": "OCaml",
    ".clj": "Clojure", ".cljs": "Clojure",
}

DEFAULT_EXCLUDES = {".git", "node_modules", "__pycache__", "dist", "build", ".venv",
                    "venv", ".next", ".nuxt", "target", "bin", "obj", ".tox",
                    "coverage", ".mypy_cache", ".pytest_cache", "vendor"}

TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX|BUG|OPTIMIZE)\b", re.IGNORECASE)


# ---------- File collection ----------

def collect_files(project_path: Path, excludes: set[str]) -> list[Path]:
    """Walk the project tree, skipping excluded directories."""
    files = []
    for root, dirs, filenames in os.walk(project_path):
        # Prune excluded dirs in-place
        dirs[:] = [d for d in dirs if d not in excludes and not d.startswith(".")]
        for fname in filenames:
            fp = Path(root) / fname
            ext = fp.suffix.lower()
            if ext in EXTENSION_MAP:
                files.append(fp)
    return files


# ---------- LOC counting ----------

def count_lines(filepath: Path) -> dict:
    """Count total, code, blank, and comment lines."""
    try:
        text = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {"total": 0, "code": 0, "blank": 0, "comment": 0}

    lines = text.splitlines()
    total = len(lines)
    blank = sum(1 for l in lines if not l.strip())
    comment = 0
    in_block = False

    for line in lines:
        stripped = line.strip()
        # Simple multi-line comment detection
        if '"""' in stripped or "'''" in stripped:
            if stripped.count('"""') == 1 or stripped.count("'''") == 1:
                in_block = not in_block
            comment += 1
            continue
        if in_block:
            comment += 1
            continue
        if stripped.startswith(("#", "//", "--", ";", "/*", "*", "'")):
            comment += 1

    code = total - blank - comment
    return {"total": total, "code": max(0, code), "blank": blank, "comment": comment}


# ---------- Cyclomatic complexity (Python only) ----------

def python_complexity(filepath: Path) -> list[dict]:
    """Calculate cyclomatic complexity for Python functions/methods."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, OSError, ValueError):
        return []

    results = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = 1  # base
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(child, ast.BoolOp):
                    complexity += len(child.values) - 1
                elif isinstance(child, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(child, ast.Assert):
                    complexity += 1
                elif isinstance(child, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                    complexity += 1

            results.append({
                "function": node.name,
                "line": node.lineno,
                "complexity": complexity,
                "rating": "low" if complexity <= 5 else "medium" if complexity <= 10 else "high" if complexity <= 20 else "very_high",
            })

    return results


# ---------- Duplicate detection ----------

def find_duplicates(files: list[Path], project_path: Path, chunk_lines: int = 6) -> list[dict]:
    """Find files with identical content hashes, and near-duplicates via chunk matching."""
    # Exact duplicates by full hash
    hash_map: dict[str, list[str]] = defaultdict(list)
    for fp in files:
        try:
            content = fp.read_bytes()
            h = hashlib.sha256(content).hexdigest()
            rel = str(fp.relative_to(project_path))
            hash_map[h].append(rel)
        except OSError:
            continue

    exact_dupes = [{"hash": h[:12], "files": paths} for h, paths in hash_map.items() if len(paths) > 1]

    # Near-duplicate: shared N-line chunks across files
    chunk_map: dict[str, list[str]] = defaultdict(list)
    for fp in files:
        try:
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue

        if len(lines) < chunk_lines:
            continue

        rel = str(fp.relative_to(project_path))
        seen_chunks_in_file: set[str] = set()
        for i in range(len(lines) - chunk_lines + 1):
            chunk = "\n".join(l.strip() for l in lines[i:i + chunk_lines] if l.strip())
            if len(chunk) < 40:  # skip trivial chunks
                continue
            ch = hashlib.md5(chunk.encode()).hexdigest()
            if ch not in seen_chunks_in_file:
                seen_chunks_in_file.add(ch)
                chunk_map[ch].append(rel)

    # Find chunks that appear in multiple distinct files
    shared_chunks = 0
    file_pair_counts: Counter = Counter()
    for ch, file_list in chunk_map.items():
        unique_files = list(set(file_list))
        if len(unique_files) > 1:
            shared_chunks += 1
            for i in range(len(unique_files)):
                for j in range(i + 1, len(unique_files)):
                    pair = tuple(sorted([unique_files[i], unique_files[j]]))
                    file_pair_counts[pair] += 1

    near_dupes = [{"files": list(pair), "shared_chunks": count}
                  for pair, count in file_pair_counts.most_common(10) if count >= 3]

    return {"exact_duplicates": exact_dupes, "near_duplicates": near_dupes, "shared_chunk_count": shared_chunks}


# ---------- TODO/FIXME scanning ----------

def scan_todos(files: list[Path], project_path: Path) -> list[dict]:
    todos = []
    for fp in files:
        try:
            lines = fp.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        rel = str(fp.relative_to(project_path))
        for i, line in enumerate(lines, 1):
            matches = TODO_PATTERN.findall(line)
            for tag in matches:
                todos.append({"file": rel, "line": i, "tag": tag.upper(), "text": line.strip()[:120]})
    return todos


# ---------- Report building ----------

def build_report(project_path: Path, files: list[Path], top_n: int) -> dict:
    lang_stats: dict[str, dict] = defaultdict(lambda: {"files": 0, "total": 0, "code": 0, "blank": 0, "comment": 0})
    file_sizes: list[dict] = []
    all_complexity: list[dict] = []

    for fp in files:
        ext = fp.suffix.lower()
        lang = EXTENSION_MAP.get(ext, "Other")
        counts = count_lines(fp)

        lang_stats[lang]["files"] += 1
        for key in ("total", "code", "blank", "comment"):
            lang_stats[lang][key] += counts[key]

        rel = str(fp.relative_to(project_path))
        try:
            size_bytes = fp.stat().st_size
        except OSError:
            size_bytes = 0

        file_sizes.append({"file": rel, "language": lang, "lines": counts["total"], "bytes": size_bytes})

        # Complexity for Python files
        if lang == "Python":
            cx = python_complexity(fp)
            for entry in cx:
                entry["file"] = rel
            all_complexity.extend(cx)

    # Sort by size
    file_sizes.sort(key=lambda x: x["lines"], reverse=True)
    largest = file_sizes[:top_n]

    # Complexity hotspots
    complexity_hotspots = sorted(all_complexity, key=lambda x: x["complexity"], reverse=True)[:top_n]

    # Duplicates
    dupes = find_duplicates(files, project_path)

    # TODOs
    todos = scan_todos(files, project_path)

    # Summary
    total_files = len(files)
    total_loc = sum(s["total"] for s in lang_stats.values())
    total_code = sum(s["code"] for s in lang_stats.values())

    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "project_path": str(project_path),
        "summary": {
            "total_files": total_files,
            "total_lines": total_loc,
            "total_code_lines": total_code,
            "languages_detected": len(lang_stats),
            "todo_count": len(todos),
            "exact_duplicate_groups": len(dupes["exact_duplicates"]),
            "complexity_hotspots": len([c for c in all_complexity if c["complexity"] > 10]),
        },
        "languages": dict(sorted(lang_stats.items(), key=lambda x: x[1]["code"], reverse=True)),
        "largest_files": largest,
        "complexity_hotspots": complexity_hotspots,
        "duplicates": dupes,
        "todos": todos[:50],  # cap at 50 for readability
    }


# ---------- Formatting ----------

def format_markdown(report: dict) -> str:
    lines = ["# Code Metrics Report",
             f"**Collected**: {report['collected_at']}",
             f"**Path**: {report['project_path']}", ""]

    s = report["summary"]
    lines.append("## Summary\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Files | {s['total_files']} |")
    lines.append(f"| Total Lines | {s['total_lines']:,} |")
    lines.append(f"| Code Lines | {s['total_code_lines']:,} |")
    lines.append(f"| Languages | {s['languages_detected']} |")
    lines.append(f"| TODOs/FIXMEs | {s['todo_count']} |")
    lines.append(f"| Exact Duplicate Groups | {s['exact_duplicate_groups']} |")
    lines.append(f"| High-Complexity Functions | {s['complexity_hotspots']} |")
    lines.append("")

    # Language breakdown
    lines.append("## Lines of Code by Language\n")
    lines.append("| Language | Files | Code | Comments | Blank | Total |")
    lines.append("|----------|-------|------|----------|-------|-------|")
    for lang, stats in report["languages"].items():
        lines.append(f"| {lang} | {stats['files']} | {stats['code']:,} | {stats['comment']:,} | {stats['blank']:,} | {stats['total']:,} |")
    lines.append("")

    # Largest files
    if report["largest_files"]:
        lines.append("## Largest Files\n")
        lines.append("| File | Language | Lines | Size |")
        lines.append("|------|----------|-------|------|")
        for f in report["largest_files"]:
            size_kb = f["bytes"] / 1024
            lines.append(f"| {f['file']} | {f['language']} | {f['lines']:,} | {size_kb:.1f} KB |")
        lines.append("")

    # Complexity
    if report["complexity_hotspots"]:
        lines.append("## Complexity Hotspots\n")
        lines.append("| File | Function | Line | Complexity | Rating |")
        lines.append("|------|----------|------|------------|--------|")
        for c in report["complexity_hotspots"]:
            lines.append(f"| {c['file']} | {c['function']} | {c['line']} | {c['complexity']} | {c['rating']} |")
        lines.append("")

    # Duplicates
    dupes = report["duplicates"]
    if dupes["exact_duplicates"]:
        lines.append("## Exact Duplicates\n")
        for group in dupes["exact_duplicates"]:
            lines.append(f"- **{group['hash']}**: {', '.join(group['files'])}")
        lines.append("")

    if dupes["near_duplicates"]:
        lines.append("## Near-Duplicate File Pairs\n")
        for pair in dupes["near_duplicates"]:
            lines.append(f"- {pair['files'][0]} <-> {pair['files'][1]} ({pair['shared_chunks']} shared chunks)")
        lines.append("")

    # TODOs
    if report["todos"]:
        lines.append(f"## TODOs / FIXMEs (showing {len(report['todos'])})\n")
        lines.append("| File | Line | Tag | Text |")
        lines.append("|------|------|-----|------|")
        for t in report["todos"]:
            text = t["text"].replace("|", "\\|")
            lines.append(f"| {t['file']} | {t['line']} | {t['tag']} | {text} |")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Universal Code Metrics Collector")
    parser.add_argument("--path", default=".", help="Project root path")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--exclude", default="",
                        help="Comma-separated directories to exclude (added to defaults)")
    parser.add_argument("--top", type=int, default=10, help="Number of top items to show (default: 10)")
    args = parser.parse_args()

    project_path = Path(args.path).resolve()
    if not project_path.is_dir():
        print(json.dumps({"error": f"Path not found: {project_path}"}), file=sys.stderr)
        sys.exit(1)

    excludes = set(DEFAULT_EXCLUDES)
    if args.exclude:
        excludes.update(s.strip() for s in args.exclude.split(","))

    files = collect_files(project_path, excludes)
    if not files:
        print(json.dumps({"message": "No recognized source files found", "path": str(project_path)}))
        sys.exit(0)

    report = build_report(project_path, files, args.top)

    if args.format == "markdown":
        print(format_markdown(report))
    else:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
