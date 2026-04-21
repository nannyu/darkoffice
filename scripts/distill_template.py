#!/usr/bin/env python3
"""卡牌蒸馏器的提示词模板与 card_data schema 校验。

本模块不执行蒸馏（蒸馏由 Agent 完成），仅提供：
1. 四种卡牌类型的蒸馏提示词模板（融入女娲深度分析框架）
2. card_data 的 JSON Schema 校验
3. 蒸馏结果写入 CLI 的辅助函数
4. 素材预分析框架（从素材中提取人物画像、事件链、权力结构）
"""

from __future__ import annotations

import json
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.materials import add_custom_card


# ---------------------------------------------------------------------------
# 素材预分析框架（女娲式深度挖掘）
# ---------------------------------------------------------------------------

MATERIAL_ANALYSIS_PROMPT = """你是一个职场博弈分析专家。请对以下真实案件素材进行深度结构化分析，提取可用于卡牌游戏设计的核心要素。

## 分析框架（女娲式六维挖掘）

### 维度1: 权力结构分析
- 涉案人物之间的汇报关系、利益同盟、对立关系
- 每个人的权力来源（职位、资源、信息、人脉）
- 关键决策点：谁在什么时刻做出了什么选择

### 维度2: 人物画像提取
对每个人物提取：
- **角色定位**: 在权力结构中的位置
- **利益动机**: 核心诉求是什么（钱？权？安全？面子？）
- **惯用手法**: 常用的施压/操控/规避手段
- **性格特征**: 果断/犹豫、强势/隐忍、精明/鲁莽
- **语言风格**: 命令式/商量式、直接/迂回、书面/口头
- **脆弱点**: 怕什么、什么情况下会退让

### 维度3: 事件链还原
- 导火索：什么小事引发了连锁反应
- 升级路径：矛盾如何一步步激化
- 关键转折：哪个选择让事态不可逆转
- 结局类型：主动坦白/被动发现/同归于尽/不了了之

### 维度4: 制度漏洞识别
- 哪些规则被绕过？怎么绕过的？
- 监督机制为什么失效？
- 制度设计上的哪些缺陷创造了作恶空间？

### 维度5: 心理博弈拆解
- 各方的心理账户（怎么算账的）
- 信息不对称如何被利用
- 沉没成本陷阱、从众压力、权威服从

### 维度6: 可游戏化元素
- 哪些场景适合做成事件卡？
- 哪些人物适合做成角色卡？
- 哪些"当时觉得没事后来爆炸"的隐患？
- 哪些选择有典型的"两害相权"困境？

## 素材内容
{material_content}

## 输出要求
请用中文输出结构化分析，每个维度至少提取3个要点。重点标注：
- ⭐ 最适合做角色卡的人物（1-2个）
- 🔥 最适合做事件卡的场景（2-3个）
- 💣 最适合做隐患卡的"定时炸弹"（1-2个）
- 🎭 最适合做剧情线的故事弧（1条）
"""


# ---------------------------------------------------------------------------
# 蒸馏提示词模板（女娲式深度分析版）
# ---------------------------------------------------------------------------

CHARACTER_DISTILL_PROMPT = """你是一个职场卡牌游戏的角色设计师。请根据以下经过深度分析的案件素材，蒸馏生成一张**立体、有层次、有内在矛盾**的角色卡。

## 设计原则（女娲式思维框架）

一个优秀的角色卡不是标签堆砌，而是一套可运行的"认知操作系统"：
- 他用什么**心智模型**看世界？（权力=零和？关系=投资？规则=障碍？）
- 他用什么**决策启发式**做判断？（"先试探再施压"？"留痕自保"？"找替罪羊"？）
- 他怎么**表达**？（DNA：句式、词汇、节奏、幽默/讽刺方式）
- 他**绝对不会**做什么？（反模式：什么底线他不碰？）
- 什么是这个角色的**内在张力**？（价值观冲突：既要...又要...）

**关键区分**：捕捉的是 HOW they think，不是 WHAT they did。

## 素材分析
{material_analysis}

## 聚焦人物
{target_person}

## 输出要求
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "name": "角色名称（2-4字，体现角色特征，如'笑面虎总监'）",
  "role_type": "角色类型（直属上司/同级同事/甲方客户/HR/财务/高管/其他）",
  "faction": "派系（管理层/职能部门/外部/无）",
  "base_weight": 10,
  "tags": ["标签1", "标签2", "标签3"],
  "persona_summary": "角色人设概述（3-4句话，体现其压迫方式、利益动机、内在矛盾）",
  "passive_effect": "被动效果描述（如何对玩家产生额外压力，要具体机制不要笼统描述）",
  "common_pressure_types": ["压力类型1", "压力类型2"],
  "speech_style": "代表性台词（4-6句，体现角色说话风格，每句要有差异：命令式/暗示式/道德绑架式/甩锅式）",
  "mind_model": "此人的核心心智模型（一句话：他怎么看这个世界？如'权力是零和游戏，别人的损失就是我的收益'）",
  "decision_heuristics": ["决策规则1：如果X，则Y", "决策规则2：如果X，则Y"],
  "inner_tension": "内在矛盾（如：既想树立清廉形象，又无法拒绝利益输送）",
  "anti_pattern": "此角色绝对不会做的事（如：从不留下书面证据、从不亲自出面施压）",
  "vulnerability": "脆弱点（什么情况下这个角色会崩溃或退让？）"
}}
```

## 设计约束
- base_weight 范围 5-25，越高越常出现
- 角色必须"坏得合理"：有利益动机、惯用手法、稳定口吻
- **必须有内在矛盾**：没有矛盾的角色是纸片人，不是人
- passive_effect 不能过于强大，应与现有角色平衡
- speech_style 的台词必须体现权力位置和说话风格，禁止脏话
- 压迫感来自机制（模糊边界、道德绑架），不来自辱骂
- **禁止**：只罗列标签没有灵魂、没有内在矛盾、台词像AI生成
"""

