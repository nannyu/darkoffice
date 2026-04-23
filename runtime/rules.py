from __future__ import annotations

from copy import deepcopy


RESOURCE_ORDER = ("hp", "en", "st", "kpi", "risk", "cor")

RESOURCE_DEFINITIONS: dict[str, dict[str, str]] = {
    "hp": {
        "label": "生命",
        "track": "生存线",
        "direction": "越高越安全",
        "failure_condition": "HP <= 0",
        "failure_outcome": "崩溃出局",
    },
    "en": {
        "label": "精力",
        "track": "心智线",
        "direction": "越高越稳定",
        "failure_condition": "EN <= 0",
        "failure_outcome": "精神崩溃",
    },
    "st": {
        "label": "体力",
        "track": "耐久线",
        "direction": "越高越能硬扛",
        "failure_condition": "ST <= 0",
        "failure_outcome": "体力耗尽",
    },
    "kpi": {
        "label": "绩效",
        "track": "组织评价线",
        "direction": "越高越能苟住岗位",
        "failure_condition": "KPI <= 0",
        "failure_outcome": "被开除",
    },
    "risk": {
        "label": "风险",
        "track": "暴雷线",
        "direction": "越低越安全",
        "failure_condition": "RISK >= 100",
        "failure_outcome": "暴雷结局",
    },
    "cor": {
        "label": "污染",
        "track": "黑化线",
        "direction": "越低越干净",
        "failure_condition": "COR >= 100",
        "failure_outcome": "黑化结局",
    },
}

# 每 24 回合为 1 个工作日（每回合 20 分钟，24 回合 = 8 小时）
TURNS_PER_DAY = 24

TIME_PERIOD_RULES: list[dict] = [
    {
        "id": "上午",
        "window": "09:00-12:00",
        "turn_start": 0,
        "turn_end": 8,
        "enabled": True,
        "mood": "例行推进",
        "summary": "常规压力平均分布，甲方与上司都可能发难。",
        "weight_modifiers": {"CHR_01": 1.0, "CHR_02": 1.0, "CHR_03": 1.2, "CHR_04": 0.8, "CHR_05": 1.0, "CHR_06": 0.8},
    },
    {
        "id": "午休",
        "window": "12:00-13:00",
        "turn_start": 9,
        "turn_end": 11,
        "enabled": True,
        "mood": "表面放松",
        "summary": "同事社交和推活更活跃，制度压力暂时回落。",
        "weight_modifiers": {"CHR_01": 0.5, "CHR_02": 1.5, "CHR_03": 0.5, "CHR_04": 0.5, "CHR_05": 0.5, "CHR_06": 0.3},
    },
    {
        "id": "下午",
        "window": "13:00-18:00",
        "turn_start": 12,
        "turn_end": 20,
        "enabled": True,
        "mood": "正式拉扯",
        "summary": "甲方需求和交付压力最容易集中爆发。",
        "weight_modifiers": {"CHR_01": 1.0, "CHR_02": 1.0, "CHR_03": 1.5, "CHR_04": 1.0, "CHR_05": 1.2, "CHR_06": 1.0},
    },
    {
        "id": "加班",
        "window": "18:00-21:00",
        "turn_start": 21,
        "turn_end": 23,
        "enabled": True,
        "mood": "透支救火",
        "summary": "上司和甲方权重上升，选择更偏向硬扛与留痕。",
        "weight_modifiers": {"CHR_01": 1.5, "CHR_02": 0.5, "CHR_03": 1.8, "CHR_04": 0.8, "CHR_05": 1.0, "CHR_06": 0.5},
    },
    {
        "id": "深夜",
        "window": "21:00+（预留）",
        "turn_start": 24,
        "turn_end": 99,
        "enabled": False,
        "mood": "危险时段",
        "summary": "文档保留的危险时段；当前 24 回合日制下尚未启用。",
        "weight_modifiers": {"CHR_01": 1.8, "CHR_02": 0.3, "CHR_03": 0.8, "CHR_04": 1.2, "CHR_05": 0.5, "CHR_06": 0.3},
    },
]

