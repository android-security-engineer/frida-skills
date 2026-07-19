---
name: swift-interop
description: Instrumenting Swift code on iOS/macOS with Frida — resolving mangled symbol names via ApiResolver('swift'), hooking native Swift functions, and the practical limits versus Objective-C.
---

# Instrumenting Swift on iOS & macOS

**When to use:** the app is written in Swift and the method you need isn't exposed
to the Objective-C runtime (so `ObjC.classes` can't see it). Swift functions are
plain native code with **mangled** symbol names; resolve them and hook with
`Interceptor`.

Reach the device with `-U` (jailbreak `frida-server` or re-signed `frida-gadget`).

## First: is it reachable via ObjC?

Swift classes that inherit `NSObject` or mark members `@objc`/`dynamic` *are*
visible in `ObjC.classes` — hook them the easy way via
[objc-method-hook.md](objc-method-hook.md). Only drop to mangled symbols when the
member is pure Swift.

## Shortest working example — find Swift symbols

```js
const r = new ApiResolver('swift');
for (const m of r.enumerateMatches('*ViewController*')) {
  console.log(m.name + '  @ ' + m.address);      // demangled, human-readable names
}
```

The `swift` ApiResolver matches **demangled** names, so you can search by readable
type/function names instead of raw mangling.

## Hooking a resolved Swift function

```js
const r = new ApiResolver('swift');
const matches = r.enumerateMatches('*LoginService.validate*');
if (matches.length > 0) {
  Interceptor.attach(matches[0].address, {
    onEnter(args) { console.log('[*] entering ' + matches[0].name); },
    onLeave(retval) { console.log('[*] -> ' + retval); }
  });
}
```

## Resolving a mangled symbol by name

If you already have a mangled symbol (e.g. from `nm`/`otool`), find it in its
module and demangle for logging:

```js
const app = Process.enumerateModules()[0];               // main executable
const sym = app.enumerateSymbols().find(s => /validate/.test(s.name));
if (sym) {
  console.log('[*] ' + DebugSymbol.fromAddress(sym.address));
  Interceptor.attach(sym.address, { onEnter() {} });
}
```

## Pitfalls

- **Calling convention is the hard part.** Swift passes `self` in a context
  register and uses its own argument/error registers, not the C ABI. `args[i]`
  won't map cleanly to Swift parameters — read `this.context` registers, and expect
  trial and error. Frida has no full Swift value bridge like `ObjC.Object`.
- **Inlined/generic code has no symbol.** Aggressive optimization and generic
  specialization erase names; you may only find a call site via a backtrace or
  scan.
- **Value types (structs/enums)** are passed by value and are laid out differently
  from ObjC objects — you can't wrap them with `ObjC.Object`.
- **Prefer the `@objc` surface** whenever it exists; pure-Swift hooking is
  best-effort.
- **`ApiResolver('swift')`** availability depends on the target carrying Swift
  metadata; on a stripped binary matches may be sparse.
