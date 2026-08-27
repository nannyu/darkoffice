"""策略原型库。

职责：
1. 定义全局策略原型（共9个），替代旧 ACTION_RULES
2. 每个原型有明确的定位、资源消耗、风险/收益结构
3. 场景中的选项是原型的"场景实例"

向后兼容：保留 ACTION_RULES 别名指向 STRATEGY_PROTOTYPES。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StrategyPrototype:
    prototype_id: str
    title: str
    summary: str
    modifier: int                          # 骰子修正
    category: str                          # 对抗/防守/回避/社交/信息/灰色
    energy_cost: str                       # low/medium/high

    # 基础数值效果
    base_effects: dict[str, int] = field(default_factory=dict)

    # 对角色关系的基础影响（按 role_type 分类）
    relation_impact_by_role: dict[str, int] = field(default_factory=dict)

    # 特殊效果描述
    special: str = ""

    # 使用建议
    when_to_use: str = ""
    when_not_to_use: str = ""

    # 子模式定义（如 PROBE 的主动/被动）
    sub_modes: Optional[dict[str, dict]] = None


# ---------------------------------------------------------------------------
# 9 个策略原型
# ---------------------------------------------------------------------------

STRATEGY_PROTOTYPES: dict[str, StrategyPrototype] = {
    # ═══════════════════════════════════════════════
    # 1. ASSERT — 强硬推进
    # ═══════════════════════════════════════════════
    "ASSERT": StrategyPrototype(
        prototype_id="ASSERT",
        title="强硬推进",
        summary="公开表态，承担冲突，快速解决问题",
        modifier=2,
        category="对抗",
        energy_cost="high",
        base_effects={"en": -12, "kpi": +4, "risk": +3, "cor": 0},
        relation_impact_by_role={
            "施压者": -3,
            "同盟者": +5,
            "中立者": -2,
            "观察者": 0,
        },
        special="对'急躁'心情的角色，应激反应效果翻倍",
        when_to_use="deadline紧迫、需要快速决策、对方是同级或下属",
        when_not_to_use="对方权力远高于你、对方心情已经很差",
    ),

    # ═══════════════════════════════════════════════
    # 2. THREATEN — 要挟施压
    # ═══════════════════════════════════════════════
    "THREATEN": StrategyPrototype(
        prototype_id="THREATEN",
        title="要挟施压",
        summary="利用信息筹码反向施压，迫使对方让步",
        modifier=2,
        category="对抗",
        energy_cost="medium",
        base_effects={"en": -6, "kpi": +2, "risk": +15, "cor": +10},
        relation_impact_by_role={
            "施压者": -25,
            "同盟者": -10,
            "中立者": -10,
            "观察者": -10,
        },
        special="需要预先掌握对方把柄（通过PROBE/DOCUMENT获取）或上位者对下位者（权力差>30）。无把柄时不可选。",
        when_to_use="握有对方致命把柄、需要立即脱身、对方是软柿子",
        when_not_to_use="对方权力远高于你（会反击）、对方也有你的把柄（互相毁灭）",
    ),

    # ═══════════════════════════════════════════════
    # 3. DOCUMENT — 留痕取证
    # ═══════════════════════════════════════════════
    "DOCUMENT": StrategyPrototype(
        prototype_id="DOCUMENT",
        title="留痕取证",
        summary="留下书面/录音证据，降低后续背锅风险",
        modifier=1,
        category="防守",
        energy_cost="low",
        base_effects={"en": -5, "kpi": -1, "risk": -8, "cor": 0},
        relation_impact_by_role={
            "施压者": -5,
            "同盟者": +2,
            "中立者": 0,
            "观察者": +5,
        },
        special="生成'已留痕'状态（持续1回合，本场景相关责任惩罚减半）。对'观察者'连续使用触发'过度防御'标签。",
        when_to_use="口头承诺、高风险任务、推活场景",
        when_not_to_use="对方已经极度不信任你（会彻底激怒）",
    ),

    # ═══════════════════════════════════════════════
    # 4. EVADE — 回避拖延
    # ═══════════════════════════════════════════════
    "EVADE": StrategyPrototype(
        prototype_id="EVADE",
        title="回避拖延",
        summary="不正面回应，争取时间，但可能积累隐患",
        modifier=-1,
        category="回避",
        energy_cost="low",
        base_effects={"en": -2, "kpi": -3, "risk": +2, "cor": 0},
        relation_impact_by_role={
            "施压者": -3,
            "同盟者": -2,
            "中立者": 0,
            "观察者": -3,
        },
        special="连续3次EVADE触发'老油条'标签（HR事件权重×2）",
        when_to_use="信息不足、需要观察、状态危急",
        when_not_to_use="对方明确要求立即答复、已有'老油条'标签",
    ),

    # ═══════════════════════════════════════════════
    # 5. ALLY — 协助站队
    # ═══════════════════════════════════════════════
    "ALLY": StrategyPrototype(
        prototype_id="ALLY",
        title="协助站队",
        summary="公开支持某一方，建立同盟但树敌",
        modifier=1,
        category="社交",
        energy_cost="medium",
        base_effects={"en": -6, "kpi": +1, "risk": +5, "cor": +2},
        relation_impact_by_role={
            "被支持者": +15,
            "对立面": -15,
            "旁观者": -3,
        },
        special="站队正确=获得派系保护；站队错误=一起沉没",
        when_to_use="派系斗争场景、需要强力盟友",
        when_not_to_use="信息不足（不知道谁赢）、对方在试探你",
    ),

    # ═══════════════════════════════════════════════
    # 6. TRADE — 互惠交易
    # ═══════════════════════════════════════════════
    "TRADE": StrategyPrototype(
        prototype_id="TRADE",
        title="互惠交易",
        summary="承诺交换利益，建立双向约束",
        modifier=1,
        category="社交",
        energy_cost="medium",
        base_effects={"en": -4, "kpi": 0, "risk": +3, "cor": +2},
        relation_impact_by_role={
            "交易对象": +8,
            "旁观者": 0,
        },
        special="生成'债务'关系（你欠对方/对方欠你）。债务未还会在未来触发追讨事件。累积3笔未还触发'债奴'标签。",
        when_to_use="需要长期合作、双方各取所需",
        when_not_to_use="对方信誉差（债务不会还）、短期一次性场景",
    ),

    # ═══════════════════════════════════════════════
    # 7. CHARM — 示好拉拢
    # ═══════════════════════════════════════════════
    "CHARM": StrategyPrototype(
        prototype_id="CHARM",
        title="示好拉拢",
        summary="讨好、送礼、表忠心，修复关系",
        modifier=0,
        category="社交",
        energy_cost="medium",
        base_effects={"en": -5, "kpi": 0, "risk": 0, "cor": +3},
        relation_impact_by_role={
            "目标角色": +15,
            "旁观者": -2,
        },
        special="对'贪婪'角色效果×1.5。对'愤怒'心情的角色效果减半（被认为虚伪）。对同一人连续3次触发'马屁精'标签。",
        when_to_use="关系破裂需要修复、争取关键支持",
        when_not_to_use="对方正处于愤怒状态",
    ),

    # ═══════════════════════════════════════════════
    # 8. PROBE — 试探情报
    # ═══════════════════════════════════════════════
    "PROBE": StrategyPrototype(
        prototype_id="PROBE",
        title="试探情报",
        summary="套话、观察、获取隐藏信息",
        modifier=0,
        category="信息",
        energy_cost="medium",
        base_effects={"en": -5, "kpi": 0, "risk": +1, "cor": 0},
        relation_impact_by_role={
            "被试探者": -3,
            "旁观者": 0,
        },
        special="多角色场景可探多个目标（1人70%，2人50%，3人30%）。对'老好人'成功率×1.5，对'多疑'角色×0.5。",
        when_to_use="新角色首次出现、信息不足、需要了解对方底牌",
        when_not_to_use="对方已经警觉、时间紧迫",
        sub_modes={
            "active": {
                "label": "主动套话",
                "modifier": 0,
                "en_cost": -5,
                "relation_impact": -3,
                "success_rate": 0.50,
                "intel_depth": "deep",
            },
            "passive": {
                "label": "被动观察",
                "modifier": +1,
                "en_cost": -2,
                "relation_impact": 0,
                "success_rate": 0.80,
                "intel_depth": "surface",
            },
        },
    ),

    # ═══════════════════════════════════════════════
    # 9. DEFLECT — 转移责任
    # ═══════════════════════════════════════════════
    "DEFLECT": StrategyPrototype(
        prototype_id="DEFLECT",
        title="转移责任",
        summary="把责任推给别人或别处，短期脱身",
        modifier=1,
        category="灰色",
        energy_cost="medium",
        base_effects={"en": -4, "kpi": 0, "risk": +8, "cor": +6},
        relation_impact_by_role={
            "被甩锅者": -20,
            "旁观者": -5,
            "施压者": +3,
        },
        special="对'老好人'角色效果翻倍（他们不容易反击）。连续3次触发'甩锅王'标签（没人愿意合作）。",
        when_to_use="高压场景、需要立即脱身、对方是软柿子",
        when_not_to_use="被甩锅者权力比你高、已有'甩锅王'标签",
    ),

    # ═══════════════════════════════════════════════
    # 10. RECOVER — 休整恢复
    # ═══════════════════════════════════════════════
    "RECOVER": StrategyPrototype(
        prototype_id="RECOVER",
        title="休整恢复",
        summary="停止对抗，恢复精力体力，减少压力",
        modifier=0,
        category="回避",
        energy_cost="low",
        base_effects={"en": +20, "st": +12, "kpi": -2, "risk": 0, "cor": 0},
        relation_impact_by_role={
            "施压者": -3,
            "同盟者": 0,
            "中立者": 0,
            "观察者": -2,
        },
        special="连续使用触发'消极怠工'标签（绩效事件权重降低）。",
        when_to_use="状态危急、需要恢复、非高压场景",
        when_not_to_use="Boss战、紧急 deadline 场景",
    ),
}


# ---------------------------------------------------------------------------
# 向后兼容：保留旧 ACTION_RULES 别名（值为 dict，不是 dataclass）
# ---------------------------------------------------------------------------
ACTION_RULES: dict[str, dict] = {
    pid: {
        "title": p.title,
        "summary": p.summary,
        "modifier": p.modifier,
        "category": p.category,
    }
    for pid, p in STRATEGY_PROTOTYPES.items()
}
ACTION_MODIFIERS: dict[str, int] = {
    pid: int(p.modifier) for pid, p in STRATEGY_PROTOTYPES.items()
}
ACTION_DISPLAY: dict[str, dict[str, str]] = {
    pid: {"title": p.title, "summary": p.summary}
    for pid, p in STRATEGY_PROTOTYPES.items()
}


# ---------------------------------------------------------------------------
# 标签系统
# ---------------------------------------------------------------------------
TAG_SYSTEM = {
    "刺头": {"trigger": "ASSERT对抗上司×3", "effect": "上司敌意+，同级尊重+"},
    "过度防御": {"trigger": "DOCUMENT×3", "effect": "被认为不信任团队，晋升事件权重-"},
    "老油条": {"trigger": "EVADE×3", "effect": "HR关注，合作事件权重-"},
    "变色龙": {"trigger": "ALLY站不同队×3", "effect": "所有人信任-"},
    "债奴": {"trigger": "未还TRADE债务×3", "effect": "追讨事件触发频率×2"},
    "马屁精": {"trigger": "对同一人CHARM×3", "effect": "同事-5，该人+20"},
    "威胁者": {"trigger": "THREATEN×2", "effect": "所有人防备，情报获取-30%"},
    "甩锅王": {"trigger": "DEFLECT×3", "effect": "没人愿意合作，推活免疫"},
}
