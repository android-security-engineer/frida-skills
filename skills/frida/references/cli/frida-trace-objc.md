---
name: frida-trace-objc
description: Use frida-trace -m to trace Objective-C selectors on iOS/macOS by class-and-selector glob, catching method calls with editable handler stubs — zero-code recon for Apple apps.
---

# `frida-trace -m` — Objective-C selector tracing

**When:** you want to see which Objective-C methods an iOS/macOS app invokes and
their arguments, without writing an agent. On iOS this needs a jailbreak
`frida-server` or a re-signed gadget — connect with `-U`.

## Canonical command

```sh
frida-trace -U -f com.apple.mobilesafari -m "-[NSURLRequest *]"
```

`-m` takes an Objective-C method pattern using the standard `±[Class selector]`
syntax with `*` wildcards. `-` = instance method, `+` = class method.

## Method-pattern syntax

```sh
frida-trace -U -n MyApp -m "-[NSURL* *]"              # any NSURL* class, any selector
frida-trace -U -n MyApp -m "+[NSString stringWith*]"  # class methods on NSString
frida-trace -U -n MyApp -m "-[* initWith*]"           # all initWith… selectors
```

Repeat `-m` for several patterns. Combine with native `-i`/`-x` in the same run.

## Common options

| Flag | Meaning |
| --- | --- |
| `-m PATTERN` | Include an Objective-C method pattern (repeatable). |
| `-f PROGRAM` | Spawn the app instead of attaching. |
| `-n NAME` | Attach to a running app by name. |
| `-o trace.log` | Write output to a file. |
| `-U` | Use the USB device. |

## Editing handlers

Matched selectors create stubs under `__handlers__/`. Edit to inspect arguments;
for ObjC, `args[0]` is `self`, `args[1]` is the selector (`_cmd`), real arguments
start at `args[2]`:

```js
onEnter(log, args, state) {
  log('URL = ' + new ObjC.Object(args[2]).toString());
},
onLeave(log, retval, state) {
  log('  => ' + new ObjC.Object(retval).toString());
}
```

## Gotchas

- Wrap object pointers in `ObjC.Object(ptr)` before calling `.toString()` — raw
  `args[i]` are NativePointers.
- Very broad patterns (`-[* *]`) hook enormous numbers of selectors and will stall
  the UI; scope to a class family.
- Classes from a framework not yet loaded won't match at spawn; drive the app to the
  relevant screen, attach with `-n`, and re-run.
- Simulator apps run on the host — use the local device (no `-U`) for those.
