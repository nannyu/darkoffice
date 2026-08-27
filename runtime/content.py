from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from runtime.rules import ACTION_DISPLAY, ACTION_MODIFIERS


# ---------------------------------------------------------------------------
# 新增：性格向量
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Personality:
    aggression: int = 50   # 攻击性 0-100
    ambition: int = 50     # 野心 0-100
    loyalty: int = 50      # 忠诚度 0-100
    cynicism: int = 50     # 犬儒程度 0-100
    greed: int = 50        # 贪婪度 0-100
    paranoia: int = 50     # 多疑度 0-100


# ---------------------------------------------------------------------------
# 新增：事件触发条件
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class EventPrerequisites:
    min_relation: Optional[int] = None
    max_relation: Optional[int] = None
    required_moods: list[str] = field(default_factory=list)
    required_status_tags: list[str] = field(default_factory=list)
    required_events: list[str] = field(default_factory=list)
    turn_min: int = 0
    turn_max: int = 999


# ---------------------------------------------------------------------------
# 扩展：角色卡
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Character:
    # === 原有字段（保留）===
    character_id: str
    name: str
    base_weight: int

    # === 叙事层（新增）===
    role_type: str = ""            # 施压者/同盟者/中立者/观察者/背叛者
    faction: str = ""              # 所属派系
    personality: Personality = field(default_factory=Personality)
    desires: list[str] = field(default_factory=list)
    fears: list[str] = field(default_factory=list)
    tagline: str = ""              # 标志性台词

    # === 动态层初始值（新增）===
    initial_relation: int = 0      # 对玩家初始关系 -100~+100
    initial_mood: str = "平静"      # 初始心情
    initial_trust: int = 50        # 初始信任
    initial_stress: int = 50       # 初始压力
    initial_power: int = 50        # 初始影响力
    hidden_stance: str = ""        # 隐藏立场

    # === 元数据 ===
    tags: list[str] = field(default_factory=list)
    speech_style: str = ""         # 说话风格标签
    portrait_prompt: str = ""      # AI生成立绘的prompt模板

    # === 向后兼容：旧字段保留 ===
    passive_effect: Optional[str] = None


# ---------------------------------------------------------------------------
# 新增：运行时角色动态状态
# ---------------------------------------------------------------------------
@dataclass
class CharacterState:
    character_id: str
    relation_to_player: int = 0
    mood: str = "平静"
    trust: int = 50
    stress: int = 50
    power: int = 50
    hidden_stance: str = ""


# ---------------------------------------------------------------------------
# 心情枚举（P1 硬编码）
# ---------------------------------------------------------------------------
VALID_MOODS = ["平静", "急躁", "阴沉", "得意", "恐慌", "冷漠"]


# ---------------------------------------------------------------------------
# 扩展：事件卡
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Event:
    # === 原有字段（保留）===
    event_id: str
    character_id: str
    name: str
    base_effect: dict[str, int]

    # === 叙事层（新增）===
    event_type: str = "施压"               # 诉求/恐惧/试探/求助/施压/情报/陷阱
    narrative_fn: str = ""                 # 渲染函数名（在 narrative_fns.py 中）
    prerequisites: EventPrerequisites = field(default_factory=EventPrerequisites)

    # === 连锁层（新增）===
    chain_id: str = ""                     # 所属事件链
    chain_position: int = 0                # 在链中的位置
    chain_delay: int = 0                   # 触发后延迟N回合

    # === 动态效果层（新增）===
    mood_modifiers: dict[str, dict] = field(default_factory=dict)
    relation_impact: dict[str, int] = field(default_factory=dict)

    # === 向后兼容：旧字段保留 ===
    event_category: Optional[str] = None
    pressure_level: Optional[str] = None
    tags: Optional[list[str]] = None
    flavor_text: Optional[str] = None
    possible_followups: Optional[list[str]] = None
    dice_dc: Optional[int] = None


# ---------------------------------------------------------------------------
# 新增：场景玩家选项
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SceneOption:
    option_id: str
    prototype: str                         # 引用策略原型ID
    label: str                             # 玩家看到的文本
    target_character: Optional[str] = None # 对谁使用
    visibility_condition: str = ""         # 显示条件，简单表达式
    custom_effect: dict[str, int] = field(default_factory=dict)
    sub_mode: Optional[str] = None         # 子模式（如PROBE的"主动/被动"）
    sort_priority: int = 0                 # 排序权重


