---
name: python-binding
description: Drive Frida from Python — get a device, spawn or attach, create and load a script, handle messages, and call the agent via script.exports_sync RPC.
---

# The `frida` Python binding

**When:** you want a repeatable, scriptable host — batch runs, test harnesses, data
collection — instead of the interactive REPL. Python is the most common host
binding; `pip install frida` gives you the `frida` module.

## End-to-end: attach, hook, collect

```python
import frida, sys

AGENT = """
const openPtr = Module.getGlobalExportByName('open');
Interceptor.attach(openPtr, {
  onEnter(args) { send({ path: args[0].readUtf8String() }); }
});
"""

def on_message(message, data):
    if message['type'] == 'send':
        print('open:', message['payload']['path'])
    elif message['type'] == 'error':
        print('agent error:', message['description'], file=sys.stderr)

device = frida.get_usb_device()          # or frida.get_local_device()
session = device.attach('com.example.app')
script = session.create_script(AGENT)
script.on('message', on_message)         # register BEFORE load()
script.load()
sys.stdin.read()                         # keep the process alive to receive events
```

## Getting a device

```python
frida.get_local_device()                 # this machine
frida.get_usb_device()                   # first USB device (Android/iOS)
frida.get_device_manager().enumerate_devices()
frida.get_device('serial-or-id')         # explicit id
frida.get_remote_device('192.168.1.5:27042')   # frida-server over TCP
```

## Spawn vs attach

Attach hooks a running process; spawn starts it **paused** so you catch startup
code (pinning setup, anti-debug). See [../cli/spawn-vs-attach.md](../cli/spawn-vs-attach.md).

```python
pid = device.spawn(['com.example.app'])   # or a full path on desktop
session = device.attach(pid)
script = session.create_script(AGENT)
script.on('message', on_message)
script.load()
device.resume(pid)                        # let the app run AFTER hooks are installed
sys.stdin.read()
```

## Calling the agent (RPC)

Expose `rpc.exports` in the agent, then call on `script.exports_sync` with
**snake_case** names (JS `listModules` → `list_modules`). Full mapping in
[../core-api/rpc-exports.md](../core-api/rpc-exports.md).

```python
# agent has: rpc.exports = { listModules() { ... } };
mods = script.exports_sync.list_modules()
print(len(mods))
```

## Lifecycle & cleanup

```python
session.on('detached', lambda reason, *a: print('detached:', reason))
script.unload()          # remove the agent
session.detach()         # drop the session
device.kill(pid)         # optional: kill a spawned target
```

## Pitfalls

- **Register `script.on('message', ...)` before `script.load()`** or you miss early
  `send()`s.
- The script only runs while your Python process lives — without `sys.stdin.read()`
  or an event loop the program exits and the agent dies immediately.
- **Version skew** between the host `frida` package and device `frida-server` is the
  top failure; match them (`pip install frida==<server-version>`).
- `.exports_sync` blocks the calling thread; messages arrive on Frida's own reactor
  thread, so keep `on_message` fast and thread-safe.
- `create_script` takes the **source string**, not a path — read the file yourself:
  `session.create_script(open('agent.js').read())`.
- For binary payloads the second callback arg `data` is Python `bytes`; see
  [message-handling.md](message-handling.md).
