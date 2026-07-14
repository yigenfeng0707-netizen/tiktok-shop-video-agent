# TikTok Shop 跨境短视频 AI 本地化生产 Agent

> iBot 杭州站黑客松参赛项目 · 赛道 A：电商经营 Agent

## 项目简介

本项目面向 TikTok Shop 跨境卖家，构建一个「一个产品 → 多国本地化短视频」的端到端 AI 生产 Agent。卖家只需输入产品信息与目标国家，Agent 即可自动完成**脚本生成 → 数字人口播 → 批量剪辑 → 数据复盘**的完整流水线，并针对各国文化禁忌、面孔语种、BGM 偏好做本地化适配，显著降低跨境短视频内容生产门槛。

## 核心功能（4 步流水线）

| 步骤 | 子 Agent | 职责 |
| ---- | -------- | ---- |
| 1 | ScriptGenerator | 基于国家配置与文化禁忌规则，生成结构化多语种短视频脚本（钩子 / 卖点 / CTA / 字幕 / 分镜） |
| 2 | DigitalHumanGenerator | 按国家自动切换面孔、语种、BGM，调用数字人 API 生成口播视频并产出 SRT 字幕 |
| 3 | BatchEditor | 基于 ffmpeg + 模板系统，批量完成字幕烧录、贴纸特效、BGM 混音、片头片尾拼接 |
| 4 | DataReviewer | 采集视频指标、分析高流量共性、生成优化建议并反哺脚本生成模块，实现闭环迭代 |

主编排由 `orchestrator/main.py` 中的 `Orchestrator` 类统一调度，支持单步失败隔离、耗时统计与分步运行。

## 技术栈

- **MiXer AI**：主编排与多 Agent 协同框架
- **数字人 API**：HeyGen / 腾讯智影 / SiliconCloud（Demo 阶段用 Mock 占位）
- **ffmpeg**：视频剪辑、字幕烧录、BGM 混音、贴纸叠加
- **MCP 协议**：模型上下文协议，打通工具调用与数据流转
- **Python 标准库**：json / os / re / random / datetime（不引入额外依赖）

## 目录结构

```
项目/
├── agents/                     # 4 个子 Agent
│   ├── script_generator.py      # 脚本生成 Agent
│   ├── digital_human.py        # 数字人视频生成 Agent
│   ├── batch_editor.py          # 批量剪辑 Agent
│   └── data_reviewer.py         # 数据复盘 Agent
├── orchestrator/                # 主编排模块
│   ├── __init__.py             # 导出 Orchestrator
│   └── main.py                  # 主编排 Agent（流水线调度）
├── demo/                        # Demo 入口
│   ├── __init__.py
│   └── run_demo.py             # 一键运行 Demo
├── config/                      # 配置文件
│   ├── country_config.json     # 5 国配置（语言/面孔/平台风格/BGM）
│   ├── mock_data.json          # 15 条样本视频数据（复盘用）
│   ├── face_voice_mapping.json # 国家→面孔→语种→数字人 ID 映射
│   ├── bgm_library.json        # 各国 BGM 库
│   ├── cultural_taboos.json    # 文化禁忌规则引擎
│   └── prompts/                # Prompt 模板
│       ├── script_generation.md
│       └── data_analysis.md
├── templates/                   # 视频模板与特效
│   ├── video_template.json
│   └── effects/effects_config.json
├── assets/                      # 产出素材
│   ├── subtitles/              # 生成的 SRT 字幕
│   ├── digital_human_output/   # 数字人视频占位输出
│   └── output/                  # 最终剪辑成片输出
├── docs/                        # 提交材料
│   ├── 使用说明.md
│   ├── 场景说明.md
│   ├── 技术路线.md
│   ├── 路演PPT大纲.md
│   ├── 团队信息.md
│   └── AI使用披露.md
└── README.md
```

## 快速开始

```bash
# 在项目根目录下执行
python demo/run_demo.py
```

Demo 将以「便携榨汁杯」为测试产品，面向 5 个国家（US / VN / SA / GB / ID）运行完整流水线，并打印每步耗时、产出数量与关键产出预览。

### 支持的目标国家

| 代码 | 国家 | 语种 | 面孔类型 | 平台风格 |
| ---- | ---- | ---- | -------- | -------- |
| US | 美国 | English | european | tiktok_short |
| VN | 越南 | Vietnamese | southeast_asian | tiktok_short |
| SA | 沙特阿拉伯 | Arabic | middle_east | product_showcase |
| GB | 英国 | English | european | tiktok_short |
| ID | 印度尼西亚 | Indonesian | southeast_asian | tiktok_short |

## 配置文件说明

| 文件 | 作用 |
| ---- | ---- |
| `config/country_config.json` | 各国语言、面孔类型、平台风格、热门 BGM 曲风、文化禁忌标记 |
| `config/mock_data.json` | 15 条样本视频数据（含 video_id / hook_type / bgm_type / publish_time），用于数据复盘演示 |
| `config/face_voice_mapping.json` | 国家 → 面孔类型 → 语种 → 数字人 avatar_id 映射 |
| `config/bgm_library.json` | 各国按品类分类的 BGM 库 |
| `config/cultural_taboos.json` | 文化禁忌规则引擎（动作类型 + 规则描述 + 适用国家/品类） |
| `templates/video_template.json` | 视频分段模板（片头 / 产品展示 / 卖点字幕 / CTA / 片尾） |
| `templates/effects/effects_config.json` | 带货特效贴纸配置（价格爆炸框 / 倒计时 / 限时优惠） |

