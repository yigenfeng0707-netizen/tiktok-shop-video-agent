# -*- coding: utf-8 -*-
"""
MCP 连通性测试脚本

用途：部署到 MiXer AI 后，验证 MCP 链接是否正常工作。
仅使用 Python 标准库（urllib.request, json, time, sys）。

命令行用法：
    python test_mcp_connectivity.py <mcp_url> [--token <api_key>]

测试项目：
    a. 连通性测试：发送 tools/list JSON-RPC 请求，检查是否返回工具列表
    b. 响应时间测试：测量 tools/list 往返时间，判断是否 < 3 秒
    c. 工具数量统计：解析工具列表，打印每个工具的 name 和 description
    d. 工具调用测试：对每个工具发送 test 调用，检查是否返回有效响应
    e. 稳定性测试：连续 3 次请求 tools/list，检查响应一致性

MCP 协议：JSON-RPC 2.0 over HTTP
    请求头：Content-Type: application/json
              Accept: application/json, text/event-stream（MCP Streamable HTTP 要求）
    鉴权头：X-API-Key: <api_key>（如有 token）
    请求体示例：
        tools/list -> {"jsonrpc":"2.0","method":"tools/list","id":1}
        tools/call -> {"jsonrpc":"2.0","method":"tools/call",
                       "params":{"name":"工具名","arguments":{}},"id":2}
"""

import sys
import json
import time
import urllib.request
import urllib.error


# 请求超时时间（秒）
REQUEST_TIMEOUT = 10
# 响应时间评分阈值（秒）
RESPONSE_TIME_THRESHOLD = 3.0


def print_usage():
    """打印用法提示并退出。"""
    print("=" * 60)
    print("MCP 连通性测试脚本")
    print("=" * 60)
    print("用法:")
    print("    python test_mcp_connectivity.py <mcp_url> [--token <api_key>]")
    print()
    print("参数说明:")
    print("    mcp_url   MCP 服务地址（必填）")
    print("    --token   API Key / 鉴权令牌（可选，没有则不带 X-API-Key 头）")
    print()
    print("示例:")
    print("    python test_mcp_connectivity.py https://xxx.mixerai.app/mcp")
    print("    python test_mcp_connectivity.py https://xxx/mcp --token sk-xxxx")
    print("=" * 60)
    sys.exit(1)


def parse_args(argv):
    """解析命令行参数。

    返回: (mcp_url, token) 元组；参数缺失时调用 print_usage 退出。
    """
    if len(argv) < 2:
        print_usage()

    mcp_url = None
    token = None
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg == "--token":
            # --token 后面应紧跟 api_key
            if i + 1 >= len(argv):
                print("[错误] --token 后面需要提供 api_key")
                sys.exit(1)
            token = argv[i + 1]
            i += 2
        elif arg.startswith("--token="):
            # 支持 --token=xxx 形式
            token = arg.split("=", 1)[1]
            i += 1
        else:
            if mcp_url is None:
                mcp_url = arg
            i += 1

    if not mcp_url:
        print_usage()

    return mcp_url, token


def send_jsonrpc(url, method, params=None, token=None, req_id=1):
    """发送 JSON-RPC 2.0 请求并返回解析后的字典。

    参数:
        url     MCP 服务地址
        method  JSON-RPC 方法名（如 tools/list、tools/call）
        params  方法参数（dict 或 None）
        token   鉴权 token（可选）
        req_id  请求 id

    返回:
        (response_dict, elapsed_seconds) 元组

    异常:
        可能抛出 URLError（网络/超时）、HTTPError（HTTP 错误码）、
        ValueError（JSON 解析失败）
    """
    # 构造 JSON-RPC 2.0 请求体
    body = {
        "jsonrpc": "2.0",
        "method": method,
        "id": req_id,
    }
    if params is not None:
        body["params"] = params

    data = json.dumps(body).encode("utf-8")

    # 构造请求头
    # MCP Streamable HTTP 要求 Accept 头同时声明 application/json 和 text/event-stream
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    if token:
        headers["X-API-Key"] = token

    # 构造 POST 请求
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        # HTTP 错误码：尝试读取响应体用于诊断
        elapsed = time.time() - start
        try:
            err_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            err_body = ""
        raise urllib.error.HTTPError(
            e.url, e.code, "HTTP {0}: {1}".format(e.code, err_body[:200]), e.headers, None
        )
    elapsed = time.time() - start

    # 解析响应：服务器可能返回纯 JSON 或 SSE 格式（event: message\ndata: {...}）
    result = _parse_mcp_response(raw)

    return result, elapsed


