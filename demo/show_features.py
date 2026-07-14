"""展示 Demo 实现的所有功能"""
import sys
sys.path.insert(0, '.')
from agents.script_generator import ScriptGenerator
from agents.digital_human import DigitalHumanGenerator
from agents.batch_editor import BatchEditor
from agents.data_reviewer import DataReviewer
from orchestrator.main import Orchestrator

print('=' * 60)
print('TikTok Shop 跨境短视频 AI 本地化生产 Agent - 功能展示')
print('=' * 60)

product_info = {
    "title": "便携榨汁杯 Portable Juicer",
    "selling_points": ["USB充电", "300ml容量", "10秒榨汁", "随身携带"],
    "category": "kitchen"
}
countries = ['US', 'VN', 'SA', 'GB', 'ID']

# ===== 功能 1: AI 脚本生成 =====
print('\n【功能 1】AI 脚本生成（5 国本土化）')
print('-' * 60)
sg = ScriptGenerator()
scripts = sg.generate_batch(product_info, countries)
print(f'成功生成 {len(scripts)} 国脚本')
for s in scripts:
    country = s.get('country', '?')
    hook = s.get('hook', s.get('hook_type', ''))
    title = s.get('title', '')
    bgm = s.get('bgm_style', '')
    notes = s.get('cultural_notes', s.get('taboo_handling', ''))
    print(f'\n  [{country}]')
    print(f'    钩子: {hook[:60] if hook else ""}')
    print(f'    标题: {title[:60] if title else ""}')
    print(f'    BGM风格: {bgm}')
    if notes:
        print(f'    文化处理: {notes[:80]}')

# ===== 功能 2: AI 数字人多语种 =====
print('\n\n【功能 2】AI 数字人多语种出镜')
print('-' * 60)
dh = DigitalHumanGenerator()
dh_results = []
for script in scripts:
    country = script.get('country', 'US')
    result = dh.generate_video(script, country)
    dh_results.append(result)
    print(f'\n  [{country}]')
    print(f'    面孔类型: {result.get("face_type", "")}')
    print(f'    语种: {result.get("language", "")}')
    print(f'    时长: {result.get("duration", "")}秒')
    out = result.get("output_path", "")
    print(f'    输出文件: {out[:80] if out else ""}')

# ===== 功能 3: AI 批量剪辑 =====
print('\n\n【功能 3】AI 批量剪辑 + 场景替换')
print('-' * 60)
be = BatchEditor()
edit_results = be.batch_edit(dh_results)
print(f'成功生成 {len(edit_results)} 条剪辑命令')
for r in edit_results[:2]:
    country = r.get('country', '?')
    cmd = r.get('ffmpeg_command', r.get('command', ''))
    print(f'\n  [{country}] ffmpeg 命令长度: {len(cmd)} 字符')
    print(f'    含字幕烧录: {"subtitles" in cmd}')
    print(f'    含BGM混音: {"amix" in cmd}')
    print(f'    含特效贴纸: {"drawtext" in cmd}')
    print(f'    含转场: {"fade" in cmd}')
    print(f'    输出: {r.get("output_path", "")[:80]}')

# ===== 功能 4: AI 数据复盘 =====
print('\n\n【功能 4】AI 数据复盘（闭环迭代）')
print('-' * 60)
dr = DataReviewer()
# 用 mock 数据跑复盘
import json
from pathlib import Path
mock_path = Path('templates/mock_data.json')
if mock_path.exists():
    mock_videos = json.loads(mock_path.read_text(encoding='utf-8'))
    review = dr.run_full_review(mock_videos)
else:
    review = dr.run_full_review([])
total = review.get('total_videos', 0)
high = review.get('high_traffic_count', 0)
avg_rate = review.get('avg_completion_rate', 0)
print(f'分析视频数: {total}')
print(f'高流量视频: {high}')
print(f'平均完播率: {avg_rate}')
sugs = review.get('suggestions', [])
print(f'\n优化建议 ({len(sugs)} 条):')
for i, sug in enumerate(sugs[:5], 1):
    priority = sug.get('priority', '')
    content = sug.get('content', sug.get('suggestion', ''))
    print(f'  {i}. [{priority}] {content[:80]}')

# ===== 完整流水线 =====
print('\n\n【完整流水线】runFullPipeline 一键执行')
print('-' * 60)
orch = Orchestrator()
result = orch.run_pipeline(
    product_title='便携榨汁杯 Portable Juicer',
    selling_points=['USB充电', '300ml容量', '10秒榨汁', '随身携带'],
    category='kitchen',
    countries=['US', 'VN', 'SA', 'GB', 'ID']
)
status = result.get('status', '')
total_time = result.get('total_time', 0)
print(f'状态: {status}')
print(f'总耗时: {total_time}s')
steps = result.get('steps', {})
for step_name, step_data in steps.items():
    if isinstance(step_data, dict):
        count = step_data.get('count', step_data.get('total', 0))
        time_s = step_data.get('time', 0)
        print(f'  {step_name}: {count} 条, {time_s}s')

print('\n' + '=' * 60)
print('全部 4 大功能 + 1 个主编排 = 5 个 MCP 工具')
print('=' * 60)
