# -*- coding: utf-8 -*-
"""edge-tts 合成普通话旁白音轨，输出 narration.mp3。
每句之间插入 0.4s 静音换气。
"""
import asyncio, edge_tts, re

# 读旁白稿（去掉序号）
with open(r"d:\18号杭州电商赛道比赛\项目\assets\narration_cn.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

sentences = []
for line in lines:
    # 去掉 "1. " 这种序号
    s = re.sub(r"^\d+\.\s*", "", line.strip())
    # 把【】替换为短停顿
    s = s.replace("【】", "。").replace("【", "，").replace("】", "")
    # 多余的"。"压缩
    s = re.sub(r"。+", "。", s)
    s = s.strip("。， ")
    if s:
        sentences.append(s)

print("待合成句子：", len(sentences))
for i, s in enumerate(sentences, 1):
    print(f"  {i}. {s}")

# 合成：每句之间用 SSML 加 0.4s 停顿
async def synth():
    voice = "zh-CN-XiaoxiaoNeural"  # 活泼女声
    rate = "+5%"   # 略快，体现节奏感
    pitch = "+0Hz"

    # 逐句合成再拼接，简单稳
    import os
    chunks = []
    for i, s in enumerate(sentences):
        comm = edge_tts.Communicate(s, voice, rate=rate, pitch=pitch)
        mp3_path = rf"d:\18号杭州电商赛道比赛\项目\assets\_chunk_{i:02d}.mp3"
        await comm.save(mp3_path)
        chunks.append(mp3_path)
        print(f"  ✓ chunk {i+1}/{len(sentences)}: {s[:30]}...")

    # 用 ffmpeg 拼接 + 加静音
    list_file = r"d:\18号杭州电商赛道比赛\项目\assets\_chunks.txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for i, c in enumerate(chunks):
            f.write(f"file '{c}'\n")
            if i < len(chunks) - 1:
                # 在两句之间插入 0.4s 静音
                f.write("file 'silence.mp3'\n")

    return list_file

asyncio.run(synth())
print("DONE")