# ---------------------------------------------------------------------------
# 新增：隐藏目标
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HiddenGoal:
    goal_id: str
    description: str = ""                  # 内部描述，不对玩家显示
    reward: dict = field(default_factory=dict)
    trigger_condition: str = ""            # 达成条件，简单表达式


# ---------------------------------------------------------------------------
# 新增：情报/把柄
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Intel:
    intel_id: str
    intel_type: str                        # leverage(把柄) / secret(秘密) / intel(情报)
    source_character: str                  # 从谁那里获得
    target_character: str                  # 针对谁（把柄的目标）
    description: str = ""                  # 描述文本
    discovery_condition: str = ""          # 发现条件（如 "PROBE_CHR_03_active"）
    usage_effect: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 新增：玩家笔记
# ---------------------------------------------------------------------------
@dataclass
class PlayerNotes:
    discovered_intel: list[str] = field(default_factory=list)           # 已发现的情报ID
    character_notes: dict[str, str] = field(default_factory=dict)       # 角色笔记 {char_id: note}
    hidden_stances_revealed: list[str] = field(default_factory=list)    # 已揭示隐藏立场的角色


# ---------------------------------------------------------------------------
# 新增：场景定义
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Scene:
    scene_id: str
    title: str
    time_periods: list[str] = field(default_factory=list)  # 可在哪些时段出现
    location: str = ""                     # 地点描述

    # 角色配置
    required_characters: list[str] = field(default_factory=list)
    optional_characters: list[str] = field(default_factory=list)
    inclusion_rules: dict[str, str] = field(default_factory=dict)
    exclusion_rules: dict[str, str] = field(default_factory=dict)
    max_characters: int = 4

    # 场景内容
    narrative_fn: str = ""                 # 渲染函数名
    player_options: list[SceneOption] = field(default_factory=list)
    hidden_goals: list[HiddenGoal] = field(default_factory=list)

    # 场景池标记
    scene_pool_tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# 新增：渲染后的角色台词
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RenderedLine:
    character_id: str
    speaker: str
    mood: str
    text: str
    subtext: str = ""                      # 叙事补充（如"他的语气不容置疑"）


# ---------------------------------------------------------------------------
# 新增：渲染后的场景
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class RenderedScene:
    opening: str = ""                      # 开场描述
    lines: list[RenderedLine] = field(default_factory=list)
    atmosphere: str = ""                   # 场景氛围描述
    options: list[SceneOption] = field(default_factory=list)
    hint: str = ""                         # 下回合提示


# ---------------------------------------------------------------------------
# 新增：场景结算结果
# ---------------------------------------------------------------------------
@dataclass
class SceneResult:
    player_delta: dict[str, int] = field(default_factory=dict)
    relation_changes: dict[str, int] = field(default_factory=dict)
    character_state_changes: dict[str, dict] = field(default_factory=dict)
    new_statuses: list[dict] = field(default_factory=list)
    new_hazards: list[dict] = field(default_factory=list)
    hidden_goals_achieved: list[str] = field(default_factory=list)
    next_turn_hint: str = ""
    chain_progress: Optional[dict] = None
    act_advanced: bool = False
    ending_triggered: Optional[str] = None


# ---------------------------------------------------------------------------
# 角色立体化定义（Phase 2）
# ---------------------------------------------------------------------------

CHR_CHEN = Character(
    character_id="CHR_01",
    name="陈总监",
    base_weight=20,
    role_type="施压者",
    faction="陈派",
    personality=Personality(
        aggression=75, ambition=80, loyalty=30,
        cynicism=70, greed=60, paranoia=55,
    ),
    desires=["升职为VP", "控制整个部门", "项目成功上线但自己不承担风险"],
    fears=["被派系总监取代", "项目失败被问责", "手下人抱团反抗"],
    tagline="这个阶段大家都不容易。",
    initial_relation=-10,
    initial_mood="平静",
    initial_trust=40,
    initial_stress=60,
    initial_power=70,
    hidden_stance="表面强势，内心焦虑，害怕被高层替换",
    speech_style="先扬后抑，把压力包装成关心",
)

