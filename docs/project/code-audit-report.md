# 暗黑职场项目代码审计报告

> 审计时间：2026-04-20 | 审计范围：runtime/、scripts/、skill/ | 代码量：~600行 Python + ~80行 TypeScript
> 修复时间：2026-04-20 | 所有问题已修复 ✅

---

## 📊 审计总览

| 类别 | 数量 | 修复状态 |
|------|------|---------|
| 🔴 严重 Bug | 2 | ✅ 已修复 |
| 🟠 逻辑缺陷 | 4 | ✅ 已修复 |
| 🟡 代码质量 | 3 | ✅ 已修复 |
| 🟢 安全问题 | 1 | ✅ 已修复 |
| ✅ 设计合理 | 5 | — |

---

## 🔴 严重 Bug

### BUG-1: 结算倍率对正值效果方向反转 ✅ 已修复

**文件**: `runtime/engine.py` 第 280 行

```python
base_event_delta = {k: int(v * multiplier) for k, v in event["base_effect"].items()}
```

**问题**: 统一倍率对负值（惩罚）方向正确，但对正值（奖励）方向反转。

| 结果等级 | 倍率 | EN:-18（惩罚） | KPI:+3（奖励） | 正确性 |
|---------|------|---------------|---------------|--------|
| CRITICAL_FAIL | ×1.5 | -27 ✅ 加重惩罚 | +4 ❌ 加重奖励 | 奖励应减少 |
| SUCCESS | ×0.4 | -7 ✅ 减轻惩罚 | +1 ❌ 减少奖励 | 奖励应保留 |
| CRITICAL_SUCCESS | ×0.2 | -3 ✅ 大幅减轻 | +0 ❌ 奖励归零 | 奖励应增加 |

**影响**: 
- 大失败时反而获得更多 KPI 奖励
- 大成功时 KPI 奖励几乎归零
- 这与核心设计"短期收益伴随长期代价"矛盾——玩家反而希望掷出低分来获取更多KPI

**修复建议**: 
```python
base_event_delta = {}
for k, v in event["base_effect"].items():
    if v >= 0:  # 正值（奖励）：好结果应保留/增加
        adjusted = int(v * (2.0 - multiplier))  # 反转倍率
    else:  # 负值（惩罚）：好结果应减轻
        adjusted = int(v * multiplier)
    base_event_delta[k] = adjusted
```

---

### BUG-2: 数据库连接泄漏 ✅ 已修复

**文件**: `runtime/engine.py` — `_pick_character()`, `_pick_event()`, `apply_turn()`

**问题**: 每次调用 `apply_turn()` 至少打开 3 个 SQLite 连接，但从未关闭。

- `apply_turn()` 本身打开 1 个
- `_pick_character()` 内部打开 1 个
- `_pick_event()` 内部打开 1 个

**影响**: 
- 30回合游戏 = 90个未关闭连接
- 模拟脚本 20 runs × 30 turns = 1800个未关闭连接
- 长时间运行可能耗尽文件描述符
- SQLite 在 WAL 模式下可能导致锁竞争

**修复建议**: 
```python
def apply_turn(session_id, action_type, action_mod=None, db_path=None):
    conn = connect(db_path)
    try:
        # 把 _pick_character 和 _pick_event 改为接收 conn 参数
        character_id = _pick_character(raw_session, conn)
        event = _pick_event(session_id, character_id, conn)
        ...
    finally:
        conn.close()
```

---

## 🟠 逻辑缺陷

### DEFECT-1: `day` 字段永远不递增 ✅ 已修复

**文件**: `runtime/db.py` + `runtime/engine.py`

`game_sessions` 表有 `day` 字段（初始值 1），但 `apply_turn()` 的 UPDATE 语句没有递增它。Skill 文档定义了"上午→午休→下午→加班→深夜"的时间段系统，但代码完全没有实现。

**影响**: 时间段相关的权重修正无法生效（晚间上司概率更高、午休恢复机会等）

**优先级**: 中（当前版本不依赖时间段，但与设计文档不一致）

---

### DEFECT-2: 部分事件缺少隐患生成 ✅ 已修复

**文件**: `runtime/engine.py` — `_new_hazard()`

Skill 文档定义了多条事件应生成隐患卡，但代码只覆盖了 4 种情况：