def _parse_mcp_response(raw: str) -> dict:
    """解析 MCP 响应，兼容纯 JSON 和 SSE 格式。

    纯 JSON: {"jsonrpc":"2.0","id":1,"result":{...}}
    SSE:     event: message\\ndata: {"jsonrpc":"2.0","id":1,"result":{...}}
    """
    raw = raw.strip()
    if not raw:
        raise ValueError("响应为空")

    # 情况 1：纯 JSON（直接以 { 开头）
    if raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError("JSON 解析失败: {0}；原始内容: {1}".format(e, raw[:200]))

    # 情况 2：SSE 格式，提取 data: 行的 JSON
    if raw.startswith("event:") or "data:" in raw:
        data_lines = []
        for line in raw.split("\n"):
            line = line.strip()
            if line.startswith("data:"):
                data_content = line[5:].strip()
                if data_content:
                    data_lines.append(data_content)
        if data_lines:
            # SSE 可能返回多行 data，合并后解析；通常只有一行
            json_str = data_lines[-1] if len(data_lines) == 1 else "\n".join(data_lines)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                raise ValueError("SSE data JSON 解析失败: {0}；data 内容: {1}".format(e, json_str[:200]))

    # 情况 3：无法识别的格式
    raise ValueError("无法解析的响应格式（非 JSON 非 SSE）；原始内容: {0}".format(raw[:200]))


def format_yes_no(condition):
    """根据布尔值返回 是/否。"""
    return "是" if condition else "否"


def grade_score(score):
    """根据总分返回等级。

    A>=90, B 80-89, C 70-79, D 60-69, E<60
    """
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "E"


def test_connectivity(url, token):
    """测试 a：连通性测试。

    发送 tools/list，检查是否返回工具列表。
    返回: dict(success, tools, message, raw_response)
    """
    print("[1/5] 连通性测试 (tools/list) ...")
    try:
        result, _ = send_jsonrpc(url, "tools/list", token=token, req_id=1)
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "tools": [],
            "message": "HTTP 错误: {0}".format(e),
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "tools": [],
            "message": "网络错误: {0}".format(e.reason),
        }
    except ValueError as e:
        return {
            "success": False,
            "tools": [],
            "message": str(e),
        }
    except Exception as e:
        return {
            "success": False,
            "tools": [],
            "message": "未知错误: {0}".format(e),
        }

    # 检查 JSON-RPC 错误
    if isinstance(result, dict) and "error" in result:
        err = result.get("error", {})
        return {
            "success": False,
            "tools": [],
            "message": "JSON-RPC 错误: {0}".format(err),
        }

    # 解析工具列表：标准 MCP 返回 {"result": {"tools": [...]}}
    tools = []
    if isinstance(result, dict):
        res = result.get("result", result)
        if isinstance(res, dict) and "tools" in res:
            tools = res.get("tools", []) or []
        elif isinstance(res, list):
            # 某些实现直接返回工具列表
            tools = res

    if not isinstance(tools, list):
        tools = []

    return {
        "success": len(tools) > 0,
        "tools": tools,
        "message": "成功获取工具列表，共 {0} 个工具".format(len(tools)) if tools else "未返回任何工具",
    }


def test_response_time(url, token):
    """测试 b：响应时间测试。

    测量 tools/list 往返时间，判断是否 < 3 秒。
    返回: dict(success, elapsed, message)
    """
    print("[2/5] 响应时间测试 ...")
    try:
        _, elapsed = send_jsonrpc(url, "tools/list", token=token, req_id=10)
    except Exception as e:
        return {
            "success": False,
            "elapsed": None,
            "message": "请求失败: {0}".format(e),
        }

    ok = elapsed < RESPONSE_TIME_THRESHOLD
    return {
        "success": ok,
        "elapsed": elapsed,
        "message": "往返时间 {0:.3f} 秒，{1} 3 秒阈值".format(
            elapsed, "满足" if ok else "超出"
        ),
    }