TURN_FLOW_STEPS: list[dict[str, str]] = [
    {"id": "TURN_START", "label": "回合开始", "phase": "维护", "summary": "初始化当前回合上下文。"},
    {"id": "TIME_ADVANCE", "label": "时间推进", "phase": "维护", "summary": "推进 20 分钟并切换时间段。"},
    {"id": "STATUS_TICK", "label": "状态结算", "phase": "维护", "summary": "让短期状态在回合开始持续生效。"},
    {"id": "HAZARD_TICK", "label": "隐患倒计时", "phase": "维护", "summary": "倒计时归零的隐患立刻翻面爆炸。"},
    {"id": "PROJECT_TICK", "label": "项目施压", "phase": "维护", "summary": "长期任务持续吞噬精力和体力。"},
    {"id": "MECHANIC_TICK", "label": "机制结算", "phase": "维护", "summary": "预留全局环境修正入口。"},
    {"id": "RENDER_STATUS_BAR", "label": "状态栏渲染", "phase": "输出", "summary": "把压力面板以聊天友好的形式展示给玩家。"},
    {"id": "DRAW_CHARACTER", "label": "抽取角色", "phase": "施压", "summary": "结合时间段和当前状态决定谁来施压。"},
    {"id": "DRAW_EVENT", "label": "抽取事件", "phase": "施压", "summary": "从角色事件池中生成本回合主冲突。"},
    {"id": "RENDER_CHOICES", "label": "渲染选项", "phase": "输出", "summary": "把内部应对卡转换成 3 到 5 个行动选项。"},
    {"id": "PLAYER_DECISION", "label": "玩家决策", "phase": "决策", "summary": "接收编号、关键词或自然语言输入。"},
    {"id": "ROLL_CHECK", "label": "判定掷骰", "phase": "结算", "summary": "关键节点用随机性决定结果质量。"},
    {"id": "RESOLVE_EFFECT", "label": "结算效果", "phase": "结算", "summary": "整合事件、行动和修正项产生最终数值变化。"},
    {"id": "GENERATE_CHAIN", "label": "生成链条", "phase": "后果", "summary": "生成状态、隐患、项目推进与后续链。"},
    {"id": "CHECK_FAIL_OR_END", "label": "检查失败", "phase": "后果", "summary": "判断是否触发崩溃、开除、暴雷或黑化。"},
    {"id": "REFRESH_ACTION_POOL", "label": "刷新行动池", "phase": "准备", "summary": "为下一回合准备新的候选行动。"},
    {"id": "TURN_END", "label": "回合结束", "phase": "准备", "summary": "写入日志并输出下一回合提示。"},
]

SETTLEMENT_ORDER: list[dict[str, str | int]] = [
    {"order": 1, "id": "EVENT_BASE", "label": "事件基础效果", "summary": "先计算事件原始压力。"},
    {"order": 2, "id": "RESPONSE", "label": "应对介入", "summary": "行动先改变风险、收益与损耗方向。"},
    {"order": 3, "id": "ROLL", "label": "骰子判定", "summary": "关键节点用档位放大或缓和效果。"},
    {"order": 4, "id": "CHARACTER_PASSIVE", "label": "人物被动", "summary": "预留角色个性化修正。"},
    {"order": 5, "id": "STATUS", "label": "状态修正", "summary": "低精力、低体力等状态影响本轮表现。"},
    {"order": 6, "id": "MECHANIC", "label": "机制修正", "summary": "预留全局环境与阶段规则入口。"},
    {"order": 7, "id": "THRESHOLD", "label": "阈值修正", "summary": "在数值逼近红线时追加惩罚。"},
    {"order": 8, "id": "GENERATE_STATUS", "label": "生成状态", "summary": "结算后推导新的持续状态。"},
    {"order": 9, "id": "GENERATE_HAZARD", "label": "生成隐患", "summary": "把口头承诺、灰色操作转成延迟爆炸。"},
    {"order": 10, "id": "GENERATE_PROJECT", "label": "项目推进", "summary": "处理项目进度与项目续压。"},
    {"order": 11, "id": "RELATION", "label": "关系变化", "summary": "预留角色态度与关系链更新。"},
    {"order": 12, "id": "FAILURE", "label": "失败检查", "summary": "统一判断多条失败线。"},
]

