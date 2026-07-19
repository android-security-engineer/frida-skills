---
name: patch-instruction
description: Frida agent that scans a module for a byte pattern and rewrites/NOPs the matched instruction in place with Memory.patchCode and an arch-specific writer.
---

# Patch an instruction in memory (NOP / rewrite)

**When:** you know the bytes of an instruction (a conditional branch, a call) and
want to neutralize it — turn a branch into a NOP, or force it never to jump.
`Memory.patchCode` handles the W^X / cache-flush dance for you.

```js
// recipe.js — find a signature and overwrite it. ARM64 example: NOP one instruction.
const mod = Process.getModuleByName('libapp.so');

// Signature bytes from your disassembler (hex, space-separated). Make it unique!
const pattern = '1f 20 03 d5 ?? ?? ?? 94';   // '??' = wildcard byte

const matches = Memory.scan(mod.base, mod.size, pattern, {
  onMatch(address, size) {
    console.log('[*] match at ' + address);
    // Patch the instruction 4 bytes into the match (adjust to your target).
    const insn = address.add(4);
    Memory.patchCode(insn, 4, code => {
      // Arch-specific writer: Arm64Writer on ARM64, X86Writer on x86/64.
      const w = new Arm64Writer(code, { pc: insn });
      w.putNop();          // replace with a no-op
      w.flush();
    });
    console.log('[+] patched (NOP) at ' + insn);
    return 'stop';         // stop after the first match; return nothing to continue
  },
  onComplete() { console.log('[*] scan done'); },
});
```

x86/64 variant — force an unconditional jump instead of NOP:

```js
// Memory.patchCode(addr, 2, code => { const w = new X86Writer(code, { pc: addr });
//   w.putJmpShortLabel('taken'); w.flush(); });   // see X86Writer docs for labels
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- Different arch: use `Arm64Writer`/`ThumbWriter` on ARM, `X86Writer` on x86/64 —
  writers are arch-specific, don't assume one exists everywhere.
- Simpler override with no assembly: if it's a whole function, prefer
  [replace-return-value.md](replace-return-value.md) or
  [short-circuit-function.md](short-circuit-function.md).
- Make the pattern unique — a short signature can match many sites. Widen it or
  first narrow the range; see [scan-memory.md](scan-memory.md).
- Just want to *see* the bytes first? `console.log(hexdump(address, { length: 16 }))`.
