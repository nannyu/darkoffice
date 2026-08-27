"""场景库。

职责：
1. 定义所有场景（Scene 实例）
2. 定义时段场景池映射
3. 提供场景查询接口
"""

from __future__ import annotations

from runtime.content import HiddenGoal, Scene, SceneOption


# ---------------------------------------------------------------------------
# 场景定义
# ---------------------------------------------------------------------------

SCENE_REVIEW_MEETING = Scene(
    scene_id="SCENE_REVIEW_MEETING",
    title="项目评审会",
    time_periods=["下午"],
    location="大会议室",
    required_characters=["CHR_01"],
    optional_characters=["CHR_02", "CHR_05"],
    inclusion_rules={
        "CHR_02": "relation>-50",           # 小林和陈总监关系不太差才会来
        "CHR_05": "budget_involved==true",  # 涉及预算才会出现财务
    },
    max_characters=4,
    narrative_fn="render_review_meeting",
    player_options=[
        SceneOption(
            option_id="OPT_ASSERT_DETAIL",
            prototype="ASSERT",
            label="我来补充技术细节",
            target_character="CHR_01",
            custom_effect={"kpi": +2},
        ),
        SceneOption(
            option_id="OPT_DOCUMENT_BUDGET",
            prototype="DOCUMENT",
            label="预算问题我可以解释",
            target_character="CHR_05",
            custom_effect={"kpi": 0},
        ),
        SceneOption(
            option_id="OPT_EVADE_PHASE2",
            prototype="EVADE",
            label="我建议小功能放到二期",
            target_character="CHR_03",
            visibility_condition="turn>5",
            custom_effect={"kpi": -1},
        ),
        SceneOption(
            option_id="OPT_PROBE_CHEN",
            prototype="PROBE",
            label="试探陈总监的真实态度",
            target_character="CHR_01",
            sub_mode="passive",
            custom_effect={"en": -5, "risk": +1},
        ),
        SceneOption(
            option_id="OPT_CHARM_CHEN",
            prototype="CHARM",
            label="会后单独向陈总监汇报进展",
            target_character="CHR_01",
            visibility_condition="relation>-20",
            custom_effect={"relation": +5, "en": -5, "cor": +2},
        ),
        SceneOption(
            option_id="OPT_DEFLECT_XIAOLIN",
            prototype="DEFLECT",
            label="小林对这块更熟悉，让他补充",
            target_character="CHR_02",
            custom_effect={"cor": +3},
        ),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_SPLIT_CHEN_XIAOLIN",
            description="让陈总监和小林在会上公开分歧",
            reward={"relation_with_CHR_06": +10},
            trigger_condition="CHR_01.mood=='急躁' and CHR_02.mood=='懒散'",
        ),
    ],
    scene_pool_tags=["正式会议", "项目评审"],
)

SCENE_LATE_NIGHT_ALONE = Scene(
    scene_id="SCENE_LATE_NIGHT_ALONE",
    title="深夜独处",
    time_periods=["深夜"],
    location="工位",
    required_characters=[],
    max_characters=1,
    narrative_fn="render_late_night_alone",
    player_options=[
        SceneOption(option_id="OPT_ALONE_WORK", prototype="ASSERT", label="继续加班，把今天的工作收尾", custom_effect={"kpi": +3, "en": -15, "st": -10}),
        SceneOption(option_id="OPT_ALONE_PROBE", prototype="PROBE", label="翻看一下同事们的邮件往来", sub_mode="passive", custom_effect={"en": -5, "risk": +2}),
        SceneOption(option_id="OPT_ALONE_RECOVER", prototype="RECOVER", label="关灯，趴在桌上眯一会儿", custom_effect={"en": +15, "st": +10}),
        SceneOption(option_id="OPT_ALONE_GRAY", prototype="DEFLECT", label="把一份文件日期往前改了一天", visibility_condition="turn>5", custom_effect={"risk": +10, "cor": +5, "kpi": +2}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_ALONE_RESIST",
            description="深夜独处时连续3次选择休息，不做任何灰色操作",
            reward={"risk": -10, "st": +15},
            trigger_condition="consecutive_recover_night>=3",
        ),
        HiddenGoal(
            goal_id="GOAL_ALONE_SNOOP",
            description="深夜独处时通过PROBE获取至少3条情报",
            reward={"risk": -5, "cor": +3},
            trigger_condition="night_intel_count>=3",
        ),
    ],
    scene_pool_tags=["独处", "灰色操作"],
)


# ==================== 早晨场景 ====================

