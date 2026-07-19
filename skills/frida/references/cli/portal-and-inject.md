---
name: portal-and-inject
description: Use frida-inject to load an agent headlessly on a device (no REPL, good for embedded/CI) and understand frida-portal for clustering many agents behind one endpoint.
---

# `frida-inject` (headless) and `frida-portal` (clustering)

**When:** you need instrumentation without an interactive host — a background/embedded
run (`frida-inject`), or a central endpoint that many devices/agents connect to
(`frida-portal`).

## `frida-inject` — headless script loading

Loads an agent into a target and stays running, with no REPL. Ideal for embedded
Linux, CI, or fire-and-forget hooks.

```sh
frida-inject -n com.example.app -s agent.js
```

Common options:

| Flag | Meaning |
| --- | --- |
| `-n NAME` | Attach to a process by name. |
| `-p PID` | Attach by pid. |
| `-f FILE` | Spawn a program. |
| `-s SCRIPT` | The agent script to inject. |
| `-D id` | Select a device. |

```sh
frida-inject -f /usr/bin/target -s agent.js          # spawn + inject headless
frida-inject -p 4211 -s hooks.js                     # attach to a pid on the host
```

It keeps the agent loaded until interrupted (Ctrl-C) or the target exits — the agent
communicates via its own `send()`/logging, since there's no console.

## `frida-portal` — a cluster endpoint

`frida-portal` runs a server that agents connect *out* to, letting you manage many
instrumented processes/devices behind one address. Nodes join the portal (via the
agent-side portal API), and a controller connects to the portal to enumerate and
message them.

```sh
frida-portal --cluster-endpoint=0.0.0.0:27052 --control-endpoint=0.0.0.0:27042
```

- **cluster endpoint** — where instrumented nodes connect in.
- **control endpoint** — where your controller (CLI/bindings) connects to drive them.

This is an advanced fleet/large-scale setup; for a single device the ordinary
`frida` + `-U` flow is simpler.

## Gotchas

- `frida-inject` has **no prompt**: design the agent to act on load and report via
  `send()`; there's nothing to `%resume`, so attach (`-n`) or ensure the agent
  resumes a spawn itself.
- Portal endpoints are unauthenticated unless you configure a token — don't expose
  them on untrusted networks.
- For most tasks you don't need either tool; reach for the REPL
  ([frida-repl.md](frida-repl.md)) or Python bindings first.
- Instrument only software you're authorized to analyze.
