#!/usr/bin/env python3
"""智能蒸馏脚本：从素材库读取素材，使用女娲式深度分析框架生成卡牌。

用法：
    # 先对素材进行六维分析
    python scripts/distill_from_material.py analyze --material-id 1

    # 基于分析结果生成角色卡
    python scripts/distill_from_material.py character --material-id 1 --person "张主任"

    # 基于分析结果生成事件卡
    python scripts/distill_from_material.py event --material-id 1 --character-id CUSTOM_CHR_001

    # 基于分析结果生成隐患卡
    python scripts/distill_from_material.py hazard --material-id 1 --trigger-event CUSTOM_EVT_001

    # 基于分析结果生成剧情线
    python scripts/distill_from_material.py storyline --material-id 1

    # 一键全流程：分析 + 生成全部卡牌类型
    python scripts/distill_from_material.py full --material-id 1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.materials import get_material, list_custom_cards
from runtime.db import connect, init_db
from scripts.distill_template import (
    get_prompt,
    validate_card_data,
    write_distilled_card,
    MATERIAL_ANALYSIS_PROMPT,
)


def _next_custom_id(card_type: str, db_path: str | None = None) -> str:
    """生成下一个自定义卡牌 ID。"""
    prefix = {"CHARACTER": "CUSTOM_CHR", "EVENT": "CUSTOM_EVT", "HAZARD": "CUSTOM_HZD"}.get(card_type, "CUSTOM")
    conn = connect(db_path)
    try:
        init_db(conn)
        rows = conn.execute(
            "SELECT card_id FROM custom_cards WHERE card_type = ? AND card_id LIKE ?",
            (card_type, f"{prefix}_%"),
        ).fetchall()
        if not rows:
            return f"{prefix}_001"
        nums = []
        for r in rows:
            try:
                num = int(r["card_id"].split("_")[-1])
                nums.append(num)
            except ValueError:
                continue
        next_num = max(nums) + 1 if nums else 1
        return f"{prefix}_{next_num:03d}"
    finally:
        conn.close()


def cmd_analyze(args: argparse.Namespace) -> None:
    """输出素材分析提示词，供 Agent 使用。"""
    material = get_material(args.material_id, args.db_path)
    content = material.get("content", "")
    # 截断过长内容
    if len(content) > 8000:
        content = content[:8000] + "\n\n[内容已截断，原长度 {} 字符]".format(len(material.get("content", "")))

    prompt = get_prompt("ANALYSIS", material_content=content)
    print(prompt)


def cmd_character(args: argparse.Namespace) -> None:
    """输出生成角色卡的提示词。"""
    material = get_material(args.material_id, args.db_path)
    content = material.get("content", "")
    if len(content) > 6000:
        content = content[:6000] + "\n\n[内容已截断]"

    # 如果没有提供分析结果，先用素材内容本身
    analysis = args.analysis or content
    target = args.person or "素材中的主要人物"

    prompt = get_prompt(
        "CHARACTER",
        material_analysis=analysis,
        target_person=target,
    )
    print(prompt)


def cmd_event(args: argparse.Namespace) -> None:
    """输出生成事件卡的提示词。"""
    material = get_material(args.material_id, args.db_path)
    content = material.get("content", "")
    if len(content) > 6000:
        content = content[:6000] + "\n\n[内容已截断]"

    analysis = args.analysis or content
    char_id = args.character_id or "CHR_01"

    # 获取角色信息
    char_info = f"关联角色ID: {char_id}"
    if char_id.startswith("CUSTOM_"):
        try:
            from runtime.materials import get_custom_card
            card = get_custom_card(char_id, args.db_path)
            data = card.get("card_data", {})
            char_info = f"角色: {data.get('name', char_id)} | {data.get('persona_summary', '')}"
        except Exception:
            pass

    prompt = get_prompt(
        "EVENT",
        material_analysis=analysis,
        character_info=char_info,
        character_id=char_id,
    )
    print(prompt)


def cmd_hazard(args: argparse.Namespace) -> None:
    """输出生成隐患卡的提示词。"""
    material = get_material(args.material_id, args.db_path)
    content = material.get("content", "")
    if len(content) > 6000:
        content = content[:6000] + "\n\n[内容已截断]"

    analysis = args.analysis or content
    trigger = args.trigger_event or "CUSTOM_EVT_001"

    prompt = get_prompt(
        "HAZARD",
        material_analysis=analysis,
        trigger_event=trigger,
    )
    print(prompt)


def cmd_storyline(args: argparse.Namespace) -> None:
    """输出生成剧情线的提示词。"""
    material = get_material(args.material_id, args.db_path)
    content = material.get("content", "")
    if len(content) > 6000:
        content = content[:6000] + "\n\n[内容已截断]"

    analysis = args.analysis or content

    # 获取可用角色列表
    chars = []
    try:
        custom_chars = list_custom_cards("CHARACTER", active_only=False, db_path=args.db_path)
        for c in custom_chars:
            chars.append(f"- {c['card_id']}: {c['card_name']}")
    except Exception:
        pass

    # 内置角色
    from runtime.content import CHARACTERS
    for c in CHARACTERS:
        chars.append(f"- {c.character_id}: {c.name} ({c.role_type or '未知'})")

    available = "\n".join(chars) if chars else "（暂无可用角色，请先蒸馏角色卡）"

    prompt = get_prompt(
        "STORYLINE",
        material_analysis=analysis,
        available_characters=available,
    )
    print(prompt)


def cmd_full(args: argparse.Namespace) -> None:
    """一键输出全流程提示词：分析 + 角色 + 事件 + 隐患 + 剧情线。"""
    material = get_material(args.material_id, args.db_path)
    title = material.get("title", "未命名素材")
    content = material.get("content", "")
    original_len = len(content)
    if len(content) > 8000:
        content = content[:8000] + f"\n\n[内容已截断，原长度 {original_len} 字符]"

    print("=" * 70)
    print(f"素材: {title} (ID: {args.material_id})")
    print(f"内容长度: {original_len} 字符")
    print("=" * 70)
    print()

    # Step 1: 分析
    print("# STEP 1: 六维深度分析")
    print("-" * 70)
    print(get_prompt("ANALYSIS", material_content=content))
    print()
    print("=" * 70)
    print("【请先将上述分析结果保存，然后在后续步骤中传入 --analysis 参数】")
    print("=" * 70)
    print()

    # Step 2-5: 生成各类卡牌的提示词（占位，需要分析结果）
    print("# STEP 2-5: 生成卡牌（需要分析结果）")
    print("-" * 70)
    print("分析完成后，请运行以下命令生成各类卡牌：")
    print()
    print(f"  # 生成角色卡")
    print(f"  python scripts/distill_from_material.py character --material-id {args.material_id} --analysis '<分析结果>' --person '主要人物名'")
    print()
    print(f"  # 生成事件卡")
    print(f"  python scripts/distill_from_material.py event --material-id {args.material_id} --analysis '<分析结果>' --character-id CUSTOM_CHR_XXX")
    print()
    print(f"  # 生成隐患卡")
    print(f"  python scripts/distill_from_material.py hazard --material-id {args.material_id} --analysis '<分析结果>' --trigger-event CUSTOM_EVT_XXX")
    print()
    print(f"  # 生成剧情线")
    print(f"  python scripts/distill_from_material.py storyline --material-id {args.material_id} --analysis '<分析结果>'")
    print()


def cmd_write(args: argparse.Namespace) -> None:
    """将 JSON 文件中的卡牌数据写入数据库。"""
    path = Path(args.file)
    if not path.exists():
        print(f"错误: 文件不存在 {args.file}")
        sys.exit(1)

    data = json.loads(path.read_text(encoding="utf-8"))
    card_type = args.type.upper()

    # 如果提供了 card_id 就用，否则自动生成
    card_id = args.card_id or _next_custom_id(card_type, args.db_path)

    result = write_distilled_card(
        card_id=card_id,
        card_type=card_type,
        card_data=data,
        source_material_id=args.material_id,
        is_active=1 if args.activate else 0,
        db_path=args.db_path,
    )

    if result["ok"]:
        print(f"✅ 卡牌已写入: {result['card_id']}")
        print(f"   类型: {card_type}")
        print(f"   名称: {data.get('name', '未命名')}")
        if args.material_id:
            print(f"   来源素材: ID {args.material_id}")
        if args.activate:
            print(f"   状态: 已激活")
    else:
        print(f"❌ 校验失败:")
        for err in result["errors"]:
            print(f"   - {err}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="智能卡牌蒸馏器（女娲式深度分析）")
    parser.add_argument("--db-path", default=None, help="SQLite 数据库路径")
    sub = parser.add_subparsers(dest="command", required=True)

    # analyze
    p_analyze = sub.add_parser("analyze", help="输出素材六维分析提示词")
    p_analyze.add_argument("--material-id", type=int, required=True, help="素材ID")
    p_analyze.set_defaults(func=cmd_analyze)

    # character
    p_char = sub.add_parser("character", help="输出生成角色卡的提示词")
    p_char.add_argument("--material-id", type=int, required=True, help="素材ID")
    p_char.add_argument("--analysis", default=None, help="预分析结果文本（可选）")
    p_char.add_argument("--person", default=None, help="目标人物名称（可选）")
    p_char.set_defaults(func=cmd_character)

    # event
    p_event = sub.add_parser("event", help="输出生成事件卡的提示词")
    p_event.add_argument("--material-id", type=int, required=True, help="素材ID")
    p_event.add_argument("--analysis", default=None, help="预分析结果文本（可选）")
    p_event.add_argument("--character-id", default=None, help="关联角色ID")
    p_event.set_defaults(func=cmd_event)

    # hazard
    p_hazard = sub.add_parser("hazard", help="输出生成隐患卡的提示词")
    p_hazard.add_argument("--material-id", type=int, required=True, help="素材ID")
    p_hazard.add_argument("--analysis", default=None, help="预分析结果文本（可选）")
    p_hazard.add_argument("--trigger-event", default=None, help="触发事件ID")
    p_hazard.set_defaults(func=cmd_hazard)

    # storyline
    p_story = sub.add_parser("storyline", help="输出生成剧情线的提示词")
    p_story.add_argument("--material-id", type=int, required=True, help="素材ID")
    p_story.add_argument("--analysis", default=None, help="预分析结果文本（可选）")
    p_story.set_defaults(func=cmd_storyline)

    # full
    p_full = sub.add_parser("full", help="一键输出全流程提示词")
    p_full.add_argument("--material-id", type=int, required=True, help="素材ID")
    p_full.set_defaults(func=cmd_full)

    # write
    p_write = sub.add_parser("write", help="将 JSON 卡牌数据写入数据库")
    p_write.add_argument("--file", required=True, help="JSON 文件路径")
    p_write.add_argument("--type", required=True, choices=["character", "event", "hazard", "storyline"], help="卡牌类型")
    p_write.add_argument("--card-id", default=None, help="指定卡牌ID（可选，自动分配）")
    p_write.add_argument("--material-id", type=int, default=None, help="来源素材ID")
    p_write.add_argument("--activate", action="store_true", help="写入后立即激活")
    p_write.set_defaults(func=cmd_write)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
