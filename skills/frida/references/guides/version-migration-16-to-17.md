---
name: version-migration-16-to-17
description: Migrating Frida 16 agents to 17 — the full removed/renamed API table, automatic rewrite rules, and a compatibility shim for code you can't change.
type: summary
---

# Frida 16 → 17 migration

Frida 17 removed several static helpers and changed return mappings. This is
the migration map. Full per-API detail in
[../reference/api-changes-16-17.md](../reference/api-changes-16-17.md).

## What changed

这张图回答："一段 16 时代的 agent 改到 17，要走的判断路径？"

```mermaid
flowchart TD
  C["16-era code"] --> Q{"uses Module.getExportByName / findExportByName static?"}
  Q -->|"yes"| R1["→ Process.getModuleByName(name).getExportByName(x)\n   or Module.getGlobalExportByName(x)"]
  Q -->|"no"| Q2{"uses Memory.readX/writeX free fns?"}
  Q2 -->|"yes"| R2["→ ptr.readX()/ptr.writeX() (instance methods)"]
  Q2 -->|"no"| Q3{"treats NativeFunction 'int' return as NativePointer?"}
  Q3 -->|"yes"| R3["→ it's a plain JS number; drop .toInt32()\n   (Interceptor retval stays NativePointer)"]
  Q3 -->|"no"| OK["compatible as-is"]
```

## Rewrite table (most common)

| 16 (removed) | 17 replacement |
| --- | --- |
| `Module.getExportByName('libc.so.6','open')` | `Process.getModuleByName('libc.so.6').getExportByName('open')` |
| `Module.findExportByName(...)` | `Process.getModuleByName(name).findExportByName(x)` or `Module.getGlobalExportByName(x)` |
| `Memory.readUtf8String(ptr)` | `ptr.readUtf8String()` |
| `Memory.writeU32(ptr, v)` | `ptr.writeU32(v)` |
| assuming `new NativeFunction(p,'int',[])(...)` is a NativePointer | it's a plain `number`; compare directly |

## Compatibility shim (for code you can't edit)

If you must run un-modified 16-era agents on 17, prepend this shim at the top
of the script — it re-exports the static helpers as thin wrappers:

```javascript
// 16→17 compat shim — re-adds removed static Module helpers
Module.getExportByName = function (modName, exp) {
  return Process.getModuleByName(modName).getExportByName(exp);
};
Module.findExportByName = function (modName, exp) {
  const m = Process.findModuleByName(modName);
  return m ? m.findExportByName(exp) : null;
};
// Memory.read*/write* free functions have NO shim — rewrite to ptr methods.
```

## Pitfalls

- The shim covers `Module.*` statics but **not** `Memory.readX/writeX` — those
  must be rewritten to pointer methods (there's no safe global to rebind).
- `retval.toInt32()` is still valid on `Interceptor` retvals; don't "fix" it.
- See [../troubleshooting/stale-removed-api.md](../troubleshooting/stale-removed-api.md)
  and [../troubleshooting/nativefunction-return.md](../troubleshooting/nativefunction-return.md).
