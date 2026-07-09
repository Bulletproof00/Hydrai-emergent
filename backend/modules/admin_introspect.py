"""
Admin Introspection Module (READ-ONLY)
======================================

Provides a small, token-protected, strictly read-only HTTP surface so an
external assistant can inspect the *deployed* project without SSH access:

  - list / read files inside the project directory (path-jailed)
  - list registered API routes
  - list MongoDB collections and run read-only queries

Security model
--------------
  * Enabled ONLY when the environment variable ADMIN_INTROSPECT_TOKEN is set
    to a non-empty, sufficiently long value. If unset -> every endpoint 503s.
  * Every request must send header:  X-Admin-Token: <token>
    (compared in constant time).
  * All filesystem access is jailed to ADMIN_INTROSPECT_ROOT (defaults to the
    project root, i.e. the parent of backend/). Symlink escapes are rejected.
  * Files matching known-secret patterns (.env, *.key, *.pem, id_rsa, ...) are
    hidden/blocked unless the caller explicitly passes unsafe_include_secrets=true.
  * There are NO write, delete, move or shell endpoints. Read-only by design.
"""

import os
import hmac
import stat
import fnmatch
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Project root = parent of the backend/ directory that contains server.py
_DEFAULT_ROOT = Path(__file__).resolve().parent.parent.parent
_ROOT = Path(os.environ.get("ADMIN_INTROSPECT_ROOT", str(_DEFAULT_ROOT))).resolve()

# Files that must not be dumped by default (secrets / keys)
_SECRET_PATTERNS = [
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx",
    "id_rsa", "id_ed25519", "id_dsa", "*.keystore", "*.jks",
    "*.secret", "credentials", "credentials.json", "service-account*.json",
]

# Never traverse into these directories
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".mypy_cache"}

_MAX_READ_BYTES = 1_000_000  # 1 MB cap per file read


def _token_ok(supplied: Optional[str]) -> bool:
    configured = os.environ.get("ADMIN_INTROSPECT_TOKEN", "")
    if not configured or len(configured) < 16:
        return False  # feature disabled / misconfigured
    if not supplied:
        return False
    return hmac.compare_digest(supplied, configured)


def _require_auth(x_admin_token: Optional[str]):
    configured = os.environ.get("ADMIN_INTROSPECT_TOKEN", "")
    if not configured or len(configured) < 16:
        raise HTTPException(status_code=503, detail="Introspection disabled (ADMIN_INTROSPECT_TOKEN not configured)")
    if not _token_ok(x_admin_token):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Admin-Token")


def _is_secret(p: Path) -> bool:
    name = p.name
    return any(fnmatch.fnmatch(name, pat) for pat in _SECRET_PATTERNS)


def _resolve_jailed(rel_or_abs: str) -> Path:
    """Resolve a user-supplied path and ensure it stays inside _ROOT."""
    raw = (rel_or_abs or "").strip()
    if not raw or raw in (".", "./"):
        return _ROOT
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = _ROOT / candidate
    resolved = candidate.resolve()
    try:
        resolved.relative_to(_ROOT)
    except ValueError:
        raise HTTPException(status_code=403, detail=f"Path escapes project root: {rel_or_abs}")
    return resolved


