# -*- coding: utf-8 -*-
"""生成 SRT 字幕（中英双行），用于 ffmpeg 硬编码。
按句子顺序生成时间轴。
"""
import re

# 读中文 + 英文
with open(r"d:\18号杭州电商赛道比赛\项目\assets\narration_cn.txt", "r", encoding="utf-8") as f:
    cn_lines = [re.sub(r"^\d+\.\s*", "", l.strip()).replace("【】", "").replace("【", "").replace("】", "") for l in f if l.strip()]
with open(r"d:\18号杭州电商赛道比赛\项目\assets\narration_en.txt", "r", encoding="utf-8") as f:
    en_lines = [re.sub(r"^\d+\.\s*", "", l.strip()).replace("【】", "").replace("【", "").replace("】", "") for l in f if l.strip()]

# 总时长 70 秒，平均每句 ~5.4 秒
total = 70.0
n = len(cn_lines)
per = total / n  # 每句时长

def fmt(t):
    """秒 -> SRT 时间码 HH:MM:SS,mmm"""
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

# 写入 srt
srt_path = r"d:\18号杭州电商赛道比赛\项目\assets\subtitle_demo.srt"
with open(srt_path, "w", encoding="utf-8") as f:
    for i in range(n):
        start = i * per
        end = (i + 1) * per - 0.15  # 提前 0.15s 切换
        f.write(f"{i+1}\n")
        f.write(f"{fmt(start)} --> {fmt(end)}\n")
        # 双行字幕：中文 + 英文
        f.write(f"{cn_lines[i]}\n")
        f.write(f"{en_lines[i]}\n")
        f.write("\n")

print(f"OK: {n} 句字幕已写入 {srt_path}")
print(f"总时长 {total}s, 每句 {per:.2f}s")
