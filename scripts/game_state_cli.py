#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.db import connect, init_db
from runtime.engine import (
    apply_turn,
    build_next_prompt,
    create_session,
    get_action_stats,
    get_history,
    get_session,
)
from runtime.materials import (
    add_material,
    list_materials,
    get_material,
    search_materials,
    delete_material,
    import_material,
    add_custom_card,
    list_custom_cards,
    get_custom_card,
    activate_card,
    deactivate_card,
    delete_custom_card,
)
from runtime.storylines import (
    create_storyline,
    list_storylines,
    get_storyline,
    delete_storyline,
    activate_storyline,
    deactivate_storyline,
    get_active_storyline,
    advance_act,
)


def _out(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description="Dark Office state CLI")
    parser.add_argument("--db", default="runtime/darkoffice.sqlite3")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # ---- 原有游戏命令 ----
    sub.add_parser("init")

    create_p = sub.add_parser("create")
    create_p.add_argument("session_id")

    show_p = sub.add_parser("show")
    show_p.add_argument("session_id")

    turn_p = sub.add_parser("turn")
    turn_p.add_argument("session_id")
    turn_p.add_argument("--action", default="DEFAULT_ACTION")
    turn_p.add_argument("--mod", type=int, default=None)

    history_p = sub.add_parser("history")
    history_p.add_argument("session_id")
    history_p.add_argument("--limit", type=int, default=10)

    stats_p = sub.add_parser("stats")
    stats_p.add_argument("session_id")

    prompt_p = sub.add_parser("prompt")
    prompt_p.add_argument("session_id")

    # ---- 素材库命令 ----
    mat_add_p = sub.add_parser("material-add", help="手动录入素材")
    mat_add_p.add_argument("--title", required=True)
    mat_add_p.add_argument("--source", default="")
    mat_add_p.add_argument("--category", default="")
    mat_add_p.add_argument("--content", default="")
    mat_add_p.add_argument("--tags", default="", help="逗号分隔标签")

    mat_import_p = sub.add_parser("material-import", help="从文件导入素材(md/txt/pdf)")
    mat_import_p.add_argument("--file", required=True, help="文件路径")
    mat_import_p.add_argument("--source", default="")
    mat_import_p.add_argument("--category", default="")
    mat_import_p.add_argument("--tags", default="", help="逗号分隔标签")

    mat_list_p = sub.add_parser("material-list", help="列出素材")
    mat_list_p.add_argument("--category", default=None)
    mat_list_p.add_argument("--source", default=None)

    mat_show_p = sub.add_parser("material-show", help="查看素材详情")
    mat_show_p.add_argument("material_id", type=int)

    mat_search_p = sub.add_parser("material-search", help="搜索素材")
    mat_search_p.add_argument("keyword")

    mat_del_p = sub.add_parser("material-delete", help="删除素材")
    mat_del_p.add_argument("material_id", type=int)

    # ---- 自定义卡牌命令 ----
    card_add_p = sub.add_parser("card-add", help="新增自定义卡牌")
    card_add_p.add_argument("--card-id", required=True, help="卡牌ID，建议 CUSTOM_ 前缀")
    card_add_p.add_argument("--card-type", required=True, help="CHARACTER/EVENT/HAZARD")
    card_add_p.add_argument("--card-name", required=True)
    card_add_p.add_argument("--card-data", required=True, help="JSON 格式的卡牌数据")
    card_add_p.add_argument("--source-material-id", type=int, default=None)
    card_add_p.add_argument("--active", type=int, default=0, help="是否立即激活 0/1")

    card_list_p = sub.add_parser("card-list", help="列出自定义卡牌")
    card_list_p.add_argument("--card-type", default=None)
    card_list_p.add_argument("--active-only", action="store_true")

    card_show_p = sub.add_parser("card-show", help="查看自定义卡牌详情")
    card_show_p.add_argument("card_id")

    card_activate_p = sub.add_parser("card-activate", help="激活自定义卡牌")
    card_activate_p.add_argument("card_id")

    card_deactivate_p = sub.add_parser("card-deactivate", help="停用自定义卡牌")
    card_deactivate_p.add_argument("card_id")

    card_del_p = sub.add_parser("card-delete", help="删除自定义卡牌")
    card_del_p.add_argument("card_id")

    # ---- 剧情线命令 ----
    sl_create_p = sub.add_parser("storyline-create", help="创建剧情线")
    sl_create_p.add_argument("--storyline-id", required=True)
    sl_create_p.add_argument("--title", required=True)
    sl_create_p.add_argument("--description", default="")
    sl_create_p.add_argument("--acts", default="[]", help="JSON 格式的幕定义数组")
    sl_create_p.add_argument("--metadata", default="{}", help="JSON 格式的元数据（含 endings 等）")

    sl_list_p = sub.add_parser("storyline-list", help="列出剧情线")

    sl_show_p = sub.add_parser("storyline-show", help="查看剧情线详情")
    sl_show_p.add_argument("storyline_id")

    sl_activate_p = sub.add_parser("storyline-activate", help="激活剧情线到指定session")
    sl_activate_p.add_argument("session_id")
    sl_activate_p.add_argument("storyline_id")

    sl_deactivate_p = sub.add_parser("storyline-deactivate", help="停用当前session的剧情线")
    sl_deactivate_p.add_argument("session_id")

    sl_progress_p = sub.add_parser("storyline-progress", help="推进剧情线到下一幕")
    sl_progress_p.add_argument("session_id")

    sl_status_p = sub.add_parser("storyline-status", help="查看当前session的剧情线状态")
    sl_status_p.add_argument("session_id")

    sl_del_p = sub.add_parser("storyline-delete", help="删除剧情线")
    sl_del_p.add_argument("storyline_id")

    args = parser.parse_args()
    db = args.db

    # ---- 原有游戏命令处理 ----
    if args.cmd == "init":
        conn = connect(db)
        init_db(conn)
        print(f"initialized: {db}")
        return

    if args.cmd == "create":
        session = create_session(args.session_id, db)
        _out(session)
        return

    if args.cmd == "show":
        session = get_session(args.session_id, db)
        _out(session)
        return

    if args.cmd == "turn":
        result = apply_turn(args.session_id, args.action, args.mod, db)
        _out(
            {
                "session_id": result.session_id,
                "turn_index": result.turn_index,
                "day": result.day,
                "time_period": result.time_period,
                "character_id": result.character_id,
                "event_id": result.event_id,
                "roll_value": result.roll_value,
                "total_score": result.total_score,
                "action_mod": result.action_mod,
                "result_tier": result.result_tier,
                "failure_type": result.failure_type,
                "delta": result.delta,
                "state": result.state,
                "statuses": result.statuses,
                "hazards": result.hazards,
                "projects": result.projects,
                "next_prompt": result.next_prompt,
                "storyline_context": result.storyline_context,
                "ending": result.ending,
            }
        )
        return

    if args.cmd == "history":
        data = get_history(args.session_id, args.limit, db)
        _out(data)
        return

    if args.cmd == "stats":
        data = get_action_stats(args.session_id, db)
        _out(data)
        return

    if args.cmd == "prompt":
        data = build_next_prompt(args.session_id, db)
        _out(data)
        return

    # ---- 素材库命令处理 ----
    if args.cmd == "material-add":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
        mat_id = add_material(
            title=args.title,
            source=args.source,
            category=args.category,
            content=args.content,
            tags=tags,
            db_path=db,
        )
        _out({"ok": True, "material_id": mat_id})
        return

    if args.cmd == "material-import":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
        mat_id = import_material(
            file_path=args.file,
            source=args.source,
            category=args.category,
            tags=tags,
            db_path=db,
        )
        _out({"ok": True, "material_id": mat_id, "file": args.file})
        return

    if args.cmd == "material-list":
        data = list_materials(category=args.category, source=args.source, db_path=db)
        _out(data)
        return

    if args.cmd == "material-show":
        data = get_material(args.material_id, db)
        _out(data)
        return

    if args.cmd == "material-search":
        data = search_materials(args.keyword, db)
        _out(data)
        return

    if args.cmd == "material-delete":
        ok = delete_material(args.material_id, db)
        _out({"ok": ok})
        return

    # ---- 自定义卡牌命令处理 ----
    if args.cmd == "card-add":
        card_data = json.loads(args.card_data)
        cid = add_custom_card(
            card_id=args.card_id,
            card_type=args.card_type,
            card_name=args.card_name,
            card_data=card_data,
            source_material_id=args.source_material_id,
            is_active=args.active,
            db_path=db,
        )
        _out({"ok": True, "card_id": cid})
        return

    if args.cmd == "card-list":
        data = list_custom_cards(card_type=args.card_type, active_only=args.active_only, db_path=db)
        _out(data)
        return

    if args.cmd == "card-show":
        data = get_custom_card(args.card_id, db)
        _out(data)
        return

    if args.cmd == "card-activate":
        ok = activate_card(args.card_id, db)
        _out({"ok": ok})
        return

    if args.cmd == "card-deactivate":
        ok = deactivate_card(args.card_id, db)
        _out({"ok": ok})
        return

    if args.cmd == "card-delete":
        ok = delete_custom_card(args.card_id, db)
        _out({"ok": ok})
        return

    # ---- 剧情线命令处理 ----
    if args.cmd == "storyline-create":
        acts = json.loads(args.acts)
        metadata = json.loads(args.metadata)
        sid = create_storyline(
            storyline_id=args.storyline_id,
            title=args.title,
            description=args.description,
            acts=acts,
            metadata=metadata,
            db_path=db,
        )
        _out({"ok": True, "storyline_id": sid})
        return

    if args.cmd == "storyline-list":
        data = list_storylines(db)
        _out(data)
        return

    if args.cmd == "storyline-show":
        data = get_storyline(args.storyline_id, db)
        _out(data)
        return

    if args.cmd == "storyline-activate":
        ok = activate_storyline(args.session_id, args.storyline_id, db)
        _out({"ok": ok})
        return

    if args.cmd == "storyline-deactivate":
        ok = deactivate_storyline(args.session_id, db)
        _out({"ok": ok})
        return

    if args.cmd == "storyline-progress":
        next_act = advance_act(args.session_id, db)
        _out({"ok": True, "next_act": next_act})
        return

    if args.cmd == "storyline-status":
        data = get_active_storyline(args.session_id, db)
        _out(data)
        return

    if args.cmd == "storyline-delete":
        ok = delete_storyline(args.storyline_id, db)
        _out({"ok": ok})
        return


if __name__ == "__main__":
    main()
