#!/usr/bin/env python3
"""平衡性模拟脚本（Scene-Driven v2）。

职责：
1. 运行 N 局游戏，每局 M 回合
2. 在场景模式下自动选择选项
3. 统计：生存率、策略使用频率、结局分布、角色状态变化
4. 生成 balance-report.md
"""

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

from runtime.db import connect, init_db
from runtime.engine import (
    apply_turn,
    build_next_prompt,
    create_session,
    _resolve_ending,
    _load_character_states,
)
from runtime.scenes import SCENES
from runtime.strategy_prototypes import STRATEGY_PROTOTYPES


# ---------------------------------------------------------------------------
# AI 玩家策略：根据当前状态选择最优选项
# ---------------------------------------------------------------------------

def _score_option(opt, player_state: dict, scene_options: list, turn_history: list) -> float:
    """为选项打分，分数越高越优先选择。"""
    score = 50.0
    proto = opt.get("prototype", "")

    # 策略原型的基础偏好（降低EVADE，提升CHARM/TRADE）
    prototype_prefs = {
        "ASSERT": 12,
        "DOCUMENT": 8,
        "EVADE": -5,
        "CHARM": 10,
        "TRADE": 9,
        "PROBE": 7,
        "DEFLECT": -3,
        "ALLY": 6,
        "THREATEN": -8,
        "RECOVER": 15,
    }
    score += prototype_prefs.get(proto, 0)

    # 检查派系总监是否在场（通过选项推断）
    has_rival = any(opt.get("target_character") == "CHR_06" for opt in scene_options)
    has_chen = any(opt.get("target_character") == "CHR_01" for opt in scene_options)

    # 状态紧急时的调整
    en = player_state.get("en", 100)
    st = player_state.get("st", 100)
    risk = player_state.get("risk", 0)
    cor = player_state.get("cor", 0)

    # 派系总监在场时，提高 CHARM/ALLY/PROBE 吸引力
    if has_rival:
        if proto in ("CHARM", "ALLY"):
            score += 15
        elif proto == "PROBE":
            score += 8

    # 陈总监在场且关系已极差时，提高 CHARM 修复意愿
    if has_chen and proto == "CHARM":
        score += 12

    # 精力管理：低精力时强烈偏好 RECOVER
    if en < 30:
        if proto == "RECOVER":
            score += 40
        elif proto in ("ASSERT", "THREATEN"):
            score -= 30
        elif proto == "EVADE":
            score += 10
    elif en < 55:
        if proto == "RECOVER":
            score += 20
        elif proto == "ASSERT":
            score -= 15

    # 风险高时优先 DOCUMENT 和 ASSERT（正面解决）
    if risk > 50:
        if proto == "DOCUMENT":
            score += 20
        elif proto in ("DEFLECT", "EVADE"):
            score -= 15

    # 污染高时避免灰色操作，鼓励 DOCUMENT/CHARM
    if cor > 40:
        if proto in ("DEFLECT", "THREATEN"):
            score -= 20
        elif proto in ("CHARM", "DOCUMENT"):
            score += 10

    # 体力低时避免高强度
    if st < 30:
        if proto == "ASSERT":
            score -= 20
        elif proto == "RECOVER":
            score += 15

    # 连续 EVADE 惩罚（避免滥用）
    recent_evades = sum(1 for h in turn_history[-3:] if h == "EVADE")
    if proto == "EVADE" and recent_evades >= 2:
        score -= 20 * recent_evades

    # 随机噪声（避免完全确定性）
    score += random.uniform(-8, 8)

    return score


