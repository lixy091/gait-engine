# Gait Engine 语义

`gait-engine/` 是声明式流程层，只保存 YAML、模板和说明；状态机执行与状态写入由 gait-cli 负责。业务项目通过 `.gait/project.yaml` 中的 `gait.engine_path` 引用该目录。修改引擎后必须执行 `python gait-engine/scripts/validate_engine.py`。

## 组件

- `workflows/*.yaml`：定义有序阶段列表。本 MVP 只有 normal-iteration：requirement-design → coding → closing。
- `stages/*.yaml`：定义阶段名称、上下文引用、退出 gate、`allow_code_modification` 和自然语言 instructions。该布尔值表达阶段约束；CLI 不拦截模型写代码行为，门禁只验证可判定的产物与 Git 状态。
- `gates/*.yaml`：声明阶段退出检查名称。GateExecutor 将声明的 gate 名映射到内置检查逻辑：设计文档 + OpenSpec artifacts + tracked 代码干净；任务完成 ID + manifest 测试命令 + manifest；summary + OpenSpec archive。
- `contexts/*.yaml`：声明当前阶段建议提供给 Agent 的项目文件上下文，本 MVP 作为引擎元数据，不自动拼接模型上下文。
- `selector.yaml`：按 task type 映射 workflow。feature 和 bugfix 当前均映射 normal-iteration。
- `registry.yaml`：登记 workflow/stage/gate/context 名到相对文件路径的组件索引。
- `templates/*.j2`：由 `gait init` 复制为运行时说明文件，强制状态文件不可手改、Agent 不可自动审批和自推阶段。

## 阶段约束

### requirement-design

`allow_code_modification: false`。阶段一先检查上下文、逐项识别需求中的未知点，并一次只问一个澄清问题；不得用自行假设代替澄清。Agent 先向用户复述需求理解，只有得到用户明确确认后，才能创建 `docs/requirement/<task_name>/需求设计文档.md` 并通过 OpenSpec propose 生成 spec、design、tasks artifacts。确认前不得启动 propose，也不得修改业务代码。这是对工作流程的约束，不会切换 Codex 内置 Plan mode；该模式需由用户使用 `/plan` 开启。退出检查验证上述文件存在，并执行 `git diff --quiet` 确认 tracked 文件无改动；无法判断 Git 状态时失败关闭。

### coding

`allow_code_modification: true`。按 tasks.md 的 task_id 逐条完成代码修改和单测；测试通过后由 gait 状态记录器追加 completed_task_ids。`docs/<task_name>/coding-manifest.md` 提供 `test_command`。退出检查要求所有任务 ID 已完成、manifest 存在且测试命令退出码为 0。

### closing

`allow_code_modification: false`。由 gait 调用 `openspec archive <change-id>`，并产出 `docs/<task_name>/summary.md`。close gate 检查归档目录和 summary；通过后 CLI 才将任务标记 completed。

## OpenSpec 必装

OpenSpec（`@fission-ai/openspec`）必须安装可用。`gait init` 可引导检查/安装，并在项目未初始化时执行 `openspec init`；任务创建使用 `openspec new change`，归档使用 `openspec archive`。propose 是 AI 助手集成提供的工作流，不是当前 OpenSpec CLI 命令。禁止在缺少 OpenSpec 时手写目录或 artifacts 作为降级。

## 状态和人工审批

状态只能由 gait-cli 的 StateManager 读写；Agent 不得手改 `.gait/`。阶段推进默认需交互确认，无 TTY 必须传 `--yes`。人工审批只有用户明确执行 `gait task gate --approve` 才会写入 approvals；Agent 不能替用户批准。advances/approvals 包含时间和说明，便于审计和跨会话恢复。
