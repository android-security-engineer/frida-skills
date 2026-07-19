---
name: api-changes-16-17
description: Complete table of Frida API removed/renamed/moved between 16 and 17 with the exact replacement call, cross-linked to troubleshooting and migration docs.
type: summary
---

# Frida 16 → 17 API changes

Verified against 17.15.3. Each row: what was removed → the 17 replacement.

| Removed (16) | Replacement (17) | Notes |
| --- | --- | --- |
| `Module.getExportByName(mod, exp)` | `Process.getModuleByName(mod).getExportByName(exp)` | throws if module absent |
| `Module.findExportByName(mod, exp)` | `Process.getModuleByName(mod).findExportByName(exp)` or `Module.getGlobalExportByName(exp)` | latter searches all modules |
| `Memory.readUtf8String(ptr)` | `ptr.readUtf8String()` | instance method on NativePointer |
| `Memory.writeU32(ptr, v)` | `ptr.writeU32(v)` | same for all read/write families |
| NativeFunction `'int'` return treated as NativePointer | plain JS **number** | no `.toInt32()` on it; Interceptor `retval` stays NativePointer |
| (assumption) default runtime V8 | default **QuickJS** | `--runtime=v8` to switch |

## Cross-links

- Migration walkthrough: [../guides/version-migration-16-to-17.md](../guides/version-migration-16-to-17.md)
- Symptom fix: [../troubleshooting/stale-removed-api.md](../troubleshooting/stale-removed-api.md),
  [../troubleshooting/nativefunction-return.md](../troubleshooting/nativefunction-return.md)
- Authoritative facts: `skills/frida/AUTHORING.md` ("Frida 16/17 API facts" section)
