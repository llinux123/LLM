from typing import List,Dict,Any, Optional

from sympy.strategies.core import switch


class Switcher:
    @staticmethod
    def switch_execution(record: Dict[str, Any]):
        return f"--- 上一轮尝试 (代码) ---\n{record['content']}"

    @staticmethod
    def switch_reflection(record: Dict[str, Any]):
        return f"--- 评审员反馈 ---\n{record['content']}"

    def switch(self, value,record: Dict[str, Any]):
        return getattr(self, f"switch_{value}")(record)

class Memory:
    def __init__(self):
        """
        初始化一个空列表来存储所有记忆
        """
        self.records:List[Dict[str, Any]] = []
        self.switcher = Switcher()
    def add_record(self, record: Dict[str, Any]) -> None:
        if  not record["record_type"]:
            record["record_type"] = "default"
        if not record["content"]:
            record["content"] = ""
        record_type = record["record_type"]
        self.records.append(record)

        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")


    def get_trajectory(self) -> str:
        trajectory_parts = []
        for record in self.records:
            trajectory_parts.append(self.switcher.switch(record["record_type"], record))
        return "\n\n".join(trajectory_parts)
    def get_last_execution(self) -> Optional[str]:
        for record in reversed(self.records):
            if record["record_type"] == "execution":
                return record["content"]
        return None


if __name__ == "__main__":
    memory = Memory()
    memory.add_record({"record_type":"execution", "content":"bilibili"})

    print(memory.get_trajectory())
    print(memory.get_last_execution())