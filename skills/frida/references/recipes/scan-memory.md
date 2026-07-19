---
name: scan-memory
description: Frida agent that pattern-scans a module's memory (or a writable range) for a byte signature or string using Memory.scan, printing each match address.
---

# Pattern-scan memory for a signature or string

**When:** you need to find where a byte sequence, magic value, or string lives in
memory — to hook it, patch it, or confirm it's loaded. `Memory.scan` walks a range
asynchronously; `Memory.scanSync` returns an array.

```js
// recipe.js — scan a module for a hex signature (?? = wildcard byte).
const mod = Process.getModuleByName('libapp.so');
const pattern = 'de ad be ef ?? ?? 00 01';

Memory.scan(mod.base, mod.size, pattern, {
  onMatch(address, size) {
    console.log(`[+] match at ${address} (+0x${address.sub(mod.base).toString(16)})`);
    console.log(hexdump(address, { length: 32, ansi: false }));
  },
  onComplete() { console.log('[*] scan complete'); },
});
```

Scan for a UTF-8 string across all writable regions (not just one module):

```js
// recipe-str.js — convert a string to a hex pattern, scan every rw- range.
const needle = 'FLAG{';
const pattern = Array.from(needle).map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join(' ');

for (const range of Process.enumerateRanges('rw-')) {
  Memory.scanSync(range.base, range.size, pattern).forEach(m => {
    console.log(`${m.address}: ${m.address.readUtf8String()}`);
  });
}
console.log('[*] done');
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- `Memory.scan` (async, callback) vs `Memory.scanSync` (blocking, returns
  `[{address, size}]`) — use sync for small ranges, async for large ones.
- Narrow the range to avoid slow full-process scans: pick one module, or filter
  `Process.enumerateRanges('r-x')` for code, `'rw-'` for data.
- Make signatures unique — short patterns match everywhere. Widen or anchor them.
- Found the site and want to patch it? See [patch-instruction.md](patch-instruction.md).
- Looking for who *references* a string, not just where it is? See
  [find-string-refs.md](find-string-refs.md).
