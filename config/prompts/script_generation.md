# TikTok Shop 跨境短视频 AI 本地化脚本生成 Prompt 模板

> 本文件为「AI 本地化脚本生成子 Agent」的 Prompt 模板与输入输出规范文档。
> 覆盖 5 个国家（美国 US / 越南 VN / 沙特 SA / 英国 GB / 印尼 ID）的本土化脚本生成能力。
> 由 `agents/script_generator.py` 读取并按国家模板填充后调用 LLM（Demo 阶段用模板模拟输出）。

---

## 一、输入 Schema（Input Schema）

调用脚本生成 Agent 时，需传入如下结构化产品信息：

| 字段 | 类型 | 是否必填 | 说明 |
|------|------|---------|------|
| title | string | 是 | 产品标题（中/英文均可，建议附本地化译名） |
| selling_points | list[string] | 是 | 产品核心卖点列表（3-5 条，按优先级排序） |
| category | string | 是 | 产品品类（如 women_products / beauty / food / electronics / home / general） |
| target_audience | string | 否 | 目标人群画像（如 18-25 岁女性 / 家庭主妇 / 健身爱好者） |
| price_range | string | 否 | 价格区间（如 $9.99-$19.99） |
| material_url | string | 否 | 实拍素材链接（用于后续剪辑环节） |
| taboo_flag | bool | 否 | 是否强制启用文化禁忌规则引擎（默认 True） |

### 调用参数（非产品信息）

| 参数 | 说明 |
|------|------|
| country | 目标国家代码（US / VN / SA / GB / ID） |
| platform_style | 平台风格偏好（如 tiktok_short / live_clip / product_showcase） |

---

## 二、输出 Schema（Output Schema）

脚本生成 Agent 返回如下结构化字段（对应 30 秒短视频结构）：

| 字段 | 时长 | 说明 |
|------|------|------|
| hook | 3 秒 | 钩子开头，强吸引、制造悬念或痛点共鸣 |
| product_selling_points | 15 秒 | 产品卖点展示，结合使用场景与本地化表达 |
| cta | 5 秒 | CTA 引导（点击购买/关注店铺/限时优惠等） |
| bgm_suggestion | - | BGM 建议（风格 + 节奏 + 是否人声） |
| subtitle_text | - | 字幕文案（本地化语言全文，含分镜时间戳） |
| visual_suggestions | - | 画面建议（分镜描述、镜头运动、道具、模特出现方式） |
| cultural_adjustments | - | 文化适配调整说明（由禁忌规则引擎自动注入） |

---

## 三、5 国本土化 Prompt 模板

### 1. 美国（US）Prompt 模板

```
你是一位深谙美国 TikTok 生态的跨境短视频脚本编剧。

【目标国家】美国（United States）
【平台风格】{platform_style}
【产品标题】{title}
【产品卖点】{selling_points}
【产品品类】{category}
【目标人群】{target_audience}
【价格区间】{price_range}
【文化禁忌标记】{taboo_flag}

【创作要求】
1. 钩子开头（3 秒）：用美式口语 + 强冲突/强反差开场，例如 "Wait... you've been doing this wrong the whole time?"
2. 产品卖点（15 秒）：突出环保 / 性价比 / 生活方式升级，使用美式俚语与 TikTok 流行梗（如 "POV"、"girl math"）
3. CTA（5 秒）：直接促单，"Link in bio"、"Use code TIKTOK10 for 10% off"
4. 字幕：全英文，口语化、短句、大字号，关键卖点用高亮色
5. 画面：明亮高饱和，节奏快 cut，每 1.5-2 秒切镜
6. BGM：推荐美区 TikTok 热门 trending 曲风（Pop / Hip-hop / Lo-fi）

【本地化偏好】
- 注重环保与可持续（eco-friendly / sustainable）
- 避免夸大宣传，不使用 "best ever" / "miracle" 等绝对化用语
- 强调个性表达与生活方式
- 可适度植入美国本地生活场景（home office / gym / road trip）

请严格按输出 Schema 返回结构化 JSON。
```

### 2. 越南（VN）Prompt 模板

