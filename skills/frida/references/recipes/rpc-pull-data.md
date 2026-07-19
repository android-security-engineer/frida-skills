---
name: rpc-pull-data
description: Frida agent that exposes rpc.exports functions so a Python driver can call into the target on demand and pull back values (memory reads, computed results).
---

# Expose rpc.exports and pull data from Python

**When:** you want your host program to *drive* the target — call functions,
read memory, retrieve results on demand — rather than passively watch logs.
Define `rpc.exports` in the agent and call them from a Python driver.

```js
// recipe.js — agent: expose callable functions to the host.
rpc.exports = {
  // JS camelCase → Python snake_case: readCString → read_c_string.
  readCString(addrStr, max) {
    return ptr(addrStr).readUtf8String(max || 256);
  },
  callSum(a, b) {
    // Resolve a real export and call it via NativeFunction.
    const fn = new NativeFunction(Module.getGlobalExportByName('abs'), 'int', ['int']);
    return fn(a) + fn(b);                        // 'int' return → plain JS number
  },
  dumpModule(name) {
    const m = Process.getModuleByName(name);      // returns a plain object to host
    return { name: m.name, base: m.base.toString(), size: m.size, path: m.path };
  },
};
console.log('[+] rpc ready');
```

```python
# driver.py — host: load the agent and call its exports synchronously.
import frida, sys

def on_message(msg, data):
    print('[msg]', msg)

device = frida.get_usb_device(timeout=5)          # USB device; use get_local_device() for local
pid = device.spawn(['com.example.app'])
session = device.attach(pid)
with open('recipe.js') as f:
    script = session.create_script(f.read())
script.on('message', on_message)
script.load()
device.resume(pid)

api = script.exports_sync                          # snake_case mirror of rpc.exports
print('sum   =', api.call_sum(3, -4))
print('mod   =', api.dump_module('libc.so'))
# print('str =', api.read_c_string('0x...', 64))
sys.stdin.read()                                   # keep the process alive
```

Run it:

```sh
python driver.py                               # driver spawns/attaches itself
```

**Tweak this:**
- Return only JSON-serializable values (numbers, strings, arrays, plain objects) —
  wrap NativePointers with `.toString()` as shown.
- `exports_sync` blocks until the agent replies; use `script.exports_async` (await)
  for concurrency.
- Large binary payloads: `send(meta, arrayBuffer)` from the agent and read `data` in
  `on_message` — see [batch-run-logging.md](batch-run-logging.md).
- Attach to a running app instead of spawning: `session = device.attach('AppName')`
  and drop the `spawn`/`resume` calls.