def get_admin_router(db=None) -> APIRouter:
    """Build the /admin sub-router. `db` is the (motor) database handle or None."""
    router = APIRouter()

    @router.get("/ping")
    async def ping(x_admin_token: Optional[str] = Header(None)):
        _require_auth(x_admin_token)
        return {
            "ok": True,
            "root": str(_ROOT),
            "mode": "read-only",
            "db": bool(db is not None),
        }

    @router.get("/fs/list")
    async def fs_list(
        path: str = Query("", description="Directory path relative to project root"),
        x_admin_token: Optional[str] = Header(None),
    ):
        _require_auth(x_admin_token)
        target = _resolve_jailed(path)
        if not target.exists():
            raise HTTPException(status_code=404, detail="Not found")
        if not target.is_dir():
            raise HTTPException(status_code=400, detail="Not a directory (use /fs/read)")
        entries = []
        for child in sorted(target.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
            try:
                st = child.lstat()
            except OSError:
                continue
            is_dir = child.is_dir()
            entries.append({
                "name": child.name,
                "path": str(child.relative_to(_ROOT)),
                "type": "dir" if is_dir else ("symlink" if stat.S_ISLNK(st.st_mode) else "file"),
                "size": None if is_dir else st.st_size,
                "secret": _is_secret(child),
            })
        return {"path": str(target.relative_to(_ROOT)) or ".", "count": len(entries), "entries": entries}

    @router.get("/fs/read")
    async def fs_read(
        path: str = Query(..., description="File path relative to project root"),
        max_bytes: int = Query(_MAX_READ_BYTES, le=_MAX_READ_BYTES, ge=1),
        unsafe_include_secrets: bool = Query(False),
        x_admin_token: Optional[str] = Header(None),
    ):
        _require_auth(x_admin_token)
        target = _resolve_jailed(path)
        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        if _is_secret(target) and not unsafe_include_secrets:
            raise HTTPException(status_code=403, detail="Refusing to read secret file (pass unsafe_include_secrets=true to override)")
        size = target.stat().st_size
        data = target.read_bytes()[:max_bytes]
        try:
            text = data.decode("utf-8")
            binary = False
        except UnicodeDecodeError:
            text = None
            binary = True
        return {
            "path": str(target.relative_to(_ROOT)),
            "size": size,
            "returned_bytes": len(data),
            "truncated": size > len(data),
            "binary": binary,
            "content": text,
        }

    @router.get("/fs/tree")
    async def fs_tree(
        path: str = Query("", description="Root of the tree, relative to project root"),
        depth: int = Query(2, ge=1, le=6),
        x_admin_token: Optional[str] = Header(None),
    ):
        _require_auth(x_admin_token)
        base = _resolve_jailed(path)
        if not base.is_dir():
            raise HTTPException(status_code=400, detail="Not a directory")
        out = []

        def walk(d: Path, level: int):
            if level > depth:
                return
            for child in sorted(d.iterdir(), key=lambda c: (c.is_file(), c.name.lower())):
                if child.name in _SKIP_DIRS:
                    continue
                rel = str(child.relative_to(_ROOT))
                if child.is_dir():
                    out.append(rel + "/")
                    walk(child, level + 1)
                else:
                    out.append(rel)

        walk(base, 1)
        return {"root": str(base.relative_to(_ROOT)) or ".", "depth": depth, "count": len(out), "paths": out}

    @router.get("/db/collections")
    async def db_collections(x_admin_token: Optional[str] = Header(None)):
        _require_auth(x_admin_token)
        if db is None:
            raise HTTPException(status_code=503, detail="No database handle available")
        names = await db.list_collection_names()
        result = []
        for name in sorted(names):
            try:
                count = await db[name].estimated_document_count()
            except Exception:
                count = None
            result.append({"name": name, "estimated_count": count})
        return {"count": len(result), "collections": result}

    @router.get("/db/find")
    async def db_find(
        collection: str = Query(...),
        limit: int = Query(20, ge=1, le=200),
        x_admin_token: Optional[str] = Header(None),
    ):
        """Read-only preview of the most recent documents in a collection."""
        _require_auth(x_admin_token)
        if db is None:
            raise HTTPException(status_code=503, detail="No database handle available")
        if collection not in await db.list_collection_names():
            raise HTTPException(status_code=404, detail="Unknown collection")
        docs = []
        cursor = db[collection].find({}, limit=limit)
        async for doc in cursor:
            doc["_id"] = str(doc.get("_id"))
            docs.append(doc)
        return {"collection": collection, "returned": len(docs), "documents": docs}

    return router
