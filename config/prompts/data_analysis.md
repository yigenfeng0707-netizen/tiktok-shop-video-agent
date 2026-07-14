# TikTok Shop 跨境短视频数据复盘分析 Prompt 模板

> 本文档定义数据复盘子 Agent 调用大模型（LLM）时使用的 Prompt 模板与数据契约。
> 用于分析高流量视频共性、标记低转化模板、生成优化建议并反哺脚本生成模块。

---

## 1. 数据分析输入 Schema

输入为「视频列表 + 各项指标」的 JSON 结构，由 `DataReviewer.collect_metrics()` 产出后传入分析模块。

```json
{
  "videos": [
    {
      "video_id": "US_001",
      "product_name": "便携式榨汁机",
      "country": "US",
      "script": "完整脚本文本内容...",
      "script_summary": "脚本摘要：以早晨场景切入，展示产品便携性，结尾促单",
      "hook_type": "场景带入型",
      "bgm_type": "节奏感强",
      "publish_time": "2025-06-15T19:30:00",
      "metrics": {
        "views": 35000,
        "ctr": 0.045,
        "conversion_rate": 0.025,
        "completion_rate": 0.55,
        "likes": 2100,
        "comments": 180,
        "shares": 350
      }
    }
  ]
}
```

### 指标字段说明

| 字段 | 类型 | 说明 | 合理区间 |
| --- | --- | --- | --- |
| views | int | 播放量 | 1000 - 50000 |
| ctr | float | 点击率（0-1） | 0.01 - 0.08 |
| conversion_rate | float | 成交转化率（0-1） | 0.005 - 0.05 |
| completion_rate | float | 完播率（0-1） | 0.20 - 0.70 |
| likes | int | 点赞数 | views × 2%-10% |
| comments | int | 评论数 | views × 0.1%-1% |
| shares | int | 分享数 | views × 0.1%-2% |

---

## 2. 分析维度

请从以下 5 个维度分析高流量视频（播放量 > 10000）的共性特征。

### 2.1 开头钩子类型（hook_type）

分析前 3 秒钩子对播放量与完播率的影响，可选类型：

- `痛点提问型` —— 以用户痛点发问开场
- `反差冲突型` —— 制造前后对比/冲突
- `福利诱饵型` —— 强调优惠/赠品
- `场景带入型` —— 还原使用场景
- `数据震撼型` —— 用销量/评分数据震撼
- `名人背书型` —— 借助 KOL/名人推荐

### 2.2 BGM 类型（bgm_type）

分析背景音乐对完播率与互动率的影响：

- `热门流行` —— 平台热门榜音乐
- `节奏感强` —— 卡点/电子节奏
- `情感抒情` —— 温情叙事类
- `搞笑段子` —— 搞笑/配音类
- `原创音乐` —— 品牌原创
- `无BGM` —— 纯人声讲解

### 2.3 卖点顺序（selling_point_order）

分析脚本中卖点的呈现顺序，典型链路：

1. 痛点引入
2. 解决方案
3. 产品展示
4. 信任背书
5. 促单转化

输出最佳卖点顺序排列。

### 2.4 视频时长（duration）

按时长分桶统计完播率与转化率：

- 短视频：≤ 15s
- 中视频：15 - 30s
- 长视频：30 - 60s

### 2.5 发布时间（publish_time）

按发布时段分桶统计平均播放量：

- 早晨：06:00 - 09:00
- 中午：12:00 - 14:00
- 晚间：18:00 - 22:00
- 深夜：22:00 - 24:00

---

## 3. 输出 Schema

LLM 分析结果输出如下 JSON 结构：

```json
{
  "high_traffic_report": {
    "common_patterns": {
      "hook_type": "场景带入型",
      "bgm_type": "节奏感强",
      "selling_point_order": ["痛点", "解决方案", "产品展示", "促单"],
      "duration_range": "15-30s",
      "publish_time_range": "18-22点"
    },
    "top_videos": [
      {
        "video_id": "US_001",
        "views": 35000,
        "hook_type": "场景带入型",
        "bgm_type": "节奏感强"
      }
    ],
    "low_conversion_templates": ["UK_002", "TH_003"]
  },
  "analysis_summary": "高流量视频共性：钩子类型 场景带入型，BGM 类型 节奏感强，发布时段集中在 18-22 点",
  "optimization_suggestions": [
    {
      "target_module": "脚本生成",
      "suggestion_type": "优化",
      "content": "优先使用 场景带入型 钩子类型",
      "priority": "high"
    }
  ]
}
```

### 输出字段说明

| 字段 | 说明 |
| --- | --- |
| common_patterns | 高流量视频在各维度的共性特征 |
| top_videos | 播放量 Top N 视频摘要 |
| low_conversion_templates | 转化率低于阈值、待淘汰的模板 video_id 列表 |
| analysis_summary | 自然语言总结 |
| optimization_suggestions | 优化建议列表 |

---

## 4. 优化建议反哺脚本生成模块的格式

`DataReviewer.feedback_to_script_generator()` 将优化建议结构化为脚本生成模块可消费的格式，供下游脚本生成 / 数字人 / 剪辑模块读取迭代。

```json
{
  "script_optimizations": [
    {
      "field": "hook_type",
      "action": "update",
      "content": "优先使用 场景带入型 钩子类型",
      "priority": "high"
    },
    {
      "field": "bgm_type",
      "action": "update",
      "content": "推荐使用 节奏感强 类型 BGM",
      "priority": "medium"
    }
  ],
  "template_updates": [
    {
      "action": "deprecate",
      "content": "以下模板转化率过低，建议淘汰：UK_002, TH_003",
      "priority": "high"
    }
  ],
  "taboos_updates": [
    "以下模板转化率过低，建议淘汰：UK_002, TH_003"
  ]
}
```

### 反哺字段说明

| 字段 | 说明 | 消费方 |
| --- | --- | --- |
| script_optimizations | 脚本字段级优化项（钩子/BGM/卖点顺序/发布时间） | 脚本生成模块 / 剪辑模块 |
| template_updates | 模板状态更新（淘汰/停用） | 脚本生成模块 |
| taboos_updates | 禁忌项列表，写入脚本生成的 taboo 词库 | 脚本生成模块 |

### target_module 取值

- `脚本生成` —— 反哺脚本生成 Agent
- `数字人` —— 反哺数字人口播模块
- `剪辑` —— 反哺剪辑模块

### suggestion_type 取值

- `优化` —— 保留并迭代该模板
- `淘汰` —— 标记为待淘汰，停止复用

### priority 取值

- `high` —— 立即生效
- `medium` —— 下一批次生效
- `low` —— 观察后决定
