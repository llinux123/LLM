import json
import os

from typing import List
import re

from llm_client import HelloAgentsLLM
# 加载 .env 文件中的环境变量







from serpapi import SerpApiClient


def search(query: str) -> str:
    """
    一个基于SerpApi的实战网页搜索引擎工具。
    它会智能地解析搜索结果，优先返回直接答案或知识图谱信息。
    """
    print(f"🔍 正在执行 [SerpApi] 网页搜索: {query}")
    try:
        api_key = os.getenv("SERPAPI_API_KEY")
        if not api_key:
            return "错误:SERPAPI_API_KEY 未在 .env 文件中配置。"

        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "gl": "cn",  # 国家代码
            "hl": "zh-cn",  # 语言代码
        }

        client = SerpApiClient(params)
        results = client.get_dict()

        # 智能解析:优先寻找最直接的答案
        if "answer_box_list" in results:
            return "\n".join(results["answer_box_list"])
        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            # 如果没有直接答案，则返回前三个有机结果的摘要
            snippets = [
                f"[{i + 1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)

        return f"对不起，没有找到关于 '{query}' 的信息。"

    except Exception as e:
        return f"搜索时发生错误: {e}"


from typing import Dict, Any

class ToolExecutor:
    """
    一个工具执行器，负责管理和执行工具。
    """
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def registerTool(self, name: str, description: str, func: callable):
        """
        向工具箱中注册一个新工具。
        """
        if name in self.tools:
            print(f"警告:工具 '{name}' 已存在，将被覆盖。")
        self.tools[name] = {"description": description, "func": func}
        print(f"工具 '{name}' 已注册。")

    def getTool(self, name: str) -> callable:
        """
        根据名称获取一个工具的执行函数。
        """
        return self.tools.get(name, {}).get("func")

    def getAvailableTools(self) -> str:
        """
        获取所有可用工具的格式化描述字符串。
        """
        return "\n".join([
            f"- {name}: {info['description']}"
            for name, info in self.tools.items()
        ])


# --- 工具初始化与使用示例 ---


# ReAct 提示词模板
REACT_PROMPT_TEMPLATE = """
请注意，你是一个有能力调用外部工具的智能助手。

可用工具如下:
{tools}

请严格按照以下格式进行回应:

1. 你必须仅输出一个合法的 JSON，对象结构如下（不要添加多余解释或前后缀）：
{{
  "thought": "你的思考过程，用于分析问题、拆解任务和规划下一步行动。",
  "action": {{
    "type": "tool",
    "tool_name": "工具名称，例如 Search",
    "tool_input": "传给工具的输入字符串"
  }}
}}

2. 当你已经得到最终答案时，请使用以下结构：
{{
  "thought": "你的思考过程，用于说明你为何已经得到最终答案。",
  "action": {{
    "type": "finish",
    "final_answer": "最终给用户的答案"
  }}
}}
现在，请开始解决以下问题:
Question: {question}
History: {history}
"""


class ReActAgent:
    def __init__(self, llm_client: HelloAgentsLLM, tool_executor: ToolExecutor, max_step: int = 5):
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.max_step = max_step
        self.history: List[str] = []
    def run(self, question: str) :
        """
        run the ReActAgent to answer the question.
        :param question:
        :return:
        """
        self.history=[]
        current_step = 0

        while current_step < self.max_step:
            current_step += 1
            print(f"第 {current_step} 步")

            tool_description = self.tool_executor.getAvailableTools()
            history_str = "\n".join(self.history)
            prompt = REACT_PROMPT_TEMPLATE.format(
                tools=tool_description,
                question=question,
                history=history_str,
            )

            messages = [{"role":"user","content":prompt}]
            response_text = self.llm_client.think(messages=messages)
            if not response_text:
                print("错误:LLM未能返回有效响应")
                break
                return None
            thought, action = self._parse_output(response_text)
            if thought:
                print(f"思考: {thought}")

            if not action:
                print("警告:未能解析出有效的Action,流程终止.")
                break
                return None

            if action.startswith("Finish"):
                final_answer = re.match(r"Finish\[(.*)]",action).group(1)
                print(f"最终答案: {final_answer}")
                return final_answer
            tool_name, tool_input = action.get("tool_name"), action.get("tool_input")

            if not tool_name or not tool_input:
                continue
            print(f"🎬 行动: {tool_name}[{tool_input}]")
            tool_function = self.tool_executor.getTool(tool_name)

            if not tool_function:
                observation = f"错误:未找到名为: {tool_name} 的工具"
            else:
                observation = tool_function(tool_input)
                print(f"👀 观察: {observation}")

                # 将本轮的Action和Observation添加到历史记录中
                self.history.append(f"Action: {action}")
                self.history.append(f"Observation: {observation}")

                # 循环结束
            print("已达到最大步数，流程终止。")
            return None
        return None

    def _parse_output(self, text: str):

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines=cleaned.splitlines()
            if len(lines) > 2 and lines[0].startswith("```"):
                cleaned = "\n".join(lines[1:]).strip()
        try:
            data = json.loads(cleaned)
        except Exception:
            return None, None
        thought = data.get("thought")
        action = data.get("action")
        return thought, action


if __name__ == '__main__':
    tool_executor = ToolExecutor()
    search_description = "一个网页搜索引擎。当你需要回答关于时事、事实以及在你的知识库中找不到的信息时，应使用此工具。"
    tool_executor.registerTool("Search", search_description,search)

    agent = ReActAgent(llm_client=HelloAgentsLLM(), tool_executor=tool_executor)
    agent.run(question="华为最新手机型号以及主要卖点")
