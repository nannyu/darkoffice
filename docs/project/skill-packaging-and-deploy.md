# Skill 封装与部署说明

## 目标

将 `darkoffice` 整理为可直接部署的 Skill 形态，支持 OpenClaw、WorkBuddy、Qclaw 三平台即插即用。

## 封装结构

- `skill.md`：根目录标准 Skill 入口文档
- `skill/adapter.ts`：统一命令入口（health/init/create/show/turn/prompt/history/stats）
- `runtime/*.py`：规则引擎与 SQLite 持久化
- `scripts/check_env.sh`：部署前环境自检
- `scripts/build_skill_bundle.py`：一键打包 `release/darkoffice-skill-bundle`
- `deploy/manifests/*.skill.json`：三平台清单文件
- `deploy/templates/DEPLOYMENT.md`：部署标准流程

## 快速部署流程

1. `npm ci`
2. `npm run skill:check-env`
3. `npm run skill:bundle`
4. 读取并导入对应平台清单：
   - OpenClaw: `deploy/manifests/openclaw.skill.json`
   - WorkBuddy: `deploy/manifests/workbuddy.skill.json`
   - Qclaw: `deploy/manifests/qclaw.skill.json`

## 运行命令（统一）

- 初始化：`npm run skill:init`
- 创建会话：`npm run skill:create -- <session_id>`
- 推进回合：`npm run skill:turn -- <session_id> --action <ACTION_TYPE>`
- 下一回合渲染块：`npm run skill:prompt -- <session_id>`
- 查询状态：`npm run skill:show -- <session_id>`
- 查询历史：`npm run skill:history -- <session_id> --limit 10`
- 查询统计：`npm run skill:stats -- <session_id>`

## 发布前验收

1. 单会话链路：init → create → turn → show → history → stats
2. 回合连续性：`turn` 返回中必须包含 `next_prompt`，且前端直接渲染，不等待“继续”
3. 自动仿真：`python3 scripts/simulate_balance.py --runs 20 --turns 30`
4. 报告确认：`docs/project/balance-report.md`
