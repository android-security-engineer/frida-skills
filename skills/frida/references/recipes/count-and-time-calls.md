---
name: count-and-time-calls
description: Frida agent that counts invocations of a hot function and measures wall-clock time spent inside it, reporting totals periodically — cheap profiling without a profiler.
---

# Count and time calls

**When:** a function is called a lot and you want throughput/latency without
flooding the log per-call. Aggregate counts and elapsed time, print a summary on
an interval.

```js
// recipe.js — count calls and sum time spent inside a target function.
const MODULE = 'libc.so.6';
const SYMBOL = 'malloc';

let calls = 0;
let totalNs = 0;   // nanoseconds accumulated across all calls

const target = Process.getModuleByName(MODULE).getExportByName(SYMBOL);
Interceptor.attach(target, {
  onEnter() {
    this.t0 = Process.getCurrentThreadId(); // touch this so it persists
    this.start = Date.now();
  },
  onLeave() {
    totalNs += (Date.now() - this.start) * 1e6;
    calls++;
  },
});

setInterval(() => {
  const avgUs = calls ? (totalNs / calls) / 1000 : 0;
  console.log(`[${SYMBOL}] calls=${calls}  total=${(totalNs / 1e6).toFixed(1)}ms  avg=${avgUs.toFixed(2)}us`);
}, 2000);

console.log(`[+] counting ${MODULE}!${SYMBOL} (summary every 2s)`);
```

Run it:

```sh
frida -U -f com.example.app -l recipe.js
frida -n myprocess -l recipe.js
```

**Tweak this:**
- `Date.now()` is millisecond-resolution; for sub-microsecond functions the timing
  is noise — trust the **count**, treat the time as a rough aggregate.
- Per-thread breakdown: key the counters by `Process.getCurrentThreadId()` in a map.
- Want the highest-frequency callers instead of one function? Hook broadly and tally
  `Thread.backtrace(this.context, Backtracer.ACCURATE)[0]` per call site.
- Reset counters each interval to see rate rather than cumulative totals.
- The `setInterval` keeps the agent alive; run headless with
  [batch-run-logging.md](batch-run-logging.md).
