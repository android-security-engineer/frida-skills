---
name: reload-workflow
description: Set up a fast edit-reload loop for Frida agent development — REPL %reload, frida-compile watch mode, and a Python driver that reloads a script on file change.
---

# Fast edit → reload loops

**When:** you're iterating on an agent and want each save reflected in the target in
seconds, without restarting the app or re-spawning. The trick is to reload the
**script**, not the process.

## Option A: REPL + `%reload`

Load the agent in the interactive REPL, then re-run it after every edit:

```sh
frida -U -f com.example.app -l agent.js
# edit agent.js in your editor, then in the REPL:
[Local::com.example.app]-> %reload
```

`%reload` re-reads the `-l` file and re-injects it into the **same** process — hooks
are torn down and re-installed. Combine with watch mode so the file is always fresh:

```sh
npx frida-compile src/index.js -o agent.js -w    # rebuild on save (other terminal)
```

Now the loop is: save source → `frida-compile -w` rebuilds `agent.js` → type
`%reload`. See [../cli/frida-repl.md](../cli/frida-repl.md) and
[../cli/frida-compile.md](../cli/frida-compile.md).

## Option B: auto-reload from Python

Reinject the script whenever the source file changes — no manual `%reload`:

```python
import frida, os, time, sys

session = frida.get_usb_device().attach('com.example.app')
script = None

def on_message(message, data):
    print(message.get('payload', message))

def reload_agent():
    global script
    if script is not None:
        script.unload()
    src = open('agent.js').read()
    script = session.create_script(src)
    script.on('message', on_message)
    script.load()
    print('reloaded')

last = 0
reload_agent()
while True:                                  # poll mtime; reinject on change
    m = os.path.getmtime('agent.js')
    if m != last:
        last = m
        try:
            reload_agent()
        except Exception as e:
            print('reload failed:', e, file=sys.stderr)
    time.sleep(0.5)
```

This keeps the **process** alive and swaps the agent, so app state (logged-in
session, loaded classes) survives across edits — much faster than re-spawning.

## Pitfalls

- **Reload re-installs hooks.** Old listeners are dropped when the script unloads, so
  design `install`/`teardown` so re-injection is idempotent (see
  [agent-structure.md](agent-structure.md)).
- If you `%reload` a spawned-but-not-resumed app, remember it is still paused — the
  hooks re-arm, but nothing runs until `%resume`.
- Startup-only code (init, pinning setup) **won't re-fire** on reload because the
  process already passed it — for those you must re-spawn (`-f`), not reload.
- Watch mode rebuilds the bundle but does **not** reload it for you in the REPL; you
  still type `%reload` (Option A) or use the Python poller (Option B).
- Poll interval vs mtime resolution: 0.5 s is safe; sub-100 ms polling can miss
  same-second writes on some filesystems.
