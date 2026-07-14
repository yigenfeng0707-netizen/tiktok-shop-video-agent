# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 数据复盘迭代子 Agent

职责：
1. 采集视频指标数据（有 TIKTOK_API_KEY 时走真实 TikTok Research API，否则回退 mock）
2. 分析高流量视频共性（钩子类型 / BGM / 卖点顺序 / 时长 / 发布时间）
3. 生成脚本优化建议并反哺脚本生成模块
4. 标记低转化模板为待淘汰

依赖：Python 标准库（json / os / random / datetime）；真实 TikTok API 调用需可选依赖 requests。
环境变量：TIKTOK_API_KEY（未配置时自动回退 mock 数据）
"""

import json
import os
import random
from datetime import datetime

try:
    import requests  # 真实 TikTok API 调用依赖；未安装时回退 mock
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


class DataReviewer:
    """数据复盘 Agent：采集指标 → 分析共性 → 生成建议 → 反哺脚本生成模块"""

    def __init__(self, config_path: str = None):
        """加载分析配置

        Args:
            config_path: 可选的自定义配置文件路径（JSON），不存在则使用默认配置
        """
        # 默认分析配置（Demo 阶段）
        self.config = {
            "high_traffic_threshold": 10000,   # 高流量视频阈值（播放量）
            "low_conversion_threshold": 0.01,  # 低转化率阈值
            "min_sample_views": 5000,          # 标记淘汰所需最小样本播放量
            "top_n": 5,                        # 取播放量前 N 条视频
            "countries": ["US", "UK", "ID", "TH", "MY"],
        }
        # 若提供配置文件则覆盖默认配置
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            self.config.update(user_config)

    def collect_metrics(self, video_list: list) -> list:
        """采集视频指标数据。

        有 TIKTOK_API_KEY 时调用真实 TikTok Research API，否则回退 mock 数据。

        Args:
            video_list: 视频列表，每个 dict 含 video_id / country / script / publish_time。

        Returns:
            带 metrics 指标的视频列表 list[dict]，每项在原 video 字段基础上
            新增 metrics 字段（views / ctr / conversion_rate 等）。
        """
        metrics_data = []
        for video in video_list:
            video_id = video.get("video_id")
            # 有 TIKTOK_API_KEY 走真实 API，否则回退 mock
            if os.environ.get("TIKTOK_API_KEY") and requests is not None:
                try:
                    metrics = self._real_tiktok_metrics(video_id)
                except Exception as e:
                    print(
                        "[Warn] TikTok API 调用失败，回退 mock: {0}".format(e)
                    )
                    metrics = self._mock_tiktok_metrics(video_id)
            else:
                metrics = self._mock_tiktok_metrics(video_id)
            video_with_metrics = dict(video)
            video_with_metrics["metrics"] = metrics
            metrics_data.append(video_with_metrics)
        return metrics_data

    def _mock_tiktok_metrics(self, video_id) -> dict:
        """生成模拟 TikTok 指标数据

        播放量 1000-50000 随机，其他指标按合理比例生成。
        基于 video_id 生成稳定随机种子，保证同一视频数据可复现。
        """
        # 基于 video_id 字符生成稳定种子（避免 hash() 跨进程随机化）
        seed = sum(ord(c) for c in str(video_id))
        random.seed(seed)

        # 播放量：1000 - 50000
        views = random.randint(1000, 50000)
        # 点击率：1% - 8%
        ctr = round(random.uniform(0.01, 0.08), 4)
        # 成交转化率：0.5% - 5%
        conversion_rate = round(random.uniform(0.005, 0.05), 4)
        # 完播率：20% - 70%
        completion_rate = round(random.uniform(0.20, 0.70), 4)
        # 互动数据按播放量比例
        likes = int(views * random.uniform(0.02, 0.10))      # 点赞率 2%-10%
        comments = int(views * random.uniform(0.001, 0.01))  # 评论率 0.1%-1%
        shares = int(views * random.uniform(0.001, 0.02))    # 分享率 0.1%-2%

        return {
            "views": views,
            "ctr": ctr,
            "conversion_rate": conversion_rate,
            "completion_rate": completion_rate,
            "likes": likes,
            "comments": comments,
            "shares": shares,
        }

    def _real_tiktok_metrics(self, video_id: str) -> dict:
        """调用 TikTok Research API 采集真实视频指标。

        TikTok Research API 通过 POST /v2/research/video/query/ 查询视频指标，
        需在 TikTok Developers 后台申请 Research API 权限并获取 access_token。
        本方法从环境变量 TIKTOK_API_KEY 读取 access_token，查询指定 video_id 的
        播放 / 互动 / 转化指标，并归一化为与 _mock_tiktok_metrics 一致的字段。

        完整流程：
        1. 从环境变量 TIKTOK_API_KEY 读取 access_token
        2. POST https://open.tiktokapis.com/v2/research/video/query/
           Headers: Authorization: Bearer <access_token>
           Body: {"query": {"and": [{"operation": "EQ",
                  "field_name": "video_id", "field_values": [video_id]}]},
                  "max_count": 1, "fields": ["view_count","like_count",
                  "comment_count","share_count"]}
        3. 解析返回 data.videos[0]，归一化为统一字段结构

        Args:
            video_id: TikTok 视频 ID。

        Returns:
            指标 dict，字段与 _mock_tiktok_metrics 对齐：
            views / ctr / conversion_rate / completion_rate /
            likes / comments / shares。

        Raises:
            RuntimeError: requests 未安装 / API Key 缺失 / 接口返回空时抛出。
        """
        if requests is None:
            raise RuntimeError(
                "requests 未安装，无法调用 TikTok API。请执行 pip install requests"
            )

        access_token = os.environ.get("TIKTOK_API_KEY", "")
        if not access_token:
            raise RuntimeError("未配置 TIKTOK_API_KEY 环境变量")

        url = "https://open.tiktokapis.com/v2/research/video/query/"
        headers = {
            "Authorization": "Bearer {0}".format(access_token),
            "Content-Type": "application/json",
        }
        payload = {
            "query": {
                "and": [
                    {
                        "operation": "EQ",
                        "field_name": "video_id",
                        "field_values": [str(video_id)],
                    }
                ]
            },
            "max_count": 1,
            "fields": [
                "view_count",
                "like_count",
                "comment_count",
                "share_count",
            ],
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        videos = data.get("videos", [])
        if not videos:
            raise RuntimeError(
                "TikTok API 未返回视频数据，video_id={0}".format(video_id)
            )

        v = videos[0]
        views = int(v.get("view_count", 0))
        likes = int(v.get("like_count", 0))
        comments = int(v.get("comment_count", 0))
        shares = int(v.get("share_count", 0))
        # 互动率与转化率由基础指标估算（TikTok Research API 不直接返回转化率）
        ctr = round(likes / views, 4) if views else 0.0
        conversion_rate = round(shares / views * 0.5, 4) if views else 0.0
        completion_rate = round(0.4, 4)  # 占位，真实值需结合视频时长与平均观看时长

        return {
            "views": views,
            "ctr": ctr,
            "conversion_rate": conversion_rate,
            "completion_rate": completion_rate,
            "likes": likes,
            "comments": comments,
            "shares": shares,
        }

    def analyze_high_traffic_patterns(self, metrics_data: list) -> dict:
        """分析高流量视频共性。

        - 高流量视频：播放量 > high_traffic_threshold
        - 识别开头钩子类型、BGM 类型、卖点顺序共性
        - 返回 {common_patterns, top_videos, low_conversion_templates}

        Args:
            metrics_data: collect_metrics 返回的带指标视频列表。

        Returns:
            分析结果 dict，字段包含 common_patterns / analysis_summary /
            top_videos / low_conversion_templates / high_traffic_count / total_count。
        """
        threshold = self.config["high_traffic_threshold"]

        # 筛选高流量视频
        high_traffic_videos = [
            v for v in metrics_data
            if v.get("metrics", {}).get("views", 0) > threshold
        ]

        # 按播放量降序取 Top N
        sorted_videos = sorted(
            metrics_data,
            key=lambda v: v.get("metrics", {}).get("views", 0),
            reverse=True,
        )
        top_videos = sorted_videos[: self.config["top_n"]]

        # 调用 LLM 分析共性（Demo 用 mock）
        prompt = "分析高流量视频的共性特征：钩子类型、BGM 类型、卖点顺序、时长、发布时间"
        analysis = self._mock_llm_analysis(prompt, high_traffic_videos)

        # 识别低转化模板
        low_conversion_templates = self.mark_low_conversion_templates(
            {"metrics_data": metrics_data}
        )

        return {
            "common_patterns": analysis.get("common_patterns", {}),
            "analysis_summary": analysis.get("analysis_summary", ""),
            "top_videos": [
                {
                    "video_id": v.get("video_id"),
                    "views": v.get("metrics", {}).get("views"),
                    "conversion_rate": v.get("metrics", {}).get("conversion_rate"),
                    "hook_type": v.get("hook_type"),
                    "bgm_type": v.get("bgm_type"),
                    "country": v.get("country"),
                }
                for v in top_videos
            ],
            "low_conversion_templates": low_conversion_templates,
            "high_traffic_count": len(high_traffic_videos),
            "total_count": len(metrics_data),
        }

    def _mock_llm_analysis(self, prompt, data) -> dict:
        """模拟 LLM 分析返回结构化结果

        真实场景：将 prompt + data 发送给 GPT-4 / Claude 等大模型解析。
        Demo 阶段：统计高频字段作为共性特征。
        """
        # 统计钩子类型与 BGM 类型分布
        hook_counter = {}
        bgm_counter = {}
        publish_hours = []
        for v in data:
            hook = v.get("hook_type", "未知")
            bgm = v.get("bgm_type", "未知")
            hook_counter[hook] = hook_counter.get(hook, 0) + 1
            bgm_counter[bgm] = bgm_counter.get(bgm, 0) + 1
            # 提取发布小时
            pt = v.get("publish_time", "")
            if pt and "T" in pt:
                try:
                    hour = int(pt.split("T")[1].split(":")[0])
                    publish_hours.append(hour)
                except (ValueError, IndexError):
                    pass

        # 取最高频共性
        common_hook = max(hook_counter, key=hook_counter.get) if hook_counter else "无"
        common_bgm = max(bgm_counter, key=bgm_counter.get) if bgm_counter else "无"

        # 推断最佳发布时段
        if publish_hours:
            avg_hour = sum(publish_hours) / len(publish_hours)
            if 18 <= avg_hour < 22:
                time_range = "18-22点"
            elif 12 <= avg_hour < 14:
                time_range = "12-14点"
            elif 6 <= avg_hour < 9:
                time_range = "06-09点"
            else:
                time_range = "22-24点"
        else:
            time_range = "18-22点"

        return {
            "common_patterns": {
                "hook_type": common_hook,
                "bgm_type": common_bgm,
                "selling_point_order": ["痛点", "解决方案", "产品展示", "信任背书", "促单"],
                "duration_range": "15-30s",
                "publish_time_range": time_range,
            },
            "analysis_summary": (
                f"高流量视频共性：钩子类型 {common_hook}，"
                f"BGM 类型 {common_bgm}，发布时段集中在 {time_range}"
            ),
        }

    def generate_optimization_suggestions(self, analysis_result: dict) -> list:
        """根据分析结果生成脚本优化建议。

        每条建议包含：
            target_module   脚本生成 / 数字人 / 剪辑
            suggestion_type 优化 / 淘汰
            content         建议内容
            priority        high / medium / low

        Args:
            analysis_result: analyze_high_traffic_patterns 返回的分析结果 dict。

        Returns:
            优化建议列表 list[dict]。
        """
        suggestions = []
        patterns = analysis_result.get("common_patterns", {})

        # 建议 1：基于高流量钩子类型优化脚本
        if patterns.get("hook_type"):
            suggestions.append({
                "target_module": "脚本生成",
                "suggestion_type": "优化",
                "content": f"优先使用 {patterns['hook_type']} 钩子类型，该类型在高流量视频中表现最佳",
                "priority": "high",
            })

        # 建议 2：基于 BGM 类型优化剪辑
        if patterns.get("bgm_type"):
            suggestions.append({
                "target_module": "剪辑",
                "suggestion_type": "优化",
                "content": f"推荐使用 {patterns['bgm_type']} 类型 BGM，有助于提升完播率",
                "priority": "medium",
            })

        # 建议 3：基于卖点顺序优化脚本
        if patterns.get("selling_point_order"):
            suggestions.append({
                "target_module": "脚本生成",
                "suggestion_type": "优化",
                "content": f"建议卖点呈现顺序：{' → '.join(patterns['selling_point_order'])}",
                "priority": "high",
            })

        # 建议 4：基于发布时间优化
        if patterns.get("publish_time_range"):
            suggestions.append({
                "target_module": "脚本生成",
                "suggestion_type": "优化",
                "content": f"建议在 {patterns['publish_time_range']} 发布视频，流量表现更佳",
                "priority": "medium",
            })

        # 建议 5：淘汰低转化模板
        low_templates = analysis_result.get("low_conversion_templates", [])
        if low_templates:
            suggestions.append({
                "target_module": "脚本生成",
                "suggestion_type": "淘汰",
                "content": f"以下模板转化率过低，建议淘汰：{', '.join(low_templates)}",
                "priority": "high",
            })

        # 建议 6：数字人口播优化
        if patterns.get("duration_range"):
            suggestions.append({
                "target_module": "数字人",
                "suggestion_type": "优化",
                "content": f"数字人口播节奏建议适配 {patterns['duration_range']} 时长，语速紧凑",
                "priority": "low",
            })

        return suggestions

    def feedback_to_script_generator(self, suggestions: list) -> dict:
        """将优化建议结构化为脚本生成模块可消费的格式。

        Args:
            suggestions: generate_optimization_suggestions 返回的建议列表。

        Returns:
            dict，字段包含 script_optimizations / template_updates / taboos_updates。
        """
        script_optimizations = []
        template_updates = []
        taboos_updates = []

        for s in suggestions:
            module = s.get("target_module")
            stype = s.get("suggestion_type")
            content = s.get("content")
            priority = s.get("priority")

            if module == "脚本生成":
                if stype == "优化":
                    # 字段级优化项
                    field = "hook_type"
                    if "卖点" in content:
                        field = "selling_point_order"
                    elif "发布" in content:
                        field = "publish_time"
                    script_optimizations.append({
                        "field": field,
                        "action": "update",
                        "content": content,
                        "priority": priority,
                    })
                elif stype == "淘汰":
                    # 模板状态更新
                    template_updates.append({
                        "action": "deprecate",
                        "content": content,
                        "priority": priority,
                    })
                    # 高优先级淘汰项加入禁忌词库
                    if priority == "high":
                        taboos_updates.append(content)
            elif module == "剪辑":
                script_optimizations.append({
                    "field": "bgm_type",
                    "action": "update",
                    "content": content,
                    "priority": priority,
                })
            elif module == "数字人":
                script_optimizations.append({
                    "field": "duration",
                    "action": "update",
                    "content": content,
                    "priority": priority,
                })

        return {
            "script_optimizations": script_optimizations,
            "template_updates": template_updates,
            "taboos_updates": taboos_updates,
        }

    def mark_low_conversion_templates(self, analysis_result: dict) -> list:
        """标记低转化模板为待淘汰。

        筛选条件：转化率 < low_conversion_threshold 且播放量 > min_sample_views
        （播放量过低样本不足，不轻易淘汰）。

        Args:
            analysis_result: 含 metrics_data 字段的分析结果 dict。

        Returns:
            待淘汰模板 video_id 列表 list[str]。
        """
        low_threshold = self.config["low_conversion_threshold"]
        min_views = self.config["min_sample_views"]
        metrics_data = analysis_result.get("metrics_data", [])

        deprecated = []
        for v in metrics_data:
            metrics = v.get("metrics", {})
            conv = metrics.get("conversion_rate", 0)
            views = metrics.get("views", 0)
            if conv < low_threshold and views > min_views:
                deprecated.append(v.get("video_id"))
        return deprecated

    def run_full_review(self, video_list: list) -> dict:
        """完整复盘流程：采集数据 → 分析共性 → 生成建议 → 反哺脚本模块。

        依次执行 collect_metrics → analyze_high_traffic_patterns →
        generate_optimization_suggestions → feedback_to_script_generator，
        返回完整复盘报告。有 TIKTOK_API_KEY 时使用真实指标，否则回退 mock。

        Args:
            video_list: 待复盘视频列表，每个 dict 含 video_id / country /
                hook_type / bgm_type / publish_time 等字段。

        Returns:
            复盘报告 dict，字段包含 review_time / total_videos / metrics_data /
            analysis_result / optimization_suggestions / script_feedback / summary。
        """
        # 1. 采集指标数据
        metrics_data = self.collect_metrics(video_list)

        # 2. 分析高流量共性
        analysis_result = self.analyze_high_traffic_patterns(metrics_data)

        # 3. 生成优化建议
        suggestions = self.generate_optimization_suggestions(analysis_result)

        # 4. 反哺脚本生成模块
        feedback = self.feedback_to_script_generator(suggestions)

        return {
            "review_time": datetime.now().isoformat(),
            "total_videos": len(video_list),
            "metrics_data": metrics_data,
            "analysis_result": analysis_result,
            "optimization_suggestions": suggestions,
            "script_feedback": feedback,
            "summary": (
                f"复盘完成：共分析 {len(video_list)} 条视频，"
                f"高流量 {analysis_result.get('high_traffic_count', 0)} 条，"
                f"生成 {len(suggestions)} 条优化建议"
            ),
        }
