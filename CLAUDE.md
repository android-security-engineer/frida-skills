# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is the **Frida umbrella repository** — the top-level Meson super-project that
stitches together Frida's independently-developed components (each a git submodule
under `subprojects/`) into a single buildable tree. There is very little source code
here; almost all real code lives in the submodules. Work usually happens *inside a
submodule*, with this repo used to configure and build the whole stack together.

Components (all git submodules):
- `subprojects/frida-gum` — low-level instrumentation C library + GumJS (JS runtime). Foundation of everything.
- `subprojects/frida-core` — session/agent orchestration, produces `frida-server`, `frida-gadget`, `frida-portal`, `frida-inject`.
- `subprojects/frida-python`, `frida-node`, `frida-swift`, `frida-clr`, `frida-qml` — language bindings.
- `subprojects/frida-tools` — the CLI tools (`frida`, `frida-trace`, `frida-ps`, `frida-ls-devices`, `frida-kill`, `frida-discover`).
- `subprojects/frida-go` — Go bindings.
- `releng` — release engineering / build machinery submodule. **Required before anything works**; it provides the Meson wrappers, `frida_version.py`, `deps.py` (toolchain/SDK rolling), and the bundled Meson.

## AI / agent enablement — the purpose of this fork

This repository (`frida-skills`) exists to teach AI agents (Claude Code, Codex, …)
**how to use Frida**. Two additions on top of upstream serve that goal; neither is a
submodule and neither requires building the tree (`pip install frida mcp` suffices):

### `skills/` — Agent Skills (primary deliverable)

`skills/frida/` is a **progressive-disclosure** Agent Skill with a **two-level**
information architecture. The entry file `SKILL.md` carries YAML frontmatter
(`name`, `description` — the description is what decides when an agent loads the
skill) and stays short: mental model, "can you reach the target?" preconditions, a
decision-routing table, and minimal examples. It routes to **10 domain indexes**
under `references/<domain>/index.md` (`concepts`, `core-api`, `cli`, `android`,
`ios`, `recipes`, `guides`, `playbooks`, `reference`, `troubleshooting`); each
index lists its **leaf docs** (172 total), loaded **only when the task matches**
— that two-step (SKILL → domain index → leaf) is the progressive disclosure.
Key concept/flow docs carry mermaid diagrams (28 total). Every leaf has its own
frontmatter (`name` = filename, `description` ≤220 chars, optional
`type: leaf | diagram | summary`).

`skills/frida/AUTHORING.md` is the single source of truth for house style and the
**verified Frida 16/17 API facts** every doc must obey — read it before adding or
editing any doc. When editing: keep `SKILL.md` and each `index.md` lean; push detail
into leaves; every link in `SKILL.md`/`index.md` must resolve. Content targets Frida
16/17 — note the removed static `Module.getExportByName/findExportByName` (use
`Process.getModuleByName(...).getExportByName(...)` or `Module.getGlobalExportByName`),
verified against 17.15.3.

### `frida-mcp/` — optional MCP server

`frida-mcp/server.py` is a `FastMCP` (stdio) **Model Context Protocol server** that
exposes Frida to agents as callable tools (discovery + one-shot `run_script` + a
stateful session/script API over a lock-guarded registry, since Frida delivers
messages on its own reactor thread). It's a *runtime* integration, complementary to
the skills (which are *knowledge*). Note: FastMCP's structured-output schema trips a
pydantic issue for scalar returns, so tools use `structured_output=False`. See
`frida-mcp/README.md`.

## Building

The `Makefile`, `configure`, `make.bat`, and `configure.bat` are thin shims: they
bootstrap submodules if needed, then delegate to Python entry points in `releng`
(`releng.meson_make`, `releng.meson_configure`). `make <target>` forwards `<target>`
straight to `meson_make` against the `./build` directory.

```sh
make                      # configure (if needed) + build everything with defaults
./configure --prefix=... [options] -- [meson-args]   # explicit configure step
make install
make test
make clean
make distclean            # remove the build directory
```

Configure options use `--enable-X` / `--disable-X` (mapped onto the Meson `feature`
options in `meson.options`), followed by `--` and then raw Meson args using the
`subproject:option=value` form. See `.cirrus.yml` for a full real-world invocation, e.g.:

```sh
./configure --prefix="$PREFIX" --enable-server --enable-gadget --disable-frida-tools \
    -- -Dfrida-gum:devkits=gum,gumjs -Dfrida-core:compiler_backend=enabled
```

Key toggles (`meson.options`): `frida_tools`, `graft_tool`, `gadget`, `server`,
`portal`, `inject`, `frida_python`, `frida_node`, `frida_swift`, `frida_clr`,
`frida_qml`. Many default to `auto` and are auto-disabled on cross-builds (see the
`disable_auto_if` logic in `meson.build`).

## Submodules — important

- `.gitignore` ignores `/subprojects/*` and `/releng/` contents even though they are
  tracked submodules; don't be confused by their "untracked" appearance.
- Submodules are fetched **shallow and on demand**. `tools/ensure-submodules.py`
  fetches `releng` first, then by default `frida-gum` and `frida-core`; pass names to
  fetch specific ones (e.g. `python tools/ensure-submodules.py frida-python frida-node`).
  `meson.build` calls this automatically for each binding it decides to build.
- To bump submodule pointers, update the submodule and commit the new SHA here. Recent
  history shows this is done frequently ("submodules: Bump outdated").

## CI

- GitHub Actions (`.github/workflows/ci.yml`) runs on every push: builds/packages for
  Windows, macOS, Linux, iOS, watchOS, tvOS, Android, QNX, and publishes releases on tags.
  Reusable per-OS setup lives in `.github/actions/`.
- Cirrus (`.cirrus.yml`) covers FreeBSD/x86_64.
- Both roll toolchain + SDK via `releng/deps.py` before building.

## Coding conventions

`CONTRIBUTING.md` is the authoritative, detailed style guide and is strictly enforced
in review. It spans C, C++, Vala, JavaScript, TypeScript, Python, and assembly, and
conventions vary per project/language. Read the relevant section before editing. The
load-bearing rules:

- **Comments explain only what code can't.** Prefer meaningful names and extracted
  functions over comments; don't narrate obvious lines.
- **Higher-level functions come before lower-level ones**, sorted by call order; in C,
  forward declarations must follow the same order.
- **DRY**, and **validate arguments** at function entry.
- Indentation and spacing rules differ by language (e.g. tabs vs. spaces) — match the
  surrounding file and the CONTRIBUTING section for that language exactly.
