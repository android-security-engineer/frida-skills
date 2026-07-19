---
name: frida-trace-java
description: Use frida-trace -j to trace Android Java/Kotlin methods by class-and-method glob (Class!method), spawning the app so early calls are caught, with editable handler stubs.
---

# `frida-trace -j` — Android Java method tracing

**When:** you want to see which Java/Kotlin methods an Android app calls, and their
arguments, without writing a `Java.perform` agent. Requires a reachable
`frida-server` (root) or a gadget-embedded APK — connect with `-U`.

## Canonical command

```sh
frida-trace -U -f com.example.app -j "com.example.crypto.*!*"
```

`-j` takes a `ClassGlob!methodGlob` pattern. `-f` spawns the app so methods invoked
during startup are captured; `frida-trace` resumes it automatically.

## Glob syntax

The pattern is `CLASSPATTERN!METHODPATTERN`, both accepting `*` wildcards:

```sh
frida-trace -U -f com.example.app -j "*!*login*"          # any class, methods containing "login"
frida-trace -U -f com.example.app -j "javax.crypto.Cipher!*"   # every Cipher method
frida-trace -U -f com.example.app -j "com.example.*!doFinal"   # doFinal in the app's packages
```

Repeat `-j` to trace several patterns in one run.

## Common companion options

| Flag | Meaning |
| --- | --- |
| `-f PACKAGE` | Spawn the app (recommended for Java — catches early calls). |
| `-n NAME` | Attach to a running app instead. |
| `-o trace.log` | Write output to a file. |
| `-U` | Use the USB device. |

## Editing handlers

Matched methods generate stubs under `__handlers__/`. Edit one to log arguments and
the return value; it hot-reloads:

```js
onEnter(log, args, state) {
  log('Cipher.doFinal(' + args[0] + ')');
},
onLeave(log, retval, state) {
  log('  => ' + retval);
}
```

For Java handlers `args`/`retval` are the Java objects/values; call `.toString()` or
index array args as needed.

## Gotchas

- **Classes must be loaded before they can match.** A class loaded later by a custom
  `ClassLoader` may not appear at spawn time; if a pattern matches nothing, let the
  app run to the relevant screen, then attach with `-n` and re-run.
- Overloaded methods are all traced under one pattern — expect multiple hits per name.
- Broad patterns like `*!*` will hook thousands of methods and can ANR the app; scope
  to the app's own package (`com.example.*!*`).
- No device shown by `frida-ls-devices`? The server isn't running — see
  [frida-server-setup.md](frida-server-setup.md).
