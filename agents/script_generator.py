# -*- coding: utf-8 -*-
"""
TikTok Shop 跨境短视频 AI 本地化脚本生成子 Agent。

本模块为 MiXer AI 主编排工作流中的第一个子 Agent，职责是：
1. 接收产品信息 + 目标国家 + 平台风格
2. 加载对应国家的本土化 Prompt 模板
3. 通过文化禁忌规则引擎自动规避当地敏感元素
4. 调用 LLM 生成结构化短视频脚本（Demo 阶段用 _mock_llm_call 模板填充，预留真实 API 接口）

依赖：Python 标准库（json / os / re）；真实 LLM 调用需可选依赖 requests。
配置文件：config/country_config.json、config/cultural_taboos.json
环境变量：OPENAI_API_KEY / OPENAI_BASE_URL / LLM_MODEL（未配置时自动回退 mock）
"""

import json
import os
import re

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import requests  # 真实 LLM API 调用依赖；未安装时回退 mock
except ImportError:  # pragma: no cover
    requests = None  # type: ignore


class ScriptGenerator:
    """AI 本地化脚本生成 Agent。

    通过加载国家配置与文化禁忌规则，为 TikTok Shop 跨境卖家生成
    符合目标国家热点、平台风格、文化禁忌的结构化短视频脚本。
    """

    # Demo 阶段各国本地化话术库（钩子 / CTA）
    # 生产阶段由 LLM 根据热点数据动态生成，此处仅作模板填充
    _PHRASE_BANK = {
        "US": {
            "hook": "Wait... you've been doing this wrong the whole time? 🤯",
            "cta": "Link in bio! Use code TIKTOK10 for 10% off 🛒",
            "selling_intro": "Here's why you need this:",
        },
        "VN": {
            "hook": "Bạn có biết? Sản phẩm này đang rất hot! 🔥",
            "cta": "Đặt hàng ngay hôm nay để nhận ưu đãi! 🛍️",
            "selling_intro": "Điểm nổi bật của sản phẩm:",
        },
        "SA": {
            "hook": "اكتشف الجودة الحقيقية لعائلتك ✨",
            "cta": "اطلب الآن واحصل على خصم حصري 🛒",
            "selling_intro": "مميزات المنتج:",
        },
        "GB": {
            "hook": "Did you know? This little thing changes everything 👀",
            "cta": "Tap the link — Free UK delivery 🇬🇧",
            "selling_intro": "Here's why it's worth it:",
        },
        "ID": {
            "hook": "Mau hemat? Coba lihat ini! Hemat banget! 💰",
            "cta": "Beli sekarang! Gratis ongkir hari ini 🚚",
            "selling_intro": "Keunggulan produk:",
        },
    }

    # 夸大宣传关键词（欧美地区需规避）
    _EXAGGERATION_WORDS = [
        "best ever", "miracle", "100% guaranteed", "cure", "perfect",
        "amazing", "incredible", "unbelievable",
    ]

    def __init__(self, config_dir: str = None):
        """初始化脚本生成 Agent，加载国家配置与文化禁忌规则。

        Args:
            config_dir: 配置文件目录路径。默认为本文件上一级目录中的 config 目录。
        """
        # 默认配置目录：agents/../config
        if config_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_dir = os.path.join(base_dir, "config")

        self._config_dir = config_dir
        self._country_config = self._load_json(
            os.path.join(config_dir, "country_config.json")
        )
        self._taboos_config = self._load_json(
            os.path.join(config_dir, "cultural_taboos.json")
        )

    # ------------------------------------------------------------------
    # 配置加载
    # ------------------------------------------------------------------
    @staticmethod
    def _load_json(path):
        """以 UTF-8 编码读取 JSON 配置文件。

        Args:
            path: JSON 文件绝对路径。

        Returns:
            解析后的 dict / list。
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_country_config(self, country):
        """获取指定国家的配置。

        Args:
            country: 国家代码（US / VN / SA / GB / ID）。

        Returns:
            国家配置 dict。

        Raises:
            ValueError: 当国家代码不支持时。
        """
        country = country.upper()
        if country not in self._country_config:
            supported = ", ".join(self._country_config.keys())
            raise ValueError(
                "不支持的目标国家: {0}，当前支持: {1}".format(country, supported)
            )
        return self._country_config[country]

    # ------------------------------------------------------------------
    # Prompt 构建
    # ------------------------------------------------------------------
    def _build_prompt(self, product_info, country, platform_style, taboos):
        """根据国家模板与产品信息构建 Prompt 文本。

        Args:
            product_info: 产品信息 dict。
            country: 目标国家代码。
            platform_style: 平台风格偏好。
            taboos: 已匹配的文化禁忌规则列表（注入 Prompt 上下文）。

        Returns:
            填充后的 Prompt 字符串。
        """
        cfg = self._get_country_config(country)
        selling_points = product_info.get("selling_points", [])
        # 卖点用分号拼接，便于 _mock_llm_call 解析回列表
        selling_points_str = "; ".join(selling_points) if selling_points else ""

        # 将禁忌规则描述拼成可读文本
        if taboos:
            taboo_text = "\n".join(
                "- [{0}] {1}".format(t.get("action", ""), t.get("rule", ""))
                for t in taboos
            )
        else:
            taboo_text = "无特殊禁忌要求"

        prompt = (
            "你是一位深谙{country_cn} TikTok 生态的跨境短视频脚本编剧。\n"
            "【目标国家】{country_cn}（{country_en}）\n"
            "【平台风格】{platform_style}\n"
            "【产品标题】{title}\n"
            "【产品卖点】{selling_points}\n"
            "【产品品类】{category}\n"
            "【目标人群】{target_audience}\n"
            "【价格区间】{price_range}\n"
            "【语种】{language_name}（{language_code}）\n"
            "【面孔类型】{face_type}\n"
            "【文化禁忌标记】True\n"
            "【适用文化禁忌规则】\n{taboo_text}\n\n"
            "请按输出 Schema（hook / product_selling_points / cta / "
            "bgm_suggestion / subtitle_text / visual_suggestions）"
            "返回结构化 JSON。"
        ).format(
            country_cn=cfg["name_cn"],
            country_en=cfg["name_en"],
            platform_style=platform_style or cfg.get("platform_style", ""),
            title=product_info.get("title", ""),
            selling_points=selling_points_str,
            category=product_info.get("category", "general"),
            target_audience=product_info.get("target_audience", "通用人群"),
            price_range=product_info.get("price_range", "未提供"),
            language_name=cfg["language_name"],
            language_code=cfg["language_code"],
            face_type=cfg["face_type"],
            taboo_text=taboo_text,
        )
        return prompt

    # ------------------------------------------------------------------
    # 文化禁忌规则引擎
    # ------------------------------------------------------------------
    def _check_taboos(self, country, category):
        """返回指定国家与品类需要应用的文化禁忌规则列表。

        匹配逻辑：规则的 countries 包含该国家，且 category 等于目标品类或为 "*"（通配）。

        Args:
            country: 目标国家代码。
            category: 产品品类。

        Returns:
            命中的禁忌规则 dict 列表。
        """
        country = country.upper()
        category = (category or "general").lower()
        matched = []
        for rule in self._taboos_config.get("rules", []):
            countries = [c.upper() for c in rule.get("countries", [])]
            rule_category = rule.get("category", "*").lower()
            if country not in countries:
                continue
            if rule_category == "*" or rule_category == category:
                matched.append(rule)
        return matched

    def _apply_taboos(self, script, taboos):
        """根据禁忌规则列表对生成的脚本进行二次校验与调整。

        Args:
            script: LLM 生成的脚本 dict。
            taboos: _check_taboos 返回的规则列表。

        Returns:
            调整后的脚本 dict（新增 cultural_adjustments 字段）。
        """
        adjustments = []
        for rule in taboos:
            action = rule.get("action", "")
            rule_desc = rule.get("rule", "")
            adjustment = self._apply_single_action(script, action, rule_desc)
            if adjustment:
                adjustments.append(adjustment)

        script["cultural_adjustments"] = adjustments
        return script

    def _apply_single_action(self, script, action, rule_desc):
        """执行单条禁忌规则动作，返回该条调整说明文本。

        Args:
            script: 脚本 dict（会被就地修改）。
            action: 执行动作标识。
            rule_desc: 规则描述。

        Returns:
            调整说明字符串；无动作时返回空串。
        """
        visuals = script.get("visual_suggestions", "")
        subtitle = script.get("subtitle_text", "")
        hook = script.get("hook", "")
        selling = script.get("product_selling_points", "")
        # AI 返回的字段可能是 list 或 dict 类型，统一转为 string
        if isinstance(visuals, (list, dict)):
            visuals = " ".join(str(v) for v in visuals.values()) if isinstance(visuals, dict) else " ".join(str(v) for v in visuals)
            script["visual_suggestions"] = visuals
        if isinstance(subtitle, (list, dict)):
            subtitle = " ".join(str(v) for v in subtitle.values()) if isinstance(subtitle, dict) else " ".join(str(v) for v in subtitle)
            script["subtitle_text"] = subtitle
        if isinstance(hook, (list, dict)):
            hook = " ".join(str(v) for v in hook.values()) if isinstance(hook, dict) else " ".join(str(v) for v in hook)
            script["hook"] = hook
        if isinstance(selling, (list, dict)):
            selling = " ".join(str(v) for v in selling.values()) if isinstance(selling, dict) else " ".join(str(v) for v in selling)
            script["product_selling_points"] = selling

        if action == "hide_model":
            # 隐藏模特：移除画面中的真人模特描述，聚焦产品
            script["visual_suggestions"] = (
                "【禁忌调整-隐藏模特】画面不出现真人模特，仅展示产品外观与功能演示；"
                + visuals
            )
            return "hide_model: 已隐藏真人模特，画面聚焦产品外观与功能演示"

        if action == "focus_product":
            # 聚焦产品：强化产品功能演示
            script["visual_suggestions"] = (
                "【禁忌调整-聚焦产品】增加产品细节特写与使用效果对比，避免身体特写；"
                + visuals
            )
            return "focus_product: 画面聚焦产品功能与使用效果"

        if action == "conservative_dress":
            script["visual_suggestions"] = (
                "【禁忌调整-保守着装】模特须保守着装，不得出现暴露服饰；" + visuals
            )
            return "conservative_dress: 模特保守着装要求已注入"

        if action == "remove_sensitive_elements":
            script["visual_suggestions"] = (
                "【禁忌调整-移除敏感元素】不得出现猪肉、酒精、夜店、赌博、占卜等元素；"
                + visuals
            )
            return "remove_sensitive_elements: 已移除猪肉/酒精/赌博等敏感元素"

        if action == "remove_religious_sensitive":
            script["visual_suggestions"] = (
                "【禁忌调整-宗教敏感】不出现非本地主流宗教符号，不贬低任何宗教；" + visuals
            )
            return "remove_religious_sensitive: 已规避宗教敏感元素"

        if action == "add_ramadan_disclaimer":
            script["subtitle_text"] = (
                subtitle + " | 【斋月提示】请尊重当地斋月习俗，避免日间饮食场景。"
            )
            return "add_ramadan_disclaimer: 已添加斋月期间提示"

        if action == "add_etiquette_note":
            script["visual_suggestions"] = (
                "【禁忌调整-礼仪】模特使用右手递物，避免左手等失礼动作；" + visuals
            )
            return "add_etiquette_note: 已注入右手递物礼仪要求"

        if action == "remove_exaggeration":
            # 欧美：剔除夸大宣传词汇
            filtered = subtitle
            for word in self._EXAGGERATION_WORDS:
                filtered = re.sub(word, "", filtered, flags=re.IGNORECASE)
            script["subtitle_text"] = filtered.strip()
            return "remove_exaggeration: 已剔除 best ever / miracle 等绝对化用语"

        if action == "highlight_eco":
            # 欧美：主动突出环保卖点
            eco_note = "Eco-friendly & sustainable 🌱"
            script["product_selling_points"] = (
                eco_note + " | " + selling
            )
            return "highlight_eco: 已主动突出环保卖点（eco-friendly / sustainable）"

        if action == "add_disclaimer":
            script["subtitle_text"] = (
                subtitle
                + " | 【Disclaimer】Results may vary. Not intended to diagnose or treat."
            )
            return "add_disclaimer: 已添加免责声明（结果因人而异）"

        if action == "add_halal_note":
            script["subtitle_text"] = (
                subtitle + " | 【Halal Certified】Produk bersertifikat Halal."
            )
            return "add_halal_note: 已添加 halal 清真认证提示"

        if action == "remove_political_sensitive":
            script["visual_suggestions"] = (
                "【禁忌调整-政治敏感】避免涉及历史争议与政治敏感元素；" + visuals
            )
            return "remove_political_sensitive: 已规避历史争议与政治敏感元素"

        # 未知动作：仅记录规则描述
        return "unknown_action({0}): {1}".format(action, rule_desc)

    # ------------------------------------------------------------------
    # LLM 调用（Demo 模拟 / 生产预留）
    # ------------------------------------------------------------------
    def _mock_llm_call(self, prompt):
        """模拟 LLM 调用，基于模板填充生成结构化脚本 JSON 字符串。

        Demo 阶段使用本方法替代真实 LLM API。从 Prompt 文本中解析已填充的
        字段（标题 / 卖点 / 国家 / 品类等），结合本地化话术库生成脚本。

        Args:
            prompt: _build_prompt 生成的完整 Prompt 文本。

        Returns:
            结构化脚本的 JSON 字符串。

        生产环境替换示例（取消注释并配置即可）::

            import requests
            resp = requests.post(
                self.LLM_API_URL,
                json={"prompt": prompt, "model": "gpt-4o", "temperature": 0.7},
                headers={"Authorization": "Bearer " + self.LLM_API_KEY},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["content"]
        """
        # 解析 Prompt 中【字段】值 的内容
        title = self._extract_field(prompt, "产品标题")
        category = self._extract_field(prompt, "产品品类")
        country_en = self._extract_field(prompt, "目标国家")
        # 目标国家行格式：「【目标国家】美国（United States）」，取括号内代码
        country_code = self._extract_country_code(country_en)
        selling_points_str = self._extract_field(prompt, "产品卖点")
        selling_points = [
            s.strip() for s in selling_points_str.split(";") if s.strip()
        ]

        cfg = self._country_config.get(country_code, self._country_config.get("US"))
        phrase = self._PHRASE_BANK.get(country_code, self._PHRASE_BANK["US"])

        # 钩子（3 秒）
        hook = phrase["hook"]
        # 产品卖点（15 秒）：本地化引语 + 编号卖点
        selling_lines = "\n".join(
            "{idx}. {point}".format(idx=i + 1, point=p)
            for i, p in enumerate(selling_points)
        )
        product_selling_points = "{intro}\n{lines}".format(
            intro=phrase["selling_intro"], lines=selling_lines
        )
        # CTA（5 秒）
        cta = phrase["cta"]
        # BGM 建议
        bgm_styles = cfg.get("hot_bgm_styles", [])
        bgm_suggestion = "推荐曲风：" + " / ".join(bgm_styles) + "；节奏轻快、无人声或低人声"
        # 字幕文案（含分镜时间戳）
        subtitle_text = (
            "[00:00-00:03] {hook}\n"
            "[00:03-00:18] {intro} {points}\n"
            "[00:18-00:23] {cta}"
        ).format(
            hook=hook,
            intro=phrase["selling_intro"],
            points="; ".join(selling_points),
            cta=cta,
        )
        # 画面建议
        face_type = cfg.get("face_type", "european")
        visual_suggestions = (
            "镜头1（0-3s）：产品特写 + 强视觉冲击字幕\n"
            "镜头2（3-18s）：{face}面孔模特使用产品场景，快切每1.5-2s\n"
            "镜头3（18-23s）：产品全景 + CTA 贴纸 + 价格爆炸框\n"
            "色调：明亮高饱和；字幕：{lang}大字号高亮"
        ).format(face=face_type, lang=cfg.get("language_name", "English"))

        script = {
            "hook": hook,
            "product_selling_points": product_selling_points,
            "cta": cta,
            "bgm_suggestion": bgm_suggestion,
            "subtitle_text": subtitle_text,
            "visual_suggestions": visual_suggestions,
        }
        return json.dumps(script, ensure_ascii=False)

    def _real_llm_call(self, prompt: str) -> str:
        """调用 OpenAI 兼容的真实 LLM API 生成脚本 JSON 字符串。

        通过环境变量读取配置：
            OPENAI_API_KEY    —— 必填，API Key
            OPENAI_BASE_URL   —— 可选，默认 https://api.openai.com/v1
            LLM_MODEL         —— 可选，默认 gpt-4o

        Args:
            prompt: _build_prompt 生成的完整 Prompt 文本。

        Returns:
            LLM 返回的结构化脚本 JSON 字符串。

        Raises:
            RuntimeError: requests 未安装或 API 调用失败时抛出。
        """
        if requests is None:
            raise RuntimeError(
                "requests 未安装，无法调用真实 LLM API。请执行 pip install requests"
            )

        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("LLM_MODEL", "gpt-4o")

        if not api_key:
            raise RuntimeError("未配置 OPENAI_API_KEY 环境变量")

        url = base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": "Bearer {0}".format(api_key),
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是 TikTok Shop 跨境短视频脚本编剧，"
                        "必须严格按 JSON Schema 返回结构化结果，"
                        "字段包含 hook / product_selling_points / cta / "
                        "bgm_suggestion / subtitle_text / visual_suggestions。"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4000,
            "response_format": {"type": "json_object"},
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        # OpenAI 兼容协议：choices[0].message.content
        content = data["choices"][0]["message"]["content"]
        return content

    def _call_llm(self, prompt: str) -> str:
        """统一 LLM 调用入口：有 OPENAI_API_KEY 时走真实 API，否则回退 mock。

        Args:
            prompt: _build_prompt 生成的完整 Prompt 文本。

        Returns:
            结构化脚本的 JSON 字符串。
        """
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key and requests is not None:
            try:
                return self._real_llm_call(prompt)
            except Exception as e:
                print(
                    "[Warn] 真实 LLM 调用失败，回退 mock 模式: {0}".format(e)
                )
        return self._mock_llm_call(prompt)

    @staticmethod
    def _extract_field(prompt, field_name):
        """从 Prompt 文本中提取【字段】值。

        Args:
            prompt: Prompt 文本。
            field_name: 字段名（不含方括号）。

        Returns:
            字段值字符串；未找到时返回空串。
        """
        pattern = r"【" + re.escape(field_name) + r"】([^\n]*)"
        match = re.search(pattern, prompt)
        return match.group(1).strip() if match else ""

    @staticmethod
    def _extract_country_code(target_country_line):
        """从「【目标国家】美国（United States）」中提取国家代码。

        通过反查国家配置的英文名匹配代码；匹配失败时默认 US。

        Args:
            target_country_line: 目标国家行内容。

        Returns:
            国家代码（US / VN / SA / GB / ID）。
        """
        # 取括号内英文名
        m = re.search(r"[（(]([^（）()]+)[)）]", target_country_line)
        en_name = m.group(1).strip() if m else ""
        # 反查配置（这里用配置实例需在调用处处理，此处仅做简单映射）
        mapping = {
            "United States": "US",
            "Vietnam": "VN",
            "Saudi Arabia": "SA",
            "United Kingdom": "GB",
            "Indonesia": "ID",
        }
        return mapping.get(en_name, "US")

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def generate(self, product_info: dict, country: str, platform_style: str = "tiktok_short") -> dict:
        """生成单个国家的本地化短视频脚本。

        流程：
        1. 校验国家代码，加载国家配置
        2. 调用 _check_taboos 获取适用文化禁忌规则
        3. 构建 Prompt（注入禁忌规则）
        4. 调用 _call_llm 生成脚本（有 OPENAI_API_KEY 时走真实 API，否则回退 mock）
        5. 调用 _apply_taboos 二次校验与调整
        6. 返回结构化脚本 dict

        Args:
            product_info: 产品信息 dict，包含
                title / selling_points / category / target_audience / price_range
            country: 目标国家代码（US / VN / SA / GB / ID）
            platform_style: 平台风格偏好（tiktok_short / live_clip / product_showcase）

        Returns:
            结构化脚本 dict，字段：
            hook / product_selling_points / cta / bgm_suggestion /
            subtitle_text / visual_suggestions / cultural_adjustments / meta
        """
        country = country.upper()
        # 校验国家代码
        self._get_country_config(country)

        category = product_info.get("category", "general")

        # 1. 文化禁忌规则匹配
        taboos = self._check_taboos(country, category)

        # 2. 构建 Prompt
        prompt = self._build_prompt(
            product_info, country, platform_style, taboos
        )

        # 3. 调用 LLM 生成脚本（有 OPENAI_API_KEY 时走真实 API，否则回退 mock）
        raw_output = self._call_llm(prompt)
        script = json.loads(raw_output)

        # 4. 文化禁忌二次校验与调整
        script = self._apply_taboos(script, taboos)

        # 附加元信息（便于下游 Agent 使用）
        script["meta"] = {
            "country": country,
            "platform_style": platform_style,
            "category": category,
            "language_code": self._country_config[country]["language_code"],
            "face_type": self._country_config[country]["face_type"],
            "taboo_rules_count": len(taboos),
        }
        return script

    def generate_batch(self, product_info: dict, countries: list) -> list:
        """批量生成多个国家的本地化短视频脚本。

        依次对 countries 中每个国家调用 generate，单国失败时该项以 error 形式返回，
        不影响其他国家的生成。

        Args:
            product_info: 产品信息 dict（同 generate）。
            countries: 目标国家代码列表（如 ["US", "VN", "SA", "GB", "ID"]）。

        Returns:
            脚本 dict 列表，顺序与 countries 一致；单个国家生成异常时
            该项为 {"country": x, "error": "..."}。
        """
        results = []
        platform_style = self._get_country_config(
            countries[0].upper()
        ).get("platform_style", "tiktok_short") if countries else "tiktok_short"

        for country in countries:
            try:
                cfg = self._get_country_config(country)
                # 各国可使用其默认平台风格
                script = self.generate(
                    product_info, country, cfg.get("platform_style", platform_style)
                )
                results.append(script)
            except ValueError as e:
                results.append({"country": country, "error": str(e)})
        return results
