---
name: codex-session-organizer
description: 整理 Codex 会话→项目归集：生成归集索引、同步 App 左侧项目栏（local-projects）、分配会话归属（thread-project-assignments）、清理冗余项目。用户说"整理 codex 会话/会话项目归集/会话没进项目/左侧项目栏没更新/清理 codex 会话"时使用。按工作区规范直接落实，不依赖 CodexCleanUp 交接契约。
---

# Codex 会话归集整理器（Session Organizer）

把 Codex 历史会话按主题归集到工作区项目（P###），并让 Codex 桌面 App 左侧项目栏真实反映归属——**直接改 App 状态文件落实**，不走"会话交接"手动流程。

## 何时使用

- 用户要求"整理我的 codex 会话项目/自动生成项目并分类归集/标注编号统一命名"
- 用户反馈"左侧项目栏并没有更新"、"项目在但会话没进项目"
- 需要清理 App 里的冗余/空壳项目

## 前置条件

1. 读工作区规范：`AGENTS.md`（P### 命名、`projects/README.md` 注册表、`_system/codex/会话登记册.md` 记账、`_system/03-全局踩坑日志.md`）
2. 定位 App 状态：`~/.codex/.codex-global-state.json`
   - `local-projects`：项目表（key=UUID，含 name / rootPaths）
   - `thread-project-assignments`：会话→项目归属（key=threadId，值 `{projectKind, projectId, cwd}`）
   - `project-order`：项目排序
3. 会话文件：`~/.codex/sessions/<YYYY>/<MM>/*.jsonl`（每文件首行 `session_meta` 有完整 session_id）

## 工作流

### 1. 盘点会话
扫描会话目录，提取每个会话的首条真实用户消息作为主题（跳过 AGENTS.md / environment_context 等系统注入）。

### 2. 主题归集（关键词规则）
关键词 → 项目（避免单字母关键词，如 `x` 会误匹配 codex；用 `x 每日`/`x情报`）。未匹配 → 归档（ARCHIVE→codex 项目）。规则存于 `scripts/session-index.py` 的 RULES，按工作区注册表定制。

### 3. 生成归集索引
输出 `<日期>-Codex会话归集索引-v1.md` 到 `_system/codex/`：统计表 + 明细表（#/日期/会话ID/主题/归属项目/说明）。

### 4. 同步 App 项目栏（local-projects）
- 工作区项目缺 App 条目 → 补（rootPaths 指向 `projects/P###`，UUID 用 uuid4）
- 用户已在 App 建的项目（ChatGPT 目录）优先复用，避免重复
- 改前**必须完全退出 App**（见坑 1），改后 `open -a Codex` 重启生效

### 5. 分配会话归属（thread-project-assignments）
每个会话 threadId → 对应项目 UUID，cwd 设为项目 rootPaths[0]。全部会话都分配（含之前未分配的）。

### 6. 冗余清理
0 会话项目分类处置：
- 重复项目（工作区版 vs App 版同主题）→ 删冗余侧（App 条目 + 工作区目录 + 注册表行）
- 空壳（用户建的 ChatGPT 目录项目无会话）→ 删 App 条目
- Obsidian 入口（rootPaths 含 Obsidian Vault）→ **保留**（日常会话入口）
- 工作区内容项目（有 README/知识库但无历史会话）→ 默认保留，用户确认后删 App 入口（工作区文件不受影响）

### 7. 记账
会话登记册补 C###；踩坑日志记 B###（契约不匹配/误匹配/异常退出恢复等教训）；git 提交（提交前 grep 凭据）。

## 附带脚本（scripts/）

- `session-index.py`：扫描会话 → 归集索引 md（RULES 可编辑）
- `assign-threads.py`：读归集结果 → 更新 thread-project-assignments（TARGET 映射表可编辑：索引项目名 → App 项目名）

## 坑（实战 2026-08）

1. **改 global-state.json 前必须完全退出 App**：`osascript -e 'quit app "Codex"'` 后主进程可能残留，且 app-server/node_repl 子进程退出时会写回旧状态覆盖修改——`ps aux | grep Codex.app` 全部 kill 干净再改，改完再 `open -a Codex`。**用 kill 强杀会触发 App 的"异常退出恢复"**，下次启动用旧备份覆盖 Live 配置（曾把 Hermes 的 model 配置还原成旧值）——尽量正常 quit。
2. **改前备份**：`cp .codex-global-state.json .codex-global-state.json.bak-<ts>`，可回滚。
3. **关键词误匹配**：单字母（'x'）、宽泛词（'应用'）会大量误归；先跑统计看分布，异常再调规则。
4. **thread-tab-routes-v1 嵌套在 electron-persisted-atom-state 之下**，顶层没有该键；改终端 cwd 要走对层级。
5. **隐私红线**：会话 jsonl 与状态文件可能含 token/key 痕迹，读/写/提交时打码，不打印明文。
6. **CodexCleanUp 契约**（GitHub manwithshit/CodexCleanUp）只做"会话交接"（禁改私有状态、禁建项目、需官方线程工具），与本 skill 的"直接落实"目标不同——用户要求"按我的要求整理"时用本 skill，不套用交接契约。
7. **"应用反复退出/进入"排查顺序**：①`launchctl list | grep` 找 Submitted 死循环 job ②VSCode 扩展目录查双版本并存（`openai.chatgpt-*`，禁用旧版）③`ps aux` 查高 CPU 僵尸进程（全盘 glob/find 卡死）④再查 App 自身。

## 验证

- 改后重启 App，`python3 -c` 读回 global-state.json 核对：项目数、每项目会话数、无残留引用
- 用户在 App 点开项目确认会话可见