EVENT_DISTILL_PROMPT = """你是一个职场卡牌游戏的事件设计师。请根据以下经过深度分析的案件素材，蒸馏生成一张**有代价、有张力、有后续连锁**的事件卡。

## 设计原则（女娲式事件设计）

一个优秀的事件卡不是"发生了什么事"，而是"你在一个**结构性困境**中被迫做选择"：
- **结构性**：这个困境不是偶然，是制度/权力/信息不对称的必然产物
- **代价性**：每个选择都有代价，没有无代价的最优解
- **延迟性**：今天的捷径，是明天的坑（为隐患卡预留钩子）
- **角色性**：这个事件只有特定角色能发起，换个人就不成立

## 素材分析
{material_analysis}

## 关联角色
{character_info}

## 输出要求
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "name": "事件名称（一句话概括，如'先倒签一下'）",
  "source_character": "{character_id}",
  "event_category": "事件分类（工作任务/甩锅/情绪压榨/政治站队/灰色合规/甲方需求/绩效制度/恢复机会）",
  "pressure_level": "压力等级（NONE/LOW/MEDIUM/HIGH）",
  "tags": ["标签1", "标签2"],
  "base_effect": {{
    "hp": 0,
    "en": -10,
    "st": -5,
    "kpi": 0,
    "risk": 3,
    "cor": 0
  }},
  "flavor_text": "事件描述（5-8行，用第二人称写，体现：1)具体场景 2)对方的潜台词 3)你的真实处境 4)选择的艰难）",
  "possible_followups": ["可能后续1：如果你选择A，3回合后可能触发...", "可能后续2：如果你选择B，角色态度会..."],
  "dice_dc": 11,
  "structural_trap": "结构性陷阱说明（为什么这个困境不可避免？制度/权力/信息哪里出了问题？）",
  "hidden_cost": "隐藏代价（表面看选择X最划算，但实际代价是什么？）",
  "hazard_hook": "隐患钩子（这个事件可能埋下什么定时炸弹？为隐患卡预留）"
}}
```

## 设计约束
- base_effect 数值范围：
  - hp: -5 ~ 0（极少数直接伤害）
  - en: -20 ~ 0（主要消耗资源）
  - st: -15 ~ 0
  - kpi: -10 ~ +5（正值是奖励）
  - risk: 0 ~ +15（正值是惩罚）
  - cor: 0 ~ +10（正值是惩罚）
- dice_dc 范围 6-15
- flavor_text 必须有现实感，不能写成数值面板说明
- **必须有结构性陷阱说明**：解释为什么这个困境不是偶然的
- **必须有隐藏代价**：表面最优解的实际代价
- **必须有隐患钩子**：为后续隐患卡预留连接点
- 事件必须有代价，不能有无代价的最优解
"""

