---
name: message-handling
description: Build a robust host message loop for Frida — dispatch send vs error messages, receive binary payloads, implement a send/recv handshake, and avoid dropping early events.
---

# Host message handling

**When:** your agent streams events with `send()` and the host must consume them
reliably — routing by type, handling binary blobs, and coordinating with `recv()`.
The agent-side channel is documented in [../core-api/send-recv.md](../core-api/send-recv.md).

## The message shape

Every host callback receives `(message, data)`:

- `message['type'] == 'send'` → `message['payload']` is your JSON object; `data` is
  the optional `ArrayBuffer` (Python `bytes`, or `Buffer` in Node) or `None`.
- `message['type'] == 'error'` → an **uncaught agent exception**, with
  `description`, `stack`, `fileName`, `lineNumber`.

## End-to-end: routed loop with binary

```python
import frida, sys

AGENT = """
const p = Module.getGlobalExportByName('open');
Interceptor.attach(p, {
  onEnter(args) {
    const path = args[0].readUtf8String();
    send({ kind: 'open', path });
    send({ kind: 'dump' }, args[0].readByteArray(16));   // binary second arg
  }
});
"""

def on_message(message, data):
    if message['type'] == 'error':
        print('AGENT ERROR:', message['description'], file=sys.stderr)
        print(message.get('stack', ''), file=sys.stderr)
        return
    payload = message['payload']
    if payload['kind'] == 'open':
        print('open', payload['path'])
    elif payload['kind'] == 'dump':
        print('bytes:', data.hex())         # data is Python `bytes`

session = frida.get_usb_device().attach('com.example.app')
script = session.create_script(AGENT)
script.on('message', on_message)            # BEFORE load(): don't drop early events
script.load()
sys.stdin.read()
```

## send/recv handshake (host pushes config to the agent)

```python
script.post({ 'type': 'config', 'sample_rate': 10 })
```

```js
// agent.js — block this flow until config arrives
recv('config', function (msg) {
  globalThis.sampleRate = msg.sample_rate;
}).wait();
```

`recv(type, cb)` returns a `RecvOperation`; `.wait()` blocks only that agent flow
until a matching message is posted.

## Pitfalls

- **Handle `type == 'error'` explicitly.** Agent exceptions arrive as messages, not
  Python/Node exceptions — a loop that only reads `payload` will `KeyError` on them.
- **Register the handler before `load()`.** Messages sent during agent startup are
  lost otherwise.
- `on_message` runs on Frida's **reactor thread**, not your main thread — don't do
  slow/blocking work there; hand off to a queue if needed.
- Binary belongs in the second `data` arg, not JSON — don't base64 large buffers
  into the payload; pass `send(obj, arrayBuffer)`.
- A `recv().wait()` whose message is never posted hangs that agent flow forever —
  always `script.post(...)` the reply.
- Don't flood `send()` from a hot hook; batch or sample (see back-pressure in
  [../core-api/send-recv.md](../core-api/send-recv.md)).