SCENE_MORNING_MEETING = Scene(
    scene_id="SCENE_MORNING_MEETING",
    title="部门晨会",
    time_periods=["早晨"],
    location="小会议室",
    required_characters=["CHR_01"],
    optional_characters=["CHR_02", "CHR_06"],
    inclusion_rules={
        "CHR_02": "relation>-30",
        "CHR_06": "turn>3",
    },
    max_characters=4,
    narrative_fn="render_morning_meeting",
    player_options=[
        SceneOption(option_id="OPT_MORNING_ASSERT", prototype="ASSERT", label="主动汇报昨晚的进展", target_character="CHR_01", custom_effect={"kpi": +3, "en": -5}),
        SceneOption(option_id="OPT_MORNING_DOCUMENT", prototype="DOCUMENT", label="把昨晚的工作记录发到群里", custom_effect={"risk": -3}),
        SceneOption(option_id="OPT_MORNING_EVADE", prototype="EVADE", label="低头看手机， hoping 不被点名", custom_effect={"kpi": -2}),
        SceneOption(option_id="OPT_MORNING_PROBE", prototype="PROBE", label="观察陈总监对谁皱了眉头", sub_mode="passive", custom_effect={"en": -3}),
        SceneOption(option_id="OPT_MORNING_CHARM", prototype="CHARM", label="会后给陈总监带杯咖啡", target_character="CHR_01", visibility_condition="relation>-10", custom_effect={"relation": +8, "en": -5, "cor": +2}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_MORNING_CALM",
            description="晨会上让陈总监心情从急躁恢复为平静",
            reward={"relation_with_CHR_01": +10, "st": +5},
            trigger_condition="CHR_01.mood=='平静' and prev_mood_CHR_01=='急躁'",
        ),
        HiddenGoal(
            goal_id="GOAL_MORNING_STAR",
            description="晨会上连续3次ASSERT获得陈总监认可",
            reward={"kpi": +5, "cor": +3},
            trigger_condition="consecutive_morning_assert>=3",
        ),
    ],
    scene_pool_tags=["晨会", "正式"],
)

SCENE_BOSS_DROP_BY = Scene(
    scene_id="SCENE_BOSS_DROP_BY",
    title="上司查岗",
    time_periods=["早晨"],
    location="你的工位",
    required_characters=["CHR_01"],
    max_characters=2,
    narrative_fn="render_boss_drop_by",
    player_options=[
        SceneOption(option_id="OPT_DROP_ASSERT", prototype="ASSERT", label="立刻打开项目文档，汇报当前进度", target_character="CHR_01", custom_effect={"kpi": +2, "en": -3}),
        SceneOption(option_id="OPT_DROP_DOCUMENT", prototype="DOCUMENT", label="把昨晚的邮件记录翻出来给他看", target_character="CHR_01", custom_effect={"risk": -5, "relation": -3}),
        SceneOption(option_id="OPT_DROP_CHARM", prototype="CHARM", label="笑着说'总监您来得正好，有个问题想请教'", target_character="CHR_01", custom_effect={"relation": +5, "en": -3}),
        SceneOption(option_id="OPT_DROP_EVADE", prototype="EVADE", label="假装在接电话，让他等一会儿", custom_effect={"kpi": -3, "risk": +2}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_DROP_CHARMED",
            description="查岗时用CHARM让陈总监关系提升到30以上",
            reward={"relation_with_CHR_01": +5, "cor": +3},
            trigger_condition="relation_with_CHR_01>30 and last_action=='CHARM'",
        ),
        HiddenGoal(
            goal_id="GOAL_DROP_PERFECT",
            description="查岗时既不逃避也不讨好，只用ASSERT或DOCUMENT应对",
            reward={"kpi": +3, "risk": -3},
            trigger_condition="boss_drop_perfect_count>=3",
        ),
    ],
    scene_pool_tags=["查岗", "突发"],
)