HAZARD_DISTILL_PROMPT = """你是一个职场卡牌游戏的隐患卡设计师。请根据以下经过深度分析的案件素材，蒸馏生成一张**有倒计时张力、有连锁反应**的隐患卡。

## 设计原则（女娲式隐患设计）

隐患是"当时觉得没事，后来爆炸"的定时炸弹：
- **起源具体**：必须关联一个具体的事件卡（哪次选择埋下了隐患）
- **倒计时张力**：玩家知道炸弹存在但不知道何时爆炸，焦虑感
- **连锁反应**：爆炸时不只伤害数值，还可能触发新事件、改变角色态度
- **可干预**：玩家在倒计时期间有机会降低 severity 或提前拆除

## 素材分析
{material_analysis}

## 输出要求
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "name": "隐患名称（2-5字，如'倒签文件'）",
  "trigger_event": "触发此隐患的事件ID（如EVT_17或CUSTOM_EVT_XX）",
  "countdown": 3,
  "severity": 2,
  "origin_story": "隐患起源（1-2句话：当时发生了什么？为什么当时觉得没事？）",
  "explosion_scene": "爆炸场景描述（2-3句话：倒计时归零时发生了什么？谁发现了？怎么发现的？）",
  "chain_reaction": "连锁反应（爆炸后可能触发什么？新事件？角色态度变化？项目延期？）",
  "intervention_chance": "干预机会（玩家在倒计时期间可以做什么来降低损失？）"
}}
```

## 设计约束
- countdown 范围 2-6（回合数）
- severity 范围 1-3（1=轻微，2=中等，3=严重）
- 爆炸时基础效果：hp -2*severity, kpi -4*severity, risk +6*severity
- trigger_event 应关联一个已有的事件卡ID
- **必须有 origin_story**：解释这个隐患是怎么埋下的
- **必须有 explosion_scene**：描述爆炸时的具体场景，增加叙事感
- **必须有 chain_reaction**：爆炸不只是数值伤害，要有后续影响
- **必须有 intervention_chance**：给玩家留一线生机
"""

STORYLINE_DISTILL_PROMPT = """你是一个职场卡牌游戏的剧情设计师。请根据以下经过深度分析的案件素材，蒸馏生成一条**有起承转合、有角色弧光**的定制剧情线。

## 设计原则（女娲式剧情设计）

一条优秀的剧情线不是事件的串联，而是**权力关系的演变史**：
- **起**：权力平衡如何建立（谁在上位？为什么？）
- **承**：矛盾如何积累（一次次小事件如何侵蚀信任？）
- **转**：临界点是什么（哪个选择让局势不可逆转？）
- **合**：结局的必然性（为什么是这种结局？制度/人性/运气？）

每幕之间要有**叙事张力**：角色的权力位置在变化，玩家的处境在恶化或好转。

## 素材分析
{material_analysis}

## 可用角色
{available_characters}

## 输出要求
请严格按照以下 JSON 格式输出，不要输出任何其他内容：

```json
{{
  "title": "剧情线标题（有张力，如'签字风云'）",
  "description": "剧情线概述（3-4句话，讲清楚：核心冲突是什么？玩家陷入什么困境？最终走向什么结局？）",
  "theme": "核心主题（如'程序正义 vs 结果导向'、'个人良知 vs 组织压力'）",
  "power_arc": "权力弧光描述（3-4句话：剧情开始时谁掌握主动权？中间如何转移？结局时权力格局如何？）",
  "acts": [
    {{
      "act_index": 0,
      "title": "第一幕标题",
      "character_id": "角色ID",
      "event_ids": ["事件ID1"],
      "narrative_bridge": "叙事过渡（用第二人称写，3-4句话，描述场景转换和心境变化）",
      "completion_condition": "turn_resolved",
      "power_shift": "本幕权力变化（如：你被动接受 → 开始试探底线）"
    }},
    {{
      "act_index": 1,
      "title": "第二幕标题",
      "character_id": "角色ID",
      "event_ids": ["事件ID2"],
      "narrative_bridge": "...",
      "completion_condition": "turn_resolved",
      "power_shift": "本幕权力变化（如：对方施压升级 → 你被迫站队）"
    }},
    {{
      "act_index": 2,
      "title": "第三幕标题",
      "character_id": "角色ID",
      "event_ids": ["事件ID3"],
      "narrative_bridge": "...",
      "completion_condition": "turn_resolved",
      "power_shift": "本幕权力变化（如：真相暴露 → 各方重新洗牌）"
    }}
  ]
}}
```

## 设计约束
- 剧情线应有 3-5 幕
- 每幕关联一个角色和 1-2 个事件
- **必须有 power_arc**：描述整个剧情中权力格局的演变
- **每幕必须有 power_shift**：描述本幕中玩家/角色的权力位置变化
- narrative_bridge 是幕与幕之间的叙事过渡，要有情绪张力
- completion_condition 目前仅支持 "turn_resolved"
- 剧情线应有明确的起承转合，避免平铺直叙
- **必须有 theme**：明确的核心主题，让玩家知道这条剧情线在探讨什么
"""