CHR_XIAOLIN = Character(
    character_id="CHR_02",
    name="小林",
    base_weight=18,
    role_type="背叛者",
    faction="无派系",
    personality=Personality(
        aggression=30, ambition=65, loyalty=20,
        cynicism=80, greed=50, paranoia=40,
    ),
    desires=["少干活多拿钱", "巴结陈总监上位", "把责任推给别人"],
    fears=["工作量增加", "被团队孤立", "陈总监失势"],
    tagline="你顺手帮我处理一下。",
    initial_relation=5,
    initial_mood="平静",
    initial_trust=30,
    initial_stress=40,
    initial_power=30,
    hidden_stance="谁强跟谁，随时准备跳船",
    speech_style="装可怜、打感情牌、事后装无辜",
)

CHR_CLIENT = Character(
    character_id="CHR_03",
    name="甲方金主",
    base_weight=15,
    role_type="施压者",
    faction="甲方公司",
    personality=Personality(
        aggression=70, ambition=60, loyalty=40,
        cynicism=50, greed=70, paranoia=45,
    ),
    desires=["项目按时交付", "少花钱多办事", "向上级展示控制力"],
    fears=["项目延期影响自己KPI", "被供应商坑", "上级质疑管理能力"],
    tagline="需求先做了再确认。",
    initial_relation=-5,
    initial_mood="急躁",
    initial_trust=35,
    initial_stress=55,
    initial_power=65,
    hidden_stance="自己对需求也不清楚，靠变更来掩盖决策失误",
    speech_style="命令式、频繁变更需求、事后否认",
)

CHR_HR = Character(
    character_id="CHR_04",
    name="HR笑面虎",
    base_weight=10,
    role_type="观察者",
    faction="公司管理层",
    personality=Personality(
        aggression=40, ambition=75, loyalty=60,
        cynicism=85, greed=55, paranoia=70,
    ),
    desires=["维持团队表面稳定", "收集员工黑料", "裁员时掌握主动权"],
    fears=["员工集体抗议", "自己被人事斗争波及", "劳动仲裁"],
    tagline="来聊聊最近的状态。",
    initial_relation=0,
    initial_mood="得意",
    initial_trust=50,
    initial_stress=35,
    initial_power=55,
    hidden_stance="公司利益第一，谁好用保谁，谁麻烦裁谁",
    speech_style="亲切开场，突然试探，永远不说真话",
)

CHR_FINANCE = Character(
    character_id="CHR_05",
    name="财务关键人",
    base_weight=12,
    role_type="中立者",
    faction="财务系",
    personality=Personality(
        aggression=25, ambition=50, loyalty=55,
        cynicism=60, greed=65, paranoia=80,
    ),
    desires=["账目平掉", "不被审计盯上", "掌握关键签字权"],
    fears=["审计出问题", "被当成替罪羊", "签字权被收回"],
    tagline="先倒签一下。",
    initial_relation=0,
    initial_mood="阴沉",
    initial_trust=45,
    initial_stress=50,
    initial_power=45,
    hidden_stance="知道很多黑幕，但选择装糊涂自保",
    speech_style="谨慎、留后路、每句话都给自己留台阶",
)

CHR_RIVAL = Character(
    character_id="CHR_06",
    name="派系总监",
    base_weight=8,
    role_type="同盟者",
    faction="李派",
    personality=Personality(
        aggression=55, ambition=85, loyalty=40,
        cynicism=65, greed=70, paranoia=60,
    ),
    desires=["扳倒陈总监", "拉拢玩家站队", "扩大自己派系"],
    fears=["被陈总监先发制人", "拉拢失败暴露意图", "高层不喜欢派系斗争"],
    tagline="你支持哪个方案？",
    initial_relation=10,
    initial_mood="平静",
    initial_trust=40,
    initial_stress=45,
    initial_power=60,
    hidden_stance="积极拉拢玩家，但也会随时牺牲棋子",
    speech_style="试探性强、话里有话、擅长暗示",
)

CHARACTERS: list[Character] = [
    CHR_CHEN, CHR_XIAOLIN, CHR_CLIENT,
    CHR_HR, CHR_FINANCE, CHR_RIVAL,
]