SCENE_PROGRESS_REPORT = Scene(
    scene_id="SCENE_PROGRESS_REPORT",
    title="项目进度汇报",
    time_periods=["早晨"],
    location="总监办公室",
    required_characters=["CHR_01", "CHR_03"],
    optional_characters=["CHR_05"],
    inclusion_rules={"CHR_05": "turn>5"},
    max_characters=4,
    narrative_fn="render_progress_report",
    player_options=[
        SceneOption(option_id="OPT_REPORT_ASSERT", prototype="ASSERT", label="承诺本周一定完成", target_character="CHR_01", custom_effect={"kpi": +4, "risk": +5}),
        SceneOption(option_id="OPT_REPORT_DOCUMENT", prototype="DOCUMENT", label="把目前的阻塞问题列成清单，要求书面确认", target_character="CHR_03", custom_effect={"risk": -8, "relation": -5}),
        SceneOption(option_id="OPT_REPORT_DEFLECT", prototype="DEFLECT", label="指出甲方的需求变更导致进度延迟", target_character="CHR_03", custom_effect={"cor": +5, "risk": +10}),
        SceneOption(option_id="OPT_REPORT_TRADE", prototype="TRADE", label="提议加人换时间，双方各退一步", custom_effect={"relation": +3, "en": -4}),
        SceneOption(option_id="OPT_REPORT_PROBE", prototype="PROBE", label="试探甲方真正的 deadline 是什么", target_character="CHR_03", sub_mode="active", custom_effect={"en": -5, "risk": +1}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_REPORT_DEADLINE",
            description="让甲方在汇报中主动提出延期",
            reward={"kpi": +3, "risk": -5, "relation_with_CHR_03": +5},
            trigger_condition="client_proposed_delay==true",
        ),
        HiddenGoal(
            goal_id="GOAL_REPORT_CLEAN",
            description="汇报中不甩锅、不承诺、只用DOCUMENT和TRADE应对",
            reward={"risk": -5, "st": +5},
            trigger_condition="report_clean_count>=3",
        ),
    ],
    scene_pool_tags=["汇报", "甲方"],
)


# ==================== 中午场景 ====================

SCENE_CAFE_ENCOUNTER = Scene(
    scene_id="SCENE_CAFE_ENCOUNTER",
    title="食堂偶遇",
    time_periods=["中午"],
    location="公司食堂",
    required_characters=[],
    optional_characters=["CHR_02", "CHR_04", "CHR_06"],
    inclusion_rules={
        "CHR_02": "relation>-40",
        "CHR_04": "turn>2",
        "CHR_06": "turn>5",
    },
    max_characters=3,
    narrative_fn="render_cafe_encounter",
    player_options=[
        SceneOption(option_id="OPT_CAFE_PROBE", prototype="PROBE", label="边吃边听他们的对话", sub_mode="passive", custom_effect={"en": -3, "risk": +1}),
        SceneOption(option_id="OPT_CAFE_CHARM", prototype="CHARM", label="主动坐过去，请他们喝饮料", custom_effect={"en": -2, "relation": +5, "cor": +2}),
        SceneOption(option_id="OPT_CAFE_EVADE", prototype="EVADE", label="端着饭去角落吃", custom_effect={"en": +3}),
        SceneOption(option_id="OPT_CAFE_ALLY", prototype="ALLY", label="附和其中一方的观点", visibility_condition="turn>3", custom_effect={"risk": +5, "cor": +3}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_CAFE_INTEL",
            description="食堂偶遇时通过PROBE获取至少2条有价值情报",
            reward={"risk": -5, "cor": +2},
            trigger_condition="cafe_intel_count>=2",
        ),
        HiddenGoal(
            goal_id="GOAL_CAFE_PEACEMAKER",
            description="在食堂偶遇中成功让两个对立角色同时保持平静心情",
            reward={"st": +10, "relation_with_CHR_02": +5, "relation_with_CHR_04": +5},
            trigger_condition="cafe_peace_made==true",
        ),
    ],
    scene_pool_tags=["食堂", "社交"],
)

SCENE_WATERCOOLER_GOSSIP = Scene(
    scene_id="SCENE_WATERCOOLER_GOSSIP",
    title="茶水间八卦",
    time_periods=["中午"],
    location="茶水间",
    required_characters=["CHR_04"],
    optional_characters=["CHR_02"],
    inclusion_rules={"CHR_02": "relation>-20"},
    max_characters=3,
    narrative_fn="render_watercooler_gossip",
    player_options=[
        SceneOption(option_id="OPT_WATER_PROBE", prototype="PROBE", label="假装倒水，偷听他们在说什么", sub_mode="passive", custom_effect={"en": -3, "risk": +1}),
        SceneOption(option_id="OPT_WATER_CHARM", prototype="CHARM", label="笑着加入：'聊什么呢这么开心'", target_character="CHR_04", custom_effect={"relation": +5, "en": -3, "cor": +2}),
        SceneOption(option_id="OPT_WATER_ALLY", prototype="ALLY", label="顺着 HR 的话说，表示认同", target_character="CHR_04", custom_effect={"relation": +8, "risk": +3}),
        SceneOption(option_id="OPT_WATER_EVADE", prototype="EVADE", label="接完水立刻离开", custom_effect={"en": +2}),
        SceneOption(option_id="OPT_WATER_DOCUMENT", prototype="DOCUMENT", label="记住他们说的话，以备后用", custom_effect={"risk": -2, "cor": +2}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_WATER_INTEL",
            description="在茶水间八卦中通过被动PROBE获取HR的隐藏信息",
            reward={"risk": -5, "cor": +3},
            trigger_condition="water_intel_unlocked==true",
        ),
        HiddenGoal(
            goal_id="GOAL_WATER_BEFRIEND",
            description="连续3次茶水间八卦选择CHARM或ALLY，与HR建立良好关系",
            reward={"relation_with_CHR_04": +10, "st": +5},
            trigger_condition="water_befriend_count>=3",
        ),
    ],
    scene_pool_tags=["茶水间", "情报"],
)

