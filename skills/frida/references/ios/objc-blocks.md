---
name: objc-blocks
description: Hooking and creating Objective-C blocks on iOS/macOS with ObjC.Block — intercept completion handlers, read their arguments, and pass a replacement block into native APIs.
---

# ObjC.Block — hook and build completion handlers

**When to use:** an API takes a block (completion handler / callback) and you want
to see what it's called with, or you need to *supply* a block to a native method
from your agent. `ObjC.Block` wraps a block pointer both ways.

Guard with `ObjC.available`; reach the device with `-U`.

## Hooking a block argument

When a block is passed as a method argument, wrap that pointer with
`new ObjC.Block(ptr)` and replace its `.implementation` to intercept invocation:

```js
if (ObjC.available) {
  // -[NSURLSession dataTaskWithURL:completionHandler:]  -> block is args[3]
  const m = ObjC.classes.NSURLSession['- dataTaskWithURL:completionHandler:'];
  Interceptor.attach(m.implementation, {
    onEnter(args) {
      const block = new ObjC.Block(args[3]);
      const original = block.implementation;
      block.implementation = function (data, response, error) {
        // data: NSData*, response: NSURLResponse*, error: NSError*  (NativePointers)
        if (!data.isNull()) {
          const body = new ObjC.Object(data);
          console.log('[*] response bytes = ' + body.length());
        }
        return original(data, response, error);        // call the app's handler
      };
    }
  });
}
```

`ObjC.Block` reads the block's type signature so the replacement receives typed
arguments; wrap object pointers with `ObjC.Object` as usual.

## Creating a block to pass into native code

```js
if (ObjC.available) {
  const handler = new ObjC.Block({
    retType: 'void',
    argTypes: ['object'],                              // e.g. void(^)(NSError*)
    implementation(error) {
      console.log('[*] done, error = ' + (error.isNull() ? 'nil' : new ObjC.Object(error)));
    }
  });

  // pass handler into a method expecting a block:
  ObjC.classes.SomeService.sharedService()
      .performRequestWithCompletion_(handler);
}
```

`retType`/`argTypes` use Frida's ObjC type names: `'void'`, `'object'` (an `id`),
`'int'`, `'bool'`, `'pointer'`, etc. Pass the `ObjC.Block` itself (not `.handle`)
where a block is expected.

## Pitfalls

- **Call the original.** If you replace `block.implementation` and forget to call
  the saved `original(...)`, the app's completion logic never runs and the flow
  hangs.
- **Signature mismatch.** `argTypes` must match the block's real prototype; a wrong
  count or type corrupts the stack. Confirm the signature from the API docs or
  header.
- **Lifetime.** A block you create must stay referenced for as long as native code
  may call it — keep it in a variable at module scope, not a short-lived local, for
  async callbacks.
- **`args` index.** The block is just another argument; remember the `self`/`_cmd`
  offset — see [objc-args-types.md](objc-args-types.md).
