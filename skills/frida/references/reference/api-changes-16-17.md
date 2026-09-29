---
name: api-changes-16-17
description: Complete table of Frida API removed/renamed/moved between 16 and 17 with the exact replacement call, cross-linked to troubleshooting and migration docs.
type: leaf
---

# Frida 16 → 17 API changes

Verified against 17.15.3. This is the **quick reference**; the migration
walkthrough with before/after agent code lives in
[../guides/version-migration-16-to-17.md](../guides/version-migration-16-to-17.md).

## Change table

Each row: what was removed (16) → the 17 replacement.

| Removed (16) | Replacement (17) | Notes |
| --- | --- | --- |
| `Module.getExportByName(mod, exp)` | `Process.getModuleByName(mod).getExportByName(exp)` | throws if module absent |
| `Module.findExportByName(mod, exp)` | `Process.getModuleByName(mod).findExportByName(exp)` or `Module.getGlobalExportByName(exp)` | latter searches all modules |
| `Memory.readUtf8String(ptr)` | `ptr.readUtf8String()` | instance method on NativePointer |
| `Memory.writeU32(ptr, v)` | `ptr.writeU32(v)` | same for all read/write families |
| NativeFunction `'int'` return treated as NativePointer | plain JS **number** | no `.toInt32()` on it; Interceptor `retval` stays NativePointer |
| default runtime V8 | default **QuickJS** | `--runtime=v8` to switch |

## Why each changed

### Static Module helpers are gone

The old `Module.getExportByName(mod, exp)` was a global lookup that *guessed*
the module. In 17 you must be explicit about which module instance you mean:

```js
// 16 (removed):
// Module.getExportByName('libc.so.6', 'open')

// 17 — module instance first:
Process.getModuleByName('libc.so.6').getExportByName('open');

// 17 — search every module when you truly mean "any":
Module.getGlobalExportByName('open');
```

`findExportByName` follows the same rule and returns `null` instead of
throwing when the symbol is absent.

### Memory free-functions moved onto NativePointer

The standalone `Memory.readUtf8String(ptr)` / `Memory.writeU32(ptr, v)` family
is removed; every read/write is now a method on the pointer itself:

```js
// 16 (removed):
// Memory.readUtf8String(addr)
// Memory.writeU32(addr, 42)

// 17:
addr.readUtf8String();
addr.writeU32(42);
```

The full read/write family — `readU8/16/32/64`, `readS8/16/32/64`, `readByteArray`,
`readUtf8String`, `writeU8/16/32/64`, `writeByteArray`, `writeUtf8String` — all
moved the same way. A stale `Memory.` prefix is the #1 "TypeError: X is not a
function" in 17; see
[../troubleshooting/stale-removed-api.md](../troubleshooting/stale-removed-api.md).

### NativeFunction `'int'` returns are plain numbers

In 17 an `'int'` return is a JS `number`, not a `NativePointer` — call
`.toInt32()` on it and you get "toInt32 is not a function". Interceptor
`onLeave`'s `retval` is **still** a NativePointer (so `retval.replace(x)` is
unchanged). See [../troubleshooting/nativefunction-return.md](../troubleshooting/nativefunction-return.md).

### Default runtime is now QuickJS

Frida 16 still shipped V8 by default on many platforms; 17 defaults to
**QuickJS** — lighter, faster start, but a different engine (no full ES2020+
V8-only features by default). Opt in with `--runtime=v8` when you need V8's
JIT or a V8-only feature:
[../troubleshooting/runtime-and-trace-noise.md](../troubleshooting/runtime-and-trace-noise.md).

## Upgrade checklist

When moving a 16-era agent to 17, grep for these patterns and fix each:

1. `Module.getExportByName(` / `Module.findExportByName(` → instance or
   `getGlobalExportByName` form.
2. `Memory.readUtf8String(` / `Memory.readU*/write*` free calls → pointer methods.
3. `retval.toInt32()` after a NativeFunction `'int'` return → use the number
   directly.
4. A V8-only feature (e.g. optional chaining is fine, but heavier ES features
   or `SharedArrayBuffer`) → consider `--runtime=v8` or port to QJS-safe code.

## Cross-links

- Migration walkthrough: [../guides/version-migration-16-to-17.md](../guides/version-migration-16-to-17.md)
- Symptom fix: [../troubleshooting/stale-removed-api.md](../troubleshooting/stale-removed-api.md),
  [../troubleshooting/nativefunction-return.md](../troubleshooting/nativefunction-return.md)
- Authoritative facts: `skills/frida/AUTHORING.md` ("Frida 16/17 API facts" section)
