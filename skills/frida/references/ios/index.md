---
name: ios-index
description: Index of Frida iOS/Objective-C docs — ObjC.classes, method hooks, ObjC.Object, blocks, jailbreak/SSL-pinning bypass, keychain dumping, Swift, gadget for non-jailbroken devices.
---

# iOS & Objective-C instrumentation

The `ObjC` bridge exists only **on-device**; guard with `ObjC.available`. Reach
the device with `-U` and a jailbreak `frida-server`, or a re-signed app carrying
`frida-gadget` for non-jailbroken testing.

## Objective-C bridge fundamentals
| Doc | Covers |
| --- | --- |
| [objc-classes.md](objc-classes.md) | `ObjC.classes`, finding classes, `$className`, `$methods`. |
| [objc-method-hook.md](objc-method-hook.md) | Hooking `'- selWith:arg:'` via `Interceptor.attach` on `.implementation`. |
| [objc-replace-implement.md](objc-replace-implement.md) | Swapping an implementation with `ObjC.implement`. |
| [objc-object.md](objc-object.md) | `ObjC.Object(ptr)`, calling methods, reading properties, `toString`. |
| [objc-args-types.md](objc-args-types.md) | Reading selectors/args, `self`/`_cmd`, boxing `NSString`/`NSData`. |
| [objc-blocks.md](objc-blocks.md) | Hooking and creating `ObjC.Block`s (completion handlers). |
| [objc-choose.md](objc-choose.md) | `ObjC.choose` to enumerate live instances of a class. |
| [objc-schedule.md](objc-schedule.md) | `ObjC.schedule` to run on a specific dispatch queue. |

## Startup & native
| Doc | Covers |
| --- | --- |
| [ios-spawn-gating.md](ios-spawn-gating.md) | Spawn + early hooks before jailbreak/pinning checks run. |
| [ios-native-hooks.md](ios-native-hooks.md) | Hooking C/`dyld` functions, `libSystem.B.dylib` exports. |
| [swift-interop.md](swift-interop.md) | Instrumenting Swift: mangled names, `ApiResolver('swift')`, limits. |

## Bypasses (authorized testing)
| Doc | Covers |
| --- | --- |
| [jailbreak-detection.md](jailbreak-detection.md) | Defeating file/URL-scheme/fork jailbreak checks. |
| [ssl-pinning-ios.md](ssl-pinning-ios.md) | NSURLSession/AFNetworking/`SecTrustEvaluate` pinning bypass. |
| [ios-debugger-detection.md](ios-debugger-detection.md) | Bypassing `ptrace(PT_DENY_ATTACH)`/`sysctl` anti-debug. |

## Data extraction
| Doc | Covers |
| --- | --- |
| [keychain-dump.md](keychain-dump.md) | Reading Keychain items via `Security` framework calls. |
| [crypto-capture-ios.md](crypto-capture-ios.md) | Hooking `CommonCrypto`/`CryptoKit` to capture keys & plaintext. |
| [gadget-ios.md](gadget-ios.md) | Embedding `frida-gadget` in a re-signed IPA; config modes. |