def pick_action(prompt: dict, turn_history: list) -> str:
    """根据 prompt 中的场景选项选择行动。"""
    scene = prompt.get("scene", {})
    options = scene.get("options", [])
    if not options:
        return "1"

    player_state = {
        "hp": 100,
        "en": 100,
        "st": 100,
        "risk": 0,
        "cor": 0,
    }
    status_bar = prompt.get("status_bar", {})
    for k, v in status_bar.items():
        if k == "生命":
            player_state["hp"] = int(v.split("/")[0])
        elif k == "精力":
            player_state["en"] = int(v.split("/")[0])
        elif k == "体力":
            player_state["st"] = int(v.split("/")[0])
        elif k == "风险":
            player_state["risk"] = int(v)
        elif k == "污染":
            player_state["cor"] = int(v)

    scored = [(opt, _score_option(opt, player_state, options, turn_history)) for opt in options]
    scored.sort(key=lambda x: -x[1])

    # 80% 概率选最高分，20% 随机探索
    if random.random() < 0.8:
        return scored[0][0]["option_id"]
    else:
        return random.choice(options)["option_id"]


# ---------------------------------------------------------------------------
# 单局模拟
# ---------------------------------------------------------------------------

def run_once(session_id: str, max_turns: int, db_path: str) -> dict:
    """运行一局游戏，返回结果。"""
    create_session(session_id, db_path)
    final_prompt = None
    ending = None
    turn_history: list[str] = []

    for turn_idx in range(max_turns):
        prompt = build_next_prompt(session_id, db_path)
        if not prompt:
            break

        final_prompt = prompt
        action = pick_action(prompt, turn_history)

        result = apply_turn(session_id, action, None, db_path)
        # 记录实际选择的原型
        chosen_proto = ""
        for opt in prompt.get("scene", {}).get("options", []):
            if opt.get("option_id") == action:
                chosen_proto = opt.get("prototype", "")
                break
        turn_history.append(chosen_proto)
        if hasattr(result, "ending") and result.ending:
            ending = result.ending
            break

    # 加载最终状态
    conn = connect(db_path)
    row = conn.execute(
        "SELECT * FROM game_sessions WHERE session_id = ?", (session_id,)
    ).fetchone()
    final_state = dict(row) if row else {}
    char_states = _load_character_states(session_id, conn)
    conn.close()

    return {
        "session_id": session_id,
        "turn_index": final_state.get("turn_index", 0),
        "final_state": {
            "hp": final_state.get("hp", 100),
            "en": final_state.get("en", 100),
            "st": final_state.get("st", 100),
            "kpi": final_state.get("kpi", 100),
            "risk": final_state.get("risk", 0),
            "cor": final_state.get("cor", 0),
        },
        "character_states": {
            cid: {
                "relation": s.relation_to_player,
                "mood": s.mood,
                "trust": s.trust,
                "stress": s.stress,
                "power": s.power,
            }
            for cid, s in char_states.items()
        },
        "ending": ending,
    }


# ---------------------------------------------------------------------------
# 报告生成
# ---------------------------------------------------------------------------

