---
name: agent-structure
description: Structure a real multi-hook Frida agent — organize install functions, make it configurable via rpc.exports and recv, track installed hooks, and clean up on unload.
---

# Structuring a multi-hook agent

**When:** your agent is more than one `Interceptor.attach` — several hooks, some
configurable, that you want to enable/disable and tear down cleanly. This is the
shape a real agent takes before you split it across files
([multi-file-compile.md](multi-file-compile.md)).

## End-to-end: configurable, controllable agent

```js
// agent.js
const listeners = [];                       // track hooks so we can revert them

function hookOpen(verbose) {
  const p = Module.getGlobalExportByName('open');
  listeners.push(Interceptor.attach(p, {
    onEnter(args) {
      const path = args[0].readUtf8String();
      if (verbose) send({ kind: 'open', path });
    }
  }));
}

function hookConnect() {
  const p = Module.getGlobalExportByName('connect');
  listeners.push(Interceptor.attach(p, {
    onEnter(args) { this.sockaddr = args[1]; },
    onLeave(retval) { send({ kind: 'connect', ret: retval.toInt32() }); }
  }));
}

function install(config) {
  if (config.open) hookOpen(config.verbose);
  if (config.connect) hookConnect();
  send({ kind: 'ready', hooks: listeners.length });
}

rpc.exports = {
  install(config) { install(config); },      // host decides what to hook
  teardown() {
    listeners.forEach(l => l.detach());
    listeners.length = 0;
    Interceptor.flush();
  }
};
```

Host drives it (Python):

```python
script.load()
script.exports_sync.install({ 'open': True, 'connect': True, 'verbose': True })
# ... collect events ...
script.exports_sync.teardown()
```

## Structure guidelines

- **One install function per concern** (`hookOpen`, `hookConnect`), each returning or
  pushing its listener. Keep hook bodies small.
- **Make behavior data-driven** via an `rpc.exports.install(config)` entry point or a
  `recv('config').wait()` handshake — don't hard-code paths and flags.
- **Keep a registry** (`listeners`) so you can `detach()` every hook and
  `Interceptor.flush()` in a `teardown` export; see
  [../core-api/interceptor-revert-flush.md](../core-api/interceptor-revert-flush.md).
- **Report readiness** with a `send({ kind: 'ready' })` so the host knows hooks are
  live before it drives the app.
- **Guard platform code:** wrap Java/ObjC hooks in `if (Java.available) Java.perform(...)`
  / `if (ObjC.available)`.

## Pitfalls

- `Interceptor.attach` returns a **listener** — keep it; you can't detach an
  anonymous hook individually, only `Interceptor.detachAll()`.
- Installing the same hook twice stacks callbacks — track state and make `install`
  idempotent.
- `this` is shared between `onEnter`/`onLeave` for a single call (stash args there),
  but is **not** shared across concurrent calls — never use module globals for
  per-call state.
- Reading `args[0].readUtf8String()` on a NULL pointer returns `null`; guard before
  using the value.
- Don't do heavy work inside hot hooks; sample or move to native
  ([../core-api/cmodule.md](../core-api/cmodule.md)).
