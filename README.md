# Dark Office

> 如果你正在加班，建议先躲进厕所再看这篇文档。
> 不是为你好，是怕你笑着笑着哭出来，同事以为你疯了。

---

## 这是个什么玩意儿

《暗黑职场》是个卡牌游戏。

但它不让你打怪升级，它让你——**上班**。

对，就是那种每天早上闹钟响了三次你还想再睡五分钟的班。那种周报写了八百字其实啥也没干的班。那种领导说"这个需求很简单"然后你通宵三天的班。

我们把职场里那些**不能明说但人人都懂**的东西，做成了游戏规则：

- 甩锅不是道德问题，是**生存技能**
- 留痕不是为了复盘，是**出事了能把自己摘干净**
- 站队不是投机，是**你不站别人就替你站了**
- 绩效不是看你干多少，是**看你怎么让领导觉得你干了很多**

你说这游戏黑暗吗？

黑暗。但话说回来，**现实职场比这还黑**——至少游戏里输了可以重开，现实中你只能更新简历。

---

## 为什么做这个

因为我发现市面上的"职场游戏"都在骗你。

它们把上班包装成打怪：你努力→你变强→你升职→你走上人生巅峰。

但真实的职场是：你努力→你背锅→你加班→你体检报告多了三个箭头→你升职的是那个会汇报的。

所以我想做一个**诚实的游戏**。

它不教你成功，它教你在一个**注定有点糟的系统里，怎么活得不那么糟**。

（当然，也可能更糟。这取决于你的选择，还有运气。）

---

## 核心玩法：聊天就能玩

不用下载，不用注册，不用看三十秒广告。

打开飞书、钉钉、微信，或者任何一个能打字的地方，跟 Agent 说：

> "我要开始上班了。"

然后你会收到一张**事件卡**：

> 【跨部门需求】产品部甩过来一个"紧急"需求，要求周五上线。但技术评估需要两周。你怎么办？

你可以：
- 硬接（展现担当，但可能猝死）
- 甩回去（建立边界，但可能被穿小鞋）
- 拉个会（转移矛盾，但可能陷入会议地狱）
- 先答应再说（赢得时间，但埋下隐患）

每个选择都有代价。有些代价当下就结算，有些像信用卡账单——**下个月才让你知道有多痛**。

---

## 游戏特色（或者说，残酷真相）

| 特色 | 翻译成人话 |
|------|-----------|
| **聊天优先** | 不用学操作，会打字就会玩 |
| **卡牌驱动** | 你的命运由抽卡决定，就像真实职场一样随机 |
| **生存叙事** | 目标不是赢，是**别死得太快** |
| **延迟代价** | 今天的捷径，是明天的坑 |
| **AI 友好** | 文档写得清楚，方便 AI 接手——毕竟人类开发者也会 burnout |

---

## 如果你第一次来

建议按这个顺序看，**别跳**——跳了后面看不懂别怪我：

1. [docs/INDEX.md](/Users/niunan/project/darkoffice/docs/INDEX.md) —— 地图
2. [docs/project/README.md](/Users/niunan/project/darkoffice/docs/project/README.md) —— 这项目到底想干嘛
3. [docs/design/README.md](/Users/niunan/project/darkoffice/docs/design/README.md) —— 怎么让玩家爽（或者说，怎么让玩家痛并爽着）
4. [docs/systems/README.md](/Users/niunan/project/darkoffice/docs/systems/README.md) —— 规则，无情的规则
5. [docs/visualizations/README.md](/Users/niunan/project/darkoffice/docs/visualizations/README.md) —— 规则引擎可视化
6. [docs/content/README.md](/Users/niunan/project/darkoffice/docs/content/README.md) —— 卡牌长什么样

## 如果你想参与

先看这三份，看完再决定要不要跳这个坑：

1. [docs/collaboration/development-guidelines.md](/Users/niunan/project/darkoffice/docs/collaboration/development-guidelines.md)
2. [docs/collaboration/source-of-truth.md](/Users/niunan/project/darkoffice/docs/collaboration/source-of-truth.md)
3. [docs/collaboration/agent-handoff.md](/Users/niunan/project/darkoffice/docs/collaboration/agent-handoff.md)

---

## 仓库结构