# ---------------------------------------------------------------------------
# Schema 校验（扩展版，支持新字段）
# ---------------------------------------------------------------------------

CHARACTER_SCHEMA = {
    "type": "object",
    "required": ["name", "base_weight"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "role_type": {"type": "string"},
        "faction": {"type": "string"},
        "base_weight": {"type": "integer", "minimum": 1, "maximum": 50},
        "tags": {"type": "array", "items": {"type": "string"}},
        "persona_summary": {"type": "string"},
        "passive_effect": {"type": "string"},
        "common_pressure_types": {"type": "array", "items": {"type": "string"}},
        "speech_style": {"type": "string"},
        # 女娲式扩展字段（可选）
        "mind_model": {"type": "string"},
        "decision_heuristics": {"type": "array", "items": {"type": "string"}},
        "inner_tension": {"type": "string"},
        "anti_pattern": {"type": "string"},
        "vulnerability": {"type": "string"},
    },
}

EVENT_SCHEMA = {
    "type": "object",
    "required": ["name", "source_character", "base_effect"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "source_character": {"type": "string"},
        "event_category": {"type": "string"},
        "pressure_level": {"type": "string", "enum": ["NONE", "LOW", "MEDIUM", "HIGH"]},
        "tags": {"type": "array", "items": {"type": "string"}},
        "base_effect": {
            "type": "object",
            "required": ["hp", "en", "st", "kpi", "risk", "cor"],
            "properties": {
                "hp": {"type": "integer", "minimum": -10, "maximum": 5},
                "en": {"type": "integer", "minimum": -25, "maximum": 5},
                "st": {"type": "integer", "minimum": -20, "maximum": 5},
                "kpi": {"type": "integer", "minimum": -15, "maximum": 10},
                "risk": {"type": "integer", "minimum": -5, "maximum": 20},
                "cor": {"type": "integer", "minimum": -5, "maximum": 15},
            },
        },
        "flavor_text": {"type": "string"},
        "possible_followups": {"type": "array", "items": {"type": "string"}},
        "dice_dc": {"type": "integer", "minimum": 5, "maximum": 18},
        # 女娲式扩展字段（可选）
        "structural_trap": {"type": "string"},
        "hidden_cost": {"type": "string"},
        "hazard_hook": {"type": "string"},
    },
}

HAZARD_SCHEMA = {
    "type": "object",
    "required": ["name", "trigger_event", "countdown", "severity"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "trigger_event": {"type": "string"},
        "countdown": {"type": "integer", "minimum": 1, "maximum": 8},
        "severity": {"type": "integer", "minimum": 1, "maximum": 3},
        # 女娲式扩展字段（可选）
        "origin_story": {"type": "string"},
        "explosion_scene": {"type": "string"},
        "chain_reaction": {"type": "string"},
        "intervention_chance": {"type": "string"},
    },
}

STORYLINE_SCHEMA = {
    "type": "object",
    "required": ["title", "description", "acts"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "theme": {"type": "string"},
        "power_arc": {"type": "string"},
        "acts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["act_index", "title", "character_id", "event_ids", "narrative_bridge", "completion_condition"],
                "properties": {
                    "act_index": {"type": "integer", "minimum": 0},
                    "title": {"type": "string"},
                    "character_id": {"type": "string"},
                    "event_ids": {"type": "array", "items": {"type": "string"}},
                    "narrative_bridge": {"type": "string"},
                    "completion_condition": {"type": "string"},
                    "power_shift": {"type": "string"},
                },
            },
        },
    },
}


