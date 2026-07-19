---
name: script-loading
description: Load agents into a Frida session with -l script.js (repeatable for multiple files), pass parameters with -P, and reload live in the REPL with %reload.
---

# Loading agents: `-l`, multiple scripts, parameters

**When:** you've written an agent (or several) and want the CLI to inject it. `-l` is
the workhorse flag across `frida` and the other tools.

## Canonical command

```sh
frida -U -f com.example.app -l agent.js
```

`-l PATH` loads a JavaScript agent. It's injected before the REPL prompt (and, for a
spawned target, before the app resumes).

## Multiple scripts

`-l` is repeatable; scripts load in order into the same session:

```sh
frida -U -n com.example.app -l bypass-pinning.js -l dump-keys.js
```

Each runs in its own script scope but shares the target process. To combine many
source files or TypeScript into one agent instead, bundle with
[frida-compile.md](frida-compile.md) and load the single output.

## Passing parameters

Pass a JSON object to the agent, readable as a runtime parameter:

```sh
frida -U -f com.example.app -l agent.js -P '{"verbose":true,"host":"10.0.0.2"}'
```

`-P`/`--parameters` accepts inline JSON or `@file.json`. The agent reads it via the
script's runtime parameters (`Script.runtime` is the engine name; parameters arrive
through the host binding / stage config).

## Live reload

In the interactive REPL, edit the file and re-inject without relaunching:

```
[Pixel::com.example.app]-> %reload        # reload all -l scripts from disk
[Pixel::com.example.app]-> %load other.js # load an additional file
```

## Gotchas

- A syntax error in the agent surfaces as a load-time error with file/line — fix and
  `%reload`.
- For a **spawned** target, hooks in `-l` are in place before startup, but you still
  must `%resume` in the REPL to let the app run. See [spawn-vs-attach.md](spawn-vs-attach.md).
- Multi-file agents using `import`/`require` won't run raw — they must be bundled
  first ([frida-compile.md](frida-compile.md)).
- For one-shot, non-interactive runs add `-q`; see [batch-mode.md](batch-mode.md).
