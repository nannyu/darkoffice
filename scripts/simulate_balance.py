#!/usr/bin/env python3
import argparse
import json
import random
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from runtime.engine import apply_turn, create_session, get_action_stats  # noqa: E402
from runtime.db import connect, init_db  # noqa: E402


ACTIONS = [
    "EMAIL_TRACE",
    "NARROW_SCOPE",
    "SOFT_REFUSE",
    "WORK_OVERTIME",
    "SHIFT_BLAME",
    "RECOVERY_BREAK",
]


def run_once(session_id: str, turns: int, db_path: str) -> dict:
    create_session(session_id, db_path)
    final = None
    for _ in range(turns):
        action = random.choice(ACTIONS)
        final = apply_turn(session_id, action, None, db_path)
        if final.failure_type:
            break
    return {
        "session_id": session_id,
        "turn_index": final.turn_index if final else 0,
        "failure_type": final.failure_type if final else None,
        "final_state": final.state if final else {},
    }


def build_report(results: list[dict], db_path: str, report_file: str) -> None:
    fail_counter = Counter(item["failure_type"] or "SURVIVED" for item in results)
    turns = [item["turn_index"] for item in results]
    risk_vals = [item["final_state"].get("risk", 0) for item in results]
    cor_vals = [item["final_state"].get("cor", 0) for item in results]

    conn = connect(db_path)
    samples = []
    for row in conn.execute("SELECT session_id FROM game_sessions").fetchall():
        samples.extend(get_action_stats(row["session_id"], db_path))

    action_agg = {}
    for item in samples:
        key = item["action_type"]
        action_agg.setdefault(key, {"turns": 0, "success": 0, "critical_fail": 0})
        action_agg[key]["turns"] += item["turns"]
        action_agg[key]["success"] += item["success_count"]
        action_agg[key]["critical_fail"] += item["critical_fail_count"]

    lines = [
        "# DarkOffice Balance Report",
        "",
        f"- Simulations: {len(results)}",
        f"- Avg turns survived: {round(statistics.mean(turns), 2) if turns else 0}",
        f"- Median turns survived: {statistics.median(turns) if turns else 0}",
        f"- Avg final RISK: {round(statistics.mean(risk_vals), 2) if risk_vals else 0}",
        f"- Avg final COR: {round(statistics.mean(cor_vals), 2) if cor_vals else 0}",
        "",
        "## Outcome Distribution",
    ]
    for key, value in fail_counter.items():
        lines.append(f"- {key}: {value}")

    lines.append("")
    lines.append("## Action Performance")
    for action, data in sorted(action_agg.items(), key=lambda x: -x[1]["turns"]):
        turns_count = data["turns"] or 1
        success_rate = round(data["success"] / turns_count, 3)
        crit_fail_rate = round(data["critical_fail"] / turns_count, 3)
        lines.append(
            f"- {action}: turns={turns_count}, success_rate={success_rate}, critical_fail_rate={crit_fail_rate}"
        )

    Path(report_file).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run darkoffice balance simulation")
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--turns", type=int, default=30)
    parser.add_argument("--db", default="runtime/sim.sqlite3")
    parser.add_argument("--report", default="docs/project/balance-report.md")
    args = parser.parse_args()

    conn = connect(args.db)
    init_db(conn)
    conn.execute("DELETE FROM turn_logs")
    conn.execute("DELETE FROM game_sessions")
    conn.commit()

    results = []
    for i in range(args.runs):
        results.append(run_once(f"sim_{i+1}", args.turns, args.db))

    build_report(results, args.db, args.report)
    print(
        json.dumps(
            {"ok": True, "runs": args.runs, "turns": args.turns, "report": args.report},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
