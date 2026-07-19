---
name: cmodule
description: Compile C in-process with Frida's CModule for fast native instrumentation callbacks, exposing symbols to JS, with performance benefits and arch/ABI caveats.
---

# CModule: compile C inside the target

**When:** a hook's callback runs so often that bouncing into JS is too slow (hot
`onEnter`, per-instruction Stalker callouts, memory scanners). `CModule` compiles a
C string in-process (via TinyCC) into native code you can call from JS or wire
directly into Interceptor/Stalker — no JS round-trip per event.

## Shortest working example

```js
const cm = new CModule(`
#include <glib.h>
void on_message(const char * text) {
  g_print("native saw: %s\\n", text);
}
`);
const fn = new NativeFunction(cm.on_message, 'void', ['pointer']);
fn(Memory.allocUtf8String('hello from JS'));
```

Every top-level C symbol becomes a NativePointer property on the CModule
(`cm.on_message` above).

## Using it as an Interceptor callback

```js
const cm = new CModule(`
#include <gum/guminterceptor.h>
void onEnter(GumInvocationContext * ic) {
  // runs entirely in native code — no JS per call
}
`);
Interceptor.attach(Process.getModuleByName('libc.so.6').getExportByName('open'), cm);
```

When you pass a CModule (with `onEnter`/`onLeave` symbols) as the second arg to
`Interceptor.attach`, the hook executes natively. Gum headers
(`gum/guminterceptor.h`, `gum/gumstalker.h`) and glib are available inside.

## Passing data in/out

```js
const cm = new CModule(cSource, {
  // JS values injected as symbols the C code can reference:
  counter: Memory.alloc(8),
});
```

The second argument maps names to NativePointers the C sees as `extern` symbols —
use a shared `Memory.alloc` buffer to exchange counters/results with JS, then read
it back through the pointer (see [nativepointer-read.md](nativepointer-read.md)).

## Performance & arch caveats

- The win is eliminating the JS boundary on hot paths; for cold or rare hooks plain
  JS is simpler and fast enough — reach for CModule only when profiling says so.
- Compiled code is **arch/ABI-specific**. The default TinyCC backend targets the
  host arch of the process (arm64/x86_64/…); code with inline asm or struct layout
  assumptions must match `Process.arch`. Test on the real device ABI.
- No libc-of-your-choice: you get the Gum runtime, glib, and a limited header set,
  not the full system SDK. Declare externs for anything else and resolve addresses
  from JS.
- A C crash faults the **target process** with no JS stack — debug with small
  increments and a `Process.setExceptionHandler` (see [process.md](process.md)).
- Free native resources on teardown; `cm.dispose()` releases the module. Symbols
  become invalid afterward.