def test_tool_list(tools):
    """测试 c：工具列表统计。

    打印每个工具的 name 和 description。
    返回: 工具数量。
    """
    print("[3/5] 工具列表统计 ...")
    count = len(tools)
    print("    工具数量: {0}".format(count))
    if count == 0:
        print("    (未返回任何工具)")
        return 0

    for idx, tool in enumerate(tools, start=1):
        if not isinstance(tool, dict):
            print("    {0}) {1}".format(idx, tool))
            continue
        name = tool.get("name", "(无名称)")
        desc = tool.get("description", "(无描述)")
        # 描述过长时截断显示
        if isinstance(desc, str) and len(desc) > 120:
            desc = desc[:120] + "..."
        print("    {0}) name: {1}".format(idx, name))
        print("       description: {0}".format(desc))
    return count


def test_tool_calls(url, token, tools):
    """测试 d：工具调用测试。

    对每个工具发送 tools/call 调用（空参数），
    检查是否返回有效响应（不要求成功，只要不超时或 500）。
    返回: dict(success_count, fail_count, total, details)
    """
    print("[4/5] 工具调用测试 (tools/call) ...")
    total = len(tools)
    if total == 0:
        print("    无工具可测试，跳过")
        return {"success_count": 0, "fail_count": 0, "total": 0, "details": []}

    success_count = 0
    fail_count = 0
    details = []

    for idx, tool in enumerate(tools, start=1):
        if not isinstance(tool, dict):
            fail_count += 1
            details.append({"name": str(tool), "ok": False, "msg": "工具定义非字典"})
            continue
        name = tool.get("name", "")
        if not name:
            fail_count += 1
            details.append({"name": "(无名称)", "ok": False, "msg": "缺少 name 字段"})
            continue

        # 构造最小参数：尝试空 arguments
        params = {"name": name, "arguments": {}}
        try:
            result, _ = send_jsonrpc(
                url, "tools/call", params=params, token=token, req_id=100 + idx
            )
        except urllib.error.HTTPError as e:
            # HTTP 500 视为失败；其他 HTTP 错误也视为失败
            code = e.code
            fail_count += 1
            details.append(
                {"name": name, "ok": False, "msg": "HTTP {0}".format(code)}
            )
            print("    [{0}/{1}] {2} -> FAIL (HTTP {3})".format(idx, total, name, code))
            continue
        except urllib.error.URLError as e:
            fail_count += 1
            details.append(
                {"name": name, "ok": False, "msg": "网络/超时: {0}".format(e.reason)}
            )
            print(
                "    [{0}/{1}] {2} -> FAIL (网络/超时: {3})".format(
                    idx, total, name, e.reason
                )
            )
            continue
        except Exception as e:
            fail_count += 1
            details.append({"name": name, "ok": False, "msg": str(e)})
            print("    [{0}/{1}] {2} -> FAIL ({3})".format(idx, total, name, e))
            continue

        # 只要返回了有效 JSON-RPC 响应（不论 result 还是 error）都算"有效响应"
        if isinstance(result, dict) and ("result" in result or "error" in result):
            success_count += 1
            # 判断是结果还是错误
            if "error" in result:
                msg = "返回 JSON-RPC error（视为有效响应）"
            else:
                msg = "返回 result（成功）"
            details.append({"name": name, "ok": True, "msg": msg})
            print("    [{0}/{1}] {2} -> PASS ({3})".format(idx, total, name, msg))
        else:
            fail_count += 1
            details.append({"name": name, "ok": False, "msg": "响应结构异常"})
            print("    [{0}/{1}] {2} -> FAIL (响应结构异常)".format(idx, total, name))

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "total": total,
        "details": details,
    }


def test_stability(url, token):
    """测试 e：稳定性测试。

    连续 3 次请求 tools/list，检查响应一致性（工具数量与名称集合一致）。
    返回: dict(success, rounds, message)
    """
    print("[5/5] 稳定性测试 (连续 3 次 tools/list) ...")
    name_sets = []
    counts = []
    for i in range(3):
        try:
            result, _ = send_jsonrpc(url, "tools/list", token=token, req_id=200 + i)
        except Exception as e:
            print("    第 {0} 次请求失败: {1}".format(i + 1, e))
            return {
                "success": False,
                "rounds": i,
                "message": "第 {0} 次请求失败: {1}".format(i + 1, e),
            }

        # 提取工具名称集合
        tools = []
        if isinstance(result, dict):
            res = result.get("result", result)
            if isinstance(res, dict) and "tools" in res:
                tools = res.get("tools", []) or []
            elif isinstance(res, list):
                tools = res
        names = sorted(
            [t.get("name", "") for t in tools if isinstance(t, dict)]
        )
        name_sets.append(names)
        counts.append(len(names))
        print(
            "    第 {0} 次: 工具数 {1}, 名称集合 {2}".format(
                i + 1, len(names), names
            )
        )

    # 比较三次结果是否一致
    consistent = (
        name_sets[0] == name_sets[1] == name_sets[2]
        and counts[0] == counts[1] == counts[2]
    )
    return {
        "success": consistent,
        "rounds": 3,
        "message": "三次响应{0}一致".format("完全" if consistent else "不"),
    }