ROLL_TRIGGER_SCENARIOS: list[dict[str, str]] = [
    {"id": "HIGH_RISK_ACTION", "label": "高风险行动", "summary": "比如甩锅、灰色处理、强行推进。"},
    {"id": "KEY_EVENT", "label": "关键事件", "summary": "剧情节点或高压事件需要额外不确定性。"},
    {"id": "HAZARD_FLIP", "label": "隐患翻面", "summary": "倒计时归零时进入结果判定。"},
    {"id": "STAGE_NODE", "label": "阶段节点", "summary": "幕推进、阶段结算等重要时刻。"},
]

RESOLUTION_TIER_RULES: list[dict[str, str | float | int]] = [
    {
        "id": "CRITICAL_FAIL",
        "label": "大失败",
        "range": "<= 5",
        "min_score": -999,
        "max_score": 5,
        "multiplier": 1.5,
        "summary": "惩罚放大，还可能额外叠加风险。",
    },
    {
        "id": "FAIL",
        "label": "失败",
        "range": "6 - 10",
        "min_score": 6,
        "max_score": 10,
        "multiplier": 1.0,
        "summary": "按事件原始压力完整吃满代价。",
    },
    {
        "id": "BARELY",
        "label": "勉强成功",
        "range": "11 - 14",
        "min_score": 11,
        "max_score": 14,
        "multiplier": 0.7,
        "summary": "目标勉强完成，但代价仍然很痛。",
    },
    {
        "id": "SUCCESS",
        "label": "成功",
        "range": "15 - 18",
        "min_score": 15,
        "max_score": 18,
        "multiplier": 0.4,
        "summary": "多数惩罚被缓和，收益保留得更完整。",
    },
    {
        "id": "CRITICAL_SUCCESS",
        "label": "强成功",
        "range": ">= 19",
        "min_score": 19,
        "max_score": 999,
        "multiplier": 0.2,
        "summary": "高质量脱身，惩罚大幅削弱。",
    },
]

ACTION_RULES: dict[str, dict[str, str | int]] = {
    "DIRECT_EXECUTE": {
        "title": "立即执行",
        "summary": "保住绩效，但精力和体力消耗较高",
        "modifier": 2,
        "category": "硬扛推进",
        "tradeoff": "短期稳 KPI，长期透支 EN/ST。",
    },
    "EMAIL_TRACE": {
        "title": "邮件留痕",
        "summary": "降低后续背锅风险，但会激怒施压方",
        "modifier": 3,
        "category": "证据管理",
        "tradeoff": "主动降低风险，但要承受关系摩擦。",
    },
    "NARROW_SCOPE": {
        "title": "缩小范围",
        "summary": "降低本回合压力，但可能留下后续争议",
        "modifier": 1,
        "category": "边界管理",
        "tradeoff": "当回合减压，后续可能转成隐患。",
    },
    "SOFT_REFUSE": {
        "title": "温和拒绝",
        "summary": "保住边界，但绩效可能受损",
        "modifier": 0,
        "category": "保守防守",
        "tradeoff": "降低透支，但容易牺牲 KPI。",
    },
    "WORK_OVERTIME": {
        "title": "熬夜硬扛",
        "summary": "短期稳住局面，但透支精力和体力",
        "modifier": 4,
        "category": "紧急救火",
        "tradeoff": "高成功率换来更重的透支。",
    },
    "REQUEST_CONFIRMATION": {
        "title": "需求确认",
        "summary": "减少口头风险，但会增加沟通摩擦",
        "modifier": 2,
        "category": "降风险",
        "tradeoff": "以沟通成本换后续确定性。",
    },
    "DELAY_AVOID": {
        "title": "拖延规避",
        "summary": "暂时减压，但后续隐患会累积",
        "modifier": -1,
        "category": "回避策略",
        "tradeoff": "把现在的痛换成以后的雷。",
    },
    "SHIFT_BLAME": {
        "title": "转移责任",
        "summary": "短期脱身，但风险和污染上升",
        "modifier": 1,
        "category": "灰色操作",
        "tradeoff": "马上轻松一点，长期更脏也更危险。",
    },
    "RECOVERY_BREAK": {
        "title": "恢复自保",
        "summary": "恢复精力体力，但当回合绩效可能下降",
        "modifier": -2,
        "category": "保命恢复",
        "tradeoff": "主动回血，但会放弃眼前绩效。",
    },
    "BOUNDARY_RESTATE": {
        "title": "边界重申",
        "summary": "明确责任边界，避免后续扯皮",
        "modifier": 0,
        "category": "边界管理",
        "tradeoff": "收益不立刻爆发，但能压住连锁后果。",
    },
}

