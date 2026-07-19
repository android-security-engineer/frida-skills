---
name: dump-registers-context
description: Frida agent that reads CPU registers and the thread context inside an Interceptor hook, printing arch-specific register values for debugging.
---

# Read CPU registers / context inside a hook

**When:** you're at a hook point and need raw register state — because arguments
aren't in the usual slots, or you're mid-function at a patched address and want to
inspect the machine state.

```js
// recipe.js — dump registers on entry. this.context holds the CpuContext.
const mod = Process.getModuleByName('libapp.so');
const target = mod.getExportByName('process');   // or mod.base.add(0xoffset)

Interceptor.attach(target, {
  onEnter(args) {
    const ctx = this.context;                     // CpuContext for this thread
    console.log(`[*] pc=${ctx.pc}  sp=${ctx.sp}`); // pc/sp exist on every arch

    if (Process.arch === 'arm64') {
      // ARM64 integer args: x0..x7. General regs x0..x28, plus fp, lr.
      console.log(`  x0=${ctx.x0}  x1=${ctx.x1}  x2=${ctx.x2}  x3=${ctx.x3}`);
      console.log(`  lr=${ctx.lr}  fp=${ctx.fp}`);
    } else if (Process.arch === 'x64') {
      // x86-64 SysV args: rdi, rsi, rdx, rcx, r8, r9.
      console.log(`  rdi=${ctx.rdi}  rsi=${ctx.rsi}  rdx=${ctx.rdx}  rax=${ctx.rax}`);
    } else if (Process.arch === 'arm') {
      console.log(`  r0=${ctx.r0}  r1=${ctx.r1}  r2=${ctx.r2}  r3=${ctx.r3}`);
    } else if (Process.arch === 'ia32') {
      console.log(`  eax=${ctx.eax}  ecx=${ctx.ecx}  edx=${ctx.edx}`);
    }
  },
});
console.log('[+] hooked; arch=' + Process.arch);
```

Registers are NativePointers — you can read what they point at, or overwrite them:

```js
// Inside onEnter: read a buffer that x1 points to, then modify x0.
// console.log(hexdump(this.context.x1, { length: 32 }));
// this.context.x0 = ptr(0);   // writing back into context changes the register
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js      # spawn
frida -n myprocess -l recipe.js               # attach by name
```

**Tweak this:**
- Register names are arch-specific — guard with `Process.arch` as above; don't
  assume `x0`/`rdi` exist everywhere.
- Context values are NativePointers: `.readUtf8String()`, `.readPointer()`, `.add()`
  all work; assigning back into `this.context.<reg>` updates the real register.
- Also available on `this`: `.returnAddress`, `.threadId`, `.errno`/`.lastError`.
- Want a symbolized call stack instead of raw regs? See
  [trace-native-call.md](trace-native-call.md) (`Thread.backtrace`).
