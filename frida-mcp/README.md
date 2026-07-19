# Frida MCP Server

Expose Frida's dynamic-instrumentation capabilities to AI agents over the
[Model Context Protocol](https://modelcontextprotocol.io). Any MCP client —
Claude Code, Claude Desktop, Cursor, or your own agent — can then enumerate
devices and processes, attach to or spawn a target, inject JavaScript, and read
back whatever those scripts emit.

This is a thin, self-contained layer on top of the `frida` Python bindings, so it
works against every target Frida supports: local Linux/macOS/Windows processes,
USB-attached Android/iOS devices, and remote `frida-server` instances.

## Why MCP

MCP is the de-facto standard for connecting agents to external tools. By wrapping
Frida as an MCP server, an agent can drive a full reverse-engineering / mobile
security loop in natural language — *"list the apps on the USB device, spawn the
banking app, hook its SSL pinning check, and show me what it logs"* — without any
bespoke integration.

## Install

```sh
pip install -r requirements.txt   # frida + mcp
```

For instrumenting a real Android/iOS device you also need `frida-server` running
on the device (or the Gadget embedded in the app) — see the
[Frida docs](https://frida.re/docs/android/).

## Run

```sh
python3 server.py                 # speaks MCP over stdio
```

You normally don't launch it by hand; the MCP client spawns it. Register it:

### Claude Code

```sh
claude mcp add frida -- python3 /absolute/path/to/frida-mcp/server.py
```

### Claude Desktop / generic MCP client

Add to the client's MCP config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "frida": {
      "command": "python3",
      "args": ["/absolute/path/to/frida-mcp/server.py"]
    }
  }
}
```

## Tools

**Discovery**

| Tool | Purpose |
| --- | --- |
| `get_frida_version` | Version of the bundled Frida bindings. |
| `list_devices` | All Frida devices (local, USB, remote, …). |
| `list_processes(device)` | Running processes on a device. |
| `list_applications(device)` | Installed apps (mobile). |

**One-shot**

| Tool | Purpose |
| --- | --- |
| `run_script(target, source, device, spawn, runtime_seconds)` | Attach or spawn, inject a script, collect its `send()` messages for a few seconds, then detach. The fast path for recon. |

**Stateful (long-lived hooks the agent polls)**

| Tool | Purpose |
| --- | --- |
| `attach(target, device)` → `session_id` | Attach and keep the session open. |
| `spawn(program, device, resume)` → `session_id, pid` | Launch suspended and attach (load scripts before `resume` to catch startup). |
| `resume(session_id)` | Resume a spawned process. |
| `create_script(session_id, source)` → `script_id` | Load an agent; its messages start buffering. |
| `read_messages(script_id, max_messages, timeout_seconds)` | Drain buffered messages since the last read. |
| `call_rpc_export(script_id, name, args)` | Invoke an `rpc.exports` function in a loaded script. |
| `list_sessions()` | Sessions and scripts currently held. |
| `unload_script(script_id)` / `detach(session_id)` | Tear down. |

`device` accepts `local` (default), `usb`, `remote`, or an explicit id from
`list_devices` (e.g. `192.168.1.90:5555`). `target` is a PID or a process name;
for `spawn` it's a program path or application identifier. Binary payloads sent
with `send(msg, data)` are returned base64-encoded under `data_base64`.

## Example agent flow

```
list_devices()                          # find the USB Android device
list_applications(device="usb")         # locate the target app identifier
spawn("com.example.app", device="usb")  # -> session_id, pid (suspended)
create_script(session_id, "<hooks>")    # install SSL-pinning bypass etc.
resume(session_id)                       # let the app start
read_messages(script_id)                # watch what the hooks report
```

## Security note

This server grants its client the **full power of Frida**: attaching to and
injecting arbitrary code into any process the host can reach. That is intended —
it is a tool for authorized security testing, reverse engineering, and research —
but it means you should only connect trusted agents, and only run it in an
environment where that level of access is appropriate. There is no sandbox here
beyond the OS permissions of the account running `server.py`.
