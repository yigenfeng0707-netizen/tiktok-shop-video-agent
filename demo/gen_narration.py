# -*- coding: utf-8 -*-
"""用阿里云 Maas qwen 生成 90-120s 普通话旁白稿 + 英文翻译。
输出：项目/assets/narration_cn.txt + narration_en.txt（一句一行，带序号）
"""
import os
from openai import OpenAI

# 读取 .env
env = {}
with open(r"d:\18号杭州电商赛道比赛\项目\.env", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()

client = OpenAI(
    api_key=env["OPENAI_API_KEY"],
    base_url=env["OPENAI_BASE_URL"],
)

PROMPT = """你是 TikTok Shop 跨境短视频 AI 本地化生产 Agent 的路演口播稿撰写专家。
产品：TikTok Shop 跨境短视频 AI 本地化生产 Agent（4 步流水线，多国一键批量本地化短视频生产）。

要求：
- 总时长 100 秒（约 250 字普通话）
- 节奏：每 8-12 秒一个换气点（用【】标记）
- 普通话口语化、有感染力，结尾有力
- 同步给一个英文版本（屏幕字幕用，同样 250 词左右，节奏一致）
- 输出 JSON 格式：{"cn": ["句子1", "句子2", ...], "en": ["sentence1", "sentence2", ...]}
- 句子数量 12-15 句（中英对齐）

结构建议：
- 开头钩子（0-10s）：抛出痛点
- 主体（10-80s）：4 步流水线 + 3 大创新（多国批量 / 文化禁忌 / 数据闭环）
- 价值（80-95s）：成本-80% / 产能+10x
- 收尾（95-100s）：行动召唤

请直接输出 JSON，不要额外解释。
"""

resp = client.chat.completions.create(
    model=env.get("LLM_MODEL", "qwen3.6-flash"),
    messages=[{"role": "user", "content": PROMPT}],
    temperature=0.7,
    max_tokens=1500,
)

text = resp.choices[0].message.content.strip()
print("=" * 60)
print("RAW OUTPUT:")
print(text)
print("=" * 60)

# 解析 JSON
import json, re
m = re.search(r"\{[\s\S]*\}", text)
if m:
    data = json.loads(m.group(0))
    cn = data.get("cn", [])
    en = data.get("en", [])
    with open(r"d:\18号杭州电商赛道比赛\项目\assets\narration_cn.txt", "w", encoding="utf-8") as f:
        for i, s in enumerate(cn, 1):
            f.write(f"{i}. {s}\n")
    with open(r"d:\18号杭州电商赛道比赛\项目\assets\narration_en.txt", "w", encoding="utf-8") as f:
        for i, s in enumerate(en, 1):
            f.write(f"{i}. {s}\n")
    print(f"OK: 写入 {len(cn)} 句中文 + {len(en)} 句英文")
else:
    print("ERROR: JSON 解析失败")
