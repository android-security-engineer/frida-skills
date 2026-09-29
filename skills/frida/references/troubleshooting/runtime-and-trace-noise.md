---
name: runtime-and-trace-noise
description: Fixes QuickJS-vs-V8 surprises (missing ES features, --runtime=v8) and frida-trace that is too slow or too noisy — narrow the include/exclude globs and edit generated handlers.
---

# Runtime surprises & frida-trace noise

## Symptom

- A script relies on a V8-only feature and behaves oddly, or you want V8's faster
  JIT for a heavy agent.
- `frida-trace` floods the terminal with thousands of calls, or slows the app to a
  crawl.

## Cause

- Frida's **default runtime is QuickJS (QJS)**, not V8. QJS is lighter and starts
  faster but is a different engine; some behavior/perf differs.
- `frida-trace` auto-instruments **every** function matching your `-i` glob and
  logs each call; a broad pattern on a hot library is overwhelming.

## Fix — runtime

Check and, if needed, switch to V8:

```sh
frida -U -n com.example.app -l agent.js --runtime=v8      # opt into V8
```

From JS you can confirm which engine is active:

```js
console.log('runtime =', Script.runtime);    // "QJS" or "V8"
```

Prefer QJS unless you have a concrete reason (a V8-only feature, or a large
compute-heavy agent) — it's the tested default.

## Fix — trace too noisy / too slow

Narrow the target set and combine include (`-i`) with exclude (`-x`) globs:

```sh
# Too broad — floods:
frida-trace -U -n com.example.app -i "*"

# Focused — only the calls you care about:
frida-trace -U -n com.example.app -i "SSL_read" -i "SSL_write"

# Include a family but exclude the hot noise (-x, lowercase, takes FUNCTION globs):
frida-trace -U -n com.example.app -i "recv*" -x "*recvmsg*"

# Android Java methods, one class only:
frida-trace -U -f com.example.app -j "com.example.crypto.*!*"
```

Then **edit the generated handlers** to log only what matters or add a filter.
`frida-trace` writes one JS file per matched function under
`__handlers__/<module>/<function>.js`; edit `onEnter`/`onLeave` there and it
hot-reloads:

```js
// __handlers__/libssl.so/SSL_read.js
onEnter(log, args, state) {
  const n = args[2].toInt32();
  if (n > 256) log('SSL_read len=' + n);   // sample: skip tiny reads
}
```

## Notes

- Delete `__handlers__/` to regenerate handlers from scratch.
- Hot-path tracing can still destabilize the target — see
  [crash-after-hook.md](crash-after-hook.md).
- If handlers never fire at all, the names/timing are wrong:
  [hooks-never-fire.md](hooks-never-fire.md).
