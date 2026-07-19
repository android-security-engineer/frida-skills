---
name: android-index
description: Index of Frida Android/Java docs — Java.perform, Java.use, overloads, spawn gating, classloaders, SSL pinning and root/debugger detection bypass, native JNI hooks, ART internals.
---

# Android & Java instrumentation

The `Java` bridge only exists **on-device**; guard with `Java.available` and do
all class work inside `Java.perform(() => { ... })`. Reach the device with `-U`
and a matching `frida-server` (or an APK carrying `frida-gadget`).

## Java bridge fundamentals
| Doc | Covers |
| --- | --- |
| [java-perform.md](java-perform.md) | Why every Java op needs `Java.perform`; main-thread vs `performNow`. |
| [java-use-hook.md](java-use-hook.md) | `Java.use`, replacing `.implementation`, calling the original. |
| [java-overloads.md](java-overloads.md) | Resolving `.overload(...)` by signature; the ambiguity error. |
| [java-constructors.md](java-constructors.md) | Hooking `$init`, creating objects with `$new`, `$dispose`. |
| [java-fields.md](java-fields.md) | Reading/writing instance & static fields; `.value`, name clashes. |
| [java-enumerate.md](java-enumerate.md) | `enumerateLoadedClasses`, `enumerateMethods`, finding what to hook. |
| [java-choose.md](java-choose.md) | `Java.choose` to grab live instances off the heap. |
| [java-cast-array.md](java-cast-array.md) | `Java.cast`, `Java.array`, boxing, `[B` byte arrays, strings. |
| [java-classloaders.md](java-classloaders.md) | Multiple classloaders, dynamically loaded/DEX classes, `Java.openClassFile`. |
| [java-registerclass.md](java-registerclass.md) | `Java.registerClass` to implement interfaces (e.g. a trust manager). |
| [java-reflection.md](java-reflection.md) | Reflection through Frida, generics, inner/anonymous classes. |

## Startup & targeting
| Doc | Covers |
| --- | --- |
| [spawn-gating.md](spawn-gating.md) | Spawn + hook-before-run so early checks are caught; `%resume`. |
| [enumerate-app.md](enumerate-app.md) | Package name, main activity, `frida-ps -Uai`, identifying targets. |
| [early-instrumentation.md](early-instrumentation.md) | Hooking `Application.onCreate`/classloader before app code runs. |

## Native side on Android
| Doc | Covers |
| --- | --- |
| [jni-hooks.md](jni-hooks.md) | Hooking native libs (`.so`) and JNI entry points from Java. |
| [system-loadlibrary.md](system-loadlibrary.md) | Catch `System.loadLibrary`/`dlopen` to hook a lib as it loads. |
| [art-internals.md](art-internals.md) | ART method structure, `Java.vm`, `getEnv`, when the bridge isn't enough. |

## Bypasses (authorized testing)
| Doc | Covers |
| --- | --- |
| [ssl-pinning-okhttp.md](ssl-pinning-okhttp.md) | OkHttp `CertificatePinner` and interceptor pinning bypass. |
| [ssl-pinning-trustmanager.md](ssl-pinning-trustmanager.md) | `SSLContext`/`X509TrustManager` trust-all bypass. |
| [ssl-pinning-native.md](ssl-pinning-native.md) | Native/BoringSSL pinning and Conscrypt-level bypass. |
| [root-detection.md](root-detection.md) | Defeating common root checks (su, packages, props, mounts). |
| [debugger-detection.md](debugger-detection.md) | Defeating `isDebuggerConnected`/tracerpid/ptrace checks. |
| [frida-detection.md](frida-detection.md) | Anti-Frida checks (port/maps/thread names) and evasion. |
| [emulator-detection.md](emulator-detection.md) | Bypassing emulator/qemu fingerprint checks. |
| [biometric-bypass.md](biometric-bypass.md) | Neutering `BiometricPrompt`/keyguard result checks. |

## Data extraction
| Doc | Covers |
| --- | --- |
| [crypto-capture.md](crypto-capture.md) | Hooking `Cipher`/`Mac`/`SecretKeySpec` to dump keys & plaintext. |
| [webview-hooks.md](webview-hooks.md) | Instrumenting `WebView`, JS bridges, URL loads. |
| [shared-prefs-sqlite.md](shared-prefs-sqlite.md) | Reading SharedPreferences and app SQLite at runtime. |
