# -*- coding: utf-8 -*-
"""ffmpeg 70 秒 TikTok 风格信息图。
策略：基础画面（黑底+顶部黄条+底部黄条）跑全程；中间文字用 drawtext + enable 分段。
简化：所有 drawtext/drawbox 都基于 [bg] 派生，最后用 overlay 覆盖。
"""
import subprocess

OUT = r"d:\18号杭州电商赛道比赛\项目\assets\demo_video_raw.mp4"
DUR = 70
W, H = 1080, 1920

F1 = "C\\:/Windows/Fonts/msyhbd.ttc"
F2 = "C\\:/Windows/Fonts/msyh.ttc"
F3 = "C\\:/Windows/Fonts/arialbd.ttf"

stages = [
    (0,  12,  "TikTok Shop 卖家注意！",  "你的视频还在被审核挂掉？",  "100 万卖家 每月烧 250-400 亿",  "white"),
    (12, 22,  "AI 本地化生产 Agent",     "1 个产品 → 5 国视频",        "从 2 周缩短到 2 小时",            "yellow"),
    (22, 30,  "Step 1 拆解爆款",         "AI 分析热门脚本结构",        "完播率 +40%",                     "white"),
    (30, 38,  "Step 2 多语种改写",       "英/越/阿/印 原生级",         "文化禁忌自动过滤",                "white"),
    (38, 46,  "Step 3 数字人配音",       "HeyGen + 智影多语种",        "口型精准对齐",                    "white"),
    (46, 52,  "Step 4 算法优化",         "自动适配各国推荐算法",       "爆款率 +60%",                     "white"),
    (52, 60,  "3 大创新",                "多国批量 | 禁忌过滤 | 数据闭环",  "成本-80%  产能+10x",         "yellow"),
    (60, 65,  "数据反哺闭环",            "爆款特征 AI 持续学习",       "脚本越用越准",                    "white"),
    (65, 70,  "立即预约演示",            "让品牌一夜爆红全球",         "扫二维码 / 点击链接",             "yellow"),
]

# 思路：1 个基色层 + 每段 1 个独立图层
# ffmpeg -filter_complex 支持多 input 流拼接

# 构造 filter_complex
filter_str = f"color=c=black:s={W}x{H}:d={DUR}:r=30[bg];"

# 给每段创建独立图层：黑底 + drawbox + drawtext
# 关键：每段用 split 从 bg 拿一个拷贝
# 但每段时间不同，用 trim+setpts 切片

# 简化版：每段单独生成 1 个流，再用 concat 拼
# 但这样要 9 次 ffmpeg 调用

# 改用：基色 + 多 drawtext 叠在基色上（用 enable 控制时间）
filter_str = f"color=c=black:s={W}x{H}:d={DUR}:r=30[bg];"

# 顶部黄底（全程）
filter_str += f"[bg]drawbox=x=0:y=0:w={W}:h=180:color=0xFFFFD500:t=fill[bg2];"
# 底部黄条（全程）
filter_str += f"[bg2]drawbox=x=0:y=1700:w={W}:h=180:color=0xFFFFD500:t=fill[bg3];"
# 底部文字（全程）
filter_str += f"[bg3]drawtext=fontfile={F3}:text='TikTok Shop AI Localizer Agent':fontcolor=black:fontsize=38:x=(w-text_w)/2:y=1770[bg4];"

# 时间码
filter_str += f"[bg4]drawtext=fontfile={F3}:text='%{{eif\\:t\\:d}}s / {DUR}s':fontcolor=0xFFFFD500:fontsize=32:x=20:y=20[tc];"

last = "tc"
for i, (s, e, top, mid, sub, accent) in enumerate(stages):
    # 顶部标题（每段不同）
    filter_str += (
        f"[{last}]drawtext=fontfile={F1}:text='{top}':"
        f"fontcolor=black:fontsize=60:x=(w-text_w)/2:y=65:"
        f"enable='between(t,{s},{e})'[a{i}_top];"
    )
    last = f"a{i}_top"

    # 中部大字幕
    color = "white" if accent == "white" else "0xFFFFD500"
    filter_str += (
        f"[{last}]drawtext=fontfile={F2}:text='{mid}':"
        f"fontcolor={color}:fontsize=82:x=(w-text_w)/2:y=850:"
        f"box=1:boxcolor=0x000000A0:boxborderw=18:"
        f"enable='between(t,{s},{e})'[a{i}_mid];"
    )
    last = f"a{i}_mid"

    # 副标
    sub_color = "0xFFFFD500" if accent == "white" else "0xFF00FF85"
    filter_str += (
        f"[{last}]drawtext=fontfile={F1}:text='{sub}':"
        f"fontcolor={sub_color}:fontsize=52:x=(w-text_w)/2:y=1020:"
        f"box=1:boxcolor=0x000000A0:boxborderw=12:"
        f"enable='between(t,{s},{e})'[a{i}_sub];"
    )
    last = f"a{i}_sub"

# 全程连到 final
filter_str += f"[{last}]null[final]"

cmd = [
    "ffmpeg", "-y",
    "-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:d={DUR}:r=30",
    "-filter_complex", filter_str,
    "-map", "[final]",
    "-c:v", "libx264", "-preset", "fast", "-crf", "22",
    "-pix_fmt", "yuv420p",
    OUT
]
print(f"Filter 长度: {len(filter_str)} 字符")
print("开始合成...")
r = subprocess.run(cmd, capture_output=True, text=True, shell=False)
if r.returncode == 0:
    print(f"OK: {OUT}")
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", OUT], capture_output=True, text=True)
    print(f"时长: {p.stdout.strip()}s")
else:
    print(f"!! 失败: {r.stderr[-1500:]}")
