"""叙事渲染函数库。

职责：
1. 定义 NarrativeContext（场景渲染的统一输入上下文）
2. 提供 narrative_fn 函数，根据角色状态动态生成场景文本
3. 每个 Scene 的 narrative_fn 字段指向本模块中的函数名
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from runtime.content import (
    CharacterState,
    RenderedLine,
    RenderedScene,
    Scene,
    SceneOption,
)
from runtime.relation_graph import RelationGraph


# ---------------------------------------------------------------------------
# 叙事上下文
# ---------------------------------------------------------------------------
@dataclass
class NarrativeContext:
    """场景渲染的统一输入上下文。"""

    session: dict
    player_state: dict
    character_states: dict[str, CharacterState]
    relation_graph: RelationGraph
    turn_history: list[dict]
    active_chains: list[dict]
    active_storyline: Optional[dict]
    time_period: str
    turn_index: int

    def get_character_state(self, character_id: str) -> Optional[CharacterState]:
        return self.character_states.get(character_id)

    def is_character_present(self, character_id: str) -> bool:
        return character_id in self.character_states

    def get_player_name(self) -> str:
        return self.player_state.get("name", "你")


# ---------------------------------------------------------------------------
# 通用渲染辅助函数
# ---------------------------------------------------------------------------
def _mood_description(mood: str) -> str:
    """心情到描述的映射。"""
    descriptions = {
        "急躁": "不耐烦地",
        "阴沉": "冷冷地",
        "得意": "带着一丝得意",
        "恐慌": "声音有些发抖",
        "冷漠": "面无表情地",
        "平静": "平静地",
    }
    return descriptions.get(mood, "")


def _relation_description(relation: int) -> str:
    """关系到描述的映射。"""
    if relation >= 50:
        return "信任"
    elif relation >= 20:
        return "认可"
    elif relation >= -20:
        return "一般"
    elif relation >= -50:
        return "冷淡"
    else:
        return "敌意"


def _parse_simple_condition(condition: str, value: int | str) -> bool:
    """解析简单条件表达式，避免 eval 安全风险。

    支持: >N, <N, >=N, <=N, ==N, =='string'
    """
    condition = condition.strip()
    for op in (">=", "<=", ">", "<", "=="):
        if condition.startswith(op):
            rhs = condition[len(op):].strip()
            # 去除引号
            if (rhs.startswith("'") and rhs.endswith("'")) or (rhs.startswith('"') and rhs.endswith('"')):
                rhs = rhs[1:-1]
                return str(value) == rhs
            try:
                rhs_val = int(rhs)
                if isinstance(value, str):
                    return False
                if op == ">=": return value >= rhs_val
                if op == "<=": return value <= rhs_val
                if op == ">": return value > rhs_val
                if op == "<": return value < rhs_val
                if op == "==": return value == rhs_val
            except ValueError:
                return False
    return False


def _filter_visible_options(options: list[SceneOption], ctx: NarrativeContext) -> list[SceneOption]:
    """根据 visibility_condition 过滤选项。最多返回6个。"""
    visible = []
    for opt in options:
        if not opt.visibility_condition:
            visible.append(opt)
            continue

        condition = opt.visibility_condition
        try:
            if condition.startswith("relation"):
                target_id = opt.target_character
                if target_id and target_id in ctx.character_states:
                    relation = ctx.character_states[target_id].relation_to_player
                    if _parse_simple_condition(condition[8:], relation):
                        visible.append(opt)
                else:
                    visible.append(opt)
            elif condition.startswith("mood=="):
                target_id = opt.target_character
                if target_id and target_id in ctx.character_states:
                    mood = ctx.character_states[target_id].mood
                    expected = condition[6:].strip("'\"")
                    if mood == expected:
                        visible.append(opt)
            elif condition.startswith("turn"):
                if _parse_simple_condition(condition[4:], ctx.turn_index):
                    visible.append(opt)
            elif condition.startswith("has_event"):
                visible.append(opt)
            else:
                visible.append(opt)
        except Exception:
            visible.append(opt)

    return visible[:6]


# ---------------------------------------------------------------------------
# 场景1：项目评审会
# ---------------------------------------------------------------------------
def render_review_meeting(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    """渲染'项目评审会'场景。"""
    lines = []

    chen = ctx.get_character_state("CHR_01")
    xiaolin = ctx.get_character_state("CHR_02")
    finance = ctx.get_character_state("CHR_05")

    # ---- 陈总监台词（5种变体） ----
    if chen:
        mood_desc = _mood_description(chen.mood)
        r = chen.relation_to_player
        if r < -50:
            if chen.stress > 80:
                text, subtext = "小陈！这个方案到底什么时候能出？大老板在等！", f"陈总监{mood_desc}拍桌子，显然已经忍无可忍。"
            else:
                text, subtext = f"小陈，这个方案下周必须交付，有问题吗？别让我再催。", f"他{mood_desc}看着你，毫不掩饰的不满。"
        elif r < -20:
            text, subtext = f"{ctx.get_player_name()}，这个方案进度我不是很满意。", f"他{mood_desc}看着你，带着审视。"
        elif r < 20:
            text, subtext = "这个方案下周必须交付，谁有问题？", f"他{mood_desc}扫视了一圈会议室。"
        elif r < 50:
            text, subtext = f"{ctx.get_player_name()}，这个方案你来牵头，有问题随时找我。", f"他冲你点了点头，{mood_desc}，语气比往常温和。"
        else:
            if chen.stress > 80:
                text, subtext = "这个项目你最清楚，你来说，我支持你的判断。", "陈总监拍了拍你的肩膀，把主导权交给了你。"
            else:
                text, subtext = f"{ctx.get_player_name()}，你来说一下目前的思路。", f"他{mood_desc}看着你，明显在给你展示的机会。"
        lines.append(RenderedLine("CHR_01", "陈总监", chen.mood, text, subtext))

    # ---- 小林台词（3种变体） ----
    if xiaolin:
        if xiaolin.relation_to_player < -20:
            text, subtext = f"{ctx.get_player_name()}说技术没问题，但我看还是让他自己负责比较好。", "小林突然开口，把锅往你这边推。"
        elif xiaolin.relation_to_player > 20:
            text, subtext = f"技术上有些风险，但{ctx.get_player_name()}之前做过类似的，他比较有经验。", "小林替你说话，让在场的人都看了过来。"
        else:
            text, subtext = f"技术上有些风险，{ctx.get_player_name()}比较清楚。", "小林低着头看手机，把话题抛给了你。"
        lines.append(RenderedLine("CHR_02", "小林", xiaolin.mood, text, subtext))

    # ---- 财务关键人台词（2种变体） ----
    if finance:
        if finance.mood == "急躁":
            text, subtext = "预算已经超了15%，而且还在涨！这部分谁负责？", "他把报表摔在桌上，明显很生气。"
        else:
            text, subtext = "预算已经超了15%，这部分谁负责？", "他翻着报表，眉头紧锁。"
        lines.append(RenderedLine("CHR_05", "财务关键人", finance.mood, text, subtext))

    # ---- 开场描述（3种变体） ----
    if chen and chen.stress > 80:
        opening = "下午两点的项目评审会。会议室里的空气几乎凝固，每个人的表情都很僵硬。"
    elif chen and chen.mood == "得意":
        opening = "下午两点的项目评审会。陈总监看起来心情不错，刚被大老板表扬过。"
    else:
        opening = "下午两点的项目评审会准时开始。"

    visible_options = _filter_visible_options(scene.player_options, ctx)
    return RenderedScene(opening, lines, "正式会议", visible_options)


# ---------------------------------------------------------------------------
# 场景2：深夜独处
# ---------------------------------------------------------------------------
def render_late_night_alone(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    """渲染'深夜独处'场景。"""
    opening = "凌晨1点，办公室里只剩下你一个人。"

    session = ctx.session
    if session.get("en", 100) < 20:
        opening += "你盯着屏幕，眼睛酸痛，手指在发抖。"
    elif session.get("risk", 0) > 50:
        opening += "桌上的咖啡已经凉了，但你不敢停下。"
    elif session.get("cor", 0) > 30:
        opening += "窗外的城市还亮着灯，但你觉得自己离它越来越远。"

    options = [
        SceneOption(
            option_id="OPT_WORK_MORE",
            prototype="ASSERT",
            label="再熬一小时，把方案收尾",
            custom_effect={"en": -15, "kpi": +3},
        ),
        SceneOption(
            option_id="OPT_REST",
            prototype="RECOVER",
            label="趴桌上眯一会儿",
            custom_effect={"en": +15, "st": +10},
        ),
        SceneOption(
            option_id="OPT_GRAY",
            prototype="DEFLECT",
            label="把明天的会议资料提前准备好（倒签日期）",
            custom_effect={"risk": +10, "cor": +5},
            visibility_condition="turn>10",  # P1 简化
        ),
    ]

    return RenderedScene(
        opening=opening,
        lines=[],
        atmosphere="深夜独处",
        options=options,
    )


# ---------------------------------------------------------------------------
# 场景3：部门晨会
# ---------------------------------------------------------------------------
def render_morning_meeting(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    chen = ctx.get_character_state("CHR_01")
    xiaolin = ctx.get_character_state("CHR_02")
    director = ctx.get_character_state("CHR_06")

    if chen:
        mood_desc = _mood_description(chen.mood)
        r = chen.relation_to_player
        if r < -40:
            text, subtext = f"小陈，你先说。昨天的进度呢？别告诉我又没做完。", f"陈总监{mood_desc}盯着你，全场安静。"
        elif r < -10:
            text, subtext = "小陈，你先说。昨天的进度呢？", f"陈总监{mood_desc}看着你。"
        elif r < 30:
            text, subtext = "大家汇报一下进度。", f"陈总监{mood_desc}扫视全场。"
        else:
            text, subtext = f"{ctx.get_player_name()}，你那边进展如何？", "陈总监的语气比平时温和。"
        lines.append(RenderedLine("CHR_01", "陈总监", chen.mood, text, subtext))

    if xiaolin:
        if xiaolin.mood == "懒散":
            text, subtext = "我这边还在等接口，没什么进展。", "小林打着哈欠，明显没睡醒。"
        elif xiaolin.mood == "急躁":
            text, subtext = "我这边被催了三次了，能不能先排期？", "小林的声音比平时大。"
        else:
            text, subtext = "我这边还在等接口。", "小林低着头看手机。"
        lines.append(RenderedLine("CHR_02", "小林", xiaolin.mood, text, subtext))

    if director:
        if chen and director.relation_to_player < -30:
            text, subtext = "我补充一点。这个项目我们公司投了资源，不能只看到短期。", "派系总监看着陈总监，话里有话。"
        else:
            text, subtext = "我补充一点。", "派系总监突然插话。"
        lines.append(RenderedLine("CHR_06", "派系总监", director.mood, text, subtext))

    opening = "早上9点，部门晨会准时开始。"
    if chen and chen.stress > 70:
        opening += "陈总监的脸色不太好，手里捏着一份报表。"
    return RenderedScene(opening, lines, "晨会", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景4：上司查岗
# ---------------------------------------------------------------------------
def render_boss_drop_by(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    chen = ctx.get_character_state("CHR_01")
    if chen:
        mood_desc = _mood_description(chen.mood)
        r = chen.relation_to_player
        if r < -50:
            text, subtext = "你在忙什么？", f"陈总监{mood_desc}盯着你的屏幕，明显在找茬。"
        elif r < -20:
            text, subtext = "你在忙什么？", f"陈总监{mood_desc}盯着你的屏幕。"
        elif r < 20:
            text, subtext = "进度怎么样了？", f"陈总监{mood_desc}站在你身后。"
        elif r < 50:
            text, subtext = f"{ctx.get_player_name()}，这个方案我看了，不错。", "陈总监拍了拍你的肩膀。"
        else:
            text, subtext = f"{ctx.get_player_name()}，有件事想听听你的意见。", "陈总监拉过一把椅子，坐在你旁边。"
        lines.append(RenderedLine("CHR_01", "陈总监", chen.mood, text, subtext))

    opening = "陈总监突然出现在你的工位旁。"
    if chen and chen.stress > 80:
        opening += "他的眼圈发黑，显然昨晚也没睡好。"
    return RenderedScene(opening, lines, "突发查岗", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景5：项目进度汇报
# ---------------------------------------------------------------------------
def render_progress_report(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    chen = ctx.get_character_state("CHR_01")
    if chen:
        if chen.stress > 80:
            text, subtext = f"{ctx.get_player_name()}，你把当前进度汇报一下。", "陈总监指节敲着桌面，明显在压火。"
        elif chen.relation_to_player > 30:
            text, subtext = f"{ctx.get_player_name()}，你来汇报，我帮你兜着。", "陈总监冲你使了个眼色。"
        else:
            text, subtext = "你把当前进度汇报一下。", "陈总监示意你开始。"
        lines.append(RenderedLine("CHR_01", "陈总监", chen.mood, text, subtext))

    client = ctx.get_character_state("CHR_03")
    if client:
        if client.mood == "急躁":
            text, subtext = "我们老板下周要看demo，再拖下去合同要重新谈。", "甲方代表拍着桌子。"
        else:
            text, subtext = "我们老板下周要看demo。", "甲方代表皱着眉。"
        lines.append(RenderedLine("CHR_03", "甲方代表", client.mood, text, subtext))

    finance = ctx.get_character_state("CHR_05")
    if finance:
        if finance.mood == "阴沉":
            text, subtext = "追加预算？需要特批，而且陈总您上次那笔——", "财务关键人欲言又止。"
        else:
            text, subtext = "追加预算需要特批。", "财务关键人摇了摇头。"
        lines.append(RenderedLine("CHR_05", "财务关键人", finance.mood, text, subtext))

    opening = "总监办公室，项目进度汇报正在进行。"
    return RenderedScene(opening, lines, "汇报", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景6：食堂偶遇
# ---------------------------------------------------------------------------
def render_cafe_encounter(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    for char_id in ["CHR_02", "CHR_04", "CHR_06"]:
        state = ctx.get_character_state(char_id)
        if state:
            name_map = {"CHR_02": "小林", "CHR_04": "HR张姐", "CHR_06": "派系总监"}
            name = name_map.get(char_id, char_id)
            if state.mood == "冷漠":
                text, subtext = "...", f"{name}看到你就转开了视线。"
            elif state.mood == "阴沉":
                text, subtext = "你听说了吗？财务部那边好像出事了。", f"{name}压低声音，神色凝重。"
            elif state.mood == "得意":
                text, subtext = "你听说了吗？有人要升职了。", f"{name}笑了笑，意味深长地看了你一眼。"
            else:
                text, subtext = "你听说了吗？", f"{name}压低声音。"
            lines.append(RenderedLine(char_id, name, state.mood, text, subtext))

    opening = "中午12点，食堂人不多，你端着饭找了个位置。"
    return RenderedScene(opening, lines, "食堂", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景7：茶水间八卦
# ---------------------------------------------------------------------------
def render_watercooler_gossip(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    hr = ctx.get_character_state("CHR_04")
    if hr:
        if hr.mood == "阴沉":
            text, subtext = "最近人员变动比较多，有些人可能待不久了。", "HR张姐意有所指，声音压得很低。"
        else:
            text, subtext = "最近人员变动比较多。", "HR张姐意有所指。"
        lines.append(RenderedLine("CHR_04", "HR张姐", hr.mood, text, subtext))

    xiaolin = ctx.get_character_state("CHR_02")
    if xiaolin:
        if xiaolin.mood == "得意":
            text, subtext = "是吗？我怎么听说有人已经找好下家了。", "小林装作不经意，但嘴角在笑。"
        else:
            text, subtext = "是吗？我没听说。", "小林装作不知情。"
        lines.append(RenderedLine("CHR_02", "小林", xiaolin.mood, text, subtext))

    opening = "茶水间里，HR张姐和小林正在低声交谈。"
    return RenderedScene(opening, lines, "茶水间", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景8：午休推活
# ---------------------------------------------------------------------------
def render_lunch_push(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    xiaolin = ctx.get_character_state("CHR_02")
    if xiaolin:
        r = xiaolin.relation_to_player
        if r < -40:
            text, subtext = "你把这个做一下，下午要。", "小林的语气像是在吩咐下属。"
        elif r < -20:
            text, subtext = "你顺便帮我看看这个，很简单的。", "小林的语气不容拒绝。"
        elif r < 20:
            text, subtext = "有空吗？帮我个小忙。", "小林笑着，但眼神闪烁。"
        else:
            text, subtext = "兄弟，帮个忙？下次我请你吃饭。", "小林的态度比往常热络。"
        lines.append(RenderedLine("CHR_02", "小林", xiaolin.mood, text, subtext))

    opening = "午休时间，小林在走廊拦住了你。"
    if xiaolin and xiaolin.stress > 70:
        opening += "他的衬衫皱巴巴的，显然也在赶工。"
    return RenderedScene(opening, lines, "推活", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景9：临时加班
# ---------------------------------------------------------------------------
def render_overtime_crunch(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    chen = ctx.get_character_state("CHR_01")
    client = ctx.get_character_state("CHR_03")

    if chen:
        mood_desc = _mood_description(chen.mood)
        if chen.stress > 80:
            text, subtext = "这个方案今晚必须出来，你留下。", f"陈总监{mood_desc}命令道，声音沙哑。"
        elif chen.relation_to_player > 30:
            text, subtext = "今晚可能要加个班，你行吗？", "陈总监的语气带着歉意。"
        else:
            text, subtext = "这个方案今晚必须出来，你留下。", f"陈总监{mood_desc}命令道。"
        lines.append(RenderedLine("CHR_01", "陈总监", chen.mood, text, subtext))

    if client:
        if client.mood == "急躁":
            text, subtext = "我们明天早上就要！现在不改就来不及了！", "甲方代表几乎是在吼。"
        else:
            text, subtext = "我们明天早上就要。", "甲方代表毫不退让。"
        lines.append(RenderedLine("CHR_03", "甲方代表", client.mood, text, subtext))

    opening = "晚上7点，办公室灯火通明。"
    if chen and chen.stress > 80:
        opening += "陈总监的办公室里传来摔东西的声音。"
    return RenderedScene(opening, lines, "加班", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景10：深夜邮件
# ---------------------------------------------------------------------------
def render_late_email(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    client = ctx.get_character_state("CHR_03")
    if client:
        if client.mood == "急躁":
            text, subtext = "需求有变更，请今晚确认！（第三次）", "手机屏幕疯狂震动，甲方又发邮件了。"
        else:
            text, subtext = "需求有变更，请今晚确认。", "手机屏幕亮起，甲方又发邮件了。"
        lines.append(RenderedLine("CHR_03", "甲方代表", client.mood, text, subtext))

    opening = "晚上9点，你刚准备下班，手机响了。"
    if ctx.session.get("en", 100) < 20:
        opening += "你的眼睛已经睁不开了。"
    return RenderedScene(opening, lines, "邮件", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景11：上司私下谈话
# ---------------------------------------------------------------------------
def render_boss_private_talk(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    lines = []
    chen = ctx.get_character_state("CHR_01")
    if chen:
        if chen.relation_to_player < -20:
            text = "最近有人跟我反映了一些事。"
            subtext = "陈总监的语气很沉。"
        elif chen.relation_to_player > 20:
            text = "有个机会，我想听听你的看法。"
            subtext = "陈总监压低声音。"
        else:
            text = "最近状态怎么样？"
            subtext = "陈总监递给你一支烟。"
        lines.append(RenderedLine("CHR_01", "陈总监", chen.mood, text, subtext))

    opening = "楼梯间里，只有你们两个人。"
    return RenderedScene(opening, lines, "私下谈话", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景12：灰色操作
# ---------------------------------------------------------------------------
def render_gray_action(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    opening = "深夜的办公室空无一人，只有你的屏幕还亮着。"
    if ctx.session.get("risk", 0) > 50:
        opening += "你知道自己在走钢丝，但似乎没有别的选择。"
    elif ctx.session.get("cor", 0) > 30:
        opening += "你的手指悬在键盘上，已经不是第一次了。"
    return RenderedScene(opening, [], "灰色", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# 场景13：联系外部
# ---------------------------------------------------------------------------
def render_contact_external(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    opening = "你站在公司楼下，夜风有些凉。"
    if ctx.session.get("risk", 0) > 60:
        opening += "你的后背在冒汗，不是因为冷。"
    return RenderedScene(opening, [], "外部", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# Boss 战场景
# ---------------------------------------------------------------------------

def render_boss_first_review(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    """首次项目评审 — 甲方的施压达到顶点。"""
    chen = ctx.character_states.get("CHR_01")
    client = ctx.character_states.get("CHR_03")
    lines = []
    opening = "大会议室里，甲方代表把笔记本重重地拍在桌上。陈总监的脸色很难看。"

    if client and client.mood == "急躁":
        lines.append(RenderedLine("CHR_03", "甲方代表", "急躁", "下周必须看到完整demo，没有商量。", "他的手指敲着桌面。"))
    else:
        lines.append(RenderedLine("CHR_03", "甲方代表", "阴沉", "我给你们的时间已经够多了。", "语气里带着不满。"))

    if chen and chen.stress > 70:
        lines.append(RenderedLine("CHR_01", "陈总监", "急躁", "……我们内部再评估一下。", "他在强撑着。"))
    else:
        lines.append(RenderedLine("CHR_01", "陈总监", "平静", "这个需求确实有难度，但不是不能谈。", "他在试图控场。"))

    return RenderedScene(opening, lines, "紧张", _filter_visible_options(scene.player_options, ctx))


def render_boss_faction_clash(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    """派系冲突 — 陈总监与派系总监公开对峙。"""
    chen = ctx.character_states.get("CHR_01")
    rival = ctx.character_states.get("CHR_06")
    lines = []
    opening = "会议室里气氛剑拔弩张。陈总监和派系总监各坐一边，中间仿佛有一条无形的分界线。"

    if rival and rival.relation_to_player > 20:
        lines.append(RenderedLine("CHR_06", "派系总监", "得意", "这个项目的问题，归根结底是管理问题。", "他意有所指地看着陈总监。"))
    else:
        lines.append(RenderedLine("CHR_06", "派系总监", "平静", "我觉得有必要重新审视项目负责人的选择。", "语气平淡，但杀机暗藏。"))

    if chen and chen.stress > 70:
        lines.append(RenderedLine("CHR_01", "陈总监", "急躁", "你什么意思？这个项目一直是我亲自抓的。", "他的声音明显拔高了。"))
    else:
        lines.append(RenderedLine("CHR_01", "陈总监", "阴沉", "有些话，关起门来可以说。", "他在压着火。"))

    return RenderedScene(opening, lines, "对峙", _filter_visible_options(scene.player_options, ctx))


def render_boss_audit_eve(scene: Scene, ctx: NarrativeContext) -> RenderedScene:
    """审计前夜 — 全员到齐，最终抉择。"""
    chen = ctx.character_states.get("CHR_01")
    finance = ctx.character_states.get("CHR_05")
    lines = []
    opening = "大会议室里坐满了人。明天审计就要来了，这是最后的摊牌时刻。"

    if finance and finance.stress > 70:
        lines.append(RenderedLine("CHR_05", "财务关键人", "恐慌", "账上有些东西……不太好解释。", "他的声音在发抖。"))
    else:
        lines.append(RenderedLine("CHR_05", "财务关键人", "阴沉", "该准备的都准备了，看各位怎么表态。", "他把球踢了出去。"))

    if chen:
        lines.append(RenderedLine("CHR_01", "陈总监", "阴沉" if chen.stress > 60 else "平静", "先把项目进度过一遍，审计的事后面再说。", "他在拖延。"))

    return RenderedScene(opening, lines, "终局", _filter_visible_options(scene.player_options, ctx))


# ---------------------------------------------------------------------------
# narrative_fn 注册表
# ---------------------------------------------------------------------------
NARRATIVE_FN_REGISTRY: dict[str, callable] = {
    "render_review_meeting": render_review_meeting,
    "render_late_night_alone": render_late_night_alone,
    "render_morning_meeting": render_morning_meeting,
    "render_boss_drop_by": render_boss_drop_by,
    "render_progress_report": render_progress_report,
    "render_cafe_encounter": render_cafe_encounter,
    "render_watercooler_gossip": render_watercooler_gossip,
    "render_lunch_push": render_lunch_push,
    "render_overtime_crunch": render_overtime_crunch,
    "render_late_email": render_late_email,
    "render_boss_private_talk": render_boss_private_talk,
    "render_gray_action": render_gray_action,
    "render_contact_external": render_contact_external,
    "render_boss_first_review": render_boss_first_review,
    "render_boss_faction_clash": render_boss_faction_clash,
    "render_boss_audit_eve": render_boss_audit_eve,
}


def get_narrative_fn(fn_name: str) -> Optional[callable]:
    """根据函数名获取 narrative_fn。"""
    return NARRATIVE_FN_REGISTRY.get(fn_name)