def _validate_schema(data: dict, schema: dict, path: str = "") -> list[str]:
    """简化的 JSON Schema 校验，返回错误列表。"""
    errors: list[str] = []

    if schema.get("type") == "object":
        if not isinstance(data, dict):
            errors.append(f"{path}: expected object, got {type(data).__name__}")
            return errors

        for field in schema.get("required", []):
            if field not in data:
                errors.append(f"{path}.{field}: required field missing")

        props = schema.get("properties", {})
        for key, prop_schema in props.items():
            if key in data:
                sub_path = f"{path}.{key}" if path else key
                val = data[key]

                # Type check
                expected = prop_schema.get("type")
                if expected == "string" and not isinstance(val, str):
                    errors.append(f"{sub_path}: expected string, got {type(val).__name__}")
                elif expected == "integer" and not isinstance(val, int):
                    errors.append(f"{sub_path}: expected integer, got {type(val).__name__}")
                elif expected == "array" and not isinstance(val, list):
                    errors.append(f"{sub_path}: expected array, got {type(val).__name__}")

                # Range check
                if isinstance(val, (int, float)):
                    if "minimum" in prop_schema and val < prop_schema["minimum"]:
                        errors.append(f"{sub_path}: value {val} below minimum {prop_schema['minimum']}")
                    if "maximum" in prop_schema and val > prop_schema["maximum"]:
                        errors.append(f"{sub_path}: value {val} above maximum {prop_schema['maximum']}")

                # String length
                if isinstance(val, str) and "minLength" in prop_schema:
                    if len(val) < prop_schema["minLength"]:
                        errors.append(f"{sub_path}: string too short (min {prop_schema['minLength']})")

                # Enum check
                if "enum" in prop_schema and val not in prop_schema["enum"]:
                    errors.append(f"{sub_path}: value '{val}' not in {prop_schema['enum']}")

                # Nested object
                if expected == "object" and isinstance(val, dict):
                    errors.extend(_validate_schema(val, prop_schema, sub_path))

                # Array items
                if expected == "array" and isinstance(val, list):
                    items_schema = prop_schema.get("items", {})
                    for i, item in enumerate(val):
                        if items_schema.get("type") == "string" and not isinstance(item, str):
                            errors.append(f"{sub_path}[{i}]: expected string")
                        elif items_schema.get("type") == "integer" and not isinstance(item, int):
                            errors.append(f"{sub_path}[{i}]: expected integer")
                        elif items_schema.get("type") == "object" and isinstance(item, dict):
                            errors.extend(_validate_schema(item, items_schema, f"{sub_path}[{i}]"))

    return errors


def validate_card_data(card_type: str, card_data: dict) -> list[str]:
    """校验自定义卡牌数据是否符合 schema。

    Args:
        card_type: CHARACTER / EVENT / HAZARD / STORYLINE
        card_data: 卡牌数据字典

    Returns:
        错误列表，空列表表示校验通过
    """
    schema_map = {
        "CHARACTER": CHARACTER_SCHEMA,
        "EVENT": EVENT_SCHEMA,
        "HAZARD": HAZARD_SCHEMA,
        "STORYLINE": STORYLINE_SCHEMA,
    }
    schema = schema_map.get(card_type)
    if not schema:
        return [f"unknown card_type: {card_type}"]
    return _validate_schema(card_data, schema)


def write_distilled_card(
    card_id: str,
    card_type: str,
    card_data: dict,
    source_material_id: int | None = None,
    is_active: int = 0,
    db_path: str | None = None,
) -> dict:
    """校验并写入蒸馏生成的自定义卡牌。

    Returns:
        {"ok": True, "card_id": ...} 或 {"ok": False, "errors": [...]}
    """
    errors = validate_card_data(card_type, card_data)
    if errors:
        return {"ok": False, "errors": errors}

    card_name = card_data.get("name", card_id)
    cid = add_custom_card(
        card_id=card_id,
        card_type=card_type,
        card_name=card_name,
        card_data=card_data,
        source_material_id=source_material_id,
        is_active=is_active,
        db_path=db_path,
    )
    return {"ok": True, "card_id": cid}


def get_prompt(card_type: str, **kwargs) -> str:
    """获取指定卡牌类型的蒸馏提示词模板。

    Args:
        card_type: CHARACTER / EVENT / HAZARD / STORYLINE / ANALYSIS
        **kwargs: 模板变量

    Returns:
        填充后的提示词字符串
    """
    prompt_map = {
        "ANALYSIS": MATERIAL_ANALYSIS_PROMPT,
        "CHARACTER": CHARACTER_DISTILL_PROMPT,
        "EVENT": EVENT_DISTILL_PROMPT,
        "HAZARD": HAZARD_DISTILL_PROMPT,
        "STORYLINE": STORYLINE_DISTILL_PROMPT,
    }
    template = prompt_map.get(card_type)
    if not template:
        raise ValueError(f"unknown card_type for prompt: {card_type}")
    return template.format(**kwargs)


# ---------------------------------------------------------------------------
# CLI 入口（独立调用用）
# ---------------------------------------------------------------------------

def main() -> None:
    """独立入口：校验一个 JSON 文件中的 card_data。"""
    import argparse

    parser = argparse.ArgumentParser(description="Card data schema validator")
    parser.add_argument("--type", required=True, choices=["CHARACTER", "EVENT", "HAZARD", "STORYLINE"])
    parser.add_argument("--data", required=True, help="JSON file path or inline JSON string")
    args = parser.parse_args()

    path = Path(args.data)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = json.loads(args.data)

    errors = validate_card_data(args.type, data)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        sys.exit(1)
    else:
        print(json.dumps({"valid": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
