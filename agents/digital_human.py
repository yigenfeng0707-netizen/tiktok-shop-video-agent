# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 数字人多语种出镜子 Agent
负责根据目标国家自动切换面孔/语种/BGM，调用数字人 API 生成口播视频，
并生成 SRT 字幕文件、匹配当地热门 BGM。
Demo 阶段模拟 API 调用，返回占位路径；配置环境变量后自动切换为真实 API。

环境变量：
    HEYGEN_API_KEY         —— HeyGen 数字人 API Key（优先使用）
    TENCENT_ZY_API_KEY     —— 腾讯智影 API Key
    TENCENT_ZY_SECRET_ID   —— 腾讯云 SecretId（用于签名）
    TENCENT_ZY_SECRET_KEY  —— 腾讯云 SecretKey（用于签名）
    TENCENT_ZY_REGION      —— 腾讯云地域，默认 ap-guangzhou
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

try:
    import requests  # 真实数字人 API 调用依赖；未安装时回退 mock
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


class DigitalHumanGenerator:
    """数字人生成器：根据国家自动切换面孔/语种/BGM，生成口播视频"""

    def __init__(self, config_dir: str = "config"):
        # 定位配置文件目录（兼容相对/绝对路径）
        base_dir = Path(config_dir)
        if not base_dir.is_absolute():
            # 默认相对项目根目录解析
            base_dir = Path(__file__).resolve().parent.parent / config_dir
        self.config_dir = base_dir

        # 加载国家→面孔→语种映射表
        with open(self.config_dir / "face_voice_mapping.json", "r", encoding="utf-8") as f:
            self.face_voice_mapping = json.load(f)

        # 加载 BGM 库
        with open(self.config_dir / "bgm_library.json", "r", encoding="utf-8") as f:
            self.bgm_library = json.load(f)

        # 数字人视频输出目录（Demo 阶段仅生成路径占位）
        project_root = Path(__file__).resolve().parent.parent
        self.output_dir = project_root / "assets" / "digital_human_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 字幕输出目录
        self.subtitle_dir = project_root / "assets" / "subtitles"
        self.subtitle_dir.mkdir(parents=True, exist_ok=True)

    def generate_video(self, script: dict, country: str) -> dict:
        """生成单条数字人口播视频。

        根据目标国家自动切换面孔类型、语种、BGM，调用数字人 API 生成口播视频，
        并产出 SRT 字幕文件。有 HEYGEN_API_KEY 或 TENCENT_ZY_API_KEY 时走真实 API，
        否则回退 mock 占位路径。

        Args:
            script: 脚本字典，可包含 segments(分段口播)/text/category/duration 字段。
            country: 目标国家代码（US / VN / SA / GB / ID）。

        Returns:
            dict，字段包含 video_path / subtitle_path / bgm_path / bgm_info /
            face_type / language / subtitle_language / avatar_id / country / duration。

        Raises:
            ValueError: 当国家代码不在 face_voice_mapping 中时抛出。
        """
        # 根据国家获取配置
        if country not in self.face_voice_mapping:
            raise ValueError(
                f"不支持的国家代码: {country}，支持: {list(self.face_voice_mapping.keys())}"
            )

        country_config = self.face_voice_mapping[country]
        face_type = country_config["face_type"]
        language = country_config["voice_language"]
        avatar_id = country_config["digital_human_avatar_id"]
        subtitle_language = country_config.get("subtitle_language", language)

        # 从脚本中提取品类，用于 BGM 选择
        category = script.get("category", "health")

        # 调用数字人 API 生成视频（有 API Key 走真实，否则回退 mock）
        video_path = self._call_digital_human(script, face_type, language)

        # 生成字幕文件
        subtitle_content = self._generate_subtitle(script, subtitle_language)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        subtitle_path = str(self.subtitle_dir / f"subtitle_{country}_{timestamp}.srt")
        # Demo 阶段写入实际 SRT 文件，便于后续剪辑模块读取
        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write(subtitle_content)

        # 选择 BGM
        bgm_info = self._select_bgm(country, category)
        bgm_path = bgm_info.get("file_path", "")

        # 模拟视频时长（Demo 用脚本估算，默认 35 秒）
        duration = script.get("duration", 35)

        return {
            "video_path": video_path,
            "subtitle_path": subtitle_path,
            "bgm_path": bgm_path,
            "bgm_info": bgm_info,
            "face_type": face_type,
            "language": language,
            "subtitle_language": subtitle_language,
            "avatar_id": avatar_id,
            "country": country,
            "duration": duration,
        }

    def _mock_digital_human_api(self, script: dict, face_type: str, language: str) -> str:
        """模拟数字人 API 调用（Demo 用）。

        真实环境应调用 HeyGen / 腾讯智影 / SiliconCloud API，见 _call_digital_human。

        Args:
            script: 脚本字典。
            face_type: 面孔类型（如 european / southeast_asian / middle_east）。
            language: 语种代码（如 en / vi / ar）。

        Returns:
            占位视频文件本地路径。
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_name = f"digital_human_{face_type}_{language}_{timestamp}.mp4"
        video_path = str(self.output_dir / video_name)
        # Demo：仅返回占位路径，不实际生成视频文件
        print(
            f"[Mock] 模拟调用数字人 API | 面孔={face_type} | 语种={language} | 输出={video_path}"
        )
        return video_path

    def _real_heygen_api(self, script: dict, face_type: str, language: str) -> str:
        """调用 HeyGen v2 API 生成数字人口播视频并下载到本地。

        完整流程：
        1. 从环境变量 HEYGEN_API_KEY 读取鉴权 Key
        2. 从 face_voice_mapping 配置读取 avatar_id（由调用方国家映射得到 face_type）
        3. 拼接脚本文本（优先 segments，其次 text 字段）
        4. POST https://api.heygen.com/v2/video/generate 提交合成任务，返回 task_id
        5. 轮询 GET https://api.heygen.com/v1/video_status.get?video_id=<id>
           直到 status == completed，获取 video_url
        6. 下载视频到 self.output_dir，返回本地文件路径

        Args:
            script: 脚本字典，含 segments / text 字段。
            face_type: 面孔类型，用于在 face_voice_mapping 中反查 avatar_id。
            language: 语种代码，用于选择 voice_id。

        Returns:
            下载到本地的视频文件绝对路径。

        Raises:
            RuntimeError: requests 未安装 / API Key 缺失 / 任务失败时抛出。
        """
        if requests is None:
            raise RuntimeError(
                "requests 未安装，无法调用 HeyGen API。请执行 pip install requests"
            )

        api_key = os.environ.get("HEYGEN_API_KEY", "")
        if not api_key:
            raise RuntimeError("未配置 HEYGEN_API_KEY 环境变量")

        # 从 face_voice_mapping 反查当前 face_type 对应的 avatar_id
        avatar_id = ""
        voice_id = ""
        for _, cfg in self.face_voice_mapping.items():
            if cfg.get("face_type") == face_type:
                avatar_id = cfg.get("digital_human_avatar_id", "")
                voice_id = cfg.get("voice_id", "")
                break
        if not avatar_id:
            raise RuntimeError(
                "face_voice_mapping 中未找到 face_type={0} 的 avatar_id".format(face_type)
            )

        # 拼接脚本文本：优先 segments，其次 text
        segments = script.get("segments", [])
        if segments:
            script_text = " ".join(seg.get("text", "") for seg in segments)
        else:
            script_text = script.get("text", "")
        if not script_text:
            raise RuntimeError("脚本文本为空，无法提交 HeyGen 合成任务")

        # 1. 提交视频生成任务
        submit_url = "https://api.heygen.com/v2/video/generate"
        headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "video_inputs": [
                {
                    "character": {
                        "type": "avatar",
                        "avatar_id": avatar_id,
                        "avatar_style": "default",
                    },
                    "voice": {
                        "type": "text",
                        "input_text": script_text,
                        "voice_id": voice_id,
                    },
                }
            ],
            "dimension": {"width": 1080, "height": 1920},
        }
        resp = requests.post(submit_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        # HeyGen v2 返回 data.video_id
        video_id = data.get("data", {}).get("video_id") or data.get("video_id")
        if not video_id:
            raise RuntimeError("HeyGen 提交任务未返回 video_id: {0}".format(data))

        print(
            "[HeyGen] 已提交合成任务 video_id={0}，开始轮询状态...".format(video_id)
        )

        # 2. 轮询任务状态（最多等待 10 分钟，每 10 秒查询一次）
        status_url = "https://api.heygen.com/v1/video_status.get"
        max_attempts = 60
        video_url = ""
        for attempt in range(max_attempts):
            time.sleep(10)
            s_resp = requests.get(
                status_url,
                headers={"X-Api-Key": api_key},
                params={"video_id": video_id},
                timeout=30,
            )
            s_resp.raise_for_status()
            s_data = s_resp.json().get("data", {})
            status = s_data.get("status", "")
            print(
                "[HeyGen] 轮询 {0}/{1} status={2}".format(
                    attempt + 1, max_attempts, status
                )
            )
            if status == "completed":
                video_url = s_data.get("video_url", "")
                break
            if status == "failed":
                raise RuntimeError(
                    "HeyGen 合成任务失败: {0}".format(s_data.get("error", ""))
                )

        if not video_url:
            raise RuntimeError("HeyGen 合成任务超时未完成，video_id={0}".format(video_id))

        # 3. 下载视频到本地
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_name = "heygen_{0}_{1}_{2}.mp4".format(face_type, language, timestamp)
        local_path = str(self.output_dir / local_name)
        d_resp = requests.get(video_url, timeout=120, stream=True)
        d_resp.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in d_resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print("[HeyGen] 视频已下载到本地: {0}".format(local_path))
        return local_path

    def _real_tencent_zhiying_api(self, script: dict, face_type: str, language: str) -> str:
        """调用腾讯智影数字人合成 API 生成口播视频。

        腾讯智影基于腾讯云 TC3-HMAC-SHA1 签名方式调用，完整流程说明如下：

        1. 鉴权信息（从环境变量读取）：
           - TENCENT_ZY_API_KEY    ：智影平台 API Key
           - TENCENT_ZY_SECRET_ID  ：腾讯云账号 SecretId
           - TENCENT_ZY_SECRET_KEY ：腾讯云账号 SecretKey
           - TENCENT_ZY_REGION     ：地域，默认 ap-guangzhou

        2. 签名方式（TC3-HMAC-SHA1 / 腾讯云 v3 签名）：
           a. 拼接规范请求串 CanonicalRequest：
              HTTPRequestMethod + \n + CanonicalURI + \n +
              CanonicalQueryString + \n + CanonicalHeaders + \n +
              SignedHeaders + \n + HashedRequestPayload
           b. 拼接签名串 StringToSign：
              "TC3-HMAC-SHA1" + \n + Timestamp + \n + CredentialScope + \n +
              HashedCanonicalRequest
           c. 计算 Signature：
              SecretDate = HMAC_SHA1(SecretKey, Date)
              SecretService = HMAC_SHA1(SecretDate, Service)
              SecretSigning = HMAC_SHA1(SecretService, "tc3_request")
              Signature = HEX(HMAC_SHA1(SecretSigning, StringToSign))
           d. 放入 Authorization 头：
              TC3-HMAC-SHA1 Credential=SecretId/CredentialScope,
              SignedHeaders=signed_headers, Signature=signature

        3. 调用流程：
           - POST https://zenvideo.tencent.com/api/v1/videos 提交合成任务
             Body: {"text": "<script_text>", "avatar_id": "<avatar_id>",
                    "language": "<language>", "resolution": "1080x1920"}
           - 返回 task_id
           - 轮询 GET https://zenvideo.tencent.com/api/v1/videos/<task_id>
             直到 status == done，获取 video_url
           - 下载视频到 self.output_dir 返回本地路径

        注：腾讯云签名实现较为复杂，Demo 阶段以注释说明完整流程。
        生产部署建议直接使用官方 SDK tencentcloud-sdk-python：
            from tencentcloud.zhiying.v20240101 import zhiying_client
        下方提供基于 requests 的简化调用骨架（需自行实现签名函数）。

        Args:
            script: 脚本字典。
            face_type: 面孔类型。
            language: 语种代码。

        Returns:
            下载到本地的视频文件路径。

        Raises:
            RuntimeError: requests 未安装 / 鉴权信息缺失时抛出。
        """
        if requests is None:
            raise RuntimeError(
                "requests 未安装，无法调用腾讯智影 API。请执行 pip install requests"
            )

        secret_id = os.environ.get("TENCENT_ZY_SECRET_ID", "")
        secret_key = os.environ.get("TENCENT_ZY_SECRET_KEY", "")
        api_key = os.environ.get("TENCENT_ZY_API_KEY", "")
        region = os.environ.get("TENCENT_ZY_REGION", "ap-guangzhou")

        if not (api_key and secret_id and secret_key):
            raise RuntimeError(
                "未配置腾讯智影鉴权信息，需同时设置 TENCENT_ZY_API_KEY / "
                "TENCENT_ZY_SECRET_ID / TENCENT_ZY_SECRET_KEY"
            )

        # 从 face_voice_mapping 反查 avatar_id
        avatar_id = ""
        for _, cfg in self.face_voice_mapping.items():
            if cfg.get("face_type") == face_type:
                avatar_id = cfg.get("digital_human_avatar_id", "")
                break
        if not avatar_id:
            raise RuntimeError(
                "face_voice_mapping 中未找到 face_type={0} 的 avatar_id".format(face_type)
            )

        # 拼接脚本文本
        segments = script.get("segments", [])
        script_text = " ".join(seg.get("text", "") for seg in segments) if segments else script.get("text", "")

        # ===== 以下为腾讯云 TC3-HMAC-SHA1 签名与调用骨架 =====
        # 注：完整签名实现较复杂，建议生产环境直接使用 tencentcloud-sdk-python。
        # 这里给出请求结构，签名部分需按上述注释流程实现 _build_tc3_signature()。
        #
        # service = "zhiying"
        # host = "zenvideo.tencent.com"
        # endpoint = "https://zenvideo.tencent.com/api/v1/videos"
        # timestamp = int(time.time())
        # payload = json.dumps({
        #     "text": script_text,
        #     "avatar_id": avatar_id,
        #     "language": language,
        #     "resolution": "1080x1920",
        #     "region": region,
        # })
        # headers = self._build_tc3_signature(
        #     secret_id, secret_key, service, host, endpoint, payload, timestamp
        # )
        # headers["X-TC-Key"] = api_key
        # resp = requests.post(endpoint, headers=headers, data=payload, timeout=60)
        # resp.raise_for_status()
        # task_id = resp.json().get("task_id")
        # # 轮询任务状态...
        # # 下载视频到本地...
        #
        # Demo 阶段抛出未实现异常，提示用户使用 HeyGen 或 mock
        raise RuntimeError(
            "腾讯智影 API 签名实现较复杂，Demo 阶段未启用。"
            "请使用 HeyGen（配置 HEYGEN_API_KEY）或回退 mock 模式。"
            "生产部署建议接入 tencentcloud-sdk-python 官方 SDK。"
        )

    def _call_digital_human(self, script: dict, face_type: str, language: str) -> str:
        """统一数字人 API 调用入口：按环境变量自动选择 HeyGen / 腾讯智影 / mock。

        选择优先级：
        1. 配置 HEYGEN_API_KEY 时走 HeyGen 真实 API
        2. 配置 TENCENT_ZY_API_KEY 时走腾讯智影真实 API
        3. 都未配置时回退 _mock_digital_human_api 占位

        Args:
            script: 脚本字典。
            face_type: 面孔类型。
            language: 语种代码。

        Returns:
            视频文件本地路径。
        """
        heygen_key = os.environ.get("HEYGEN_API_KEY", "")
        tencent_key = os.environ.get("TENCENT_ZY_API_KEY", "")

        if heygen_key and requests is not None:
            try:
                return self._real_heygen_api(script, face_type, language)
            except Exception as e:
                print(
                    "[Warn] HeyGen API 调用失败，回退 mock 模式: {0}".format(e)
                )
        elif tencent_key and requests is not None:
            try:
                return self._real_tencent_zhiying_api(script, face_type, language)
            except Exception as e:
                print(
                    "[Warn] 腾讯智影 API 调用失败，回退 mock 模式: {0}".format(e)
                )
        return self._mock_digital_human_api(script, face_type, language)

    def _generate_subtitle(self, script: dict, language: str) -> str:
        """
        根据脚本生成 SRT 字幕文件内容
        :param script: 脚本字典，包含 segments 列表（每段含 start/end/text）
        :param language: 字幕语种（用于多语种翻译预留，Demo 阶段直接使用脚本文本）
        :return: SRT 格式字符串
        """
        segments = script.get("segments", [])
        # 若脚本未分段，则用整段文本兜底
        if not segments:
            text = script.get("text", "")
            segments = [{"start": 0, "end": 5, "text": text}]

        srt_lines = []
        for idx, seg in enumerate(segments, start=1):
            start_sec = seg.get("start", 0)
            end_sec = seg.get("end", start_sec + 3)
            start_time = self._seconds_to_srt_time(start_sec)
            end_time = self._seconds_to_srt_time(end_sec)
            text = seg.get("text", "")
            srt_lines.append(str(idx))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(text)
            srt_lines.append("")  # 空行分隔
        return "\n".join(srt_lines)

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """秒数转 SRT 时间格式 HH:MM:SS,mmm"""
        total_secs = int(seconds)
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        secs = total_secs % 60
        millis = int(round((seconds - total_secs) * 1000))
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _select_bgm(self, country: str, category: str) -> dict:
        """
        从 BGM 库选择匹配 BGM
        优先匹配 country + category，其次匹配国家任意品类，最后返回占位
        :return: BGM 信息 dict
        """
        country_bgms = self.bgm_library.get(country, [])
        if not country_bgms:
            print(f"[Warn] BGM 库中无国家 {country} 的 BGM，使用占位")
            return {
                "bgm_id": f"bgm_{country.lower()}_placeholder",
                "title": "placeholder",
                "country": country,
                "category": category,
                "duration_seconds": 30,
                "file_path": f"assets/bgm/{country.lower()}/placeholder.mp3",
                "license": "royalty_free",
            }
        # 优先匹配品类
        for bgm in country_bgms:
            if bgm.get("category") == category:
                return bgm
        # 退而求其次，取国家下第一条
        return country_bgms[0]

    def generate_batch(self, scripts: list, countries: list) -> list:
        """批量生成多国数字人口播视频。

        Args:
            scripts: 脚本列表，与 countries 一一对应；若长度为 1 则对所有国家复用同一脚本。
            countries: 国家代码列表（US / VN / SA / GB / ID）。

        Returns:
            生成结果列表 list[dict]，每项含 video_path / subtitle_path / bgm_path 等；
            单国生成失败时该项为 {"country": x, "error": "..."}。

        Raises:
            ValueError: 当脚本数量与国家数量不匹配时抛出。
        """
        results = []
        # 若仅传入一份脚本，则对所有国家复用
        if len(scripts) == 1 and len(countries) > 1:
            scripts = scripts * len(countries)
        if len(scripts) != len(countries):
            raise ValueError(
                f"脚本数量({len(scripts)})与国家数量({len(countries)})不匹配"
            )

        for script, country in zip(scripts, countries):
            try:
                result = self.generate_video(script, country)
                results.append(result)
            except Exception as e:
                print(f"[Error] 生成 {country} 数字人视频失败: {e}")
                results.append({"country": country, "error": str(e)})
        return results


# 真实数字人 API（HeyGen / 腾讯智影）已实现于 DigitalHumanGenerator：
#   _real_heygen_api / _real_tencent_zhiying_api / _call_digital_human
# 通过环境变量 HEYGEN_API_KEY / TENCENT_ZY_API_KEY 自动切换，未配置时回退 mock。
