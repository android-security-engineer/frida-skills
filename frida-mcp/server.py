#!/usr/bin/env python3
"""Frida MCP server.

Exposes Frida's dynamic-instrumentation capabilities as Model Context Protocol
tools so that AI agents (Claude Code, Claude Desktop, or any MCP client) can
enumerate devices/processes, attach to or spawn targets, inject JavaScript, and
collect the messages those scripts emit.

Two usage styles are provided:

  * One-shot: ``run_script`` attaches (or spawns), loads a script, collects
    everything it sends for a few seconds, then tears everything down. Ideal for
    quick recon where the agent just wants an answer.

  * Stateful: ``attach``/``spawn`` return a session id; ``create_script`` returns
    a script id whose messages accumulate in a buffer that ``read_messages``
    drains on demand. This supports long-lived hooks that the agent polls over
    several tool calls.

Transport is stdio, the default for local MCP servers.
"""

import base64
import queue
import threading
import time
from typing import Any, Optional

import frida
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("frida")

# ---------------------------------------------------------------------------
# Registries for the stateful API. Frida delivers script messages on its own
# reactor thread, so every shared structure is guarded by a lock and messages
# are handed off through a thread-safe queue.
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_sessions: dict[str, dict[str, Any]] = {}
_scripts: dict[str, dict[str, Any]] = {}
_counter = 0


def _next_id(prefix: str) -> str:
    global _counter
    with _lock:
        _counter += 1
        return f"{prefix}-{_counter}"


def resolve_device(spec: Optional[str]) -> frida.core.Device:
    """Turn a device spec into a Frida device.

    Accepts ``local`` (default), ``usb``, ``remote``, or an explicit device id
    such as ``192.168.1.90:5555`` from ``list_devices``.
    """
    if spec in (None, "", "local"):
        return frida.get_local_device()
    if spec == "usb":
        return frida.get_usb_device(timeout=5)
    if spec == "remote":
        return frida.get_remote_device()
    return frida.get_device(spec, timeout=5)


def _coerce_target(target: str) -> Any:
    """A numeric target is a PID; anything else is a process name."""
    return int(target) if target.isdigit() else target


def _serialize_message(message: dict, data: Optional[bytes]) -> dict:
    out = dict(message)
    if data is not None:
        out["data_base64"] = base64.b64encode(data).decode("ascii")
    return out


# ---------------------------------------------------------------------------
# Discovery tools
# ---------------------------------------------------------------------------


@mcp.tool(structured_output=False)
def get_frida_version() -> str:
    """Return the version of the Frida bindings backing this server."""
    return frida.__version__


@mcp.tool(structured_output=False)
def list_devices() -> list[dict]:
    """List all Frida devices (local, USB, remote/network, etc.)."""
    devices = []
    for d in frida.enumerate_devices():
        devices.append({"id": d.id, "name": d.name, "type": d.type})
    return devices


@mcp.tool(structured_output=False)
def list_processes(device: str = "local") -> list[dict]:
    """List running processes on a device.

    Args:
        device: Device spec — ``local`` (default), ``usb``, ``remote``, or an id.
    """
    dev = resolve_device(device)
    return [{"pid": p.pid, "name": p.name} for p in dev.enumerate_processes()]


@mcp.tool(structured_output=False)
def list_applications(device: str = "usb") -> list[dict]:
    """List installed applications on a device (mobile devices).

    Args:
        device: Device spec — defaults to ``usb`` since this is a mobile concept.
    """
    dev = resolve_device(device)
    apps = []
    for a in dev.enumerate_applications():
        apps.append(
            {
                "identifier": a.identifier,
                "name": a.name,
                "pid": a.pid,  # 0 when not running
            }
        )
    return apps


# ---------------------------------------------------------------------------
# One-shot execution
# ---------------------------------------------------------------------------


@mcp.tool(structured_output=False)
def run_script(
    target: str,
    source: str,
    device: str = "local",
    spawn: bool = False,
    runtime_seconds: float = 2.0,
) -> dict:
    """Attach (or spawn), inject a JavaScript script, collect its messages, and detach.

    This is the fast path for one-off instrumentation: whatever the script emits
    via ``send(...)`` (and any errors) within ``runtime_seconds`` is returned.

    Args:
        target: PID or process name to attach to; when ``spawn`` is true, the
            program path / application identifier to launch instead.
        source: The Frida JavaScript agent source to inject.
        device: Device spec (``local`` by default).
        spawn: Launch ``target`` suspended and resume after the script loads,
            so early startup can be instrumented.
        runtime_seconds: How long to collect messages before tearing down.

    Returns:
        A dict with the resolved ``pid`` and the list of collected ``messages``.
    """
    dev = resolve_device(device)
    q: "queue.Queue[tuple[dict, Optional[bytes]]]" = queue.Queue()

    if spawn:
        pid = dev.spawn(target)
        session = dev.attach(pid)
    else:
        session = dev.attach(_coerce_target(target))
        pid = session._impl.pid if hasattr(session, "_impl") else None

    script = session.create_script(source)
    script.on("message", lambda message, data: q.put((message, data)))
    script.load()
    if spawn:
        dev.resume(pid)

    deadline = time.monotonic() + max(0.0, runtime_seconds)
    messages: list[dict] = []
    while time.monotonic() < deadline:
        try:
            message, data = q.get(timeout=deadline - time.monotonic())
            messages.append(_serialize_message(message, data))
        except queue.Empty:
            break

    try:
        script.unload()
    except frida.InvalidOperationError:
        pass
    try:
        session.detach()
    except frida.InvalidOperationError:
        pass

    return {"pid": pid, "messages": messages}


# ---------------------------------------------------------------------------
# Stateful session/script API
# ---------------------------------------------------------------------------


