---
name: batch-mode
description: Run Frida non-interactively for automation — -q quiet mode to load an agent and exit, -o to log output to a file, and -t to bound run time, for CI and one-shot dumps.
---

# Batch / non-interactive runs

**When:** you want `frida` to load an agent, do its job, and exit without a prompt —
CI pipelines, scripted dumps, reproducible captures.

## Canonical command

```sh
frida -U -n com.example.app -l agent.js -q
```

`-q`/`--quiet` skips the interactive REPL banner and prompt: the agent loads, its
`send()`/`console.log` output streams to stdout, and Frida exits when the script
finishes (or the process detaches).

## Common options

| Flag | Effect |
| --- | --- |
| `-q` / `--quiet` | No REPL; suitable for piping and scripts. |
| `-o FILE` / `--output FILE` | Write output (logs, traces) to a file. |
| `-t SECONDS` / `--timeout SECONDS` | Auto-detach and exit after N seconds. |
| `-e CODE` / `--eval CODE` | Evaluate a snippet instead of `-l` (quick one-liners). |

## Examples

```sh
# spawn, run agent, quit — capture to a log
frida -U -f com.example.app -l dump.js -q -o dump.log

# time-bounded trace for CI
frida-trace -U -n com.example.app -i "SSL_read" -o trace.log &
sleep 20 && kill %1

# one-liner without a file
frida -U -n com.example.app -q -e 'console.log(Process.arch)'
```

## Making the agent finish

In quiet mode there's no human at a prompt, so the run ends when the agent
finishes, the process detaches, or your `-t` bound expires. With `-f` the CLI
auto-resumes the spawned app right after the script loads (default
`on_spawn_complete="resume"`), so a spawned target runs freely; to *hold* it
paused at entry (e.g. to gate before app code), pass `--pause` and resume from
the agent via `Process.resume()` or RPC. To end the run deliberately, bound it
with `-t`:

```sh
frida -U -f com.example.app -l capture.js -q -t 30
```

## Gotchas

- **Spawn (`-f`) in `-q` mode:** the app is auto-resumed after the script loads
  (resume is *not* gated on a prompt — quiet just removes the REPL), so agent
  hooks land during the brief paused window and the app then runs freely. If you
  need the app held paused longer, use `--pause` and resume from inside the
  agent (`Process.resume()`).
- Without `-t`, a quiet attach can hang if the agent never exits — always bound
  long-running captures.
- `-o` captures Frida's output stream; it does not silence the target's own stdout.
- For programmatic control beyond flags, drive Frida from Python/Node instead of the
  CLI (see the guides index).
