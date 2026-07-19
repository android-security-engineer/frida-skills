---
name: multi-file-compile
description: Split a Frida agent across multiple files or npm modules and bundle them into one loadable script with frida-compile, including watch mode and the load flow.
---

# Multi-file agents with `frida-compile`

**When:** your agent has grown past one file — separate modules per concern, shared
helpers, or an npm dependency. The `frida`/`frida-trace` CLIs and the bindings load a
**single** JS string, so you bundle first with
[../cli/frida-compile.md](../cli/frida-compile.md).

## End-to-end: a three-file agent

```sh
mkdir agent && cd agent
npm init -y
npm install --save-dev @types/frida-gum frida-compile
```

```js
// src/hooks/open.js
export function hookOpen() {
  const p = Module.getGlobalExportByName('open');
  Interceptor.attach(p, {
    onEnter(args) { send({ kind: 'open', path: args[0].readUtf8String() }); }
  });
}
```

```js
// src/log.js
export function report(kind, data) { send({ kind, ...data }); }
```

```js
// src/index.js   <- entry point
import { hookOpen } from './hooks/open.js';
import { report } from './log.js';

hookOpen();
report('ready', { hooks: 1 });
```

Bundle the entry point into one file and load it:

```sh
npx frida-compile src/index.js -o agent.js
frida -U -f com.example.app -l agent.js
```

## Watch mode for iteration

```sh
npx frida-compile src/index.js -o agent.js -w      # rebuild on every save
```

Pair `-w` with the REPL's `%reload` after each rebuild — see
[reload-workflow.md](reload-workflow.md).

## Using npm dependencies

Any pure-JS package that runs without Node built-ins works — install it and
`import`; `frida-compile` bundles it in:

```sh
npm install js-sha256
```

```js
// src/index.js
import { sha256 } from 'js-sha256';
send({ digest: sha256('hello') });
```

## Pitfalls

- **Load the compiled output, never the source.** Loading a file with `import`
  yields `SyntaxError: import` — bundle first.
- Give `frida-compile` the **entry file**; it follows the import graph. Pointing it
  at a leaf module bundles only that leaf.
- Packages needing Node APIs (`fs`, `net`, native addons) won't run inside the agent
  — the agent lives in the target process, not Node. Use Frida's own `File`, `Socket`
  globals instead.
- Keep source maps on while developing so stack traces map to your source files.
- TypeScript sources compile the same way (`frida-compile src/index.ts -o agent.js`);
  see [typescript-agent.md](typescript-agent.md).
