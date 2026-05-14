# BongoCat 迁移计划

## 目标

把当前 Web MVP 迁移为 BongoCat 的增强版功能：保留 BongoCat 的桌面宠物体验，增加摄像头感知、语音交互和多模态 Agent。

## 参考 BongoCat 能力

根据 BongoCat 仓库页面和 README，它已经具备以下适合作为项目39底座的能力：

- 跨平台：Windows、macOS、Linux。
- 桌面宠物：桌面常驻、输入动作同步。
- 技术栈：Tauri、Vue、TypeScript、Rust。
- 可扩展：支持自定义模型、动作、键盘/鼠标/手柄响应。
- 隐私友好：可离线运行，适合在本地处理桌宠表现层。

## 模块迁移

| Web MVP 文件 | BongoCat 中的目标模块 | 说明 |
| --- | --- | --- |
| `src/app.js` 中的状态机 | `src/modules/ai-pet/agent.ts` | 拆出 mood、presence、activity、reply strategy |
| 摄像头采样逻辑 | `src/modules/ai-pet/perception.ts` | Vue composable 管理摄像头权限和帧采样 |
| 聊天模型调用 | `src/modules/ai-pet/modelClient.ts` | 支持 DeepSeek、Qwen、OpenAI 兼容接口 |
| 语音播报/输入 | `src/modules/ai-pet/voice.ts` | Web Speech 先行，后续接 EdgeTTS/Whisper |
| CSS 宠物动画 | Live2D/Pixi 动作映射 | 将 mood 映射到 Live2D motion/expression |
| 设置面板 | `src/components/AiPetSettings.vue` | 摄像头、模型、语音、隐私配置 |

## Tauri 权限与桌面能力

1. 摄像头和麦克风权限：在首次开启时显示用途说明。
2. 全局键鼠监听：沿用 BongoCat 输入同步能力，把事件转成 Agent 活跃度。
3. 透明窗口与置顶：桌宠留在桌面层，设置面板可单独显示。
4. 本地配置：API key、模型名、角色设定保存到本地安全存储。
5. 隐私策略：摄像头帧默认只本地分析，上传给视觉模型必须二次确认。

## Prompt 设计

系统提示词建议：

```text
你是一个中文具身AI桌面宠物。你会收到用户文本、摄像头状态摘要、键鼠活跃度和可选图像。
回复必须短、自然、温和。不要声称看到了未提供的信息。必要时输出动作指令：
idle, typing, curious, cheer, sleepy, thinking。
```

多模态用户消息建议：

```json
{
  "text": "用户问题",
  "state": {
    "presence": "用户在屏幕前",
    "brightness": 72,
    "motion": 11,
    "lastAction": "键盘输入"
  },
  "image": "可选摄像头快照"
}
```

## 里程碑

| 周期 | 目标 | 验收 |
| --- | --- | --- |
| 第 1 周 | Web MVP 和课程材料 | 可本地演示，完成报告与海报草稿 |
| 第 2 周 | 迁移 Tauri 壳层 | 透明置顶窗口运行，键鼠状态可驱动桌宠 |
| 第 3 周 | 接入多模态模型 | Qwen-VL 能描述快照，LLM 能生成动作指令 |
| 第 4 周 | 语音与展示优化 | 支持语音输入/播报，完成现场演示脚本 |

## 风险与应对

| 风险 | 影响 | 应对 |
| --- | --- | --- |
| 摄像头权限难配置 | 桌面端无法感知 | 先 WebView 权限验证，再接 Tauri 插件 |
| 大模型接口延迟 | 互动不自然 | 本地状态机先即时响应，模型回复异步补充 |
| 隐私担忧 | 用户不愿开启摄像头 | 默认本地分析，上传前显式确认 |
| Live2D 动作不足 | 表现单调 | 先映射基础 mood，再补充自定义动作 |
