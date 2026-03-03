#!/usr/bin/env python3
"""
DuckDB-backed global memory store for cross-session AI context.

Features:
- Durable memory entries (global/project/session scope)
- Upsert by key for stable facts
- Full-text search via DuckDB FTS extension (BM25 ranking) with ILIKE fallback
- Columnar storage + vectorized execution for fast analytical queries
- Recent entry listing
- JSON or markdown output for agent consumption

Usage examples:
    python global_memory.py init
    python global_memory.py upsert --scope global --namespace conventions --key python-style --title "Python Style" --content "Use type hints..."
    python global_memory.py append --scope project --namespace findings --title "Auth bug" --content "Root cause..."
    python global_memory.py search --query "auth timeout" --limit 5 --format markdown
    python global_memory.py recent --limit 10

Requirements:
    pip install duckdb
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import duckdb
except ImportError:
    print(json.dumps({"status": "error", "message": "duckdb not installed. Run: pip install duckdb"}))
    sys.exit(1)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_db_path() -> Path:
    # Keep memory near the toolkit installation by default.
    # .../v3/tools/global_memory.py -> .../v3/memory/shared/global-memory.duckdb
    return Path(__file__).resolve().parent.parent / "memory" / "shared" / "global-memory.duckdb"


class MemoryStore:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _load_fts(self, conn: duckdb.DuckDBPyConnection) -> bool:
        """Attempt to load DuckDB FTS extension. Install it if not yet present."""
        try:
            conn.execute("LOAD fts")
            return True
        except Exception:
            try:
                conn.execute("INSTALL fts")
                conn.execute("LOAD fts")
                return True
            except Exception:
                return False

    def _rows_to_dicts(
        self, conn: duckdb.DuckDBPyConnection, include_score: bool = False
    ) -> list[dict[str, Any]]:
        cols = [d[0] for d in (conn.description or [])]
        rows = conn.fetchall()
        result = []
        for row in rows:
            d = dict(zip(cols, row))
            tags_json = d.pop("tags_json", "[]")
            d["tags"] = json.loads(tags_json) if tags_json else []
            d["key"] = d.pop("memory_key", None)
            if not include_score:
                d.pop("score", None)
            result.append(d)
        return result

    def _row_to_dict(
        self, conn: duckdb.DuckDBPyConnection, include_score: bool = False
    ) -> dict[str, Any] | None:
        rows = self._rows_to_dicts(conn, include_score)
        return rows[0] if rows else None

    def init(self) -> dict[str, Any]:
        conn = self._connect()
        try:
            # Sequence for auto-incrementing IDs
            conn.execute("CREATE SEQUENCE IF NOT EXISTS memories_id_seq START 1")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id        BIGINT PRIMARY KEY DEFAULT nextval('memories_id_seq'),
                    scope     VARCHAR NOT NULL CHECK (scope IN ('global', 'project', 'session')),
                    namespace VARCHAR NOT NULL,
                    memory_key VARCHAR,
                    title     VARCHAR NOT NULL,
                    content   VARCHAR NOT NULL,
                    tags_json VARCHAR NOT NULL DEFAULT '[]',
                    source    VARCHAR,
                    created_at VARCHAR NOT NULL,
                    updated_at VARCHAR NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_memories_scope_ns ON memories(scope, namespace)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_memories_updated_at ON memories(updated_at)"
            )
            fts_enabled = self._load_fts(conn)
            return {"status": "ok", "db": str(self.db_path), "fts_enabled": fts_enabled}
        finally:
            conn.close()

    def upsert(
        self,
        scope: str,
        namespace: str,
        key: str,
        title: str,
        content: str,
        tags: list[str],
        source: str | None,
    ) -> dict[str, Any]:
        now = utc_now()
        conn = self._connect()
        try:
            conn.execute(
                "SELECT id FROM memories WHERE scope = ? AND namespace = ? AND memory_key = ?",
                [scope, namespace, key],
            )
            existing = conn.fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE memories
                    SET title = ?, content = ?, tags_json = ?, source = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    [title, content, json.dumps(tags), source, now, existing[0]],
                )
            else:
                conn.execute(
                    """
                    INSERT INTO memories
                        (scope, namespace, memory_key, title, content, tags_json, source, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [scope, namespace, key, title, content, json.dumps(tags), source, now, now],
                )
            conn.execute(
                """
                SELECT id, scope, namespace, memory_key, title, content, tags_json, source, created_at, updated_at
                FROM memories
                WHERE scope = ? AND namespace = ? AND memory_key = ?
                """,
                [scope, namespace, key],
            )
            entry = self._row_to_dict(conn)
        finally:
            conn.close()
        return {"status": "ok", "action": "upsert", "entry": entry}

    def append(
        self,
        scope: str,
        namespace: str,
        title: str,
        content: str,
        tags: list[str],
        source: str | None,
    ) -> dict[str, Any]:
        now = utc_now()
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO memories
                    (scope, namespace, memory_key, title, content, tags_json, source, created_at, updated_at)
                VALUES (?, ?, NULL, ?, ?, ?, ?, ?, ?)
                RETURNING id
                """,
                [scope, namespace, title, content, json.dumps(tags), source, now, now],
            )
            row_id = conn.fetchone()[0]
            conn.execute(
                """
                SELECT id, scope, namespace, memory_key, title, content, tags_json, source, created_at, updated_at
                FROM memories
                WHERE id = ?
                """,
                [row_id],
            )
            entry = self._row_to_dict(conn)
        finally:
            conn.close()
        return {"status": "ok", "action": "append", "entry": entry}

    def get_by_key(self, scope: str, namespace: str, key: str) -> dict[str, Any]:
        conn = self._connect()
        try:
            conn.execute(
                """
                SELECT id, scope, namespace, memory_key, title, content, tags_json, source, created_at, updated_at
                FROM memories
                WHERE scope = ? AND namespace = ? AND memory_key = ?
                """,
                [scope, namespace, key],
            )
            entry = self._row_to_dict(conn)
        finally:
            conn.close()
        if not entry:
            return {"status": "not_found", "scope": scope, "namespace": namespace, "key": key}
        return {"status": "ok", "entry": entry}

    def recent(
        self, limit: int, scope: str | None, namespace: str | None
    ) -> dict[str, Any]:
        where: list[str] = []
        params: list[Any] = []
        if scope:
            where.append("scope = ?")
            params.append(scope)
        if namespace:
            where.append("namespace = ?")
            params.append(namespace)
        sql = (
            "SELECT id, scope, namespace, memory_key, title, content, tags_json, source, created_at, updated_at"
            " FROM memories"
        )
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        conn = self._connect()
        try:
            conn.execute(sql, params)
            entries = self._rows_to_dicts(conn)
        finally:
            conn.close()
        return {"status": "ok", "count": len(entries), "entries": entries}

    def search(
        self,
        query: str,
        limit: int,
        scope: str | None,
        namespace: str | None,
    ) -> dict[str, Any]:
        conn = self._connect()
        try:
            fts_ok = self._load_fts(conn)

            if fts_ok:
                # Rebuild FTS index so newly inserted rows are visible.
                # Fast for typical AI memory sizes (<10k rows).
                try:
                    conn.execute(
                        """
                        PRAGMA create_fts_index(
                            'memories', 'id', 'title', 'content',
                            stemmer='english', stopwords='english', overwrite=1
                        )
                        """
                    )
                except Exception:
                    fts_ok = False

            if fts_ok:
                extra_where: list[str] = []
                params: list[Any] = [query]
                if scope:
                    extra_where.append("scope = ?")
                    params.append(scope)
                if namespace:
                    extra_where.append("namespace = ?")
                    params.append(namespace)
                extra_clause = ("AND " + " AND ".join(extra_where)) if extra_where else ""
                params.append(limit)
                sql = f"""
                    WITH scored AS (
                        SELECT id, scope, namespace, memory_key, title, content,
                               tags_json, source, created_at, updated_at,
                               fts_main_memories.match_bm25(id, ?) AS score
                        FROM memories
                    )
                    SELECT * FROM scored
                    WHERE score IS NOT NULL {extra_clause}
                    ORDER BY score DESC
                    LIMIT ?
                """
                conn.execute(sql, params)
                entries = self._rows_to_dicts(conn, include_score=True)
                mode = "fts_bm25"
            else:
                # Vectorized ILIKE fallback — faster than SQLite LIKE
                like = f"%{query}%"
                ilike_where: list[str] = ["(title ILIKE ? OR content ILIKE ?)"]
                ilike_params: list[Any] = [like, like]
                if scope:
                    ilike_where.append("scope = ?")
                    ilike_params.append(scope)
                if namespace:
                    ilike_where.append("namespace = ?")
                    ilike_params.append(namespace)
                ilike_params.append(limit)
                sql = (
                    "SELECT id, scope, namespace, memory_key, title, content,"
                    " tags_json, source, created_at, updated_at, 0.0 AS score"
                    " FROM memories"
                    f" WHERE {' AND '.join(ilike_where)}"
                    " ORDER BY updated_at DESC LIMIT ?"
                )
                conn.execute(sql, ilike_params)
                entries = self._rows_to_dicts(conn, include_score=True)
                mode = "ilike"
        finally:
            conn.close()

        return {
            "status": "ok",
            "query": query,
            "mode": mode,
            "count": len(entries),
            "entries": entries,
        }


def split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


def format_markdown(data: dict[str, Any]) -> str:
    status = data.get("status", "unknown")
    lines = ["# Global Memory Output", f"**Status**: {status}", ""]

    if "query" in data:
        lines.append(f"**Query**: {data['query']}")
        lines.append(f"**Search Mode**: {data.get('mode', 'unknown')}")
        lines.append("")

    entry = data.get("entry")
    if entry:
        lines.append("## Entry")
        lines.append(f"- **ID**: {entry['id']}")
        lines.append(f"- **Scope**: {entry['scope']}")
        lines.append(f"- **Namespace**: {entry['namespace']}")
        lines.append(f"- **Key**: {entry.get('key') or '(none)'}")
        lines.append(f"- **Title**: {entry['title']}")
        lines.append(f"- **Tags**: {', '.join(entry.get('tags', [])) or '(none)'}")
        lines.append(f"- **Source**: {entry.get('source') or '(none)'}")
        lines.append("- **Content**:")
        lines.append(f"  {entry['content']}")
        return "\n".join(lines)

    entries = data.get("entries", [])
    if entries:
        lines.append(f"## Entries ({len(entries)})")
        lines.append("| ID | Scope | Namespace | Key | Title | Updated |")
        lines.append("|----|-------|-----------|-----|-------|---------|")
        for e in entries:
            title = e["title"].replace("|", "\\|")
            lines.append(
                f"| {e['id']} | {e['scope']} | {e['namespace']} | {e.get('key') or ''} | {title} | {e['updated_at']} |"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="DuckDB-backed global memory for AI context")
    parser.add_argument(
        "--db",
        default=str(default_db_path()),
        help="Path to DuckDB database file (default: v3/memory/shared/global-memory.duckdb)",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="json")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="Initialize database schema")

    upsert_p = sub.add_parser("upsert", help="Upsert memory by (scope, namespace, key)")
    upsert_p.add_argument("--scope", choices=["global", "project", "session"], default="global")
    upsert_p.add_argument("--namespace", default="general")
    upsert_p.add_argument("--key", required=True)
    upsert_p.add_argument("--title", required=True)
    upsert_p.add_argument("--content", required=True)
    upsert_p.add_argument("--tags", default="")
    upsert_p.add_argument("--source", default=None)

    append_p = sub.add_parser("append", help="Append an immutable memory entry")
    append_p.add_argument("--scope", choices=["global", "project", "session"], default="session")
    append_p.add_argument("--namespace", default="events")
    append_p.add_argument("--title", required=True)
    append_p.add_argument("--content", required=True)
    append_p.add_argument("--tags", default="")
    append_p.add_argument("--source", default=None)

    get_p = sub.add_parser("get", help="Fetch one memory by key")
    get_p.add_argument("--scope", choices=["global", "project", "session"], default="global")
    get_p.add_argument("--namespace", default="general")
    get_p.add_argument("--key", required=True)

    search_p = sub.add_parser("search", help="Full-text search memory (BM25 or ILIKE fallback)")
    search_p.add_argument("--query", required=True)
    search_p.add_argument("--limit", type=int, default=10)
    search_p.add_argument("--scope", choices=["global", "project", "session"], default=None)
    search_p.add_argument("--namespace", default=None)

    recent_p = sub.add_parser("recent", help="List recent memory entries")
    recent_p.add_argument("--limit", type=int, default=10)
    recent_p.add_argument("--scope", choices=["global", "project", "session"], default=None)
    recent_p.add_argument("--namespace", default=None)

    args = parser.parse_args()
    store = MemoryStore(Path(args.db).resolve())

    if args.command == "init":
        result = store.init()
    else:
        # Ensure schema exists for all operations.
        store.init()

        if args.command == "upsert":
            result = store.upsert(
                scope=args.scope,
                namespace=args.namespace,
                key=args.key,
                title=args.title,
                content=args.content,
                tags=split_tags(args.tags),
                source=args.source,
            )
        elif args.command == "append":
            result = store.append(
                scope=args.scope,
                namespace=args.namespace,
                title=args.title,
                content=args.content,
                tags=split_tags(args.tags),
                source=args.source,
            )
        elif args.command == "get":
            result = store.get_by_key(args.scope, args.namespace, args.key)
        elif args.command == "search":
            result = store.search(args.query, args.limit, args.scope, args.namespace)
        elif args.command == "recent":
            result = store.recent(args.limit, args.scope, args.namespace)
        else:
            result = {"status": "error", "message": f"Unsupported command: {args.command}"}

    if args.format == "markdown":
        print(format_markdown(result))
    else:
        print(json.dumps(result, indent=2))

    return 0 if result.get("status") != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