SCENE_LUNCH_PUSH = Scene(
    scene_id="SCENE_LUNCH_PUSH",
    title="午休推活",
    time_periods=["中午"],
    location="走廊",
    required_characters=["CHR_02"],
    max_characters=2,
    narrative_fn="render_lunch_push",
    player_options=[
        SceneOption(option_id="OPT_LUNCH_ASSERT", prototype="ASSERT", label="答应下来，但要求书面确认", target_character="CHR_02", custom_effect={"kpi": +1, "risk": -3}),
        SceneOption(option_id="OPT_LUNCH_DEFLECT", prototype="DEFLECT", label="说陈总监已经给你安排了别的活", target_character="CHR_02", custom_effect={"cor": +3}),
        SceneOption(option_id="OPT_LUNCH_TRADE", prototype="TRADE", label="可以帮他，但下个项目他得帮你", target_character="CHR_02", custom_effect={"relation": +3, "en": -4, "cor": +2}),
        SceneOption(option_id="OPT_LUNCH_EVADE", prototype="EVADE", label="说你要去开会，回头再说", custom_effect={"kpi": -1}),
        SceneOption(option_id="OPT_LUNCH_DOCUMENT", prototype="DOCUMENT", label="当场发邮件确认分工", target_character="CHR_02", custom_effect={"risk": -5, "relation": -5}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_LUNCH_REFUSE",
            description="成功拒绝推活且不破裂关系（relation保持-30以上）",
            reward={"en": +5, "st": +5},
            trigger_condition="lunch_refuse_count>=3 and relation_with_CHR_02>-30",
        ),
        HiddenGoal(
            goal_id="GOAL_LUNCH_TRAPPER",
            description="通过DOCUMENT留下小林推活的书面证据，累计3次",
            reward={"cor": +5, "risk": -5},
            trigger_condition="lunch_document_count>=3",
        ),
    ],
    scene_pool_tags=["推活", "小林"],
)


# ==================== 晚上场景 ====================

SCENE_OVERTIME_CRUNCH = Scene(
    scene_id="SCENE_OVERTIME_CRUNCH",
    title="临时加班",
    time_periods=["晚上"],
    location="办公室",
    required_characters=["CHR_01"],
    optional_characters=["CHR_03"],
    inclusion_rules={"CHR_03": "turn>7"},
    max_characters=3,
    narrative_fn="render_overtime_crunch",
    player_options=[
        SceneOption(option_id="OPT_OT_ASSERT", prototype="ASSERT", label="留下加班，全力赶进度", target_character="CHR_01", custom_effect={"kpi": +5, "en": -20, "st": -15}),
        SceneOption(option_id="OPT_OT_DOCUMENT", prototype="DOCUMENT", label="问陈总监要书面加班确认", target_character="CHR_01", custom_effect={"risk": -5, "relation": -8}),
        SceneOption(option_id="OPT_OT_EVADE", prototype="EVADE", label="说家里有事，能不能明天再做", target_character="CHR_01", custom_effect={"kpi": -5, "relation": -5}),
        SceneOption(option_id="OPT_OT_TRADE", prototype="TRADE", label="答应加班，但要求调休", target_character="CHR_01", custom_effect={"relation": +5, "en": -6, "cor": +2}),
        SceneOption(option_id="OPT_OT_CHARM", prototype="CHARM", label="主动提出帮陈总监一起盯进度", target_character="CHR_01", custom_effect={"en": -10, "relation": +10}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_OT_HERO",
            description="连续3次加班场景选择留下（ASSERT/TRADE/CHARM），成为'加班英雄'",
            reward={"kpi": +5, "cor": +3, "relation_with_CHR_01": +10},
            trigger_condition="consecutive_overtime_count>=3",
        ),
        HiddenGoal(
            goal_id="GOAL_OT_ESCAPE",
            description="连续3次成功拒绝加班且不被记过",
            reward={"en": +10, "st": +10, "cor": +5},
            trigger_condition="consecutive_overtime_evade>=3",
        ),
    ],
    scene_pool_tags=["加班", "紧急"],
)

