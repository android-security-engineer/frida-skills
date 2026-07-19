---
name: frida-gadget
description: Explains frida-gadget, the embeddable shared library for non-rooted or re-signed apps, its config interaction modes, and when to choose it over frida-server.
---

# frida-gadget: instrumentation without a server

`frida-gadget` is a shared library you **embed inside the app itself**. When the
app loads it, it brings up GumJS in-process — no `frida-server`, no root, no
external injection. This is the go-to for **non-rooted Android** and **re-signed
iOS** apps where you cannot run a privileged daemon.

The tradeoff: you must get the gadget *into* the app. That means modifying the
APK/IPA (repackaging, adding the library, and pointing a loaded library or the
app's `System.loadLibrary` at it) and, on iOS, re-signing. Objection and similar
tools automate the patching; conceptually they all just add the gadget so the app
loads it early.

## Reaching the gadget

Because the gadget lives inside the app, the host connects to it like any process
on the device (`-U`), and you use `-n Gadget` / attach by name — you do **not**
spawn via the gadget the way you do with a server:

```sh
frida-ps -U                       # the gadget-hosting app appears
frida -U -n Gadget -l agent.js    # attach to the embedded gadget, load your agent
```

## Interaction modes (the `.config` file)

A `libgadget.config.json` beside the library selects how the gadget behaves at
load. Three interaction modes:

- **`listen`** (default) — the gadget opens a port and *waits* for the host to
  connect and send a script. Good for interactive work; the app pauses on launch
  until you connect (configurable).

  ```json
  { "interaction": { "type": "listen", "address": "127.0.0.1", "port": 27042, "on_load": "wait" } }
  ```

- **`script`** — the gadget loads a JS file from a fixed path at startup and runs
  it with no host attached. Ideal for autonomous hooks (e.g. pinning bypass) that
  must run before any network call.

  ```json
  { "interaction": { "type": "script", "path": "/data/local/tmp/agent.js" } }
  ```

- **`script-directory`** — like `script` but loads/manages every `.js` in a
  directory, hot-reloading as files change.

## Server vs gadget — which to use

| Situation | Use |
| --- | --- |
| Rooted Android / jailbroken iOS | [frida-server.md](frida-server.md) — simplest, spawn-capable. |
| Non-rooted Android, can repackage APK | gadget (patch the app). |
| iOS without jailbreak, can re-sign | gadget (add library + re-sign). |
| Need hooks *before* app code, no host present | gadget in `script` mode. |
| Ephemeral, don't want to modify the app | server (if you have root). |

## Timing note

In `script` mode the gadget runs your JS as the app initializes, so it can install
hooks early — similar in spirit to spawn gating with a server
([spawn-attach-gating.md](spawn-attach-gating.md)). In `listen` mode with
`"on_load": "wait"`, the app blocks until the host connects, giving you the same
early-hook window interactively.

## Version match still applies

The gadget's version must match the host `frida` you connect with, exactly as the
server does. Mismatched versions fail the handshake.
