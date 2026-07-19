---
name: recipe-remote-cluster
description: Drive a cluster of remote frida-server instances over -H, install the same agent on each, and fan-in results to one host.
---

# Remote cluster injection

**When:** you have several devices/servers reachable over TCP and want the
same agent on all of them.

```python
# cluster.py
import frida, threading

NODES = ['10.0.0.5:27042', '10.0.0.6:27042']
TARGET = 'com.example.app'   # or a PID
results = []

def run_on(host):
    device = frida.get_device_manager().add_remote_device(host)
    session = device.attach(TARGET)
    script = session.create_script(open('agent.js').read())
    script.on('message', lambda m, d: results.append((host, m)))
    script.load()
    # leave it running; gather later
    return script

scripts = [run_on(h) for h in NODES]
input('enter to stop> ')
for s in scripts: s.unload()
for host, m in results: print(host, m)
```

```sh
# on each node: frida-server listening on the network, matching host version
frida-server -l 0.0.0.0:27042
python3 cluster.py
```

**Tweak:** version skew across nodes fails silently-ish — pin the same
`frida-server` build on every node. For USB-over-TCP, `adb forward
tcp:27042 tcp:27042` then treat as `127.0.0.1:27042`. See
[../troubleshooting/remote-connect.md](../troubleshooting/remote-connect.md).
