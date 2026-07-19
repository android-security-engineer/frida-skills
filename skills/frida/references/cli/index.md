---
name: cli-index
description: Index of Frida command-line tool docs — frida, frida-trace, frida-ps, frida-ls-devices, frida-discover, frida-kill, frida-apk, spawn/attach flags, and scripting the REPL.
---

# CLI tools — drive Frida without writing bindings

The command line is the fastest path for recon and one-off instrumentation.
Reach for `frida-trace` first (zero code), then the `frida` REPL with `-l`.

## Core tools
| Doc | Covers |
| --- | --- |
| [frida-repl.md](frida-repl.md) | The `frida` REPL: attach/spawn, `-l`, `%load`, `%resume`, `.exit`. |
| [frida-trace.md](frida-trace.md) | `frida-trace` native tracing: `-i/-x` includes/excludes, handler stubs. |
| [frida-trace-java.md](frida-trace-java.md) | `frida-trace -j` for Android Java methods; glob syntax. |
| [frida-trace-objc.md](frida-trace-objc.md) | `frida-trace -m` for Objective-C selectors on iOS/macOS. |
| [frida-ps.md](frida-ps.md) | `frida-ps` — list processes/apps, `-U`/`-a`/`-i` variants. |
| [frida-ls-devices.md](frida-ls-devices.md) | `frida-ls-devices` — what's reachable; first diagnostic. |
| [frida-discover.md](frida-discover.md) | `frida-discover` — find functions that run during an action. |
| [frida-kill.md](frida-kill.md) | `frida-kill` — terminate a target by name/pid. |

## Targeting & options
| Doc | Covers |
| --- | --- |
| [spawn-vs-attach.md](spawn-vs-attach.md) | `-f` (spawn) vs `-n`/`-p` (attach); when each is required. |
| [device-selection.md](device-selection.md) | `-U`, `-H host:port`, `-D id`, `--device`; remote servers. |
| [target-selection.md](target-selection.md) | `-n name`, `-p pid`, `-f program`, `-N identifier` differences. |
| [script-loading.md](script-loading.md) | `-l script.js`, multiple `-l`, `-P parameters`, `-e eval`. |
| [batch-mode.md](batch-mode.md) | `-q` quiet, `-o logfile`, `-t timeout`, non-interactive automation. |
| [runtime-flags.md](runtime-flags.md) | `--runtime=qjs|v8`, `--debug`, `--squelch-crash`. |

## Packaging & advanced
| Doc | Covers |
| --- | --- |
| [frida-apk.md](frida-apk.md) | `frida-apk` — inject `frida-gadget` into an APK for non-rooted devices. |
| [frida-server-setup.md](frida-server-setup.md) | Download, push, and run `frida-server` on Android/iOS. |
| [frida-compile.md](frida-compile.md) | `frida-compile` — bundle a multi-file/TypeScript agent into one script. |
| [portal-and-inject.md](portal-and-inject.md) | `frida-inject` (headless) and Portal cluster basics. |
