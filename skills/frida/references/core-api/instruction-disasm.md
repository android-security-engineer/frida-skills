---
name: instruction-disasm
description: Disassemble machine code at an address in a Frida agent with Instruction.parse — read mnemonics, operands, and instruction size to step through code or locate patch sites.
---

# Instruction.parse: disassemble at an address

**When:** you need to understand or navigate code at a specific address — find the
length of an instruction before patching, walk a function, confirm what's at a
scan hit, or locate a `bl`/`call` to redirect.

## Shortest working example

```js
const addr = Process.getModuleByName('libssl.so').getExportByName('SSL_read');
const insn = Instruction.parse(addr);
console.log(insn.address, insn.mnemonic, insn.opStr);   // e.g. "0x... stp x29, x30, ..."
console.log('length', insn.size, 'next', insn.next);
```

## Walking instructions

```js
let cursor = Process.getModuleByName('libssl.so').getExportByName('SSL_read');
for (let i = 0; i < 8; i++) {
  const insn = Instruction.parse(cursor);
  console.log(insn.address, insn.mnemonic, insn.opStr);
  cursor = insn.next;                 // advance by this instruction's size
}
```

`Instruction.parse(ptr)` returns an object with:

| Field | Meaning |
| --- | --- |
| `.address` | where it was decoded (NativePointer) |
| `.mnemonic` | `'mov'`, `'bl'`, `'stp'`, … |
| `.opStr` | operand text as a string |
| `.size` | byte length of this instruction |
| `.next` | pointer to the following instruction |
| `.toString()` | full formatted line |

The underlying disassembler is Capstone; deeper per-arch operand details are
available via the arch-specific instruction subtype (e.g. register/immediate
operand lists) when present.

## Pitfalls

- **Read permission required.** Parsing at an unmapped or execute-only address can
  fault; ensure the region is readable (see
  [process-ranges.md](process-ranges.md)).
- On ARM, Thumb vs. ARM decoding depends on the address's mode bit; parse at the
  correct (thumb-tagged if applicable) address or mnemonics will be garbage.
- `size` is what to use for safe patch windows — with
  [memory-protect-patchcode.md](memory-protect-patchcode.md), never overwrite fewer
  bytes than a full instruction.
- To *emit* or relocate instructions (not just read them) you need the
  **arch-specific** writers/relocators (`Arm64Writer`/`X86Writer`,
  `X86Relocator`…), which only exist for the matching `Process.arch`.
- Parsing is per-instruction and cheap, but a tight loop over a large region still
  adds up — bound it.
