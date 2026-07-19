---
name: headless-automation
description: Run Frida fully unattended — a Python driver with timeouts and exit codes, batch CLI runs with -q, and frida-inject for REPL-less headless script loading.
---

# Headless automation

**When:** you need Frida to run with no human at the REPL — a scripted collection
step, a test, or a background hook on an embedded device. The run must start, do its
job, and **exit with a meaningful code**.

## End-to-end: bounded Python driver

Spawn, hook, collect for a fixed window, then exit 0/1 based on what was seen:

```python
import frida, sys, time

FOUND = {'ok': False}

AGENT = """
const p = Module.getGlobalExportByName('open');
Interceptor.attach(p, {
  onEnter(args) { send({ path: args[0].readUtf8String() }); }
});
"""

def on_message(message, data):
    if message['type'] == 'error':
        print('agent error:', message['description'], file=sys.stderr)
        return
    path = message['payload'].get('path')
    print('open', path)
    if path and 'config' in path:
        FOUND['ok'] = True

device = frida.get_usb_device()
pid = device.spawn(['com.example.app'])
session = device.attach(pid)
script = session.create_script(AGENT)
script.on('message', on_message)
script.load()
device.resume(pid)                       # resume AFTER hooks are installed

deadline = time.time() + 20              # hard timeout
while time.time() < deadline and not FOUND['ok']:
    time.sleep(0.2)

script.unload()
device.kill(pid)                         # clean up the spawned target
sys.exit(0 if FOUND['ok'] else 1)        # exit code drives CI / callers
```

The timeout guarantees the run terminates; the exit code lets a caller or CI job
branch on success.

## Batch CLI runs (no bindings)

For a quick unattended run, the REPL's batch flags suffice:

```sh
frida -U -f com.example.app -l agent.js -q --exit-on-error       # run, quit, fail loudly
frida -U -n com.example.app -l agent.js -q -e "rpc.exports.dump()" --eval
```

`-q` (quiet, no prompt), `--exit-on-error`, and `-e/--eval` are covered in
[../cli/batch-mode.md](../cli/batch-mode.md).

## `frida-inject` — REPL-less injection

On embedded Linux or CI where you just want the agent resident:

```sh
frida-inject -f /usr/bin/target -s agent.js       # spawn + inject, no prompt
frida-inject -n com.example.app -s agent.js        # attach headless
```

It has no console — the agent must act on load and report via `send()`/logging. See
[../cli/portal-and-inject.md](../cli/portal-and-inject.md).

## Pitfalls

- **Always bound the run.** Without a timeout a hook that never fires hangs forever;
  a deadline plus a clear exit code is the whole point of automation.
- **Resume after loading** a spawned target, or the app stays paused and nothing
  happens.
- Clean up: `script.unload()`, `device.kill(pid)` — leftover paused spawns pile up
  (clear with [../cli/frida-kill.md](../cli/frida-kill.md)).
- `frida-inject` gives no output channel but `send()`; design the agent to be
  autonomous since there's nothing to `%resume`.
- Version skew (host `frida` vs device `frida-server`) fails non-interactively with
  cryptic errors — pin versions in your automation environment.
