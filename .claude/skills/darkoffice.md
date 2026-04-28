# DarkOffice

## Description

《暗黑职场》—— 一个以恶性职场为背景的卡牌驱动叙事生存游戏。玩家在权力、金钱、道德的夹缝中求生存，每个选择都可能改变命运。

## Tools

- `npm run skill:init` — 初始化数据库
- `npm run skill:create -- <session_id>` — 创建新游戏会话
- `npm run skill:show -- <session_id>` — 查看当前状态
- `npm run skill:turn -- <session_id> --action <ACTION_TYPE>` — 执行一回合结算
- `npm run skill:prompt -- <session_id>` — 获取下一回合完整展示块
- `npm run skill:history -- <session_id>` — 查看回合历史
- `npm run skill:stats -- <session_id>` — 查看行动统计
- `npm run skill:health` — 环境健康检查

## Workflow

当用户说"开始游戏""新游戏"或类似表述时：

1. 初始化：`npm run skill:init`
2. 创建会话：`npm run skill:create -- <session_id>`（session_id 用 `darkoffice_<日期>_<序号>`）
3. 查询剧情库：`python3 scripts/game_state_cli.py storyline-list`
4. 若剧情库非空，展示剧情选项让用户选择
5. 激活剧情线：`python3 scripts/game_state_cli.py storyline-activate <session_id> <storyline_id>`
6. 开始第一回合：`npm run skill:turn -- <session_id> --action <ACTION_TYPE>`

每回合输出固定 5 段：
1. 状态栏（来自 `show` 或 `prompt`）
2. 事件摘要（2-4 行）
3. 可选行动（3-5 个，只写收益/代价）
4. 用户输入提示
5. 结算回执（骰子、结果等级、delta）

## Rules

- 任何数值结算必须通过 `turn` 命令写入数据库，禁止"口算"
- 禁止向用户展示内部字段 ID（如 EVT_02、CHR_01）
- `turn` 响应中的 `next_prompt` 必须直接用于渲染下一回合
- 回合结算后检查失败条件（HP/EN/ST/KPI <=0 或 RISK/COR >=100）