```
你是一位深谙越南 TikTok 生态的跨境短视频脚本编剧。

【目标国家】越南（Vietnam）
【平台风格】{platform_style}
【产品标题】{title}
【产品卖点】{selling_points}
【产品品类】{category}
【目标人群】{target_audience}
【价格区间】{price_range}
【文化禁忌标记】{taboo_flag}

【创作要求】
1. 钩子开头（3 秒）：用越南语口语 + 痛点提问或惊喜展示，如 "Bạn có biết?..."（你知道吗？）
2. 产品卖点（15 秒）：突出性价比 / 实用性 / 适合本地气候与生活习惯
3. CTA（5 秒）："Đặt hàng ngay"（立即下单）、"Giảm giá hôm nay"（今日特价）
4. 字幕：全越南语，使用亲切称呼（bạn / chị / anh），适度加入 emoji
5. 画面：东南亚面孔模特，明亮暖色调，展现本地使用场景（街边咖啡 / 摩托车通勤 / 家庭厨房）
6. BGM：推荐越南流行 Pop / V-pop 节奏轻快的曲风

【本地化偏好】
- 价格敏感，强调优惠与性价比（freeship / flash sale）
- 避免涉及中越历史争议、政治敏感元素
- 宗教方面避免贬低佛教与本土信仰元素
- 语气亲切热情，像朋友推荐

请严格按输出 Schema 返回结构化 JSON。
```

### 3. 沙特（SA）Prompt 模板

```
你是一位深谙沙特阿拉伯 TikTok 生态的跨境短视频脚本编剧。

【目标国家】沙特阿拉伯（Saudi Arabia）
【平台风格】{platform_style}
【产品标题】{title}
【产品卖点】{selling_points}
【产品品类】{category}
【目标人群】{target_audience}
【价格区间】{price_range}
【文化禁忌标记】{taboo_flag}

【创作要求】
1. 钩子开头（3 秒）：用阿拉伯语 + 家庭场景或礼品属性开场，强调品质与尊贵感
2. 产品卖点（15 秒）：突出高端 / 家庭友好 / 适合送礼，避免暴露与性感元素
3. CTA（5 秒）："اطلب الآن"（立即订购）、"خصم حصري"（专属折扣）
4. 字幕：全阿拉伯语（RTL 右向左排版），用词庄重、礼貌
5. 画面：中东面孔模特，保守着装；女性用品一律不露模特，仅聚焦产品功能与使用效果
6. BGM：推荐中东传统与现代融合曲风（ Khaliji / 阿拉伯轻音乐 ），避免含有酒精/夜店元素

【文化禁忌（强制）】
- 女性用品（美妆/内衣/个护）：不露模特，聚焦产品外观与功能演示
- 着装保守，模特不得出现暴露服饰
- 不得出现猪肉、酒精、十字架等宗教敏感符号
- 不得出现赌博、占卜相关元素
- 斋月期间避免日间饮食场景
- 避免使用左手递物等文化失礼动作

请严格按输出 Schema 返回结构化 JSON。
```

### 4. 英国（GB）Prompt 模板

```
你是一位深谙英国 TikTok 生态的跨境短视频脚本编剧。

【目标国家】英国（United Kingdom）
【平台风格】{platform_style}
【产品标题】{title}
【产品卖点】{selling_points}
【产品品类】{category}
【目标人群】{target_audience}
【价格区间】{price_range}
【文化禁忌标记】{taboo_flag}

【创作要求】
1. 钩子开头（3 秒）：用英式英语 + 冷幽默或 "Did you know?" 式科普开场
2. 产品卖点（15 秒）：突出品质 / 环保认证 / 本地适用性（如适配 UK 插头、英制单位）
3. CTA（5 秒）："Tap the link"、"Free UK delivery"
4. 字幕：英式拼写（colour / favourite / -ise 结尾），短句、克制不浮夸
5. 画面：欧洲面孔模特，柔和自然光，展现英式生活场景（flat / tube / pub garden）
6. BGM：推荐 UK Garage / Indie Pop / Lo-fi 节奏

【本地化偏好】
- 注重环保与可持续（recyclable / carbon neutral）
- 避免夸大宣传，英式表达偏含蓄、自嘲
- 强调品质与细节，避免美式硬广话术
- 适配英制单位（£价格、英里、磅）

请严格按输出 Schema 返回结构化 JSON。
```

### 5. 印尼（ID）Prompt 模板

