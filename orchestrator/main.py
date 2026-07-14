# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 本地化生产 Agent - 主编排工作流

主编排 Agent 负责串联以下 4 个子 Agent，构成完整生产流水线：
    步骤 1：ScriptGenerator      —— 多国本地化脚本生成
    步骤 2：DigitalHumanGenerator —— 多国数字人口播视频生成
    步骤 3：BatchEditor           —— 批量剪辑（字幕 / 贴纸 / BGM / 模板）
    步骤 4：DataReviewer          —— 数据复盘与优化建议反哺

设计要点：
- 单步失败仅记录错误并继续，不中断整条流水线
- 每步记录耗时，便于 Demo 展示与性能分析
- 提供 run_step 单步运行接口，便于分步演示
- 仅依赖 Python 标准库
"""

import json
import os
import time

from agents.script_generator import ScriptGenerator
from agents.digital_human import DigitalHumanGenerator
from agents.batch_editor import BatchEditor
from agents.data_reviewer import DataReviewer


class Orchestrator:
    """主编排 Agent：调度脚本生成 / 数字人 / 批量剪辑 / 数据复盘 4 步流水线。

    通过组合 4 个子 Agent，实现「一个产品 → 多国本地化短视频」的端到端生产，
    并对每步产出进行耗时统计与错误隔离。
    """

    def __init__(self, project_root=None):
        """初始化主编排 Agent，加载国家配置与 4 个子 Agent。

        Args:
            project_root: 项目根目录。默认为本文件上一级目录（即项目根）。
        """
        # 定位项目根目录：orchestrator/../
        if project_root is None:
            project_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            )
        self.project_root = project_root

        config_dir = os.path.join(project_root, "config")

        # 加载国家配置（用于状态展示与国家校验）
        self.country_config = self._load_json(
            os.path.join(config_dir, "country_config.json")
        )
        # 加载 mock 视频数据（数据复盘步骤使用）
        self.mock_videos = self._load_json(
            os.path.join(config_dir, "mock_data.json")
        ).get("videos", [])

        # 初始化 4 个子 Agent
        self.script_generator = ScriptGenerator(config_dir=config_dir)
        self.digital_human = DigitalHumanGenerator(config_dir=config_dir)
        self.batch_editor = BatchEditor(
            config_dir=config_dir,
            templates_dir=os.path.join(project_root, "templates"),
        )
        self.data_reviewer = DataReviewer()

        # 流水线运行状态
        self._status = {
            "pipeline": "idle",          # idle / running / done
            "current_step": 0,           # 当前执行步骤 1-4
            "total_steps": 4,
            "step_names": ["脚本生成", "数字人视频", "批量剪辑", "数据复盘"],
            "errors": [],                # 各步错误记录
            "last_run": None,            # 上次运行摘要
        }

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    @staticmethod
    def _load_json(path):
        """以 UTF-8 编码读取 JSON 配置文件。"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ------------------------------------------------------------------
    # 主流水线
    # ------------------------------------------------------------------
    def run_pipeline(
        self,
        product_info: dict,
        countries: list,
        platform_style: str = "tiktok_short",
        raw_footage_path: str = "",
    ) -> dict:
        """运行完整 4 步流水线。

        Args:
            product_info: 产品信息 dict（title / selling_points / category /
                          target_audience / price_range）。
            countries: 目标国家代码列表（US / VN / SA / GB / ID）。
            platform_style: 平台风格偏好（用于记录与单步调用）。
            raw_footage_path: 产品实拍素材路径，可为空（Demo 阶段不强制要求）。

        Returns:
            dict，包含 pipeline_result / scripts / videos / edited_videos /
            review_report / total_time / step_times / errors。
        """
        total_start = time.time()
        self._status["pipeline"] = "running"
        self._status["current_step"] = 0
        self._status["errors"] = []

        step_times = {}
        scripts, videos, edited_videos = [], [], []
        review_report = None

        # ===== 步骤 1：脚本生成 =====
        self._status["current_step"] = 1
        print("[步骤 1/4] 开始生成多国本地化脚本...")
        t0 = time.time()
        try:
            scripts = self.script_generator.generate_batch(product_info, countries)
            step_times["step1_script"] = round(time.time() - t0, 3)
            ok_count = sum(1 for s in scripts if "error" not in s)
            print(
                "[步骤 1/4] 脚本生成完成，成功 {0}/{1} 条，耗时 {2}s".format(
                    ok_count, len(scripts), step_times["step1_script"]
                )
            )
        except Exception as e:
            step_times["step1_script"] = round(time.time() - t0, 3)
            self._status["errors"].append({"step": 1, "error": str(e)})
            print("[步骤 1/4] 脚本生成失败: {0}".format(e))

        # ===== 步骤 2：数字人视频生成 =====
        self._status["current_step"] = 2
        print("[步骤 2/4] 开始生成多国数字人视频...")
        t0 = time.time()
        try:
            # 过滤掉脚本生成失败的国家，保持脚本与国家一一对应
            valid_pairs = [
                (s, c) for s, c in zip(scripts, countries) if "error" not in s
            ]
            if valid_pairs:
                valid_scripts = [p[0] for p in valid_pairs]
                valid_countries = [p[1] for p in valid_pairs]
                videos = self.digital_human.generate_batch(
                    valid_scripts, valid_countries
                )
            else:
                videos = []
            step_times["step2_digital_human"] = round(time.time() - t0, 3)
            ok_count = sum(1 for v in videos if "error" not in v)
            print(
                "[步骤 2/4] 数字人视频生成完成，成功 {0}/{1} 条，耗时 {2}s".format(
                    ok_count, len(videos), step_times["step2_digital_human"]
                )
            )
        except Exception as e:
            step_times["step2_digital_human"] = round(time.time() - t0, 3)
            self._status["errors"].append({"step": 2, "error": str(e)})
            print("[步骤 2/4] 数字人视频生成失败: {0}".format(e))

        # ===== 步骤 3：批量剪辑 =====
        self._status["current_step"] = 3
        print("[步骤 3/4] 开始批量剪辑...")
        t0 = time.time()
        try:
            # 剪辑模块的 product_info 使用 product_name 字段，这里基于 title 补充
            editor_product_info = dict(product_info)
            editor_product_info.setdefault(
                "product_name", product_info.get("title", "product")
            )
            items = []
            for v in videos:
                if "error" in v:
                    continue
                items.append(
                    {
                        "digital_human_result": v,
                        "raw_footage_path": raw_footage_path,
                        "country": v.get("country", ""),
                        "product_info": editor_product_info,
                    }
                )
            if items:
                edited_videos = self.batch_editor.batch_edit(items)
            else:
                edited_videos = []
            step_times["step3_batch_edit"] = round(time.time() - t0, 3)
            print(
                "[步骤 3/4] 批量剪辑完成，产出 {0} 条，耗时 {1}s".format(
                    len(edited_videos), step_times["step3_batch_edit"]
                )
            )
        except Exception as e:
            step_times["step3_batch_edit"] = round(time.time() - t0, 3)
            self._status["errors"].append({"step": 3, "error": str(e)})
            print("[步骤 3/4] 批量剪辑失败: {0}".format(e))

        # ===== 步骤 4：数据复盘（使用 mock_data）=====
        self._status["current_step"] = 4
        print("[步骤 4/4] 开始数据复盘...")
        t0 = time.time()
        try:
            review_report = self.data_reviewer.run_full_review(self.mock_videos)
            step_times["step4_data_review"] = round(time.time() - t0, 3)
            print(
                "[步骤 4/4] 数据复盘完成，耗时 {0}s".format(
                    step_times["step4_data_review"]
                )
            )
        except Exception as e:
            step_times["step4_data_review"] = round(time.time() - t0, 3)
            self._status["errors"].append({"step": 4, "error": str(e)})
            print("[步骤 4/4] 数据复盘失败: {0}".format(e))

        # 汇总
        total_time = round(time.time() - total_start, 3)
        self._status["pipeline"] = "done"
        self._status["last_run"] = {
            "total_time": total_time,
            "step_times": step_times,
            "scripts_count": len(scripts),
            "videos_count": len(videos),
            "edited_count": len(edited_videos),
            "review_done": review_report is not None,
        }

        return {
            "pipeline_result": "success" if not self._status["errors"] else "partial",
            "scripts": scripts,
            "videos": videos,
            "edited_videos": edited_videos,
            "review_report": review_report,
            "total_time": total_time,
            "step_times": step_times,
            "errors": self._status["errors"],
        }

    # ------------------------------------------------------------------
    # 单步运行（用于 Demo 分步展示）
    # ------------------------------------------------------------------
    def run_step(self, step: int, *args) -> dict:
        """单独运行某一步，便于 Demo 分步展示与调试。

        Args:
            step: 步骤序号 1-4。
            *args: 该步骤所需的参数：
                步骤 1: (product_info, countries)
                步骤 2: (scripts, countries)
                步骤 3: (items,)  —— 批量剪辑任务列表
                步骤 4: (video_list,)  —— 待复盘视频列表

        Returns:
            该步骤的产出结果 dict。

        Raises:
            ValueError: 当 step 不在 1-4 范围内时抛出。
        """
        if step == 1:
            print("[单独运行 步骤 1] 脚本生成")
            self._status["current_step"] = 1
            return self.script_generator.generate_batch(args[0], args[1])
        elif step == 2:
            print("[单独运行 步骤 2] 数字人视频生成")
            self._status["current_step"] = 2
            return self.digital_human.generate_batch(args[0], args[1])
        elif step == 3:
            print("[单独运行 步骤 3] 批量剪辑")
            self._status["current_step"] = 3
            return self.batch_editor.batch_edit(args[0])
        elif step == 4:
            print("[单独运行 步骤 4] 数据复盘")
            self._status["current_step"] = 4
            return self.data_reviewer.run_full_review(args[0])
        else:
            raise ValueError(
                "无效步骤: {0}，仅支持 1-4".format(step)
            )

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------
    def get_status(self) -> dict:
        """返回当前流水线状态。"""
        return dict(self._status)
