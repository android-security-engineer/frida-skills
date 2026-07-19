---
name: objc-schedule
description: Running Objective-C code on a specific Grand Central Dispatch queue on iOS/macOS with ObjC.schedule, needed for UIKit/main-thread-only APIs called from a Frida callback.
---

# ObjC.schedule — run on the right dispatch queue

**When to use:** you need to call an Objective-C API that *must* run on a
particular thread — most commonly UIKit on the main queue — but you're inside a
Frida callback running on some other thread. `ObjC.schedule(queue, fn)` enqueues
`fn` onto that GCD queue.

Guard with `ObjC.available`; reach the device with `-U`.

## Shortest working example

```js
if (ObjC.available) {
  const mainQueue = ObjC.mainQueue;                    // dispatch_get_main_queue()

  ObjC.schedule(mainQueue, () => {
    // UIKit is main-thread-only: safe to touch here
    const app = ObjC.classes.UIApplication.sharedApplication();
    const alert = ObjC.classes.UIAlertController
      .alertControllerWithTitle_message_preferredStyle_('Frida', 'hooked', 1);
    app.keyWindow().rootViewController().presentViewController_animated_completion_(
      alert, 1, NULL);
  });
}
```

`ObjC.mainQueue` is the main dispatch queue. `ObjC.schedule` returns immediately;
`fn` runs later on that queue.

## Getting a non-main queue

Any `dispatch_queue_t` pointer works. You can capture one from a hook, or create a
serial queue via the C API:

```js
if (ObjC.available) {
  const dispatch_queue_create = new NativeFunction(
    Module.getGlobalExportByName('dispatch_queue_create'),
    'pointer', ['pointer', 'pointer']);
  const q = dispatch_queue_create(Memory.allocUtf8String('com.frida.work'), NULL);

  ObjC.schedule(q, () => console.log('[*] running on custom queue'));
}
```

## Pitfalls

- **Don't do heavy work synchronously on the main queue.** Blocking it freezes the
  UI; keep the scheduled `fn` short.
- **Ordering is async.** Code after `ObjC.schedule(...)` runs before `fn`. Don't
  assume the scheduled work has finished; use a callback/`send()` if you need the
  result.
- **Wrong queue = crash.** Calling UIKit off the main queue can crash the app —
  that's exactly why you schedule. Conversely, scheduling non-UI work needlessly on
  the main queue hurts responsiveness.
- **Exceptions inside `fn`** surface as agent errors on the host `message` handler;
  wrap risky calls in `try/catch` if the app must keep running.
