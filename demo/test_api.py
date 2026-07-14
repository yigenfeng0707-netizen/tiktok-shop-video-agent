"""测试大模型 API 连通性"""
import os
from dotenv import load_dotenv
load_dotenv()
import requests

api_key = os.environ.get('OPENAI_API_KEY', '')
base_url = os.environ.get('OPENAI_BASE_URL', '')

# 测试多个模型 ID
models = [
    'qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-long',
    'qwen2.5-7b-instruct', 'qwen2.5-14b-instruct', 'qwen2-72b-instruct',
    'deepseek-v3', 'deepseek-r1', 'claude-3-5-sonnet-20241022'
]
url = base_url.rstrip('/') + '/chat/completions'
headers = {'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}

print('Base URL:', base_url)
print('测试模型列表:', models)
print('-' * 60)

found = False
for model in models:
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': 'hi'}],
        'max_tokens': 10
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            content = data['choices'][0]['message']['content']
            print('[OK] {} -> {}'.format(model, content[:50]))
            found = True
            break
        else:
            err = resp.json().get('error', {})
            msg = err.get('message', '')[:60] if isinstance(err, dict) else str(err)[:60]
            print('[{}] {}: {}'.format(resp.status_code, model, msg))
    except Exception as e:
        print('[ERR] {}: {}'.format(model, str(e)[:60]))

if not found:
    print('\n主模型全部失败，尝试备用模型...')
    # 测试 fallback1: 商汤
    fb1_url = os.environ.get('FALLBACK1_BASE_URL', '')
    fb1_key = os.environ.get('FALLBACK1_API_KEY', '')
    fb1_model = os.environ.get('FALLBACK1_MODEL', '')
    if fb1_url:
        url1 = fb1_url.rstrip('/') + '/chat/completions'
        h1 = {'Authorization': 'Bearer ' + fb1_key, 'Content-Type': 'application/json'}
        p1 = {'model': fb1_model, 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 10}
        try:
            r1 = requests.post(url1, headers=h1, json=p1, timeout=15)
            print('\n商汤 SenseNova:', r1.status_code)
            if r1.status_code == 200:
                print('返回:', r1.json()['choices'][0]['message']['content'][:50])
                print('建议使用: FALLBACK1')
            else:
                print('错误:', r1.text[:200])
        except Exception as e:
            print('商汤异常:', e)

    # 测试 fallback2: 阶跃
    fb2_url = os.environ.get('FALLBACK2_BASE_URL', '')
    fb2_key = os.environ.get('FALLBACK2_API_KEY', '')
    fb2_model = os.environ.get('FALLBACK2_MODEL', '')
    if fb2_url:
        url2 = fb2_url.rstrip('/') + '/chat/completions'
        h2 = {'Authorization': 'Bearer ' + fb2_key, 'Content-Type': 'application/json'}
        p2 = {'model': fb2_model, 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 10}
        try:
            r2 = requests.post(url2, headers=h2, json=p2, timeout=15)
            print('\n阶跃 Step:', r2.status_code)
            if r2.status_code == 200:
                print('返回:', r2.json()['choices'][0]['message']['content'][:50])
                print('建议使用: FALLBACK2')
            else:
                print('错误:', r2.text[:200])
        except Exception as e:
            print('阶跃异常:', e)
