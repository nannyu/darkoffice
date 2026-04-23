# 可视化总览

本目录收纳《暗黑职场》的可视化页面，用来把规则引擎、机制链路和内容池结构更直观地展示出来。

当前页面：

1. `game-mechanics.html`：游戏机制总览页，展示回合状态机、正式结算顺序、资源红线、动作策略、角色事件池和隐患爆炸链。

生成方式：

1. `python3 scripts/game_state_cli.py mechanics`
2. `python3 scripts/render_mechanics_visual.py`

说明：

1. 页面数据来自 `runtime/rules.py` + `runtime/mechanics.py` 的共享规则快照。
2. 若规则引擎发生变更，重新运行渲染脚本即可同步可视化页面。