SCENE_LATE_EMAIL = Scene(
    scene_id="SCENE_LATE_EMAIL",
    title="深夜邮件",
    time_periods=["晚上"],
    location="工位",
    required_characters=["CHR_03"],
    max_characters=2,
    narrative_fn="render_late_email",
    player_options=[
        SceneOption(option_id="OPT_EMAIL_ASSERT", prototype="ASSERT", label="立刻回复：今晚就改", target_character="CHR_03", custom_effect={"kpi": +3, "en": -15}),
        SceneOption(option_id="OPT_EMAIL_DOCUMENT", prototype="DOCUMENT", label="回复邮件确认需求变更，抄送陈总监", target_character="CHR_03", custom_effect={"risk": -8, "cor": +2}),
        SceneOption(option_id="OPT_EMAIL_EVADE", prototype="EVADE", label="假装没看到，明天再回", custom_effect={"kpi": -3, "risk": +5}),
        SceneOption(option_id="OPT_EMAIL_TRADE", prototype="TRADE", label="回复：可以改，但 deadline 要延后", target_character="CHR_03", custom_effect={"relation": +3, "en": -4}),
        SceneOption(option_id="OPT_EMAIL_THREATEN", prototype="THREATEN", label="回复：这是第三次变更了，请书面确认", target_character="CHR_03", visibility_condition="turn>10", custom_effect={"relation": -10, "risk": +5}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_EMAIL_PAPER_TRAIL",
            description="深夜邮件场景中连续3次使用DOCUMENT留痕",
            reward={"risk": -10, "cor": +5},
            trigger_condition="email_document_count>=3",
        ),
        HiddenGoal(
            goal_id="GOAL_EMAIL_STAND",
            description="深夜邮件中首次对甲方使用THREATEN且不被报复",
            reward={"relation_with_CHR_03": +5, "st": +10},
            trigger_condition="email_first_threaten_survived==true",
        ),
    ],
    scene_pool_tags=["邮件", "甲方"],
)

SCENE_BOSS_PRIVATE_TALK = Scene(
    scene_id="SCENE_BOSS_PRIVATE_TALK",
    title="上司私下谈话",
    time_periods=["晚上"],
    location="楼梯间",
    required_characters=["CHR_01"],
    max_characters=2,
    narrative_fn="render_boss_private_talk",
    player_options=[
        SceneOption(option_id="OPT_TALK_PROBE", prototype="PROBE", label="问他：'总监，是不是出什么事了？'", target_character="CHR_01", sub_mode="active", custom_effect={"en": -5, "risk": +1}),
        SceneOption(option_id="OPT_TALK_CHARM", prototype="CHARM", label="表忠心：'有什么需要我做的，您直说'", target_character="CHR_01", custom_effect={"relation": +10, "en": -5, "cor": +3}),
        SceneOption(option_id="OPT_TALK_ASSERT", prototype="ASSERT", label="直接问：是不是有人在背后说我", target_character="CHR_01", custom_effect={"relation": -5}),
        SceneOption(option_id="OPT_TALK_ALLY", prototype="ALLY", label="暗示你知道一些事，愿意跟他分享", target_character="CHR_01", custom_effect={"cor": +3, "risk": +2}),
        SceneOption(option_id="OPT_TALK_EVADE", prototype="EVADE", label="打哈哈：'总监您太客气了，我先去忙了'", target_character="CHR_01", custom_effect={"relation": -3}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_TALK_TRUSTED",
            description="私下谈话中陈总监信任提升到60以上",
            reward={"relation_with_CHR_01": +10, "cor": +5},
            trigger_condition="trust_CHR_01>=60 and last_scene=='SCENE_BOSS_PRIVATE_TALK'",
        ),
        HiddenGoal(
            goal_id="GOAL_TALK_INSIDER",
            description="连续3次私下谈话选择PROBE，获取陈总监的隐藏情报",
            reward={"cor": +5, "risk": -5},
            trigger_condition="talk_probe_count>=3",
        ),
    ],
    scene_pool_tags=["私下", "谈话"],
)


# ==================== 深夜场景 ====================

