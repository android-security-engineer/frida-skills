---
name: frida-compile
description: Use frida-compile to bundle a multi-file or TypeScript Frida agent (with imports/npm deps) into a single script the CLIs can load with -l; supports watch and source maps.
---

# `frida-compile` — bundle a multi-file / TypeScript agent

**When:** your agent spans multiple files, uses `import`/`require`, npm packages, or
TypeScript. The `frida`/`frida-trace` CLIs load a **single** JS file, so you compile
your sources into one bundle first.

## Canonical command

```sh
frida-compile agent.ts -o agent.js
```

This resolves imports and transpiles TypeScript into one self-contained `agent.js`
you then load normally:

```sh
frida -U -f com.example.app -l agent.js
```

## Common options

| Flag | Effect |
| --- | --- |
| `-o FILE` | Output path for the bundled script. |
| `-w` / `--watch` | Rebuild automatically when sources change. |
| `-S` / `--no-source-maps` | Omit inline source maps (smaller output). |
| `-c` / `--compress` | Minify/compress the bundle. |

## Typical project loop

```sh
npm init -y
npm install @types/frida-gum --save-dev      # types for the agent API
frida-compile agent.ts -o agent.js -w        # watch: rebuild on save
# in another terminal, live-reload in the REPL:
frida -U -f com.example.app -l agent.js       # then %reload after each rebuild
```

Your `agent.ts` can now split into modules:

```ts
// agent.ts
import { bypassPinning } from "./pinning";
bypassPinning();
```

## Gotchas

- The CLI cannot load raw `import`-using files — **always compile first**; a
  "SyntaxError: import" at load time means you skipped this step.
- Source maps make agent stack traces reference your `.ts` lines; keep them on while
  developing, drop with `-S` for release.
- Agent API types come from `@types/frida-gum`; install them for editor
  autocompletion, but they don't ship in the bundle.
- Pair `-w` (watch) with the REPL's `%reload` for a fast edit loop; see
  [script-loading.md](script-loading.md).
