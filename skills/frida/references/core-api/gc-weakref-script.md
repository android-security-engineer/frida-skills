---
name: gc-weakref-script
description: Manage agent lifecycle in Frida with Script.bindWeak weak references and cleanup callbacks, Script.runtime detection, and keeping objects alive past script unload.
---

# Script lifecycle: weak refs, runtime, cleanup

**When:** you need a callback to run when a JS object is garbage-collected (to free
a paired native allocation), want to know which JS engine you're on, or must clean
up hooks/resources when the script unloads.

## Which runtime am I on?

```js
console.log(Script.runtime);        // 'QJS' (default) or 'V8'
```

The default is **QuickJS**. Branch on this only if you use an engine-specific
feature; most agent code is identical on both.

## Weak references with cleanup

```js
let obj = { note: 'temporary' };
const id = Script.bindWeak(obj, () => {
  console.log('obj was collected — free its native buffer here');
});
// Later, if you want to run the callback deterministically instead of waiting:
Script.unbindWeak(id);              // triggers the cleanup callback now
obj = null;                         // drop the strong ref; GC may then fire it
```

`Script.bindWeak(value, fn)` registers `fn` to run when `value` is
garbage-collected; it returns an id you can pass to `Script.unbindWeak(id)` to run
the callback immediately. Use it to tie a native `Memory.alloc`/`CModule`
allocation to the lifetime of a JS wrapper so it's freed automatically.

## Running code at script unload

```js
Script.on('unload', () => {
  Interceptor.detachAll();          // remove hooks
  Interceptor.flush();
  // close files/sockets, dispose CModules, etc.
});
```

This fires when the host unloads the script or the session detaches — the place to
release everything you allocated.

## Keeping objects alive past the current call

A NativeCallback or hook you want to survive beyond the function that created it
must stay referenced. Keep it in a module-level variable (or, for long-lived
injected code independent of the script, use `Interceptor`/`Stalker` which retain
their own targets). Don't rely on locals — once out of scope they can be collected
and the native side left dangling.

## Pitfalls

- Weak callbacks fire **non-deterministically** — whenever GC runs, possibly much
  later or not before unload. Use `unbindWeak` when you need timing, and always add
  a `Script.on('unload')` net so nothing leaks.
- QuickJS and V8 collect on different schedules; don't assume a weak callback runs
  promptly on either.
- Inside a weak/cleanup callback the object is already gone — capture what you need
  (the native pointer to free) at bind time, not from the dead object.
- Forgetting to detach hooks/close resources on unload can crash or destabilize the
  target on the next load; make `Script.on('unload')` a habit.