SCENE_GRAY_ACTION = Scene(
    scene_id="SCENE_GRAY_ACTION",
    title="灰色操作",
    time_periods=["深夜"],
    location="空无一人的办公室",
    required_characters=[],
    max_characters=1,
    narrative_fn="render_gray_action",
    player_options=[
        SceneOption(option_id="OPT_GRAY_BACKDATE", prototype="DEFLECT", label="把之前的文件倒签日期", custom_effect={"risk": +15, "cor": +8, "kpi": +3}),
        SceneOption(option_id="OPT_GRAY_FAKE_DATA", prototype="DEFLECT", label="修改报表数据，让进度看起来正常", custom_effect={"risk": +20, "cor": +10, "kpi": +5}),
        SceneOption(option_id="OPT_GRAY_CONTACT", prototype="PROBE", label="搜索猎头的联系方式", sub_mode="active", custom_effect={"en": -3, "risk": +2}),
        SceneOption(option_id="OPT_GRAY_RECOVER", prototype="RECOVER", label="什么都不做，趴桌上睡觉", custom_effect={"en": +20, "st": +15}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_GRAY_CLEAN",
            description="深夜灰色操作场景中连续3次选择不做任何违规操作",
            reward={"risk": -15, "cor": -5, "st": +10},
            trigger_condition="gray_clean_count>=3",
        ),
        HiddenGoal(
            goal_id="GOAL_GRAY_DOUBLE_AGENT",
            description="在灰色操作中累计5次使用PROBE搜索外部信息",
            reward={"cor": +5, "risk": -5},
            trigger_condition="gray_probe_count>=5",
        ),
    ],
    scene_pool_tags=["灰色", "独处"],
)

SCENE_CONTACT_EXTERNAL = Scene(
    scene_id="SCENE_CONTACT_EXTERNAL",
    title="联系外部",
    time_periods=["深夜"],
    location="公司楼下",
    required_characters=[],
    max_characters=1,
    narrative_fn="render_contact_external",
    player_options=[
        SceneOption(option_id="OPT_EXT_HUNTER", prototype="PROBE", label="给猎头发消息，了解市场行情", sub_mode="active", custom_effect={"en": -3, "risk": +1}),
        SceneOption(option_id="OPT_EXT_FRIEND", prototype="CHARM", label="请前同事吃饭，打听内部消息", custom_effect={"en": -5, "risk": -3, "cor": +2}),
        SceneOption(option_id="OPT_EXT_RECOVER", prototype="RECOVER", label="回家睡觉，明天再说", custom_effect={"en": +25, "st": +20}),
        SceneOption(option_id="OPT_EXT_DOCUMENT", prototype="DOCUMENT", label="整理自己的工作成果，备份到个人云盘", custom_effect={"risk": -5, "cor": +2}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_EXT_NETWORK",
            description="深夜联系外部时累计3次使用PROBE获取市场情报",
            reward={"risk": -5, "cor": +3},
            trigger_condition="ext_probe_intel_count>=3",
        ),
        HiddenGoal(
            goal_id="GOAL_EXT_EXIT_PLAN",
            description="同时建立了猎头联系和前同事关系（各至少1次）",
            reward={"en": +5, "st": +5, "cor": +5},
            trigger_condition="ext_hunter_count>=1 and ext_friend_count>=1",
        ),
    ],
    scene_pool_tags=["外部", "退路"],
)


# ==================== Boss 战场景 ====================

SCENE_BOSS_FIRST_REVIEW = Scene(
    scene_id="SCENE_BOSS_FIRST_REVIEW",
    title="【Boss战】首次项目评审",
    time_periods=["下午"],
    location="大会议室，气氛凝重",
    required_characters=["CHR_01", "CHR_03"],
    optional_characters=["CHR_05"],
    inclusion_rules={"CHR_05": "turn>5"},
    max_characters=4,
    narrative_fn="render_boss_first_review",
    player_options=[
        SceneOption(option_id="OPT_BOSS1_ASSERT", prototype="ASSERT", label="承诺按时交付，承担风险", target_character="CHR_01", custom_effect={"kpi": +8, "risk": +10, "en": -15}),
        SceneOption(option_id="OPT_BOSS1_DEFLECT", prototype="DEFLECT", label="指出甲方变更导致延期", target_character="CHR_03", custom_effect={"cor": +8, "risk": +5, "relation": -10}),
        SceneOption(option_id="OPT_BOSS1_TRADE", prototype="TRADE", label="提议砍功能保 deadline", target_character="CHR_01", custom_effect={"kpi": +3, "relation": +5, "cor": +3}),
        SceneOption(option_id="OPT_BOSS1_DOCUMENT", prototype="DOCUMENT", label="拿出变更记录和工时统计", target_character="CHR_03", custom_effect={"risk": -10, "cor": +5}),
        SceneOption(option_id="OPT_BOSS1_PROBE", prototype="PROBE", label="私下试探陈总监的真实底线", target_character="CHR_01", sub_mode="active", custom_effect={"en": -5, "relation": +3}),
        SceneOption(option_id="OPT_BOSS1_ALLY_CHEN", prototype="ALLY", label="公开支持陈总监的方案", target_character="CHR_01", visibility_condition="relation>-20", custom_effect={"relation": +15, "cor": +5, "risk": +3}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_BOSS1_DOCUMENT_WIN",
            description="Boss战中仅用DOCUMENT应对，让甲方无话可说",
            reward={"kpi": +5, "risk": -5, "relation_with_CHR_03": +10},
            trigger_condition="boss1_document_only==true",
        ),
    ],
    scene_pool_tags=["Boss战", "项目评审"],
)

