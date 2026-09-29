---
name: batch-run-logging
description: Frida agent plus Python driver that runs headless and quiet, streaming send() events and error messages to a timestamped log file for unattended capture.
---

# Run headless, quiet, forever — log to a file

**When:** you want to capture events unattended (overnight, CI, a long repro) —
no interactive REPL, structured `send()` events written to a file, and clean
handling of errors. Use `send()` in the agent and a Python driver that writes logs.

```js
// recipe.js — agent: emit structured events instead of console.log.
const libc = Process.getModuleByName('libc.so.6');   // 'libc.so' on Android
Interceptor.attach(libc.getExportByName('open'), {
  onEnter(args) { this.path = args[0].readUtf8String(); },
  onLeave(retval) {
    // send() is async, one-way, agent→host. Payload must be JSON-serializable.
    send({ event: 'open', path: this.path, fd: retval.toInt32() });
  },
});
send({ event: 'ready' });
```

```python
# driver.py — host: load agent, append every event/error to a log file.
import frida, time, json, sys

logf = open('capture.log', 'a', buffering=1)          # line-buffered

def log(obj):
    logf.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {json.dumps(obj)}\n")

def on_message(msg, data):
    if msg['type'] == 'send':
        log(msg['payload'])
    elif msg['type'] == 'error':                       # agent exception
        log({'error': msg.get('description'), 'stack': msg.get('stack')})

device = frida.get_usb_device(timeout=5)
pid = device.spawn(['com.example.app'])
session = device.attach(pid)
session.on('detached', lambda reason, *a: (log({'detached': reason}), sys.exit(0)))
script = session.create_script(open('recipe.js').read())
script.on('message', on_message)
script.load()
device.resume(pid)

while True:                                            # run until detached/killed
    time.sleep(1)
```

Run it:

```sh
python driver.py                               # writes events to capture.log
python driver.py >driver.out 2>&1 &            # fully detached; tail capture.log
```

**Tweak this:**
- Prefer `send()` over `console.log` for machine-readable output; reserve
  `console.log` for human debugging.
- Ship binary blobs efficiently: `send({n: buf.byteLength}, buf.readByteArray(n))`
  in the agent, then use the `data` arg of `on_message`.
- The `detached` handler catches process death, crashes, and version skew — the
  reason string tells you which.
- Need to also *call in* to the target, not just receive? See
  [rpc-pull-data.md](rpc-pull-data.md).
