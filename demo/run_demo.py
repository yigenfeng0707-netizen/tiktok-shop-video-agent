# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 本地化生产 Agent - Demo 入口脚本

直接运行：
    python demo/run_demo.py

功能：以「便携榨汁杯」为测试产品，面向 5 个国家（US/VN/SA/GB/ID），
运行完整 4 步流水线（脚本生成→数字人→批量剪辑→数据复盘），
并打印每步耗时、产出数量与关键产出预览。
"""

import os
import sys

# 将项目根目录加入 sys.path，便于以包形式导入 orchestrator / agents
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orchestrator import Orchestrator


def main():
    """Demo 主流程：构造测试产品 → 运行流水线 → 打印结果。"""
    # 测试产品：便携榨汁杯
    product_info = {
        "title": "便携榨汁杯 Portable Juicer",
        "selling_points": [
            "USB充电",
            "304不锈钢刀头",
            "30秒快速榨汁",
            "500ml大容量",
            "便携旅行",
        ],
        "category": "kitchen_appliances",
        "target_audience": "年轻上班族、健身爱好者",
        "price_range": "$15-30",
    }
    # 目标国家：美国 / 越南 / 沙特 / 英国 / 印尼
    countries = ["US", "VN", "SA", "GB", "ID"]
    # 平台风格
    platform_style = "tiktok_short_video"

    print("=" * 60)
    print("TikTok Shop 跨境短视频 AI 本地化生产 Agent - Demo")
    print("=" * 60)
    print("产品: {0}".format(product_info["title"]))
    print("目标国家: {0}".format(", ".join(countries)))
    print("平台风格: {0}".format(platform_style))
    print("-" * 60)

    # 初始化主编排 Agent
    orchestrator = Orchestrator()

    # 运行完整流水线
    result = orchestrator.run_pipeline(
        product_info=product_info,
        countries=countries,
        platform_style=platform_style,
        raw_footage_path="",
    )

    # ===== 打印详细结果 =====
    print("\n" + "=" * 60)
    print("流水线结果详情")
    print("=" * 60)
    print("总体结果: {0}".format(result["pipeline_result"]))
    print("总耗时: {0}s".format(result["total_time"]))

    # 各步耗时
    print("\n[各步耗时]")
    for step_name, elapsed in result["step_times"].items():
        print("  - {0}: {1}s".format(step_name, elapsed))

    # 步骤 1：脚本生成
    print("\n[步骤 1 脚本生成] 产出 {0} 条".format(len(result["scripts"])))
    for s in result["scripts"][:1]:
        preview = s.get("hook", "") or s.get("error", "")
        print("  预览(首条): {0}".format(preview[:70]))

    # 步骤 2：数字人视频
    print("\n[步骤 2 数字人视频] 产出 {0} 条".format(len(result["videos"])))
    for v in result["videos"][:1]:
        if "error" in v:
            print("  预览(首条): 错误 {0}".format(v["error"]))
        else:
            print(
                "  预览(首条): 国家={0} 面孔={1} 语种={2}".format(
                    v.get("country"),
                    v.get("face_type"),
                    v.get("language"),
                )
            )

    # 步骤 3：批量剪辑
    print("\n[步骤 3 批量剪辑] 产出 {0} 条".format(len(result["edited_videos"])))
    for e in result["edited_videos"][:1]:
        preview = e.get("output_path", "") or e.get("error", "")
        print("  预览(首条): {0}".format(preview[:80]))

    # 步骤 4：数据复盘
    print("\n[步骤 4 数据复盘]")
    review_report = result["review_report"]
    if review_report:
        print("  {0}".format(review_report.get("summary", "")))
        suggestions = review_report.get("optimization_suggestions", [])
        print("  优化建议数: {0}".format(len(suggestions)))
        for sug in suggestions[:3]:
            print(
                "    - [{0}][{1}] {2}".format(
                    sug.get("target_module"),
                    sug.get("priority"),
                    sug.get("content", "")[:60],
                )
            )

    # 错误记录
    if result.get("errors"):
        print("\n[错误记录]")
        for err in result["errors"]:
            print("  - 步骤 {0}: {1}".format(err.get("step"), err.get("error")))

    # 总结
    print("\n" + "=" * 60)
    print("Demo 运行完成")
    print("  脚本: {0} 条 | 数字人视频: {1} 条 | 剪辑成片: {2} 条".format(
        len(result["scripts"]),
        len(result["videos"]),
        len(result["edited_videos"]),
    ))
    print("=" * 60)


if __name__ == "__main__":
    # 捕获异常并打印，保证 Demo 不崩溃
    try:
        main()
    except Exception as e:
        print("[Demo 异常] {0}: {1}".format(type(e).__name__, e))
        sys.exit(1)
