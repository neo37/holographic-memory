"""Minimal MCP server over stdio (newline-delimited JSON-RPC 2.0).

Implemented on the standard library only so the server runs with zero install
beyond numpy. Logs go to stderr; the protocol channel is stdout.
"""
from __future__ import annotations

import json
import os
import sys

from . import __version__
from .license import ensure_licensed
from .memory import HolographicMemory

PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "store_holographic_snapshot",
        "description": "Store a structured memory (fact + context + emotional valence + importance + tags) as a superposed hypervector.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "fact": {"type": "string", "description": "The fact to remember"},
                "context": {"type": "string", "description": "Where/why this came up"},
                "importance": {"type": "number", "description": "0.0–1.0", "default": 0.5},
                "valence": {"type": "string", "description": "positive | neutral | negative", "default": "neutral"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["fact"],
        },
    },
    {
        "name": "recall_by_association",
        "description": "Retrieve a de-noised meaning cloud from a vague or emotional cue. Use when the user refers to the past indirectly.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Vague description or context"},
                "top_k": {"type": "integer", "default": 5},
                "association_depth": {"type": "integer", "default": 2},
            },
            "required": ["query"],
        },
    },
    {
        "name": "interference_analysis",
        "description": "Check whether a new fact collides with an existing belief; returns the conflict and confidence.",
        "inputSchema": {
            "type": "object",
            "properties": {"new_fact": {"type": "string"}},
            "required": ["new_fact"],
        },
    },
    {
        "name": "consolidate_and_prune",
        "description": "Sleep: drop weak/unused associations, keep the store fast.",
        "inputSchema": {
            "type": "object",
            "properties": {"max_loss_tolerance": {"type": "number", "default": 0.1}},
        },
    },
]


def _dispatch_tool(mem: HolographicMemory, name: str, args: dict) -> dict:
    if name == "store_holographic_snapshot":
        return mem.store_snapshot(
            fact=args["fact"],
            context=args.get("context", ""),
            importance=args.get("importance", 0.5),
            valence=args.get("valence", "neutral"),
            tags=args.get("tags", []),
        )
    if name == "recall_by_association":
        return mem.recall(args["query"], int(args.get("top_k", 5)), int(args.get("association_depth", 2)))
    if name == "interference_analysis":
        return mem.interference(args["new_fact"])
    if name == "consolidate_and_prune":
        return mem.consolidate(float(args.get("max_loss_tolerance", 0.1)))
    raise ValueError(f"unknown tool: {name}")


def _handle(mem: HolographicMemory, msg: dict):
    method = msg.get("method")
    mid = msg.get("id")

    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "holographic-memory", "version": __version__},
        }
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        params = msg.get("params", {})
        result = _dispatch_tool(mem, params["name"], params.get("arguments", {}))
        return {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}
    if method == "ping":
        return {}
    if method and method.startswith("notifications/"):
        return None  # notifications get no response
    raise LookupError(f"method not found: {method}")


def main() -> None:
    ensure_licensed()
    store_path = os.getenv("MEMORY_STORE_PATH", "~/.holographic-memory")
    dim = int(os.getenv("MEMORY_DIM", "10000"))
    mem = HolographicMemory(store_path, dim=dim)
    print(f"holographic-memory {__version__} ready (dim={dim}, store={store_path})", file=sys.stderr)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        is_notification = "id" not in msg
        try:
            result = _handle(mem, msg)
        except Exception as exc:  # surface as a JSON-RPC error
            if not is_notification:
                _send({"jsonrpc": "2.0", "id": msg.get("id"), "error": {"code": -32603, "message": str(exc)}})
            continue
        if is_notification or result is None:
            continue
        _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": result})


def _send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
