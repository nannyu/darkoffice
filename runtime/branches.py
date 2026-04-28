"""剧情线分支条件匹配引擎。

职责：
1. 根据当前回合数据（action_type、result_tier、state）匹配分支
2. 根据 state 和 turn_logs 匹配结局
3. 所有条件判断都是纯函数，无副作用
"""

from __future__ import annotations


def _check_value_match(actual, expected) -> bool:
    """检查单个值是否匹配期望值（支持字符串或列表）。"""
    if expected is None:
        return True
    if isinstance(expected, (list, tuple, set)):
        return actual in expected
    return actual == expected


def _check_threshold(state: dict, cond: dict) -> bool:
    """检查数值阈值条件（*_min、*_max）。"""
    attrs = ["hp", "en", "st", "kpi", "risk", "cor"]
    for attr in attrs:
        value = state.get(attr)
        if value is None:
            continue
        min_key = f"{attr}_min"
        max_key = f"{attr}_max"
        if min_key in cond and value < cond[min_key]:
            return False
        if max_key in cond and value > cond[max_key]:
            return False
    return True


def _check_action_history(cond: dict, turn_logs: list[dict]) -> bool:
    """检查历史行动中是否包含指定类型。"""
    required = cond.get("action_history")
    if not required:
        return True
    if isinstance(required, str):
        required = [required]
    actions = {log.get("action_type", "").upper() for log in turn_logs}
    return any(r.upper() in actions for r in required)


def check_condition(
    cond: dict,
    action_type: str | None = None,
    result_tier: str | None = None,
    state: dict | None = None,
    turn_logs: list[dict] | None = None,
    turn_index: int | None = None,
) -> bool:
    """检查条件是否满足。

    条件字段：
    - action_type: str | list[str] — 当前回合行动类型
    - result_tier: str | list[str] — 当前回合结果等级
    - *_min / *_max — 属性阈值（hp/en/st/kpi/risk/cor）
    - action_history: str | list[str] — 历史行动中是否包含
    - turn_index_min / turn_index_max — 回合数阈值
    """
    if action_type is not None and "action_type" in cond:
        if not _check_value_match(action_type.upper(), cond["action_type"]):
            return False
    if result_tier is not None and "result_tier" in cond:
        if not _check_value_match(result_tier.upper(), cond["result_tier"]):
            return False
    if state is not None:
        if not _check_threshold(state, cond):
            return False
    if turn_logs is not None and "action_history" in cond:
        if not _check_action_history(cond, turn_logs):
            return False
    if turn_index is not None:
        if "turn_index_min" in cond and turn_index < cond["turn_index_min"]:
            return False
        if "turn_index_max" in cond and turn_index > cond["turn_index_max"]:
            return False
    return True


def match_branch(
    branches: list[dict],
    action_type: str,
    result_tier: str,
    state: dict,
    turn_logs: list[dict] | None = None,
    turn_index: int | None = None,
) -> dict | None:
    """按顺序匹配第一个满足条件的分支。

    Returns:
        匹配的分支 dict（含 target_act、label、narrative 等），或 None。
    """
    for b in branches:
        cond = b.get("condition", {})
        if check_condition(cond, action_type, result_tier, state, turn_logs, turn_index):
            return b
    return None


def check_endings(
    endings: list[dict],
    state: dict,
    turn_logs: list[dict] | None = None,
    turn_index: int | None = None,
) -> dict | None:
    """检查是否触发结局，按 endings 数组顺序优先级匹配。

    Returns:
        触发的结局 dict（含 ending_id、name、description、ending_type），或 None。
    """
    for e in endings:
        cond = e.get("condition", {})
        if check_condition(cond, None, None, state, turn_logs, turn_index):
            return e
    return None
