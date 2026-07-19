---
name: find-string-refs
description: Frida agent that locates a string in a module's memory then scans code ranges for pointers that reference it, revealing which code uses the string.
---

# Find a string and who references it

**When:** you found an interesting string ("license invalid", a URL, a key name)
and want the *code* that uses it. First locate the string bytes, then scan for a
pointer-sized value equal to that address.

```js
// recipe.js — locate a string, then find code that points at it.
const mod = Process.getModuleByName('libapp.so');
const needle = 'license invalid';

// 1) Find the string bytes in the module.
const strPattern = Array.from(needle)
  .map(c => c.charCodeAt(0).toString(16).padStart(2, '0')).join(' ');
const hits = Memory.scanSync(mod.base, mod.size, strPattern);
if (hits.length === 0) { console.log('[-] string not found'); }

hits.forEach(hit => {
  const strAddr = hit.address;
  console.log(`[+] string "${needle}" at ${strAddr} (+0x${strAddr.sub(mod.base).toString(16)})`);

  // 2) Build a pointer-width byte pattern from that address and scan code ranges.
  const bytes = [];
  for (let i = 0; i < Process.pointerSize; i++) {
    bytes.push(strAddr.shr(8 * i).and(0xff).toString(16).padStart(2, '0'));  // little-endian
  }
  const ptrPattern = bytes.join(' ');

  Memory.scan(mod.base, mod.size, ptrPattern, {
    onMatch(ref) {
      console.log(`    referenced from ${ref} -> ${DebugSymbol.fromAddress(ref)}`);
    },
    onComplete() {},
  });
});
console.log('[*] done');
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- This finds *absolute* pointer references (data/GOT-style). ARM often builds string
  addresses with `adrp`+`add` immediates, not a stored pointer — in that case fall
  back to a disassembler and hook the resulting function by offset (see
  [replace-return-value.md](replace-return-value.md)).
- Endianness: the loop above is little-endian (ARM/x86). Fine on Android/iOS.
- `DebugSymbol.fromAddress` gives a name only if symbols exist; otherwise you get
  `module!0xoffset`, still enough to hook.
- Just want the string location, not references? Use [scan-memory.md](scan-memory.md).