SCENE_BOSS_FACTION_CLASH = Scene(
    scene_id="SCENE_BOSS_FACTION_CLASH",
    title="【Boss战】派系冲突",
    time_periods=["加班"],
    location="会议室，两派对峙",
    required_characters=["CHR_01", "CHR_06"],
    optional_characters=["CHR_02", "CHR_04"],
    inclusion_rules={"CHR_02": "relation>-30", "CHR_04": "turn>10"},
    max_characters=4,
    narrative_fn="render_boss_faction_clash",
    player_options=[
        SceneOption(option_id="OPT_BOSS2_ALLY_CHEN", prototype="ALLY", label="站陈总监这边", target_character="CHR_01", custom_effect={"relation": +20, "cor": +5, "risk": +5}),
        SceneOption(option_id="OPT_BOSS2_ALLY_RIVAL", prototype="ALLY", label="站派系总监这边", target_character="CHR_06", custom_effect={"relation": +20, "cor": +5, "risk": +5}),
        SceneOption(option_id="OPT_BOSS2_EVADE", prototype="EVADE", label="保持中立，两边不得罪", custom_effect={"relation": -5, "kpi": -3, "st": -5}),
        SceneOption(option_id="OPT_BOSS2_PROBE", prototype="PROBE", label="观察双方底牌，暂不表态", sub_mode="passive", custom_effect={"en": -3}),
        SceneOption(option_id="OPT_BOSS2_DOCUMENT", prototype="DOCUMENT", label="拿出项目数据，让事实说话", custom_effect={"risk": -5, "kpi": +3, "cor": +3}),
        SceneOption(option_id="OPT_BOSS2_TRADE", prototype="TRADE", label="提议各退一步，先保项目", custom_effect={"kpi": +5, "relation": +5, "cor": +5}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_BOSS2_PEACE",
            description="派系冲突中成功让双方各退一步，不发生公开决裂",
            reward={"st": +10, "kpi": +5, "relation_with_CHR_01": +5, "relation_with_CHR_06": +5},
            trigger_condition="boss2_peace_made==true",
        ),
    ],
    scene_pool_tags=["Boss战", "派系斗争"],
)

SCENE_BOSS_AUDIT_EVE = Scene(
    scene_id="SCENE_BOSS_AUDIT_EVE",
    title="【Boss战】审计前夜",
    time_periods=["下午"],
    location="公司大会议室，全员到齐",
    required_characters=["CHR_01", "CHR_05"],
    optional_characters=["CHR_02", "CHR_03", "CHR_04", "CHR_06"],
    inclusion_rules={
        "CHR_02": "relation>-40",
        "CHR_03": "turn>20",
        "CHR_04": "turn>15",
        "CHR_06": "turn>10",
    },
    max_characters=5,
    narrative_fn="render_boss_audit_eve",
    player_options=[
        SceneOption(option_id="OPT_BOSS3_DOCUMENT", prototype="DOCUMENT", label="提交完整的项目文档和审计材料", custom_effect={"risk": -15, "kpi": +5, "cor": +3}),
        SceneOption(option_id="OPT_BOSS3_DEFLECT", prototype="DEFLECT", label="指出问题主要在甲方变更和财务流程", custom_effect={"cor": +10, "risk": +10, "kpi": -5}),
        SceneOption(option_id="OPT_BOSS3_ASSERT", prototype="ASSERT", label="主动承担责任，提出补救方案", target_character="CHR_01", custom_effect={"kpi": +10, "risk": +5, "en": -15}),
        SceneOption(option_id="OPT_BOSS3_ALLY_CHEN", prototype="ALLY", label="支持陈总监的应对方案", target_character="CHR_01", custom_effect={"relation": +15, "cor": +5}),
        SceneOption(option_id="OPT_BOSS3_ALLY_RIVAL", prototype="ALLY", label="支持派系总监趁机发难", target_character="CHR_06", visibility_condition="relation>-20", custom_effect={"relation": +15, "cor": +8, "risk": +5}),
        SceneOption(option_id="OPT_BOSS3_THREATEN", prototype="THREATEN", label="亮出掌握的证据，逼各方让步", target_character="CHR_01", visibility_condition="turn>30", custom_effect={"cor": +15, "risk": +10, "relation": -20}),
    ],
    hidden_goals=[
        HiddenGoal(
            goal_id="GOAL_BOSS3_SURVIVE",
            description="审计前夜Boss战中存活且risk不超过60",
            reward={"st": +15, "kpi": +10},
            trigger_condition="boss3_survived==true",
        ),
    ],
    scene_pool_tags=["Boss战", "审计", "终局"],
)


