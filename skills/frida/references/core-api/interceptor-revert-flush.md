---
name: interceptor-revert-flush
description: Remove Frida hooks with Interceptor.revert and understand when Interceptor.flush must run so pending hook installs/removals actually take effect (Frida 16/17).
---

# Interceptor.revert and flush — removing hooks cleanly

**When:** you want to undo a hook installed with
[`attach`](interceptor-attach.md) or [`replace`](interceptor-replace.md), or you
need a just-installed hook to be active *right now* before you call the target
yourself.

```js
const openPtr = Process.getModuleByName('libc.so.6').getExportByName('open');
const listener = Interceptor.attach(openPtr, {
  onEnter(args) { console.log('open', args[0].readUtf8String()); }
});

// …later, stop this specific hook:
listener.detach();

// Or remove ALL hooks on that address (attach + replace):
Interceptor.revert(openPtr);
```

## Two ways to remove a hook

- **`listener.detach()`** — `Interceptor.attach` returns a listener object; call
  `.detach()` to remove *that* hook only. Best when several hooks share one
  address and you want to keep the others.
- **`Interceptor.revert(target)`** — removes *every* attach/replace hook on
  `target` and restores the original bytes. Use for `Interceptor.replace`, which
  returns no listener.

## Why flush matters

Frida batches hook installs and removals; they are committed at the end of the
current tick, or when you call `Interceptor.flush()`. This matters when, in the
*same* synchronous block, you install (or revert) a hook and then immediately
invoke the target through a [`NativeFunction`](nativefunction.md):

```js
const p = Process.getModuleByName('libc.so.6').getExportByName('getpid');
const getpid = new NativeFunction(p, 'int', []);

Interceptor.replace(p, new NativeCallback(() => 1234, 'int', []));
Interceptor.flush();              // commit the replacement now…
console.log(getpid());            // …so this synchronous call sees 1234
```

Without the `flush()`, the direct call may still hit the original because the
replacement hasn't been committed yet. In normal event-driven code (hooks fire on
their own from later native calls) you rarely need it — Frida flushes between
ticks automatically.

## Key details

- `flush()` applies **all** pending transactions, installs and reverts alike.
- After `Interceptor.revert(target)`, any `NativeFunction` you built over that
  address now reaches the original again.
- Detaching an already-detached listener is harmless; reverting an unhooked
  address is a no-op.
- On script unload Frida reverts your hooks automatically — explicit cleanup is
  for mid-session changes, not shutdown.

## Pitfalls

- **Forgetting flush before a same-tick self-call** is the classic surprise: the
  hook "doesn't work," but it just wasn't committed yet.
- **Reverting the wrong pointer** silently does nothing. Revert the exact address
  you hooked (keep the resolved pointer in a variable).
- If a replacement's [`NativeCallback`](nativecallback.md) was GC'd, reverting
  won't retroactively fix crashes that already happened — keep callbacks alive
  for the hook's whole lifetime.