| 事件 | 文档要求 | 代码实现 |
|------|---------|---------|
| EVT_04 (上次那个问题是谁负责的) | 生成"责任未明确"隐患 | ❌ 缺失 |
| EVT_07 (先做了再说) | 生成"口头承诺"隐患 | ❌ 缺失 |
| EVT_17 (先倒签一下) | 生成"倒签文件"隐患(countdown=5) | ⚠️ 只生成了通用"合规隐患"(countdown=3) |
| EVT_18 (报销材料再补一下) | 生成"报销缺材料"隐患 | ❌ 缺失 |
| EVT_14 (先别发邮件) | 阻止留痕→RISK+5 | ❌ 完全缺失 |

**影响**: 隐患系统深度不足，"延迟爆炸"的核心体验被削弱

---

### DEFECT-3: "被盯上"状态生成逻辑与文档不一致 ✅ 已修复

**文件**: `runtime/engine.py` — `_derive_statuses()`

代码逻辑：当任意隐患 countdown ≤ 1 时生成"被盯上"。

文档定义："被盯上"应由特定事件（EVT_03、EVT_11）触发，不是隐患倒计时的副作用。

**影响**: 
- 隐患即将爆炸的玩家会额外获得"被盯上"惩罚
- 这可能导致滚雪球效应：隐患→被盯上→更多压力→更多隐患

---

### DEFECT-4: 项目自动补充未记录在文档 ✅ 已修复

**文件**: `runtime/engine.py` 第 304-305 行

```python
if not projects:
    projects = [{"id": "PRJ_WEEKLY", "name": "本周交付", ...}]
```

当所有项目完成后，自动补充一个新项目。这个行为没有在任何文档中定义，也没有在 Skill 中告知玩家。

**影响**: 玩家可能认为完成项目就能喘口气，但系统会立即压上新项目

---

## 🟡 代码质量

### QUALITY-1: `_status_modifier` 增加了文档未定义的修正

代码中 `KPI < 40` 给 -1 修正，`RISK >= 50` 给 -1 修正。但 Skill 文档中这两个只影响事件权重，不影响骰子修正。

---

### QUALITY-2: `content.py` 事件效果值与 Skill 文档不一致

Skill 文档定义了范围值（如 EN -15~-25），但代码使用固定值。部分固定值落在文档范围外：

| 事件 | 文档范围 | 代码值 | 偏差 |
|------|---------|--------|------|
| EVT_01 EN | -15~-25 | -18 | 在范围内 ✅ |
| EVT_01 KPI | +2~+6 | +3 | 在范围内 ✅ |
| EVT_09 ST | -10~-20 | -14 | 在范围内 ✅ |
| EVT_17 RISK | +10~+20 | +15 | 在范围内 ✅ |

大部分值在范围内，但固定值丧失了随机性，降低了重玩体验。

---

### QUALITY-3: Persistent Skill 文档只列出 6 种行动

`skill/darkoffice-persistent-skill.md` 只列出了 6 种行动修正，但 `content.py` 定义了 10 种。缺失：`DIRECT_EXECUTE`、`REQUEST_CONFIRMATION`、`DELAY_AVOID`、`BOUNDARY_RESTATE`。

---

## 🟢 安全问题

### SEC-1: 相对路径数据库 ✅ 已修复

`DEFAULT_DB_PATH = Path("runtime/darkoffice.sqlite3")` 是相对路径，依赖 CWD。如果从不同目录运行 CLI，会在错误位置创建数据库。

**修复建议**: 改为基于项目根目录的绝对路径：
```python
DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "runtime" / "darkoffice.sqlite3"
```

---

## ✅ 设计合理的部分

1. **参数化 SQL 查询** — session_id 全部使用 `?` 占位符，无 SQL 注入风险
2. **SQLite 持久化架构** — game_sessions + turn_logs 分层设计合理，支持审计和回溯
3. **数据库迁移机制** — `_migrate_turn_logs()` 逐列检测补齐，向后兼容
4. **骰子边界正确** — `_tier_by_roll()` 阈值与文档完全一致
5. **adapter.ts 桥接层** — Node.js → Python 的桥接设计简洁清晰

---

## 🔧 修复优先级建议

| 优先级 | 项目 | 工作量 |
|--------|------|--------|
| P0 | BUG-1: 结算倍率正值反转 | 30分钟 |
| P0 | BUG-2: 连接泄漏 | 1小时 |
| P1 | DEFECT-1: day 递增 | 2小时（需设计时间段系统） |
| P1 | DEFECT-2: 补全隐患生成 | 1小时 |
| P2 | DEFECT-3/4: 状态与项目逻辑 | 1小时 |
| P2 | SEC-1: 相对路径 | 15分钟 |
| P3 | QUALITY-1~3: 文档同步 | 1小时 |
