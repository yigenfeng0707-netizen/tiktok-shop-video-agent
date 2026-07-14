# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 批量剪辑子 Agent
基于 ffmpeg + 模板系统，对数字人视频与实拍素材进行裁剪、拼接、
字幕烧录、贴纸叠加、BGM 混音，一键批量产出多国版本。
Demo 阶段仅生成 ffmpeg 命令字符串并打印，不实际执行。
"""
import json
from datetime import datetime
from pathlib import Path


class BatchEditor:
    """批量剪辑器：应用视频模板、烧录字幕、添加带货特效、混入 BGM"""

    def __init__(
        self,
        ffmpeg_path: str = "ffmpeg",
        config_dir: str = "config",
        templates_dir: str = "templates",
    ):
        self.ffmpeg_path = ffmpeg_path

        project_root = Path(__file__).resolve().parent.parent

        # 定位模板目录
        t_dir = Path(templates_dir)
        if not t_dir.is_absolute():
            t_dir = project_root / templates_dir
        self.templates_dir = t_dir

        # 加载视频模板
        with open(self.templates_dir / "video_template.json", "r", encoding="utf-8") as f:
            self.video_template = json.load(f)

        # 加载特效配置
        with open(
            self.templates_dir / "effects" / "effects_config.json", "r", encoding="utf-8"
        ) as f:
            self.effects_config = json.load(f)

        # 输出目录
        self.output_dir = project_root / "assets" / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def edit_video(
        self,
        digital_human_result: dict,
        raw_footage_path: str,
        country: str,
        product_info: dict,
    ) -> dict:
        """编辑单条视频：拼接数字人视频与实拍素材、应用模板、字幕、贴纸、BGM。

        依次执行：应用视频模板（滤镜链）→ 字幕烧录 → 带货特效贴纸 → BGM 混音 →
        拼接完整 ffmpeg 命令。Demo 阶段仅生成命令字符串并打印，不实际执行。

        Args:
            digital_human_result: 数字人 Agent 输出 dict，含 video_path /
                subtitle_path / bgm_path 等字段。
            raw_footage_path: 产品实拍素材路径，可为空。
            country: 目标国家代码（US / VN / SA / GB / ID）。
            product_info: 产品信息 dict（含 product_name / category 等）。

        Returns:
            dict，字段包含 output_path / ffmpeg_command / duration /
            file_size_mb / country / product_name。
        """
        video_path = digital_human_result.get("video_path", "")
        srt_path = digital_human_result.get("subtitle_path", "")
        bgm_path = digital_human_result.get("bgm_path", "")

        product_name = product_info.get("product_name", "product")

        # 1. 应用视频模板（返回 ffmpeg 滤镜链）
        filter_chain = self._apply_template(
            video_path, self.video_template.get("template_name", "default")
        )

        # 2. 字幕烧录命令
        subtitle_cmd = self._add_subtitles(video_path, srt_path)

        # 3. 添加带货特效贴纸（默认使用价格爆炸框）
        sticker_cmd = self._add_stickers(video_path, "price_burst")

        # 4. 混入 BGM
        bgm_cmd = self._add_bgm(video_path, bgm_path)

        # 5. 生成输出文件名
        output_filename = self._generate_output_filename(product_name, country, "v1")
        output_path = str(self.output_dir / output_filename)

        # 6. 拼接完整 ffmpeg 命令（Demo 阶段仅打印不执行）
        ffmpeg_command = self._build_full_command(
            video_path=video_path,
            raw_footage_path=raw_footage_path,
            output_path=output_path,
            filter_chain=filter_chain,
            subtitle_cmd=subtitle_cmd,
            sticker_cmd=sticker_cmd,
            bgm_cmd=bgm_cmd,
        )

        print(f"[Mock] 批量剪辑 ffmpeg 命令（不实际执行）:\n{ffmpeg_command}")

        # 模拟返回值
        duration = self.video_template.get("total_duration_seconds", 35)
        file_size_mb = round(duration * 0.8, 2)  # 占位估算

        return {
            "output_path": output_path,
            "ffmpeg_command": ffmpeg_command,
            "duration": duration,
            "file_size_mb": file_size_mb,
            "country": country,
            "product_name": product_name,
        }

    def _apply_template(self, video_path: str, template_name: str) -> list:
        """
        应用视频模板，返回 ffmpeg 滤镜链列表
        模板结构：片头/产品展示/卖点字幕/CTA/片尾
        :return: list[str]，每个元素为一段 ffmpeg 滤镜表达式
        """
        segments = self.video_template.get("segments", [])
        # 累计时间偏移，用于定位各段在最终视频中的时间区间
        offset = 0
        filter_chain = []
        for seg in segments:
            name = seg.get("name", "")
            duration = seg.get("duration", 0)
            start = offset
            end = offset + duration
            # 各段对应的 ffmpeg 滤镜（占位）
            if name == "intro":
                # 片头：品牌 logo 淡入
                filter_chain.append(
                    f"drawtext=text='Brand':fontsize=48:fontcolor=white:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2:enable='between(t,{start},{end})'"
                )
            elif name == "product_showcase":
                # 产品展示：实拍素材位，淡入
                filter_chain.append(
                    f"fade=t=in:st={start}:d=0.5"
                )
            elif name == "selling_points":
                # 卖点字幕：数字人口播
                filter_chain.append(
                    f"drawtext=text='Selling Points':fontsize=36:fontcolor=yellow:"
                    f"x=60:y=h-120:enable='between(t,{start},{end})'"
                )
            elif name == "cta":
                # CTA：购买引导
                filter_chain.append(
                    f"drawtext=text='Shop Now!':fontsize=56:fontcolor=red:"
                    f"x=(w-text_w)/2:y=h-200:enable='between(t,{start},{end})'"
                )
            elif name == "outro":
                # 片尾：品牌信息，淡出
                filter_chain.append(f"fade=t=out:st={start}:d=0.5")
            offset = end
        return filter_chain

    def _add_subtitles(self, video_path: str, srt_path: str) -> str:
        """
        生成字幕烧录 ffmpeg 命令片段
        使用 subtitles 滤镜将 SRT 字幕硬编码到视频
        :return: subtitles 滤镜表达式字符串
        """
        if not srt_path:
            return ""
        # Windows 路径需转义反斜杠与冒号，subtitles 滤镜对路径敏感
        srt_path_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        return (
            f"subtitles='{srt_path_escaped}':force_style="
            f"'FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3'"
        )

    def _add_stickers(self, video_path: str, sticker_type: str) -> str:
        """
        生成贴纸叠加 ffmpeg 命令片段
        支持跨境带货特效：countdown / price_burst / limited_time
        :return: ffmpeg 滤镜表达式字符串
        """
        effect = self.effects_config.get(sticker_type, {})
        if not effect:
            return ""
        position = effect.get("position", {"x": 320, "y": 80})
        duration = effect.get("duration", 3)
        name = effect.get("name", sticker_type)
        # 占位 ffmpeg 滤镜（实际应叠加 PNG 贴纸序列）
        return (
            f"drawtext=text='{name}':fontsize=40:fontcolor=red:"
            f"x={position.get('x', 320)}:y={position.get('y', 80)}:"
            f"enable='between(t,0,{duration})'"
        )

    def _add_bgm(self, video_path: str, bgm_path: str) -> str:
        """
        生成 BGM 混音 ffmpeg 命令片段
        将 BGM 以指定音量混入视频，BGM 音量 0.3，口播音频为主
        :return: ffmpeg 输入与混音参数字符串
        """
        if not bgm_path:
            return ""
        bgm_path_escaped = bgm_path.replace("\\", "/")
        return (
            f"-i '{bgm_path_escaped}' -filter_complex "
            f"'[1:a]volume=0.3[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]' "
            f"-map 0:v -map '[aout]'"
        )

    def _build_full_command(
        self,
        video_path: str,
        raw_footage_path: str,
        output_path: str,
        filter_chain: list,
        subtitle_cmd: str,
        sticker_cmd: str,
        bgm_cmd: str,
    ) -> str:
        """拼接完整 ffmpeg 命令字符串"""
        parts = [self.ffmpeg_path]
        parts.append(f"-i '{video_path}'")
        if raw_footage_path:
            parts.append(f"-i '{raw_footage_path}'")

        # 合并所有视频滤镜（模板/字幕/贴纸）
        filters = []
        if filter_chain:
            filters.extend(filter_chain)
        if subtitle_cmd:
            filters.append(subtitle_cmd)
        if sticker_cmd:
            filters.append(sticker_cmd)

        if filters:
            filter_str = ",".join(filters)
            parts.append(f'-filter_complex "{filter_str}"')

        # BGM 混音参数（已含 -i 与 -map）
        if bgm_cmd:
            parts.append(bgm_cmd)

        parts.append(f"'{output_path}'")
        return " ".join(parts)

    def batch_edit(self, items: list) -> list:
        """批量处理多个剪辑任务。

        Args:
            items: list[dict]，每个 dict 含 digital_human_result / raw_footage_path /
                country / product_info 四个字段，与 edit_video 入参对应。

        Returns:
            剪辑结果列表 list[dict]，每项含 output_path / ffmpeg_command 等；
            单条剪辑失败时该项为 {"error": "..."}。
        """
        results = []
        for item in items:
            try:
                result = self.edit_video(
                    digital_human_result=item.get("digital_human_result", {}),
                    raw_footage_path=item.get("raw_footage_path", ""),
                    country=item.get("country", ""),
                    product_info=item.get("product_info", {}),
                )
                results.append(result)
            except Exception as e:
                print(f"[Error] 批量剪辑失败: {e}")
                results.append({"error": str(e)})
        return results

    def _generate_output_filename(
        self, product_name: str, country: str, version: str
    ) -> str:
        """
        生成输出文件名，命名规范：产品名_国家_版本号_日期.mp4
        """
        date_str = datetime.now().strftime("%Y%m%d")
        # 清理产品名中的特殊字符，仅保留字母数字与 -_
        safe_name = "".join(c for c in product_name if c.isalnum() or c in "-_") or "product"
        return f"{safe_name}_{country}_{version}_{date_str}.mp4"


# ===== 真实 ffmpeg 执行预留接口（Demo 阶段不启用） =====
#
# 真实执行时使用 subprocess 调用 ffmpeg：
#   import subprocess
#   result = subprocess.run(ffmpeg_command, shell=True, capture_output=True, text=True)
#   if result.returncode != 0:
#       raise RuntimeError(f"ffmpeg 执行失败: {result.stderr}")
#
# Demo 阶段仅打印命令字符串，便于评审查看剪辑逻辑与参数