def build_report(results: list[dict], db_path: str, report_file: str) -> None:
    """生成平衡性报告。"""
    conn = connect(db_path)

    # 统计行动选择
    prototype_counter = Counter()
    scene_counter = Counter()
    for row in conn.execute(
        "SELECT action_type, event_id FROM turn_logs"
    ).fetchall():
        action = row["action_type"]
        scene_id = row["event_id"]
        # 从 option_id 推断原型
        if action.startswith("OPT_"):
            for scene in SCENES.values():
                for opt in scene.player_options:
                    if opt.option_id == action:
                        prototype_counter[opt.prototype] += 1
                        break
        scene_counter[scene_id] += 1

    conn.close()

    # 结局统计
    endings = [r["ending"] for r in results if r.get("ending")]
    ending_counter = Counter(e["name"] for e in endings if e)
    survived = sum(1 for r in results if not r.get("ending"))

    # 数值统计
    turns = [r["turn_index"] for r in results]
    risk_vals = [r["final_state"]["risk"] for r in results]
    cor_vals = [r["final_state"]["cor"] for r in results]
    en_vals = [r["final_state"]["en"] for r in results]
    st_vals = [r["final_state"]["st"] for r in results]
    kpi_vals = [r["final_state"]["kpi"] for r in results]

    # 角色关系统计
    relation_avgs = {}
    for cid in ["CHR_01", "CHR_02", "CHR_03", "CHR_04", "CHR_05", "CHR_06"]:
        vals = [
            r["character_states"].get(cid, {}).get("relation", 0)
            for r in results
            if r.get("character_states")
        ]
        if vals:
            relation_avgs[cid] = round(statistics.mean(vals), 1)

    lines = [
        "# DarkOffice Balance Report (Scene-Driven v2)",
        "",
        f"- Simulations: {len(results)}",
        f"- Max turns per run: {max(turns) if turns else 0}",
        f"- Avg turns played: {round(statistics.mean(turns), 2) if turns else 0}",
        f"- Median turns: {statistics.median(turns) if turns else 0}",
        "",
        "## Player State (Final)",
        f"- Avg HP: {round(statistics.mean([r['final_state']['hp'] for r in results]), 2)}",
        f"- Avg EN: {round(statistics.mean(en_vals), 2)}",
        f"- Avg ST: {round(statistics.mean(st_vals), 2)}",
        f"- Avg KPI: {round(statistics.mean(kpi_vals), 2)}",
        f"- Avg RISK: {round(statistics.mean(risk_vals), 2)}",
        f"- Avg COR: {round(statistics.mean(cor_vals), 2)}",
        "",
        "## Ending Distribution",
        f"- Survived (no ending): {survived} ({round(survived/len(results)*100, 1)}%)",
    ]
    for name, count in ending_counter.most_common():
        pct = round(count / len(results) * 100, 1)
        lines.append(f"- {name}: {count} ({pct}%)")

    lines.extend([
        "",
        "## Strategy Prototype Usage",
    ])
    total_prototype = sum(prototype_counter.values()) or 1
    for proto, count in prototype_counter.most_common():
        pct = round(count / total_prototype * 100, 1)
        info = STRATEGY_PROTOTYPES.get(proto)
        title = info.title if info else proto
        lines.append(f"- {title} ({proto}): {count} ({pct}%)")

    lines.extend([
        "",
        "## Scene Frequency",
    ])
    for scene_id, count in scene_counter.most_common(10):
        scene = SCENES.get(scene_id)
        title = scene.title if scene else scene_id
        lines.append(f"- {title}: {count}")

    lines.extend([
        "",
        "## Character Relations (Avg)",
    ])
    char_names = {
        "CHR_01": "陈总监", "CHR_02": "小林", "CHR_03": "甲方",
        "CHR_04": "HR", "CHR_05": "财务", "CHR_06": "派系总监",
    }
    for cid, avg in sorted(relation_avgs.items()):
        name = char_names.get(cid, cid)
        lines.append(f"- {name}: {avg}")

    Path(report_file).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run darkoffice balance simulation")
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--turns", type=int, default=35)
    parser.add_argument("--db", default="runtime/sim.sqlite3")
    parser.add_argument("--report", default="docs/project/balance-report.md")
    args = parser.parse_args()

    db_path = args.db
    conn = connect(db_path)
    init_db(conn)
    conn.execute("DELETE FROM turn_logs")
    conn.execute("DELETE FROM game_sessions")
    conn.execute("DELETE FROM character_states")
    conn.execute("DELETE FROM intel_discovered")
    conn.execute("DELETE FROM player_notes")
    conn.execute("DELETE FROM relation_edges")
    conn.commit()
    conn.close()

    results = []
    for i in range(args.runs):
        results.append(run_once(f"sim_{i+1}", args.turns, db_path))

    build_report(results, db_path, args.report)

    # 摘要输出
    endings = [r["ending"] for r in results if r.get("ending")]
    ending_counter = Counter(e["name"] for e in endings if e)
    survived = sum(1 for r in results if not r.get("ending"))

    print(json.dumps({
        "ok": True,
        "runs": args.runs,
        "max_turns": args.turns,
        "report": args.report,
        "summary": {
            "survived": survived,
            "endings": dict(ending_counter),
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