# ---------------------------------------------------------------------------
# 场景注册表
# ---------------------------------------------------------------------------
SCENES: dict[str, Scene] = {
    "SCENE_REVIEW_MEETING": SCENE_REVIEW_MEETING,
    "SCENE_LATE_NIGHT_ALONE": SCENE_LATE_NIGHT_ALONE,
    "SCENE_MORNING_MEETING": SCENE_MORNING_MEETING,
    "SCENE_BOSS_DROP_BY": SCENE_BOSS_DROP_BY,
    "SCENE_PROGRESS_REPORT": SCENE_PROGRESS_REPORT,
    "SCENE_CAFE_ENCOUNTER": SCENE_CAFE_ENCOUNTER,
    "SCENE_WATERCOOLER_GOSSIP": SCENE_WATERCOOLER_GOSSIP,
    "SCENE_LUNCH_PUSH": SCENE_LUNCH_PUSH,
    "SCENE_OVERTIME_CRUNCH": SCENE_OVERTIME_CRUNCH,
    "SCENE_LATE_EMAIL": SCENE_LATE_EMAIL,
    "SCENE_BOSS_PRIVATE_TALK": SCENE_BOSS_PRIVATE_TALK,
    "SCENE_GRAY_ACTION": SCENE_GRAY_ACTION,
    "SCENE_CONTACT_EXTERNAL": SCENE_CONTACT_EXTERNAL,
    "SCENE_BOSS_FIRST_REVIEW": SCENE_BOSS_FIRST_REVIEW,
    "SCENE_BOSS_FACTION_CLASH": SCENE_BOSS_FACTION_CLASH,
    "SCENE_BOSS_AUDIT_EVE": SCENE_BOSS_AUDIT_EVE,
}


# ---------------------------------------------------------------------------
# 时段场景池
# ---------------------------------------------------------------------------
TIME_PERIOD_SCENE_POOLS: dict[str, dict] = {
    "上午": {
        "themes": ["正式推进"],
        "scenes": ["SCENE_MORNING_MEETING", "SCENE_BOSS_DROP_BY", "SCENE_PROGRESS_REPORT"],
        "weight_modifiers": {"CHR_01": 1.5, "CHR_03": 1.2, "CHR_06": 1.0},
    },
    "午休": {
        "themes": ["非正式社交"],
        "scenes": ["SCENE_CAFE_ENCOUNTER", "SCENE_WATERCOOLER_GOSSIP", "SCENE_LUNCH_PUSH"],
        "weight_modifiers": {"CHR_02": 1.8, "CHR_04": 1.3},
    },
    "下午": {
        "themes": ["交付压力"],
        "scenes": ["SCENE_REVIEW_MEETING"],
        "weight_modifiers": {"CHR_03": 1.8, "CHR_01": 1.2, "CHR_05": 1.2},
    },
    "加班": {
        "themes": ["透支救火"],
        "scenes": ["SCENE_OVERTIME_CRUNCH", "SCENE_LATE_EMAIL", "SCENE_BOSS_PRIVATE_TALK"],
        "weight_modifiers": {"CHR_01": 1.8, "CHR_03": 1.5},
        "special": "玩家EN<30时，50%概率跳过本时段（累倒）",
    },
    "深夜": {
        "themes": ["独处/灰色"],
        "scenes": ["SCENE_LATE_NIGHT_ALONE", "SCENE_GRAY_ACTION", "SCENE_CONTACT_EXTERNAL"],
        "weight_modifiers": {},
        "special": "无其他角色在场",
    },
}


# ---------------------------------------------------------------------------
# 查询接口
# ---------------------------------------------------------------------------
def get_scene(scene_id: str) -> Optional[Scene]:
    return SCENES.get(scene_id)


def get_scenes_for_period(time_period: str) -> list[str]:
    """获取指定时段的场景池。"""
    pool = TIME_PERIOD_SCENE_POOLS.get(time_period, {})
    return pool.get("scenes", [])


def get_scene_weight_modifiers(time_period: str) -> dict[str, float]:
    """获取指定时段的角色权重修正。"""
    pool = TIME_PERIOD_SCENE_POOLS.get(time_period, {})
    return pool.get("weight_modifiers", {})
