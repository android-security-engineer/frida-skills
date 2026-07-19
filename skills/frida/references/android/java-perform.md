---
name: java-perform
description: Explains why every Android Java operation must run inside Java.perform, guarded by Java.available, plus performNow, the main thread, and re-entrancy.
---

# Java.perform — the gate for all Java work

**When to use:** always, before touching any Java class, method, or field on
Android. The `Java` bridge attaches the current native thread to the ART VM and
only exposes classes once inside `Java.perform`. Calling `Java.use` (or anything
Java) outside it throws or crashes.

## Shortest working example

```js
if (Java.available) {
  Java.perform(() => {
    const System = Java.use('java.lang.System');
    System.exit.overload('int').implementation = function (code) {
      console.log('[*] blocked System.exit(' + code + ')');
    };
  });
} else {
  console.log('[!] Java VM not present — not an Android/ART process');
}
```

Run it with a reachable device: `frida-server` (root, matching ABI+version) or an
APK carrying `frida-gadget`, connected with `-U`:

```sh
frida -U -f com.example.app -l agent.js
```

## Why the guard and the wrapper both matter

- `Java.available` is `true` only in a process that hosts an ART/Dalvik VM. On
  Linux/iOS/Windows it is `false`; guarding avoids a hard error at load time.
- `Java.perform(fn)` schedules `fn` on a VM-attached thread and detaches when it
  returns. Every `Java.use`, `Java.choose`, `Java.cast`, field access, `$new`,
  and `$init` must happen inside that callback.
- Hooks installed inside `Java.perform` **stay installed** after the callback
  returns — the callback is setup, not a loop. Your `implementation` closures fire
  later, on whatever app thread calls the method.

## Java.perform vs Java.performNow

- `Java.perform(fn)` — enqueues `fn`; safe from any context, runs as soon as the
  VM thread is ready. Preferred for agent top-level code.
- `Java.performNow(fn)` — runs `fn` synchronously on the current thread if it can
  attach immediately. Use only when you need the result before the next line and
  you know the VM is up.

You may nest calls or call `Java.perform` again from inside a hook; each attaches
as needed. Frida caches the wrappers, so repeated `Java.use('same.Class')` is cheap.

## Pitfalls

- **Hooking too early.** If the target class is loaded later (dynamic DEX, a
  plugin classloader), `Java.use` throws `ClassNotFoundException` even inside
  `Java.perform`. See [java-classloaders.md](java-classloaders.md) and
  [early-instrumentation.md](early-instrumentation.md).
- **Calling Java from a raw Interceptor callback.** Native `onEnter`/`onLeave`
  run on an arbitrary, possibly non-attached thread. Wrap any Java access there in
  `Java.perform(() => { ... })` before using the bridge.
- **Assuming the callback blocks the app.** It does not; the app keeps running.
  Install hooks, then return.
- **Forgetting the availability guard.** An agent meant to run on multiple
  platforms must branch on `Java.available`, or it dies on the first non-Android
  target.
- **Doing heavy synchronous work inside performNow on a UI thread** can ANR the
  app. Keep hook installation fast; defer analysis to the fired callbacks.
