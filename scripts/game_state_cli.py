#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.db import connect, init_db
from runtime.engine import apply_turn, create_session, get_session


def main() -> None:
    parser = argparse.ArgumentParser(description="Dark Office state CLI")
    parser.add_argument("--db", default="runtime/darkoffice.sqlite3")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")

    create_p = sub.add_parser("create")
    create_p.add_argument("session_id")

    show_p = sub.add_parser("show")
    show_p.add_argument("session_id")

    turn_p = sub.add_parser("turn")
    turn_p.add_argument("session_id")
    turn_p.add_argument("--action", default="DEFAULT_ACTION")
    turn_p.add_argument("--mod", type=int, default=0)

    args = parser.parse_args()

    if args.cmd == "init":
        conn = connect(args.db)
        init_db(conn)
        print(f"initialized: {args.db}")
        return

    if args.cmd == "create":
        session = create_session(args.session_id, args.db)
        print(json.dumps(session, ensure_ascii=False, indent=2))
        return

    if args.cmd == "show":
        session = get_session(args.session_id, args.db)
        print(json.dumps(session, ensure_ascii=False, indent=2))
        return

    if args.cmd == "turn":
        result = apply_turn(args.session_id, args.action, args.mod, args.db)
        print(
            json.dumps(
                {
                    "session_id": result.session_id,
                    "turn_index": result.turn_index,
                    "roll_value": result.roll_value,
                    "result_tier": result.result_tier,
                    "delta": result.delta,
                    "state": result.state,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return


if __name__ == "__main__":
    main()