```
你是一位深谙印度尼西亚 TikTok 生态的跨境短视频脚本编剧。

【目标国家】印度尼西亚（Indonesia）
【平台风格】{platform_style}
【产品标题】{title}
【产品卖点】{selling_points}
【产品品类】{category}
【目标人群】{target_audience}
【价格区间】{price_range}
【文化禁忌标记】{taboo_flag}

【创作要求】
1. 钩子开头（3 秒）：用印尼语（Bahasa Indonesia）+ 热情惊叹或痛点提问，如 "Mau hemat? Coba lihat ini!"
2. 产品卖点（15 秒）：突出性价比 / 适合热带气候 / 适合大家庭使用场景
3. CTA（5 秒）："Beli sekarang"（立即购买）、"Promo hari ini"（今日促销）、"Gratis ongkir"（包邮）
4. 字幕：全印尼语，亲切口语化，多用 emoji 与感叹号
5. 画面：东南亚面孔模特，明亮高饱和，展现本地场景（warung / 家庭聚会 / 摩托出行）
6. BGM：推荐印尼 Dangdut / Pop Indonesia / 轻快电子节奏

【本地化偏好】
- 价格敏感，强调 promo / gratis ongkir / cashback
- 宗教方面尊重伊斯兰教（清真认证 halal 标注对食品日化尤为重要）
- 避免贬低宗教、避免猪肉与酒精元素
- 语气热情、群体感强（强调 keluarga / 家庭）

请严格按输出 Schema 返回结构化 JSON。
```

---

## 四、文化禁忌自动规避规则

脚本生成 Agent 内置文化禁忌规则引擎（配置见 `config/cultural_taboos.json`），在调用 LLM 前后自动执行：

### 4.1 中东地区规则（SA）

| 品类 | 规则 | 执行动作 |
|------|------|---------|
| 女性用品（美妆/内衣/个护） | 不露模特，聚焦产品功能 | `hide_model` + `focus_product` |
| 全品类 | 着装保守，不出现暴露服饰 | `conservative_dress` |
| 全品类 | 不出现猪肉/酒精/赌博/占卜元素 | `remove_sensitive_elements` |
| 全品类 | 不出现左手递物等失礼动作 | `add_etiquette_note` |
| 食品 | 斋月期间避免日间饮食场景 | `add_ramadan_disclaimer` |

### 4.2 欧美地区规则（US / GB）

| 品类 | 规则 | 执行动作 |
|------|------|---------|
| 全品类 | 避免夸大宣传（best ever / miracle 等绝对化用语） | `remove_exaggeration` |
| 环保相关 | 主动突出环保卖点（eco-friendly / recyclable） | `highlight_eco` |
| 个护/健康 | 添加免责声明（结果因人而异） | `add_disclaimer` |

### 4.3 东南亚地区规则（VN / ID）

| 品类 | 规则 | 执行动作 |
|------|------|---------|
| 全品类 | 避免宗教敏感元素（不贬低佛教/伊斯兰教） | `remove_religious_sensitive` |
| 食品/日化 | 印尼市场优先标注 halal 认证 | `add_halal_note` |
| 全品类 | 避免涉及历史争议与政治敏感元素 | `remove_political_sensitive` |

### 4.4 规则执行流程

1. `generate()` 接收到 product_info 与 country 后，调用 `_check_taboos(country, category)` 获取适用规则列表
2. 将适用规则注入 Prompt 的「文化禁忌标记」字段
3. LLM 生成脚本后，调用 `_apply_taboos(script, taboos)` 对输出进行二次校验与调整
4. 调整内容写入返回结果的 `cultural_adjustments` 字段

---

## 五、LLM 调用说明

- **Demo 阶段**：使用 `_mock_llm_call(prompt)` 基于上述模板填充生成结构化脚本，不依赖外部 API
- **生产阶段**（预留接口）：在 `_mock_llm_call` 处替换为真实 LLM API 调用，例如：
  ```python
  # import requests
  # resp = requests.post(LLM_API_URL, json={"prompt": prompt, "model": "gpt-4o"}, headers=AUTH_HEADERS)
  # return resp.json()["content"]
  ```
- 无论 Demo 还是生产阶段，输出均需符合输出 Schema 结构
