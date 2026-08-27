"""角色关系网：无向加权图。

职责：
1. 存储角色之间的关系值（-100~+100）
2. 提供查询、修改、衰减等操作
3. 支持传导计算（A→B→C 的影响传递）
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RelationGraph:
    """角色关系网：无向加权图，边权重 -100~+100。"""

    edges: dict[frozenset[str], int] = field(default_factory=dict)

    def _key(self, a: str, b: str) -> frozenset[str]:
        return frozenset({a, b})

    def get(self, a: str, b: str) -> int:
        """获取 A 和 B 之间的关系值。"""
        return self.edges.get(self._key(a, b), 0)

    def set(self, a: str, b: str, value: int):
        """设置 A 和 B 之间的关系值，自动截断到 [-100, 100]。"""
        self.edges[self._key(a, b)] = max(-100, min(100, value))

    def modify(self, a: str, b: str, delta: int):
        """增量修改关系值。"""
        self.set(a, b, self.get(a, b) + delta)

    def get_allies(self, character_id: str, threshold: int = 30) -> list[str]:
        """返回与指定角色关系值 >= threshold 的所有角色。"""
        result = []
        for edge_key, value in self.edges.items():
            if value >= threshold and character_id in edge_key:
                result.append([c for c in edge_key if c != character_id][0])
        return result

    def get_enemies(self, character_id: str, threshold: int = -30) -> list[str]:
        """返回与指定角色关系值 <= threshold 的所有角色。"""
        result = []
        for edge_key, value in self.edges.items():
            if value <= threshold and character_id in edge_key:
                result.append([c for c in edge_key if c != character_id][0])
        return result

    def get_connected(self, character_id: str) -> list[str]:
        """返回与指定角色有关系的所有角色（无论正负）。"""
        result = []
        for edge_key in self.edges:
            if character_id in edge_key:
                result.append([c for c in edge_key if c != character_id][0])
        return result

    def to_dict(self) -> dict:
        """序列化为可JSON化的字典。"""
        return {
            f"{sorted(list(k))[0]}::{sorted(list(k))[1]}": v
            for k, v in self.edges.items()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RelationGraph":
        """从字典反序列化。"""
        edges = {}
        for key, value in data.items():
            a, b = key.split("::")
            edges[frozenset({a, b})] = value
        return cls(edges=edges)


# ---------------------------------------------------------------------------
# 初始派系关系（基于角色人设的预设关系）
# ---------------------------------------------------------------------------
INITIAL_FACTION_RELATIONS: dict[str, dict[str, int]] = {
    # 陈派 vs 李派：公开对立
    "陈派": {"李派": -60},
    "李派": {"陈派": -60},
    # 甲方公司：与内部派系若即若离
    "甲方公司": {"陈派": -10, "李派": -10},
    # 公司管理层：表面上和各方都保持关系
    "公司管理层": {"陈派": 10, "李派": 10, "财务系": 15},
    # 财务系：中立但偏向管理层
    "财务系": {"公司管理层": 15, "陈派": 0, "李派": 0},
    # 无派系：无预设关系
}


def build_initial_relation_graph() -> RelationGraph:
    """根据角色人设构建初始关系图。

    关系值来源：
    1. 同派系角色之间：+20（天然同盟）
    2. 对立派系角色之间：取派系关系值
    3. 跨派系但非对立：0
    4. 特殊预设（如小林骑墙：与陈总监+5，与其他人均为0）
    """
    from runtime.content import CHARACTERS

    graph = RelationGraph()
    char_map = {c.character_id: c for c in CHARACTERS}

    # 两两初始化关系
    for i, c1 in enumerate(CHARACTERS):
        for c2 in CHARACTERS[i + 1 :]:
            # 同派系
            if c1.faction and c1.faction == c2.faction and c1.faction != "无派系":
                graph.set(c1.character_id, c2.character_id, 20)
                continue

            # 对立派系
            if c1.faction and c2.faction:
                faction_rel = INITIAL_FACTION_RELATIONS.get(c1.faction, {}).get(c2.faction)
                if faction_rel is not None:
                    graph.set(c1.character_id, c2.character_id, faction_rel)
                    continue

            # 小林特殊处理：骑墙，与陈总监微正（巴结），与派系总监微负（竞争）
            if c1.character_id == "CHR_02" or c2.character_id == "CHR_02":
                other = c2 if c1.character_id == "CHR_02" else c1
                if other.character_id == "CHR_01":
                    graph.set(c1.character_id, c2.character_id, 10)
                elif other.character_id == "CHR_06":
                    graph.set(c1.character_id, c2.character_id, -5)
                else:
                    graph.set(c1.character_id, c2.character_id, 0)
                continue

            # 默认
            graph.set(c1.character_id, c2.character_id, 0)

    return graph
