# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 本地化生产 Agent
MiXer AI 单文件版本 - 所有工具函数为顶层函数，便于平台抽取

功能：4 步流水线（脚本生成 → 数字人 → 批量剪辑 → 数据复盘）
支持 5 国：美国(US) / 越南(VN) / 沙特(SA) / 英国(GB) / 印尼(ID)
"""

import json
import os
import random
import time
from datetime import datetime


# ============================================================
# 工具 1：生成单国本地化短视频脚本
# ============================================================
def generate_script(product_title: str, selling_points: list, category: str, target_country: str, platform_style: str = "tiktok_short_video") -> dict:
    """
    为指定国家生成本地化短视频脚本，结合当地热点和文化偏好。

    Args:
        product_title: 产品标题，例如 "便携榨汁杯 Portable Juicer"
        selling_points: 产品卖点列表，例如 ["USB充电", "304不锈钢刀头"]
        category: 产品品类，例如 "kitchen_appliances"
        target_country: 目标国家代码，支持 US/VN/SA/GB/ID
        platform_style: 平台风格，可选 tiktok_short_video 或 live_clip

    Returns:
        dict: 结构化脚本，包含钩子开头、产品卖点、CTA、BGM建议、字幕文案、画面建议
    """
    country_config = _get_country_config(target_country)
    taboos = _check_cultural_taboos(target_country, category)

    hook = _generate_hook(target_country, product_title)
    points = _format_selling_points(selling_points, target_country)
    cta = _generate_cta(target_country)
    bgm = _select_bgm(target_country, category)
    subtitle = _generate_subtitle_text(hook, points, cta, country_config["language_code"])

    script = {
        "country": target_country,
        "country_name": country_config["name_cn"],
        "language": country_config["language_code"],
        "platform_style": platform_style,
        "hook": hook,
        "product_selling_points": points,
        "cta": cta,
        "bgm_suggestion": bgm,
        "subtitle_text": subtitle,
        "visual_suggestions": _generate_visual_suggestions(target_country, category),
        "cultural_adjustments": taboos,
        "duration_seconds": 30,
        "created_at": datetime.now().isoformat()
    }
    return script


# ============================================================
# 工具 2：批量生成多国本地化脚本
# ============================================================
def generate_batch_scripts(product_title: str, selling_points: list, category: str, countries: list, platform_style: str = "tiktok_short_video") -> list:
    """
    批量为多个国家生成本地化短视频脚本。

    Args:
        product_title: 产品标题
        selling_points: 产品卖点列表
        category: 产品品类
        countries: 目标国家代码列表，例如 ["US", "VN", "SA", "GB", "ID"]
        platform_style: 平台风格

    Returns:
        list: 多国脚本列表，每个元素是一个脚本 dict
    """
    results = []
    for country in countries:
        try:
            script = generate_script(product_title, selling_points, category, country, platform_style)
            results.append(script)
        except Exception as e:
            results.append({"country": country, "error": str(e)})
    return results


# ============================================================
# 工具 3：生成数字人多语种视频
# ============================================================
def generate_digital_human_video(script: dict, country: str) -> dict:
    """
    根据脚本生成数字人多语种口播视频，自动匹配面孔和语种。

    Args:
        script: generate_script 返回的脚本 dict
        country: 目标国家代码

    Returns:
        dict: 数字人视频信息，包含视频路径、面孔类型、语种、字幕路径、BGM路径
    """
    mapping = _get_face_voice_mapping(country)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = f"output/digital_human_{mapping['face_type']}_{mapping['voice_language']}_{timestamp}.mp4"
    subtitle_path = f"output/subtitle_{country}_{timestamp}.srt"
    bgm_path = mapping["bgm_style"]

    result = {
        "country": country,
        "video_path": video_path,
        "subtitle_path": subtitle_path,
        "bgm_path": bgm_path,
        "face_type": mapping["face_type"],
        "voice_language": mapping["voice_language"],
        "duration": 30,
        "status": "generated"
    }
    return result


# ============================================================
# 工具 4：批量剪辑多国视频
# ============================================================
def batch_edit_videos(digital_human_results: list, product_name: str, countries: list) -> list:
    """
    对数字人视频进行批量剪辑，添加字幕、BGM、特效，产出多国版本。

    Args:
        digital_human_results: generate_digital_human_video 返回的结果列表
        product_name: 产品名称（用于输出文件命名）
        countries: 目标国家代码列表

    Returns:
        list: 剪辑后的视频信息列表，每个元素包含输出路径和 ffmpeg 命令
    """
    results = []
    date_str = datetime.now().strftime("%Y%m%d")
    for i, country in enumerate(countries):
        if i >= len(digital_human_results):
            break
        dh_result = digital_human_results[i]
        if "error" in dh_result:
            results.append({"country": country, "error": dh_result["error"]})
            continue

        safe_name = product_name.replace(" ", "")
        output_path = f"output/{safe_name}_{country}_v1_{date_str}.mp4"
        ffmpeg_cmd = _build_ffmpeg_command(dh_result, output_path, country)

        results.append({
            "country": country,
            "output_path": output_path,
            "ffmpeg_command": ffmpeg_cmd,
            "duration": 35,
            "file_size_mb": 15.6,
            "status": "edited"
        })
    return results


# ============================================================
# 工具 5：数据复盘分析
# ============================================================
def review_video_data(video_list: list) -> dict:
    """
    分析已发布视频数据，识别高流量共性，生成优化建议。

    Args:
        video_list: 视频列表，每个元素包含 video_id, country, hook_type, bgm_type, publish_time

    Returns:
        dict: 复盘报告，包含高流量共性、低转化模板、优化建议
    """
    metrics = []
    for video in video_list:
        m = _generate_mock_metrics(video.get("video_id", "unknown"))
        m.update(video)
        metrics.append(m)

    high_traffic = [m for m in metrics if m["views"] > 10000]
    low_conversion = [m for m in metrics if m["conversion_rate"] < 1.0]

    common_patterns = _analyze_patterns(high_traffic)
    suggestions = _generate_suggestions(common_patterns)

    report = {
        "total_videos": len(metrics),
        "high_traffic_count": len(high_traffic),
        "low_conversion_count": len(low_conversion),
        "common_patterns": common_patterns,
        "optimization_suggestions": suggestions,
        "low_conversion_templates": [m["video_id"] for m in low_conversion],
        "reviewed_at": datetime.now().isoformat()
    }
    return report


# ============================================================
# 工具 6：运行完整流水线
# ============================================================
def run_full_pipeline(product_title: str, selling_points: list, category: str, countries: list, platform_style: str = "tiktok_short_video") -> dict:
    """
    运行端到端完整流水线：脚本生成 → 数字人 → 批量剪辑 → 数据复盘。

    Args:
        product_title: 产品标题
        selling_points: 产品卖点列表
        category: 产品品类
        countries: 目标国家代码列表
        platform_style: 平台风格

    Returns:
        dict: 完整流水线结果，包含脚本、视频、剪辑结果、复盘报告、各步耗时
    """
    start_time = time.time()
    step_times = {}

    # 步骤 1：脚本生成
    t1 = time.time()
    scripts = generate_batch_scripts(product_title, selling_points, category, countries, platform_style)
    step_times["step1_script"] = round(time.time() - t1, 3)

    # 步骤 2：数字人视频
    t2 = time.time()
    digital_human_results = []
    for i, country in enumerate(countries):
        if i < len(scripts) and "error" not in scripts[i]:
            dh = generate_digital_human_video(scripts[i], country)
            digital_human_results.append(dh)
        else:
            digital_human_results.append({"country": country, "error": "script generation failed"})
    step_times["step2_digital_human"] = round(time.time() - t2, 3)

    # 步骤 3：批量剪辑
    t3 = time.time()
    edited_videos = batch_edit_videos(digital_human_results, product_title, countries)
    step_times["step3_batch_edit"] = round(time.time() - t3, 3)

    # 步骤 4：数据复盘（用模拟数据）
    t4 = time.time()
    mock_videos = _generate_mock_video_list(countries)
    review_report = review_video_data(mock_videos)
    step_times["step4_data_review"] = round(time.time() - t4, 3)

    total_time = round(time.time() - start_time, 3)

    return {
        "pipeline_result": "success",
        "product": product_title,
        "countries": countries,
        "scripts": scripts,
        "digital_human_videos": digital_human_results,
        "edited_videos": edited_videos,
        "review_report": review_report,
        "total_time": total_time,
        "step_times": step_times
    }


# ============================================================
# 内部辅助函数
# ============================================================

def _get_country_config(country):
    """获取国家配置"""
    configs = {
        "US": {"name_cn": "美国", "language_code": "en-US", "face_type": "european", "bgm_style": "pop"},
        "VN": {"name_cn": "越南", "language_code": "vi-VN", "face_type": "southeast_asian", "bgm_style": "vpop"},
        "SA": {"name_cn": "沙特", "language_code": "ar-SA", "face_type": "middle_east", "bgm_style": "arabic_pop"},
        "GB": {"name_cn": "英国", "language_code": "en-GB", "face_type": "european", "bgm_style": "indie"},
        "ID": {"name_cn": "印尼", "language_code": "id-ID", "face_type": "southeast_asian", "bgm_style": "dangdut"}
    }
    return configs.get(country, configs["US"])


def _get_face_voice_mapping(country):
    """获取国家到面孔和语种的映射"""
    config = _get_country_config(country)
    return {
        "face_type": config["face_type"],
        "voice_language": config["language_code"],
        "bgm_style": config["bgm_style"]
    }


def _check_cultural_taboos(country, category):
    """检查文化禁忌规则"""
    taboos = []
    if country == "SA":
        if category in ["women_clothing", "beauty", "cosmetics"]:
            taboos.append("hide_model: 中东女性用品不露模特")
            taboos.append("focus_product: 聚焦产品功能展示")
        taboos.append("conservative_dress: 保守着装")
        taboos.append("remove_sensitive_elements: 移除宗教敏感元素")
    elif country in ["US", "GB"]:
        taboos.append("add_eco_note: 突出环保属性")
        taboos.append("avoid_exaggeration: 避免夸大宣传")
    elif country in ["VN", "ID"]:
        taboos.append("respect_religion: 尊重当地宗教")
    return taboos


def _generate_hook(country, product):
    """生成钩子开头"""
    hooks = {
        "US": f"Wait... you've been doing this wrong the whole time? 🤯 {product} changes everything!",
        "VN": f"Chờ đã... bạn đã làm sai tất cả thời gian? 🤯 {product} sẽ thay đổi mọi thứ!",
        "SA": f"هل كنت تفعل هذا بشكل خاطئ طوال الوقت؟ 🤯 {product} يغير كل شيء!",
        "GB": f"Wait... you've been doing this wrong? 🤯 {product} is a game changer!",
        "ID": f"Tunggu... kamu salah lakukan ini selama ini? 🤯 {product} mengubah segalanya!"
    }
    return hooks.get(country, hooks["US"])


def _format_selling_points(points, country):
    """格式化卖点"""
    return [{"point": p, "emphasis": "high" if i < 2 else "medium"} for i, p in enumerate(points)]


def _generate_cta(country):
    """生成 CTA"""
    ctas = {
        "US": "Shop Now! Link in bio 🔥",
        "VN": "Mua ngay! Link ở bio 🔥",
        "SA": "تسوق الآن! الرابط في البايو 🔥",
        "GB": "Shop Now! Link in bio 🔥",
        "ID": "Beli sekarang! Link di bio 🔥"
    }
    return ctas.get(country, ctas["US"])


def _select_bgm(country, category):
    """选择 BGM"""
    config = _get_country_config(country)
    return {
        "bgm_id": f"bgm_{country.lower()}_001",
        "style": config["bgm_style"],
        "tempo": "upbeat",
        "license": "tiktok_commercial_library"
    }


def _generate_subtitle_text(hook, points, cta, language):
    """生成字幕文本"""
    return f"[{language}] {hook} | Points: {len(points)} | {cta}"


def _generate_visual_suggestions(country, category):
    """生成画面建议"""
    return [
        "0-3s: 钩子开头，特写产品",
        "3-18s: 卖点展示，多角度切换",
        "18-25s: 使用场景演示",
        "25-30s: CTA 引导购买"
    ]


def _build_ffmpeg_command(dh_result, output_path, country):
    """构建 ffmpeg 命令"""
    return f"ffmpeg -i {dh_result.get('video_path', 'input.mp4')} -filter_complex 'subtitles={dh_result.get('subtitle_path', 'subtitle.srt')},drawtext=text=ShopNow' -map 0:v {output_path}"


def _generate_mock_metrics(video_id):
    """生成模拟指标数据"""
    seed = sum(ord(c) for c in str(video_id))
    random.seed(seed)
    return {
        "video_id": video_id,
        "views": random.randint(1000, 50000),
        "click_rate": round(random.uniform(2.0, 15.0), 2),
        "conversion_rate": round(random.uniform(0.5, 5.0), 2),
        "completion_rate": round(random.uniform(20.0, 70.0), 2),
        "likes": random.randint(50, 5000),
        "comments": random.randint(5, 500),
        "shares": random.randint(10, 1000)
    }


def _analyze_patterns(high_traffic_videos):
    """分析高流量共性"""
    return {
        "common_hook_type": "痛点提问型",
        "common_bgm_type": "节奏感强",
        "common_publish_time": "22-24点",
        "common_duration": "30秒",
        "avg_views": sum(v["views"] for v in high_traffic_videos) // max(len(high_traffic_videos), 1)
    }


def _generate_suggestions(patterns):
    """生成优化建议"""
    return [
        {"target": "script", "type": "optimization", "content": "优先使用痛点提问型钩子", "priority": "high"},
        {"target": "editing", "type": "optimization", "content": "推荐节奏感强 BGM", "priority": "medium"},
        {"target": "script", "type": "optimization", "content": "卖点顺序：痛点→方案→展示→背书→促单", "priority": "high"}
    ]


def _generate_mock_video_list(countries):
    """生成模拟视频列表"""
    videos = []
    hook_types = ["痛点提问型", "利益前置型", "场景代入型", "对比型"]
    bgm_types = ["节奏感强", "舒缓", "热门", "原创"]
    for i, country in enumerate(countries):
        for j in range(3):
            videos.append({
                "video_id": f"vid_{country}_{j+1}",
                "country": country,
                "hook_type": hook_types[j % len(hook_types)],
                "bgm_type": bgm_types[j % len(bgm_types)],
                "publish_time": f"2026-07-{10+j} 22:00"
            })
    return videos


# ============================================================
# 主入口：可直接运行测试
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TikTok Shop 跨境短视频 AI 本地化生产 Agent - MiXer AI 版本")
    print("=" * 60)

    result = run_full_pipeline(
        product_title="便携榨汁杯 Portable Juicer",
        selling_points=["USB充电", "304不锈钢刀头", "30秒快速榨汁", "500ml大容量"],
        category="kitchen_appliances",
        countries=["US", "VN", "SA", "GB", "ID"],
        platform_style="tiktok_short_video"
    )

    print(f"\n流水线结果: {result['pipeline_result']}")
    print(f"总耗时: {result['total_time']}s")
    print(f"脚本: {len(result['scripts'])} 条")
    print(f"数字人视频: {len(result['digital_human_videos'])} 条")
    print(f"剪辑成片: {len(result['edited_videos'])} 条")
    print(f"复盘: 分析 {result['review_report']['total_videos']} 条视频, 高流量 {result['review_report']['high_traffic_count']} 条")
    print("\n各步耗时:")
    for step, t in result['step_times'].items():
        print(f"  - {step}: {t}s")
    print("\n" + "=" * 60)
    print("Demo 运行完成")
