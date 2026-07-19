---
name: memory-protect-patchcode
description: Change page permissions and safely patch code in a Frida agent with Memory.protect and Memory.patchCode, which handles write-protection and instruction-cache flushing (Frida 16/17).
---

# Memory.protect and Memory.patchCode — patch code safely

**When:** you want to overwrite instructions or read-only data in the target —
NOP out a check, redirect a branch, or flip a constant that lives on a
non-writable page. Writing to code pages directly throws; these APIs make it safe.

```js
// NOP the first 4 bytes of a function (x86/x64: 0x90 = NOP).
const fn = Process.getModuleByName('libc.so.6').getExportByName('getpid');
Memory.patchCode(fn, 4, code => {
  code.writeByteArray([0x90, 0x90, 0x90, 0x90]);
});
```

`Memory.patchCode(address, size, callback)` maps a temporarily-writable view,
gives your callback a `NativePointer` to write through, then restores protection
**and flushes the CPU instruction cache** — the last step is essential on ARM,
where stale i-cache would otherwise run the old bytes.

## Memory.protect for data

For non-code writable-page needs, change protection directly:

```js
const p = /* NativePointer into a read-only data page */
  Process.getModuleByName('libc.so.6').base;
Memory.protect(p, Process.pageSize, 'rw-');   // make it writable
p.writeU32(0);
```

`Memory.protect(ptr, size, prot)` sets permissions on the page(s) covering the
range. `prot` is a string like `'rwx'`, `'rw-'`, `'r-x'`, `'r--'`. It returns
`true` on success.

## protect vs patchCode

| Task | Use |
| --- | --- |
| Overwrite instructions | `Memory.patchCode` (handles cache flush) |
| Make a data page writable to poke a value | `Memory.protect` |
| Write executable code you generated | `Memory.protect(..., 'rwx')` then write, or use a code writer |

For anything beyond raw bytes — assembling real instructions — use the
arch-specific writers (`X86Writer` on x86/64, `Arm64Writer`/`ThumbWriter` on
ARM); they exist per-architecture, so pick the one matching `Process.arch`.

## Generating and running code

```js
// Allocate RWX memory and drop in an instruction (x64 example: RET = 0xC3).
const code = Memory.alloc(Process.pageSize);
Memory.protect(code, Process.pageSize, 'rwx');
code.writeU8(0xC3);
const fn = new NativeFunction(code, 'void', []);
fn();                                  // calls the RET stub
```

## Pitfalls

- **Never write code bytes without a cache flush on ARM.** Use `Memory.patchCode`;
  a plain `writeByteArray` to a code page (even after `protect`) may execute stale
  instructions on ARM/ARM64.
- **Patch whole instructions.** Overwriting a partial instruction desyncs the
  decoder and crashes — know the instruction length (disassemble with
  [`instruction-disasm.md`](instruction-disasm.md) first).
- **Wrong NOP encoding per arch.** `0x90` is x86 only; ARM64 NOP is
  `1f 20 03 d5`, ARM Thumb is `00 bf`. Match `Process.arch`.
- **W^X / code signing** on iOS and hardened platforms may block `'rwx'`; there
  `patchCode` still works for existing code, but freshly allocated executable
  memory can be restricted (`Process.codeSigningPolicy`).
- Re-protecting too small a range leaves adjacent bytes at the wrong permission —
  size the call to cover every byte you touch.
