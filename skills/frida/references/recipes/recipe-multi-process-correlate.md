---
name: recipe-multi-process-correlate
description: Hook several processes at once from one Python driver and correlate events by wall-clock time into a single ordered timeline.
---

# Multi-process event correlation

**When:** you're tracing a flow that crosses process boundaries (e.g. an app
and a helper daemon), and need one ordered timeline.

```python
# driver.py — attach to several PIDs, install the same agent, merge messages
import frida, json, threading, time

TARGETS = {1234: 'app', 2345: 'daemon'}
events = []
lock = threading.Lock()

def make_handler(role):
    def on_message(message, data):
        if message['type'] == 'send':
            with lock:
                events.append((time.time(), role, message['payload']))
    return on_message

device = frida.get_local_device()
scripts = []
for pid, role in TARGETS.items():
    session = device.attach(pid)
    script = session.create_script(open('agent.js').read())
    script.on('message', make_handler(role))
    script.load()
    scripts.append(script)

input('enter to stop> ')   # let it run
for s in scripts: s.unload()

events.sort()
for t, role, payload in events:
    print(f'{t:.3f} [{role}] {payload}')
```

`agent.js` is the same simple hook you'd write for one process — the
correlation happens on the host by sorting on `time.time()`.

```sh
python3 driver.py
```

**Tweak:** swap `frida.get_local_device()` for `frida.get_usb_device()` to do
this across on-device processes; use `frida-ps -U` to find PIDs.