CHARACTER_NAME_MAP: dict[str, str] = {c.character_id: c.name for c in CHARACTERS}


# ---------------------------------------------------------------------------
# 原有内置事件（保留，新字段用默认值）
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Phase 3: 全局情报池（把柄 / 秘密 / 情报）
# ---------------------------------------------------------------------------
INTEL_POOL: list[Intel] = [
    # ===== 把柄类（解锁 THREATEN） =====
    Intel(
        intel_id="INTEL_CHEN_PANIC",
        intel_type="leverage",
        source_character="CHR_01",
        target_character="CHR_01",
        description="陈总监在压力下多次情绪失控，曾经当众摔过文件夹",
        discovery_condition="scene_has_CHR_01 and PROBE_passive and stress_CHR_01>70",
        tags=["情绪失控", "公开记录"],
    ),
    Intel(
        intel_id="INTEL_XIAOLIN_SHIRK",
        intel_type="leverage",
        source_character="CHR_02",
        target_character="CHR_02",
        description="小林过去三个月至少推掉了5项任务给其他人，有邮件记录",
        discovery_condition="scene==SCENE_LUNCH_PUSH and DOCUMENT",
        tags=["推活", "书面证据"],
    ),
    Intel(
        intel_id="INTEL_CLIENT_CHANGE",
        intel_type="leverage",
        source_character="CHR_03",
        target_character="CHR_03",
        description="甲方过去两周变更了7次需求，每次都在邮件里说是'最后确认'",
        discovery_condition="scene_has_CHR_03 and DOCUMENT",
        tags=["需求变更", "邮件链"],
    ),
    Intel(
        intel_id="INTEL_FINANCE_BACKDATE",
        intel_type="leverage",
        source_character="CHR_05",
        target_character="CHR_05",
        description="财务曾在群里说'先倒签，后面补手续'，聊天记录还在",
        discovery_condition="scene_has_CHR_05 and PROBE and turn>5",
        tags=["倒签", "聊天记录"],
    ),
    # ===== 秘密类 =====
    Intel(
        intel_id="INTEL_CHEN_RIVAL_FEAR",
        intel_type="secret",
        source_character="CHR_01",
        target_character="CHR_01",
        description="陈总监私下跟人说过，他最怕的就是派系总监上位",
        discovery_condition="scene==SCENE_BOSS_PRIVATE_TALK and PROBE_active and trust_CHR_01>30",
        tags=["派系斗争", "恐惧"],
    ),
    Intel(
        intel_id="INTEL_HR_WATCHLIST",
        intel_type="secret",
        source_character="CHR_04",
        target_character="ALL",
        description="HR 维护着一份'重点关注员工'名单，上面有评分",
        discovery_condition="scene==SCENE_WATERCOOLER_GOSSIP and PROBE_passive",
        tags=["监控", "名单"],
    ),
    Intel(
        intel_id="INTEL_RIVAL_RECRUIT",
        intel_type="secret",
        source_character="CHR_06",
        target_character="CHR_06",
        description="派系总监最近在逐个约谈团队成员，试图挖角",
        discovery_condition="scene_has_CHR_06 and PROBE",
        tags=["挖角", "派系扩张"],
    ),
    # ===== 情报类 =====
    Intel(
        intel_id="INTEL_PROJECT_REAL_DEADLINE",
        intel_type="intel",
        source_character="CHR_03",
        target_character="CHR_03",
        description="甲方真正的 deadline 其实还有三周，'下周'只是施压手段",
        discovery_condition="scene==SCENE_PROGRESS_REPORT and PROBE_active",
        tags=["deadline", "施压手段"],
    ),
    Intel(
        intel_id="INTEL_AUDIT_DATE",
        intel_type="intel",
        source_character="CHR_05",
        target_character="ALL",
        description="审计定在下个月15号，财务已经开始准备了",
        discovery_condition="scene_has_CHR_05 and turn>3",
        tags=["审计", "时间"],
    ),
]

INTEL_BY_TARGET: dict[str, list[Intel]] = {}
for intel in INTEL_POOL:
    INTEL_BY_TARGET.setdefault(intel.target_character, []).append(intel)

INTEL_BY_ID: dict[str, Intel] = {i.intel_id: i for i in INTEL_POOL}