```
docs/                     # 正式文档事实源
├── INDEX.md              # 地图
├── project/              # 项目定位、术语、设计支柱
├── design/               # 核心循环、进程推进、结局方向
├── systems/              # 卡牌系统、回合流程、判定规则
├── visualizations/       # 机制总览与结构化规则可视化
├── content/              # 角色池、事件库、应对库
├── collaboration/        # 开发规范、交接文档
└── archive/              # 历史的尘埃

runtime/                  # 规则执行与数据存取
├── db.py                 # SQLite 持久化（5张表 + 迁移）
├── engine.py             # 回合结算引擎（状态机、判定、隐患、项目）
├── rules.py              # 共享规则表（动作、档位、时段、隐患映射）
├── mechanics.py          # 机制快照导出（CLI / 可视化共用）
├── content.py            # Character/Event dataclass
├── materials.py          # 素材库 + 自定义卡牌管理
└── storylines.py         # 剧情线 CRUD + 激活/推进

scripts/                  # 初始化、调试、运维脚本
├── game_state_cli.py     # CLI 入口（init/create/turn/show/material/card/storyline）
├── render_mechanics_visual.py # 机制总览页渲染器
├── distill_template.py   # 卡牌蒸馏模板 + Schema 校验
├── simulate_balance.py   # 平衡性模拟
├── crawl_jingzhong.py    # 警钟栏目爬取
└── fetch_and_import_jingzhong.py  # 详情抓取 + 素材库导入

skill/                    # 可交付 Agent Skill
├── darkoffice-persistent-skill.md  # 持久化版 Skill（含完整规则 + DB 约束）
└── adapter.ts            # Node.js → Python 桥接

data/                     # 运行时数据（SQLite + 素材文件）
```

---

## 现在能玩吗

能。

**现在是个可运行的"职场模拟器原型"**，支持持久化存档、素材库、卡牌蒸馏和剧情线。

你可以：
- 创建角色，存档自动落盘 SQLite
- 抽事件卡，回合结算含 d20 判定
- 做选择，看数值变化（HP/EN/ST/KPI/RISK/COR）
- 导入素材（新闻案例、历史事件等），AI 蒸馏成角色卡/事件卡
- 编排剧情线，让游戏按你的剧本推进
- 体验"我怎么又死了"的挫败感

你不能：
- 看到华丽的画面（本来也没有）
- 通关（本来也没有通关）
- 获得成就感（这个……看你怎么定义了）

---

## 快速上手

### Python 原生版

```bash
# 1. 初始化数据库
python3 scripts/game_state_cli.py init

# 2. 创建一个倒霉蛋
python3 scripts/game_state_cli.py create demo

# 3. 让他开始受苦
python3 scripts/game_state_cli.py turn demo --action EMAIL_TRACE --mod 3

# 4. 查看他还活着吗
python3 scripts/game_state_cli.py show demo

# 5. 导出规则快照 / 重绘机制图
python3 scripts/game_state_cli.py mechanics
python3 scripts/render_mechanics_visual.py

# 6. 素材库操作
python3 scripts/game_state_cli.py material-list
python3 scripts/game_state_cli.py material-search --keyword 腐败

# 7. 剧情线操作
python3 scripts/game_state_cli.py storyline-list
python3 scripts/game_state_cli.py storyline-activate demo --storyline-id demo_arc
```

### Node.js 适配版（给 WorkBuddy/OpenClaw 用的）

```bash
npm run skill:health
npm run skill:init
npm run skill:create -- demo
npm run skill:turn -- demo --action EMAIL_TRACE --mod 3
npm run skill:show -- demo
```

---

## 下一步干嘛

### 内容规模化

游戏机制是骨架，**事件卡才是血肉**。现在有几张卡，但不够。我们已建立素材库和卡牌蒸馏器，可以：

1. **导入素材**：把新闻案例、历史事件、个人经历录入素材库
2. **AI 蒸馏**：运行 `scripts/distill_template.py`，从素材生成角色卡/事件卡/隐患卡
3. **激活卡牌**：自定义卡牌激活后自动合并入默认池
4. **编排剧情**：用 `storylines.py` 设计多幕剧情线

### 已有素材

- 中央纪委"警钟"栏目：19 条反腐案例已导入素材库

如果你也有**被职场毒打的经历**，欢迎贡献。你的痛苦，可以成为别人的游戏素材。

（当然，我们会把名字改掉，保护当事人。）

---

## 最后

这游戏不会教你如何在职场成功。

但如果你玩完觉得"原来大家都这样"，或者"至少游戏里我还能选"，那它就值了。

**人间不值得，但上班还得上。**

开心点朋友们。

---

*P.S. 如果你在凌晨两点看到这个文档，建议去睡觉。真的。*