ACTION_OPTION_POLICY = {
    "core": ["DIRECT_EXECUTE", "EMAIL_TRACE", "NARROW_SCOPE", "SOFT_REFUSE"],
    "low_energy_bonus": "RECOVERY_BREAK",
    "default_bonus": "REQUEST_CONFIRMATION",
}

ACTION_MODIFIERS: dict[str, int] = {
    action_id: int(rule["modifier"])
    for action_id, rule in ACTION_RULES.items()
}

ACTION_DISPLAY: dict[str, dict[str, str]] = {
    action_id: {
        "title": str(rule["title"]),
        "summary": str(rule["summary"]),
    }
    for action_id, rule in ACTION_RULES.items()
}

STATUS_RULES: list[dict[str, str | int]] = [
    {"id": "STATUS_EXHAUSTED", "name": "濒临崩溃", "trigger": "EN < 10", "duration": 1, "impact": "判定严重受挫。"},
    {"id": "STATUS_LOW_EN", "name": "低精力", "trigger": "10 <= EN < 30", "duration": 1, "impact": "行动效率下降。"},
    {"id": "STATUS_LOW_ST", "name": "低体力", "trigger": "ST < 30", "duration": 1, "impact": "持续作业更容易翻车。"},
    {"id": "STATUS_LOW_KPI", "name": "危险绩效", "trigger": "KPI < 40", "duration": 1, "impact": "组织压力会继续抬头。"},
    {"id": "STATUS_HIGH_RISK", "name": "高风险", "trigger": "RISK >= 50", "duration": 1, "impact": "暴雷链条被放大。"},
    {"id": "STATUS_HIGH_COR", "name": "高污染", "trigger": "COR >= 50", "duration": 1, "impact": "政治型与灰色后果增强。"},
    {"id": "STATUS_UNDER_WATCH", "name": "被盯上", "trigger": "EVT_03 / EVT_11 / EVT_16", "duration": 2, "impact": "后续会继续收到敌意追击。"},
]

CHARACTER_WEIGHT_RULES: list[dict[str, str | float]] = [
    {
        "id": "TIME_PERIOD",
        "scope": "global",
        "label": "时间段修正",
        "condition": "按当前时间段读取角色权重表",
        "effect": "不同时段改变角色出现概率",
    },
    {
        "id": "REPEAT_DAMPING",
        "scope": "global",
        "label": "重复抑制",
        "condition": "若与上一回合是同一角色",
        "effect": "该角色权重乘以 0.45",
    },
    {
        "id": "HR_LOW_KPI",
        "scope": "character",
        "character_id": "CHR_04",
        "label": "绩效压迫",
        "condition": "KPI < 40",
        "effect": "HR 权重乘以 2.0",
    },
    {
        "id": "FINANCE_HIGH_RISK",
        "scope": "character",
        "character_id": "CHR_05",
        "label": "审计逼近",
        "condition": "RISK >= 50",
        "effect": "财务关键人权重乘以 1.6",
    },
    {
        "id": "DIRECTOR_HIGH_COR",
        "scope": "character",
        "character_id": "CHR_06",
        "label": "站队加压",
        "condition": "COR >= 50",
        "effect": "派系总监权重乘以 1.6",
    },
]

EVENT_HAZARD_MAP: dict[str, dict[str, str | int]] = {
    "EVT_04": {"id": "HZD_RESPONSIBILITY", "name": "责任未明确", "countdown": 3, "severity": 2},
    "EVT_06": {"id": "HZD_RESPONSIBILITY", "name": "责任未明确", "countdown": 3, "severity": 2},
    "EVT_07": {"id": "HZD_ORAL_PROMISE", "name": "口头承诺", "countdown": 2, "severity": 1},
    "EVT_08": {"id": "HZD_REQ_UNCONFIRMED", "name": "需求未确认", "countdown": 3, "severity": 1},
    "EVT_10": {"id": "HZD_ORAL_PROMISE", "name": "口头承诺", "countdown": 2, "severity": 1},
    "EVT_17": {"id": "HZD_BACKDATED_DOC", "name": "倒签文件", "countdown": 5, "severity": 2},
    "EVT_18": {"id": "HZD_MISSING_RECEIPT", "name": "报销缺材料", "countdown": 3, "severity": 1},
    "EVT_19": {"id": "HZD_COMPLIANCE", "name": "合规隐患", "countdown": 3, "severity": 2},
    "EVT_23": {"id": "HZD_WEEKLY_REPORT", "name": "周报未交", "countdown": 2, "severity": 1},
    "EVT_24": {"id": "HZD_UNREAD_MSG", "name": "未回消息", "countdown": 2, "severity": 1},
}

