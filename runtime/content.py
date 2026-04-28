from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from runtime.rules import ACTION_DISPLAY, ACTION_MODIFIERS


@dataclass(frozen=True)
class Character:
    character_id: str
    name: str
    base_weight: int
    # 扩展可选字段（自定义卡牌使用，内置卡牌保持默认值）
    role_type: Optional[str] = None
    faction: Optional[str] = None
    tags: Optional[list[str]] = None
    passive_effect: Optional[str] = None
    speech_style: Optional[str] = None


@dataclass(frozen=True)
class Event:
    event_id: str
    character_id: str
    name: str
    base_effect: dict[str, int]
    # 扩展可选字段（自定义卡牌使用，内置卡牌保持默认值）
    event_category: Optional[str] = None
    pressure_level: Optional[str] = None
    tags: Optional[list[str]] = None
    flavor_text: Optional[str] = None
    possible_followups: Optional[list[str]] = None
    dice_dc: Optional[int] = None


CHARACTERS: list[Character] = [
    Character("CHR_01", "PUA上司", 20),
    Character("CHR_02", "推活同事", 18),
    Character("CHR_03", "甲方金主", 15),
    Character("CHR_04", "HR笑面虎", 10),
    Character("CHR_05", "财务关键人", 12),
    Character("CHR_06", "派系总监", 8),
]

CHARACTER_NAME_MAP: dict[str, str] = {c.character_id: c.name for c in CHARACTERS}

# 先接入一组稳定的基础事件，用于跑通角色差异与链路验证。
EVENTS: list[Event] = [
    Event("EVT_01", "CHR_01", "今晚先把新版方案出掉", {"hp": 0, "en": -18, "st": -12, "kpi": 3, "risk": 2, "cor": 0}),
    Event("EVT_02", "CHR_01", "这个阶段大家都不容易", {"hp": 0, "en": -10, "st": -4, "kpi": 0, "risk": 1, "cor": 0}),
    Event("EVT_03", "CHR_01", "上次那个问题是谁负责", {"hp": 0, "en": -12, "st": -5, "kpi": -8, "risk": 6, "cor": 0}),
    Event("EVT_05", "CHR_02", "你顺手帮我处理一下", {"hp": 0, "en": -7, "st": -4, "kpi": 1, "risk": 1, "cor": 0}),
    Event("EVT_06", "CHR_02", "这不是大家一起的吗", {"hp": 0, "en": -8, "st": -3, "kpi": -3, "risk": 4, "cor": 0}),
    Event("EVT_07", "CHR_02", "先做了再说", {"hp": 0, "en": -7, "st": -2, "kpi": 0, "risk": 3, "cor": 0}),
    Event("EVT_08", "CHR_03", "需求先做了再确认", {"hp": 0, "en": -14, "st": -9, "kpi": 2, "risk": 7, "cor": 0}),
    Event("EVT_09", "CHR_03", "明天老板要看", {"hp": -1, "en": -18, "st": -14, "kpi": 4, "risk": 4, "cor": 0}),
    Event("EVT_10", "CHR_03", "之前不是说好的吗", {"hp": 0, "en": -9, "st": -3, "kpi": -5, "risk": 4, "cor": 0}),
    Event("EVT_11", "CHR_04", "来聊聊最近的状态", {"hp": 0, "en": -7, "st": -2, "kpi": -3, "risk": 2, "cor": 0}),
    Event("EVT_12", "CHR_04", "绩效沟通安排一下", {"hp": 0, "en": -11, "st": -3, "kpi": -8, "risk": 3, "cor": 0}),
    Event("EVT_16", "CHR_04", "你最近态度有点问题", {"hp": 0, "en": -9, "st": -3, "kpi": -5, "risk": 2, "cor": 2}),
    Event("EVT_17", "CHR_05", "先倒签一下", {"hp": -1, "en": -6, "st": -3, "kpi": 2, "risk": 15, "cor": 8}),
    Event("EVT_18", "CHR_05", "报销材料再补一下", {"hp": 0, "en": -5, "st": -2, "kpi": 0, "risk": 4, "cor": 1}),
    Event("EVT_19", "CHR_05", "审计要来了", {"hp": -3, "en": -12, "st": -5, "kpi": -6, "risk": 10, "cor": 2}),
    Event("EVT_20", "CHR_06", "你支持哪个方案", {"hp": 0, "en": -9, "st": -2, "kpi": 0, "risk": 8, "cor": 5}),
    Event("EVT_21", "CHR_06", "有空聊聊", {"hp": 0, "en": -6, "st": -1, "kpi": 0, "risk": 3, "cor": 3}),
    Event("EVT_22", "CHR_06", "你在陈总监那边怎么汇报", {"hp": 0, "en": -11, "st": -2, "kpi": -1, "risk": 7, "cor": 4}),
]

EVENTS_BY_CHARACTER: dict[str, list[Event]] = {}
for event in EVENTS:
    EVENTS_BY_CHARACTER.setdefault(event.character_id, []).append(event)
