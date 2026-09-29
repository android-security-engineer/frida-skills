# Frida 学习站

> 从概念、核心 API、CLI 到 Android / iOS 实战 —— 一个围绕 **Frida 动态插桩**（dynamic instrumentation）的系统化学习知识库。

本网站由 [`android-security-engineer/frida-skills`](https://github.com/android-security-engineer/frida-skills)
仓库的知识库直接渲染而来：172 篇文档覆盖概念、API、工具与完整实战流程，
即一份**给 AI Agent 用的渐进式知识库**，也是**给人类学习者的完整教程**。

---

## 从哪开始

按下面 5 步走完，你会从零建立 Frida 的完整心智模型：

!!! tip "最小闭环"
    ```sh
    pip install frida frida-tools
    frida-ps -U                # 看到设备上的进程 → 环境就绪
    frida-trace -U -i "open*"  # 零代码追踪调用，最快找到感觉
    ```

| 步骤 | 学什么 | 入口 |
| --- | --- | --- |
| 1️⃣ 建立心智模型 | Frida 怎么工作：注入、server/gadget、host/agent 分工 | [概念 Concepts](references/concepts/index.md) |
| 2️⃣ 掌握核心 API | 在目标进程里跑 JS：Interceptor、NativeFunction、Memory、Module… | [核心 API Core API](references/core-api/index.md) |
| 3️⃣ 驱动命令行 | 不写绑定也能干活：`frida`、`frida-trace`、`frida-ps` | [CLI 工具](references/cli/index.md) |
| 4️⃣ 平台实战 | Android/Java 与 iOS/ObjC 的 hook、绕过检测 | [Android](references/android/index.md) · [iOS](references/ios/index.md) |
| 5️⃣ 抄作业与排障 | 拿来即用的脚本、完整演练、出错了查这里 | [配方](references/recipes/index.md) · [排障](references/troubleshooting/index.md) |

---

## 知识库地图

按主题浏览全部内容：

<div class="grid cards" markdown>

- **🧠 概念 Concepts** — [索引](references/concepts/index.md)
    Frida 架构、注入模型、frida-server vs gadget、消息协议、运行时、spawn gating、内存模型。

- **⚙️ 核心 API Core API** — [索引](references/core-api/index.md)
    Agent 端 JavaScript API 全解：Interceptor、NativeFunction、Memory、Module、Stalker、rpc。

- **💻 CLI 工具** — [索引](references/cli/index.md)
    不写绑定直接干活：`frida` REPL、`frida-trace`、`frida-ps`、`frida-ls-devices`、`frida-apk`。

- **🤖 Android 实战** — [索引](references/android/index.md)
    Java 层 hook、spawn gating、SSL pinning / root / 反调试 / 反 Frida 绕过、WebView、biometric。

- **🍎 iOS 实战** — [索引](references/ios/index.md)
    Objective-C 方法 hook、blocks、越狱检测绕过、pinning、Keychain、gadget 集成。

- **🧩 配方 Recipes** — [索引](references/recipes/index.md)
    针对具体目标的复制即用脚本：追踪、dump、改返回值、内存扫描、批量日志。

- **📚 指南 Guides** — [索引](references/guides/index.md)
    端到端工作流：Python/Node/TypeScript 绑定、agent 结构、编译、错误处理、CI。

- **🎯 演练手册 Playbooks** — [索引](references/playbooks/index.md)
    完整攻防演练：recon → hook → verify，Android/iOS/加密密钥提取。

- **📑 参考表 Reference** — [索引](references/reference/index.md)
    平台差异矩阵、16→17 API 变更、全局变量速查、术语表。

- **🔧 排障 Troubleshooting** — [索引](references/troubleshooting/index.md)
    症状 → 原因 → 修复：连不上、版本错配、hook 不触发、崩溃、反调试退出。

</div>

---

## 五个会坑你的约定（Frida 16/17）

- **这是 Frida ≥ 16 的 API。** `Module.getExportByName()` / `Module.findExportByName()`
  在 **Frida 17 已移除**。改用
  `Process.getModuleByName('libc.so.6').getExportByName('open')` 或
  `Module.getGlobalExportByName('open')`。
- **读写要走指针：** `ptr.readUtf8String()`、`ptr.writeInt(0)`、`hexdump(ptr, {length: 64})`，
  而不是 `Memory.read*(ptr)`。
- **默认运行时是 QuickJS (QJS)**，不是 V8（`--runtime=v8` 可切换）。
- **Java/ObjC 只在设备上存在。** 用 `Java.available` / `ObjC.available` 守卫。
- **`send()` 是异步单向的；** 需要 host→agent 返回值的调用用 `rpc.exports`。

详见 [入门入口 SKILL.md](SKILL.md) 与 [概念总览](references/concepts/index.md)。

---

## 给 AI Agent / 维护者

- 面向 Agent 的决策路由与渐进式披露入口：[SKILL.md](SKILL.md)
- 文档写作规范与已验证的 Frida 17 API 事实：[作者指南 AUTHORING.md](AUTHORING.md)
