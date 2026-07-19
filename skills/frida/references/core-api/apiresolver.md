---
name: apiresolver
description: Glob-search functions and methods in a Frida target with ApiResolver — module exports/imports, Objective-C selectors, and Swift symbols — to find hook targets fast.
---

# ApiResolver: find hook targets by glob

**When:** you know *roughly* what you want to hook ("every `SSL_*` export",
"all `-[NSURL* ...]` methods") but not exact addresses. `ApiResolver` returns
matching `{name, address}` pairs you can feed straight into
[interceptor-attach.md](interceptor-attach.md).

## Shortest working example

```js
const r = new ApiResolver('module');
r.enumerateMatches('exports:libssl.so!SSL_read').forEach(m => {
  console.log(m.name, m.address);
  Interceptor.attach(m.address, { onLeave(retval) { console.log('ret', retval); } });
});
```

## Resolver types

| Type | Query syntax | Matches |
| --- | --- | --- |
| `'module'` | `exports:libc.so!open*` / `imports:app!*` / `sections:...` | native exports/imports/sections across modules |
| `'objc'` | `-[NSURLSession* dataTaskWith*]` or `+[Cls method]` | Objective-C instance/class methods (iOS/macOS) |
| `'swift'` | `functions:*!*doSomething*` | Swift functions (where Swift metadata is present) |

The `objc` resolver needs `ObjC.available`; `swift` needs Swift runtime present.
Both throw on construction when the runtime is missing — guard first.

## Module query grammar

```
exports:MODULEGLOB!SYMBOLGLOB     # e.g. exports:libssl.so!SSL_*
imports:MODULEGLOB!SYMBOLGLOB
sections:MODULEGLOB!SECTIONGLOB
```

`*` is a wildcard; matching is case-insensitive by default. Append `/i`, `/n` flags
after the query to force case-insensitive / non-case-insensitive if needed.

```js
new ApiResolver('module')
  .enumerateMatches('exports:*!malloc')   // malloc in ANY module
  .forEach(m => console.log(m.name, m.address));
```

## Objective-C example

```js
if (ObjC.available) {
  new ApiResolver('objc')
    .enumerateMatches('-[NSURLConnection *]')
    .slice(0, 10)
    .forEach(m => console.log(m.name));
}
```

## Pitfalls

- The resolver **snapshots** available APIs when constructed; create a fresh one
  after new libraries load, or matches for late-loaded modules are missed.
- A too-broad glob (`exports:*!*`) can return thousands of matches and be slow —
  scope the module part whenever possible.
- `m.name` is a descriptive string (e.g. `libssl.so!SSL_read`), not something to
  pass back into `getExportByName`; hook `m.address` directly.
- For Objective-C, prefer this over manual class walking, but the plain
  [module.md](module.md) export lookup is right for C functions.