@mcp.tool(structured_output=False)
def attach(target: str, device: str = "local") -> dict:
    """Attach to a process and keep the session open.

    Args:
        target: PID or process name.
        device: Device spec (``local`` by default).

    Returns:
        ``{"session_id", "pid"}``. Use the session id with ``create_script`` etc.
    """
    dev = resolve_device(device)
    session = dev.attach(_coerce_target(target))
    sid = _next_id("session")
    with _lock:
        _sessions[sid] = {"session": session, "device": dev, "pid": None}
    return {"session_id": sid}


@mcp.tool(structured_output=False)
def spawn(program: str, device: str = "local", resume: bool = False) -> dict:
    """Spawn a program suspended and attach to it.

    Args:
        program: Program path or application identifier to launch.
        device: Device spec.
        resume: Resume immediately after attaching (skip suspended state).

    Returns:
        ``{"session_id", "pid"}``. The process stays suspended unless ``resume``
        is set or you later call ``resume``; load scripts first to catch startup.
    """
    dev = resolve_device(device)
    pid = dev.spawn(program)
    session = dev.attach(pid)
    sid = _next_id("session")
    with _lock:
        _sessions[sid] = {"session": session, "device": dev, "pid": pid}
    if resume:
        dev.resume(pid)
    return {"session_id": sid, "pid": pid}


@mcp.tool(structured_output=False)
def resume(session_id: str) -> str:
    """Resume the spawned process associated with a session."""
    with _lock:
        entry = _sessions.get(session_id)
    if entry is None:
        raise ValueError(f"unknown session_id: {session_id}")
    if entry["pid"] is None:
        raise ValueError("session was not created via spawn; nothing to resume")
    entry["device"].resume(entry["pid"])
    return "resumed"


@mcp.tool(structured_output=False)
def create_script(session_id: str, source: str) -> dict:
    """Load a JavaScript agent into a session and start buffering its messages.

    Args:
        session_id: Id returned by ``attach`` or ``spawn``.
        source: The Frida JavaScript agent source.

    Returns:
        ``{"script_id"}``. Poll it with ``read_messages``; drop it with
        ``unload_script``.
    """
    with _lock:
        entry = _sessions.get(session_id)
    if entry is None:
        raise ValueError(f"unknown session_id: {session_id}")

    q: "queue.Queue[tuple[dict, Optional[bytes]]]" = queue.Queue()
    script = entry["session"].create_script(source)
    script.on("message", lambda message, data: q.put((message, data)))
    script.load()

    scrid = _next_id("script")
    with _lock:
        _scripts[scrid] = {"script": script, "queue": q, "session_id": session_id}
    return {"script_id": scrid}


@mcp.tool(structured_output=False)
def read_messages(script_id: str, max_messages: int = 100, timeout_seconds: float = 1.0) -> list[dict]:
    """Drain buffered messages emitted by a script since the last read.

    Args:
        script_id: Id returned by ``create_script``.
        max_messages: Cap on how many messages to return this call.
        timeout_seconds: How long to wait for the first message if the buffer is
            currently empty (subsequent messages are drained without waiting).
    """
    with _lock:
        entry = _scripts.get(script_id)
    if entry is None:
        raise ValueError(f"unknown script_id: {script_id}")
    q: "queue.Queue[tuple[dict, Optional[bytes]]]" = entry["queue"]

    messages: list[dict] = []
    try:
        message, data = q.get(timeout=max(0.0, timeout_seconds))
        messages.append(_serialize_message(message, data))
    except queue.Empty:
        return messages

    while len(messages) < max_messages:
        try:
            message, data = q.get_nowait()
            messages.append(_serialize_message(message, data))
        except queue.Empty:
            break
    return messages


@mcp.tool(structured_output=False)
def call_rpc_export(script_id: str, name: str, args: Optional[list] = None) -> Any:
    """Call an ``rpc.exports`` function defined by a loaded script.

    Args:
        script_id: Id returned by ``create_script``.
        name: The export name (as declared in ``rpc.exports = { ... }``).
        args: Positional arguments to pass.
    """
    with _lock:
        entry = _scripts.get(script_id)
    if entry is None:
        raise ValueError(f"unknown script_id: {script_id}")
    exports = entry["script"].exports_sync
    fn = getattr(exports, name, None)
    if fn is None:
        raise ValueError(f"script has no rpc export named {name!r}")
    return fn(*(args or []))


@mcp.tool(structured_output=False)
def list_sessions() -> dict:
    """List currently open sessions and scripts held by this server."""
    with _lock:
        sessions = [
            {"session_id": sid, "pid": e["pid"]} for sid, e in _sessions.items()
        ]
        scripts = [
            {"script_id": scrid, "session_id": e["session_id"]}
            for scrid, e in _scripts.items()
        ]
    return {"sessions": sessions, "scripts": scripts}


@mcp.tool(structured_output=False)
def unload_script(script_id: str) -> str:
    """Unload a script and forget its buffer."""
    with _lock:
        entry = _scripts.pop(script_id, None)
    if entry is None:
        raise ValueError(f"unknown script_id: {script_id}")
    try:
        entry["script"].unload()
    except frida.InvalidOperationError:
        pass
    return "unloaded"


@mcp.tool(structured_output=False)
def detach(session_id: str) -> str:
    """Detach a session and drop any scripts still attached to it."""
    with _lock:
        entry = _sessions.pop(session_id, None)
        orphaned = [sid for sid, e in _scripts.items() if e["session_id"] == session_id]
        for sid in orphaned:
            _scripts.pop(sid, None)
    if entry is None:
        raise ValueError(f"unknown session_id: {session_id}")
    try:
        entry["session"].detach()
    except frida.InvalidOperationError:
        pass
    return "detached"


if __name__ == "__main__":
    mcp.run()
