---
name: error-handling
description: Handle failures in Frida agents and hosts — catch agent exceptions via the error message, guard hook bodies, use SystemFunction for errno, and detect session detach.
---

# Error handling in agents and hosts

**When:** hooks throw, targets crash, sessions drop, or a lookup fails — you need the
run to fail loudly on the host instead of silently doing nothing. Frida surfaces
agent errors as **messages**, not host exceptions.

## Agent exceptions reach the host as `error` messages

An uncaught throw inside a hook doesn't stop your Python/Node program — it arrives in
the message callback with `type == 'error'`. Always handle it:

```python
import frida, sys

def on_message(message, data):
    if message['type'] == 'error':
        print('AGENT ERROR:', message['description'], file=sys.stderr)
        print('  at', message.get('fileName'), 'line', message.get('lineNumber'), file=sys.stderr)
        print(message.get('stack', ''), file=sys.stderr)
    elif message['type'] == 'send':
        print(message['payload'])

session = frida.get_usb_device().attach('com.example.app')
script = session.create_script(open('agent.js').read())
script.on('message', on_message)
script.load()
sys.stdin.read()
```

## Defensive hooks (agent side)

Wrap risky work so one bad call doesn't kill the hook, and check lookups:

```js
// agent.js
const p = Process.findModuleByName('libssl.so')?.findExportByName('SSL_read');
if (p === null || p === undefined) {
  send({ warn: 'SSL_read not found' });          // report instead of throwing
} else {
  Interceptor.attach(p, {
    onEnter(args) {
      try {
        this.len = args[2].toInt32();
      } catch (e) {
        send({ error: String(e) });               // contain the failure
      }
    }
  });
}
```

Use the `find*` (null-returning) variants when a symbol may be absent; the `get*`
variants throw. See [../core-api/module.md](../core-api/module.md).

## Reading errno from a syscall

Native calls that set `errno` need `SystemFunction`, which returns `{ value, errno }`:

```js
const openPtr = Module.getGlobalExportByName('open');
const openFn = new SystemFunction(openPtr, 'int', ['pointer', 'int']);
const path = Memory.allocUtf8String('/nope');
const r = openFn(path, 0);
send({ value: r.value, errno: r.errno });          // errno valid even on -1
```

Details in [../core-api/system-functions-errno.md](../core-api/system-functions-errno.md).

## Detect session loss on the host

```python
session.on('detached', lambda reason, *a: print('DETACHED:', reason, file=sys.stderr))
```

`reason` is e.g. `'process-terminated'`, `'connection-terminated'`,
`'application-requested'` — tells you whether the target died or Frida disconnected.

## Pitfalls

- **A "hook that does nothing" is usually a swallowed error.** If you never handle
  `type == 'error'`, a typo in the agent looks like silence — always log it.
- `RPC` calls propagate agent exceptions to the host call site (Python raises,
  Node's Promise rejects) — wrap `exports_sync` calls in `try/except`.
- `get*`/`getExportByName` **throw** on absence; `find*` return `null`. Pick the one
  matching your control flow.
- A crashed target detaches the session — pending `send`s may be lost; treat
  `detached` as terminal and stop the run.
- For global safety nets over undefined-global access, see
  [../core-api/gc-weakref-script.md](../core-api/gc-weakref-script.md).