ACTION_HAZARD_MAP: dict[str, dict[str, str | int]] = {
    "SHIFT_BLAME": {"id": "HZD_ACTION_BLAME", "name": "甩锅痕迹", "countdown": 3, "severity": 1},
    "DELAY_AVOID": {"id": "HZD_ACTION_DELAY", "name": "拖延积压", "countdown": 2, "severity": 1},
}

DEFAULT_PROJECT: dict[str, str | int] = {
    "id": "PRJ_WEEKLY",
    "name": "本周交付",
    "progress": 0,
    "target": 5,
    "pressure": 2,
}

FAILURE_RULES: list[dict[str, str | int]] = [
    {"id": "HP_DEPLETED", "label": "崩溃结局", "condition": "HP <= 0", "priority": 1},
    {"id": "EN_DEPLETED", "label": "精神崩溃结局", "condition": "EN <= 0", "priority": 2},
    {"id": "ST_DEPLETED", "label": "体力耗尽结局", "condition": "ST <= 0", "priority": 3},
    {"id": "KPI_DEPLETED", "label": "被开除结局", "condition": "KPI <= 0", "priority": 4},
    {"id": "RISK_OVERFLOW", "label": "暴雷结局", "condition": "RISK >= 100", "priority": 5},
    {"id": "COR_OVERFLOW", "label": "黑化结局", "condition": "COR >= 100", "priority": 6},
]


def time_period_for_turn(turn_index: int) -> dict:
    """按回合数获取当前时间段定义。"""
    day_turn = turn_index % TURNS_PER_DAY
    for rule in TIME_PERIOD_RULES:
        if not bool(rule.get("enabled", True)):
            continue
        if int(rule["turn_start"]) <= day_turn <= int(rule["turn_end"]):
            return deepcopy(rule)
    return deepcopy(TIME_PERIOD_RULES[0])


def time_period_weight_modifiers(time_period: str) -> dict[str, float]:
    """获取指定时间段的角色权重修正表。"""
    for rule in TIME_PERIOD_RULES:
        if rule["id"] == time_period:
            return dict(rule.get("weight_modifiers", {}))
    return dict(TIME_PERIOD_RULES[0].get("weight_modifiers", {}))


def resolution_tier_for_score(score: int) -> dict:
    """按总分获取结算档位定义。"""
    for rule in RESOLUTION_TIER_RULES:
        if int(rule["min_score"]) <= score <= int(rule["max_score"]):
            return deepcopy(rule)
    return deepcopy(RESOLUTION_TIER_RULES[-1])


def default_project() -> dict:
    """返回一份可安全修改的默认项目对象。"""
    return deepcopy(DEFAULT_PROJECT)


def rules_catalog() -> dict:
    """导出可供外部系统消费的规则目录。"""
    return {
        "resources": deepcopy(RESOURCE_DEFINITIONS),
        "resource_order": list(RESOURCE_ORDER),
        "turns_per_day": TURNS_PER_DAY,
        "time_periods": deepcopy(TIME_PERIOD_RULES),
        "turn_flow": deepcopy(TURN_FLOW_STEPS),
        "settlement_order": deepcopy(SETTLEMENT_ORDER),
        "roll_triggers": deepcopy(ROLL_TRIGGER_SCENARIOS),
        "resolution_tiers": deepcopy(RESOLUTION_TIER_RULES),
        "actions": deepcopy(ACTION_RULES),
        "action_option_policy": deepcopy(ACTION_OPTION_POLICY),
        "statuses": deepcopy(STATUS_RULES),
        "character_weight_rules": deepcopy(CHARACTER_WEIGHT_RULES),
        "event_hazard_map": deepcopy(EVENT_HAZARD_MAP),
        "action_hazard_map": deepcopy(ACTION_HAZARD_MAP),
        "default_project": deepcopy(DEFAULT_PROJECT),
        "failure_rules": deepcopy(FAILURE_RULES),
    }
