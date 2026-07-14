@echo off
chcp 65001
echo === MCP 连通性测试 ===
set /p url="请输入 MCP 链接: "
set /p token="请输入 API Key (没有直接回车): "
if "%token%"=="" (
  python test_mcp_connectivity.py %url%
) else (
  python test_mcp_connectivity.py %url% --token %token%
)
pause
