---
name: recipes-index
description: Index of copy-paste Frida recipe scripts — trace calls, dump buffers/args, patch returns, scan memory, hook crypto, bypass pinning, dump strings, and drive from Python.
---

# Recipes — working scripts for a concrete goal

Each recipe is a complete agent you can run with
`frida -U -f <target> -l recipe.js` (spawn) or `-n <name>` (attach). Copy, adjust
the target name, run. All use Frida 16/17 API.

## Tracing & observation
| Doc | Covers |
| --- | --- |
| [trace-native-call.md](trace-native-call.md) | Log a libc/native function's args, return, and backtrace. |
| [dump-buffer.md](dump-buffer.md) | Hexdump a buffer argument (e.g. `SSL_read`) as it flows. |
| [dump-args-generic.md](dump-args-generic.md) | Generic multi-arg logger with type guesses for any export. |
| [log-string-functions.md](log-string-functions.md) | Trace `strcmp`/`strstr`/`open` to see paths & comparisons. |
| [count-and-time-calls.md](count-and-time-calls.md) | Count calls and measure time spent in a hot function. |

## Modification & patching
| Doc | Covers |
| --- | --- |
| [replace-return-value.md](replace-return-value.md) | Force a function (license/flag check) to return a constant. |
| [patch-instruction.md](patch-instruction.md) | Scan a pattern and NOP/patch bytes with `Memory.patchCode`. |
| [swap-argument.md](swap-argument.md) | Rewrite an argument before the original runs. |
| [short-circuit-function.md](short-circuit-function.md) | Skip a function body entirely via `Interceptor.replace`. |

## Memory & discovery
| Doc | Covers |
| --- | --- |
| [scan-memory.md](scan-memory.md) | Pattern-scan a module's memory for a signature or string. |
| [find-string-refs.md](find-string-refs.md) | Locate a string in memory and who references it. |
| [enumerate-modules-exports.md](enumerate-modules-exports.md) | Dump modules and their exports to find a hook point. |
| [dump-registers-context.md](dump-registers-context.md) | Read CPU registers/context inside a hook. |

## Android
| Doc | Covers |
| --- | --- |
| [android-crypto-capture.md](android-crypto-capture.md) | Dump `Cipher`/`SecretKeySpec` keys and plaintext. |
| [android-ssl-pinning.md](android-ssl-pinning.md) | Multi-path SSL pinning bypass (OkHttp + TrustManager). |
| [android-find-class.md](android-find-class.md) | Search loaded classes/methods by regex at runtime. |
| [android-stacktrace.md](android-stacktrace.md) | Print a Java stack trace from inside a hooked method. |

## iOS
| Doc | Covers |
| --- | --- |
| [ios-log-urls.md](ios-log-urls.md) | Log every NSURL request the app makes. |
| [ios-jailbreak-bypass.md](ios-jailbreak-bypass.md) | Neutralize common jailbreak-detection calls. |

## Host-driven
| Doc | Covers |
| --- | --- |
| [rpc-pull-data.md](rpc-pull-data.md) | Expose `rpc.exports` and pull values from a Python driver. |
| [batch-run-logging.md](batch-run-logging.md) | Run headless, quiet, forever, logging to a file. |

## Advanced scenarios
| Doc | Covers |
| --- | --- |
| [recipe-multi-process-correlate.md](recipe-multi-process-correlate.md) | 同时 hook 多进程并按时间线关联事件。 |
| [recipe-eternalize-persistent.md](recipe-eternalize-persistent.md) | `Script.eternalize()` 让 agent 在断开后存活。 |
| [recipe-remote-cluster.md](recipe-remote-cluster.md) | 经 `-H` 远程连多台设备组成的工作集群批量注入。 |
| [recipe-ci-reproducible.md](recipe-ci-reproducible.md) | 在 CI 中确定性运行 agent：固定版本、固定 seed、断言输出。 |