## 提交材料位置

所有路演与评审材料统一置于 `docs/` 目录：

- `docs/使用说明.md`：产品使用文档
- `docs/场景说明.md`：业务场景与目标用户
- `docs/技术路线.md`：技术架构与实现路线
- `docs/路演PPT大纲.md`：路演演示大纲
- `docs/团队信息.md`：团队成员信息
- `docs/AI使用披露.md`：AI 工具使用披露说明

## 注意事项

1. **Demo 阶段使用模拟数据**：脚本生成、数字人 API、ffmpeg 执行均使用 Mock / 占位实现，不产生真实视频文件，仅生成路径占位与命令字符串，便于评审查看逻辑。
2. **正式部署需替换 Mock 方法**：
   - `ScriptGenerator._mock_llm_call` → 替换为真实 LLM API（GPT-4 / Claude / 豆包）
   - `DigitalHumanGenerator._mock_digital_human_api` → 替换为 HeyGen / 腾讯智影 API
   - `BatchEditor` 中的 ffmpeg 命令 → 通过 `subprocess` 真实执行
   - `DataReviewer._mock_tiktok_metrics` → 替换为 TikTok Business API
3. **错误隔离设计**：主编排 Agent 对每步进行 try/except 包裹，单步失败仅记录错误并继续后续步骤，不中断整条流水线。
4. **仅依赖 Python 标准库**：Demo 可在任意安装 Python 3.8+ 的环境中直接运行，无需 `pip install`。

## 真实 API 接入

项目已内置真实 API 调用代码，通过环境变量自动切换「真实 / Mock」模式：未配置任何 API Key 时使用 Mock 占位实现；配置后自动走真实 API。

### 配置步骤

1. 复制 `.env.example` 为 `.env`：
   ```bash
   cp .env.example .env
   ```
2. 在 `.env` 中填入真实的 API Key（按需配置，未配置的服务会自动回退 Mock）
3. 安装可选依赖（真实 API 调用需要 requests）：
   ```bash
   pip install requests
   ```
4. 运行 Demo 或主编排时，环境变量会自动被读取

### 环境变量说明

| 环境变量 | 对应服务 | 申请入口 | 作用 |
| -------- | -------- | -------- | ---- |
| `OPENAI_API_KEY` | OpenAI / 兼容 LLM | https://platform.openai.com/ | 脚本生成 Agent 的 LLM 调用，不配置则回退模板填充 |
| `OPENAI_BASE_URL` | OpenAI 兼容服务 | —— | LLM API 基础地址，默认 `https://api.openai.com/v1`，可指向豆包 / DeepSeek 等兼容服务 |
| `LLM_MODEL` | LLM 模型名 | —— | 使用的模型，默认 `gpt-4o`，可改为 `deepseek-chat` / `doubao-pro` 等 |
| `HEYGEN_API_KEY` | HeyGen 数字人 | https://app.heygen.com/ | 数字人视频生成（优先），配置后走真实合成 + 轮询下载 |
| `TENCENT_ZY_API_KEY` | 腾讯智影 | https://zenvideo.tencent.com/ | 数字人视频生成（备选），需同时配置 SECRET_ID / SECRET_KEY |
| `TENCENT_ZY_SECRET_ID` | 腾讯云账号 | https://console.cloud.tencent.com/cam/capi | 腾讯云 SecretId，用于 TC3-HMAC-SHA1 签名 |
| `TENCENT_ZY_SECRET_KEY` | 腾讯云账号 | https://console.cloud.tencent.com/cam/capi | 腾讯云 SecretKey，用于签名 |
| `TENCENT_ZY_REGION` | 腾讯云地域 | —— | 地域代码，默认 `ap-guangzhou` |
| `TIKTOK_API_KEY` | TikTok Research API | https://developers.tiktok.com/ | 数据复盘 Agent 采集真实视频指标，不配置则回退 mock 数据 |
| `USER_API_ENDPOINT` | 自定义业务 API | —— | 扩展用，自定义业务端点 |
| `API_KEY` | 自定义业务鉴权 | —— | 扩展用，自定义 API Key |
| `HOST` | 服务监听地址 | —— | 默认 `0.0.0.0` |
| `PORT` | 服务监听端口 | —— | 默认 `8000` |

### API 选择优先级

- **脚本生成**：有 `OPENAI_API_KEY` → 走真实 OpenAI 兼容 API；否则 → mock 模板填充
- **数字人视频**：有 `HEYGEN_API_KEY` → HeyGen；否则有 `TENCENT_ZY_API_KEY` → 腾讯智影；否则 → mock 占位
- **数据复盘**：有 `TIKTOK_API_KEY` → TikTok Research API；否则 → mock 随机指标

### 自动回退机制

所有真实 API 调用均包裹 try/except，调用失败时会打印告警并自动回退到 Mock 模式，保证流水线不中断。例如 HeyGen API Key 配额耗尽时，会回退到 mock 占位路径继续执行后续步骤。
