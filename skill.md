# DarkOffice Skill

《暗黑职场》Agent Skill —— 从文档到可运行状态的完整游戏引擎。

## 快速开始

```bash
# 1. 环境检查
npm run skill:health

# 2. 初始化数据库
npm run skill:init

# 3. 创建游戏会话
npm run skill:create -- darkoffice_$(date +%Y%m%d)_001

# 4. 查看剧情库，选择剧情线
python3 scripts/game_state_cli.py storyline-list
python3 scripts/game_state_cli.py storyline-activate <session_id> <storyline_id>

# 5. 开始游戏（执行回合）
npm run skill:turn -- <session_id> --action DIRECT_EXECUTE

# 6. 查看状态
npm run skill:show -- <session_id>
```

## 完整命令清单

| 命令 | 说明 |
|------|------|
| `npm run skill:health` | 环境健康检查 |
| `npm run skill:init` | 初始化 SQLite 数据库 |
| `npm run skill:create -- <sid>` | 创建新游戏会话 |
| `npm run skill:show -- <sid>` | 查看当前状态快照 |
| `npm run skill:turn -- <sid> --action <ACTION>` | 执行回合结算 |
| `npm run skill:prompt -- <sid>` | 获取下一回合展示块 |
| `npm run skill:history -- <sid>` | 查看回合历史 |
| `npm run skill:stats -- <sid>` | 查看行动统计 |
| `npm run skill:check-env` | 完整环境验证 |
| `npm run skill:bundle` | 打包发布 |
| `npm run sim:balance` | 平衡性模拟（20轮×30回合）|

## 行动类型

| 行动 | 修正 | 说明 |
|------|:----:|------|
| `DIRECT_EXECUTE` | +2 | 稳定但消耗大 |
| `EMAIL_TRACE` | +3 | 对模糊责任类事件特别有效 |
| `NARROW_SCOPE` | +1 | 通用性强 |
| `SOFT_REFUSE` | +0 | 无修正，看运气 |
| `WORK_OVERTIME` | +4 | 高修正但高消耗 |
| `REQUEST_CONFIRMATION` | +2 | 对甲方/上司事件有效 |
| `DELAY_AVOID` | -1 | 容易生成隐患 |
| `SHIFT_BLAME` | +1 | 成功获益大但 COR 上升 |
| `RECOVERY_BREAK` | -2 | 恢复精力体力，KPI 下降 |
| `BOUNDARY_RESTATE` | +0 | 降低后续 RISK |

## 项目结构

```
skill/
  adapter.ts              # Node.js 适配器（调用 Python CLI）
  darkoffice-persistent-skill.md  # Agent 指令文档

runtime/
  engine.py               # 核心游戏引擎
  db.py                   # SQLite 数据存取
  content.py              # 内置角色/事件数据
  materials.py            # 素材库与自定义卡牌
  storylines.py           # 剧情线管理

scripts/
  game_state_cli.py       # Python CLI 入口
  simulate_balance.py     # 平衡性模拟
  build_skill_bundle.py   # 打包脚本
  check_env.sh            # 环境检查
  verify_skill.sh         # 一键功能验证
```

## 验证

```bash
# 一键验证所有核心功能
bash scripts/verify_skill.sh

# 平衡性测试
npm run sim:balance
```