def main():
    """主流程：解析参数 → 依次执行 5 项测试 → 汇总评分。"""
    # Windows 控制台编码兼容处理
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    mcp_url, token = parse_args(sys.argv)

    print("=" * 60)
    print("MCP 连通性测试报告")
    print("=" * 60)
    print("测试目标: {0}".format(mcp_url))
    print("鉴权 Token: {0}".format("已提供" if token else "未提供"))
    print("测试时间: {0}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    print("-" * 60)

    # ---- 测试 a：连通性 ----
    conn_result = test_connectivity(mcp_url, token)
    tools = conn_result.get("tools", [])
    conn_ok = conn_result.get("success", False)
    print("    结果: {0}".format("PASS" if conn_ok else "FAIL"))
    print("    说明: {0}".format(conn_result.get("message", "")))
    print()

    # ---- 测试 b：响应时间 ----
    rt_result = test_response_time(mcp_url, token)
    rt_ok = rt_result.get("success", False)
    rt_elapsed = rt_result.get("elapsed")
    if rt_elapsed is not None:
        print("    往返时间: {0:.3f} 秒".format(rt_elapsed))
        print("    是否 < 3 秒: {0}".format(format_yes_no(rt_ok)))
    print("    结果: {0}".format("PASS" if rt_ok else "FAIL"))
    print("    说明: {0}".format(rt_result.get("message", "")))
    print()

    # ---- 测试 c：工具列表 ----
    tool_count = test_tool_list(tools)
    print()

    # ---- 测试 d：工具调用 ----
    call_result = test_tool_calls(mcp_url, token, tools)
    call_ok_count = call_result.get("success_count", 0)
    call_total = call_result.get("total", 0)
    call_fail = call_result.get("fail_count", 0)
    call_pass = call_total > 0 and call_ok_count > 0
    print(
        "    成功: {0} / {1}, 失败: {2}".format(call_ok_count, call_total, call_fail)
    )
    print("    结果: {0}".format("PASS" if call_pass else "FAIL"))
    print()

    # ---- 测试 e：稳定性 ----
    stab_result = test_stability(mcp_url, token)
    stab_ok = stab_result.get("success", False)
    print("    结果: {0}".format("PASS" if stab_ok else "FAIL"))
    print("    说明: {0}".format(stab_result.get("message", "")))
    print()

    # ---- 评分 ----
    # 连通性 40 分
    if conn_ok and tool_count > 0:
        conn_score = 40.0
    elif conn_ok:
        conn_score = 20.0
    else:
        conn_score = 0.0

    # 响应时间 30 分
    if rt_elapsed is None:
        rt_score = 0.0
    elif rt_elapsed < 1.0:
        rt_score = 30.0
    elif rt_elapsed < RESPONSE_TIME_THRESHOLD:
        rt_score = 30.0
    elif rt_elapsed < 5.0:
        rt_score = 15.0
    else:
        rt_score = 5.0

    # 工具调用 30 分
    if call_total > 0:
        call_score = 30.0 * (call_ok_count / call_total)
    else:
        call_score = 0.0

    total_score = conn_score + rt_score + call_score
    grade = grade_score(total_score)

    print("=" * 60)
    print("评分明细:")
    print("    连通性:   满分 40, 实际 {0:.1f}".format(conn_score))
    print("    响应时间: 满分 30, 实际 {0:.1f}".format(rt_score))
    print("    工具调用: 满分 30, 实际 {0:.1f}".format(call_score))
    print("    ------------------------------")
    print("    总分:     {0:.1f} / 100".format(total_score))
    print("    等级:     {0}".format(grade))
    print("=" * 60)
    print(
        "等级说明: A>=90 | B 80-89 | C 70-79 | D 60-69 | E<60"
    )

    # 非零退出码表示测试未完全通过，便于脚本集成判断
    if total_score >= 90:
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
