from serpapi import SerpApiClient
import os


def search(query: str) -> str:

    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            print(f"attach environment variable 'SERPAPI_API_KEY' Error")
            return f"SERAPI_API_KEY fails to config in .env file"

        params  = {
            "engine": "google",
            "q": "query",
            "api_key": api_key,
            "gl":"cn",
            "hl":"zh-cn"
        }
        client = SerpApiClient(params)
        result = client.get_dict()
        if "answer_box_list" in result:
            return "\n".join(result["answer_box_list"])
        if "answer_box" in result and "answer" in result["answer_box"]:
            return result["answer_box"]["answer"]
        if "knowledge_graph" in result and "description" in result["knowledge_graph"]:
            return result["knowledge_graph"]["description"]
        if "organic_result" in result and result["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(result["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"


