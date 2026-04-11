from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseSkill(ABC):
    name: str = "" # 技能名称
    description: str = "" # 技能描述，简要说明技能的功能和用途

    @abstractmethod
    # 定义技能输入的参数结构，返回一个字典，描述每个参数的名称、类型和说明，供调用方参考和使用
    def input_schema(self) -> dict[str, Any]:
        raise NotImplementedError

    # 定义技能的核心逻辑，接受参数并执行相应的操作，返回一个字典作为结果，供调用方使用
    @abstractmethod
    def run(self, **kwargs) -> dict[str, Any]:
        raise NotImplementedError
