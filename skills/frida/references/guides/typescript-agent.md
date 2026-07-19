---
name: typescript-agent
description: Write a Frida agent in TypeScript with @types/frida-gum for autocompletion and type-checking, then bundle it to one JS file with frida-compile for the CLIs or bindings.
---

# Writing agents in TypeScript

**When:** you want editor autocompletion, type-checking of the Gum API, and larger
agents split across modules. TypeScript agents are transpiled and bundled by
[../cli/frida-compile.md](../cli/frida-compile.md) into one JS file the CLIs and
bindings load normally.

## End-to-end: project → compile → run

```sh
mkdir myagent && cd myagent
npm init -y
npm install --save-dev @types/frida-gum frida-compile   # types + bundler
```

```ts
// agent.ts
const openPtr = Module.getGlobalExportByName("open");

Interceptor.attach(openPtr, {
  onEnter(args: InvocationArguments) {
    const path = args[0].readUtf8String();
    send({ event: "open", path });
  },
});

rpc.exports = {
  ping(): string {
    return "pong";
  },
};
```

```sh
npx frida-compile agent.ts -o agent.js       # bundle + transpile to one file
frida -U -f com.example.app -l agent.js       # load like any script
```

## Recommended `tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "es2020",
    "lib": ["es2020"],
    "module": "es2020",
    "moduleResolution": "node",
    "strict": true,
    "types": ["frida-gum"]
  }
}
```

`@types/frida-gum` declares the globals (`Interceptor`, `Module`, `NativePointer`,
`send`, `rpc`, `Java`, `ObjC`, …) so no `import` is needed to use them — they are
ambient. Add `"types": ["frida-gum"]` so the compiler finds them.

## Splitting into modules

```ts
// pinning.ts
export function bypassPinning(): void { /* ... */ }
```

```ts
// agent.ts
import { bypassPinning } from "./pinning";
bypassPinning();
```

See [multi-file-compile.md](multi-file-compile.md) for the multi-file bundling
details and watch mode.

## Pitfalls

- **The CLIs cannot load `.ts` or `import`-using files** — always `frida-compile`
  first; a load-time `SyntaxError: import` means you skipped the build.
- Types don't change runtime behavior: the default runtime is still **QuickJS**, so
  avoid V8-only language features unless you pass `--runtime=v8`.
- `@types/frida-gum` is dev-only — it is stripped at compile time and never ships in
  the bundle; don't `import` from it.
- Keep source maps on while developing (default) so agent stack traces point at your
  `.ts` lines; drop them with `-S` for release.
- `args[0].readUtf8String()` can return `null` for a NULL pointer — type it as
  `string | null` and guard before use.
