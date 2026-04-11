from __future__ import annotations

from backend.skills.base import BaseSkill

#要添加新的技能，只需：1 创建新文件 backend/skills/your_skill.py;2 继承 BaseSkill;3 实现 input_schema() 和 run();4 在 dependencies.py 中注册
class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> BaseSkill:
        if name not in self._skills:
            raise KeyError(f"Skill not found: {name}")
        return self._skills[name]

    def list_names(self) -> list[str]:
        return list(self._skills.keys())


'''

📄 DocSearchSkill - 文档检索
输入参数：query(搜索词), file_ids(文件ID列表), top_k(返回数量)
功能：调用 RAG 服务检索上传的文档
输出：{"summary": "命中X个文档片段...", "results": [...]}

🌐 WebSearchSkill - 网页搜索
输入参数：query(搜索词), max_results(返回数量)
功能：通过 DuckDuckGo API 获取网页搜索结果
输出：{"summary": "已获取X条网页结果...", "results": [...]}

📝 SummarizeSkill - 内容总结
输入参数：query(用户问题), content(待总结内容)
功能：调用 LLM 服务将工具结果压缩成简短摘要
输出：{"summary": "3-5句总结...", "results": []}

'''