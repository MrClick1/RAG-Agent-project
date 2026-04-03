"""
MCP天气工具 - 使用langchain_mcp_adapters连接高德MCP服务器

使用 MultiServerMCPClient 连接官方 @amap/amap-maps-mcp-server
提供的工具：
- maps_weather: 天气预报
- maps_geo: 地理编码（地址转坐标）
- maps_regeocode: 逆地理编码（坐标转地址）
- maps_ip_location: IP定位
等
"""

import os
import json
import asyncio
from typing import List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool, tool
from utils.config_handler import agent_conf


# ============================================================
# MCP 客户端
# ============================================================

def get_mcp_client() -> MultiServerMCPClient:
    """
    创建 MCP 客户端连接高德地图服务器

    环境变量：
    - AMAP_MAPS_API_KEY: 高德地图 API Key
    """
    amap_key = agent_conf.get("amap_api_key")
    if not amap_key:
        raise ValueError("AMAP_MAPS_API_KEY is required. Please configure in .env file")

    return MultiServerMCPClient(
        {
            "amap": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@amap/amap-maps-mcp-server"],
                "env": {"AMAP_MAPS_API_KEY": amap_key},
            }
        }
    )


async def get_mcp_tools_async() -> List[BaseTool]:
    """异步获取 MCP 工具列表"""
    client = get_mcp_client()
    tools = await client.get_tools(server_name="amap")
    return tools


def get_mcp_tools() -> List[BaseTool]:
    """同步获取 MCP 工具列表"""
    try:
        loop = asyncio.get_running_loop()
        # 如果已经在事件循环中，创建一个新任务
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, get_mcp_tools_async())
            return future.result()
    except RuntimeError:
        # 没有运行中的事件循环
        return asyncio.run(get_mcp_tools_async())


# ============================================================
# 工具缓存
# ============================================================

_mcp_tools_cache: List[BaseTool] = None


def get_cached_mcp_tools() -> List[BaseTool]:
    """获取缓存的 MCP 工具列表"""
    global _mcp_tools_cache
    if _mcp_tools_cache is None:
        _mcp_tools_cache = get_mcp_tools()
    return _mcp_tools_cache


def get_mcp_tool(tool_name: str) -> Optional[BaseTool]:
    """获取指定名称的 MCP 工具"""
    tools = get_cached_mcp_tools()
    for t in tools:
        if t.name == tool_name:
            return t
    return None


# ============================================================
# 便捷封装函数
# ============================================================

async def get_weather_async(city: str) -> str:
    """
    获取城市天气预报（异步版本）

    Args:
        city: 城市名称，如"深圳"、"北京"

    Returns:
        格式化的天气信息字符串
    """
    weather_tool = get_mcp_tool("maps_weather")
    if not weather_tool:
        return "错误：未找到天气查询工具"

    try:
        result = await weather_tool.ainvoke({"city": city})
        # 解析返回结果
        if isinstance(result, list) and len(result) > 0:
            content = result[0].get("text", "")
            data = json.loads(content)
            return _format_weather_response(data)
        return "解析天气数据失败"
    except Exception as e:
        return f"查询异常：{str(e)}"


def get_weather(city: str) -> str:
    """
    获取城市天气预报（同步版本）

    Args:
        city: 城市名称

    Returns:
        格式化的天气信息字符串
    """
    return asyncio.run(get_weather_async(city))


def _format_weather_response(data: dict) -> str:
    """格式化天气响应数据"""
    if "status" in data and data["status"] != "1":
        return f"查询失败：{data.get('info', '未知错误')}"

    city = data.get("city", "未知")
    forecasts = data.get("forecasts", [])

    if not forecasts:
        return f"{city}：暂无预报数据"

    result = [f"{city} 天气预报："]

    # 今天
    today = forecasts[0]
    result.append(
        f"今天({today['date']})："
        f"{today['dayweather']}，气温{today['nighttemp']}~{today['daytemp']}°C，"
        f"{today['daywind']}风{today['daypower']}级"
    )

    # 未来几天
    for fc in forecasts[1:4]:
        result.append(
            f"{fc['date']}："
            f"{fc['dayweather']}，气温{fc['nighttemp']}~{fc['daytemp']}°C"
        )

    return "\n".join(result)


# ============================================================
# LangChain 工具封装（用于直接注册到 Agent）
# ============================================================

@tool(description="获取指定城市的天气预报，返回未来几天的天气情况")
def get_weather_tool(city: str) -> str:
    """
    获取城市天气预报

    Args:
        city: 城市名称，如"深圳"、"北京"、"上海"

    Returns:
        格式化的天气信息，包含今天和未来3天的预报
    """
    return get_weather(city)


def get_weather_tools() -> List[BaseTool]:
    """
    获取天气相关的 LangChain 工具列表

    Returns:
        可直接注册到 Agent 的工具列表
    """
    return [get_weather_tool]


# ============================================================
# 使用说明
# ============================================================
"""
## 快速开始

1. 配置环境变量（在 .env 文件中）：
   AMAP_KEY=你的高德API Key

2. 获取天气工具并注册到 Agent：

   from agent.tools.mcp_weather_tools import get_weather_tools

   # 获取天气工具
   weather_tools = get_weather_tools()

3. 注册到 Agent：

   self.agent = create_agent(
       model=chat_model,
       tools=[rag_summarize, *weather_tools, ...],
       ...
   )

## 可用的 MCP 工具

- maps_weather: 天气预报
- maps_geo: 地址转坐标
- maps_regeocode: 坐标转地址/城市
- maps_ip_location: IP定位
- maps_search_detail: 地点详情搜索
- maps_direction_walking: 步行路线规划
- maps_direction_driving: 驾车路线规划
- maps_direction_transit_integrated: 公交路线规划
- maps_distance: 距离测量
- maps_text_search: 文本搜索
- maps_around_search: 周边搜索
- maps_bicycling: 骑行路线规划

## 直接调用示例

from agent.tools.mcp_weather_tools import get_weather

weather = get_weather("深圳")
print(weather)
"""


if __name__ == "__main__":
    print("=== 测试 MCP 天气工具 ===\n")

    # 测试天气查询
    print("1. 测试天气查询：")
    weather = get_weather("深圳")
    print(weather)

    print("\n2. 获取所有 MCP 工具：")
    tools = get_cached_mcp_tools()
    print(f"共 {len(tools)} 个工具：")
    for t in tools:
        print(f"  - {t.name}")
