# Content Docs

本目录用于定义内容资产与生产规则，回答“写什么内容、按什么模板写、文本调性如何统一”。

当前已建立：

1. [card-templates.md](/Users/niunan/project/darkoffice/docs/content/card-templates.md)
2. [tone-and-writing.md](/Users/niunan/project/darkoffice/docs/content/tone-and-writing.md)
3. [card-taxonomy.md](/Users/niunan/project/darkoffice/docs/content/card-taxonomy.md)
4. [character-roster.md](/Users/niunan/project/darkoffice/docs/content/character-roster.md)
5. [event-library.md](/Users/niunan/project/darkoffice/docs/content/event-library.md)
6. [response-library.md](/Users/niunan/project/darkoffice/docs/content/response-library.md)
7. [sample-card-set.md](/Users/niunan/project/darkoffice/docs/content/sample-card-set.md)

## 素材库与卡牌蒸馏

内容生产现已接入素材库系统和 AI 卡牌蒸馏器：

| 能力 | 说明 | 对应文件 |
|------|------|---------|
| 素材库 | 支持 md/txt/pdf 导入、手动录入、关键词搜索、分类过滤 | `runtime/materials.py` |
| 卡牌蒸馏器 | AI 从素材生成角色卡/事件卡/隐患卡，含 schema 校验 | `scripts/distill_template.py` |
| 自定义卡牌 | 激活后与默认池合并，支持角色/事件/隐患三类 | `runtime/materials.py` |
| 剧情线 | 多幕式剧情编排，激活后引擎按剧情推进 | `runtime/storylines.py` |

### 素材来源示例

- 中央纪委"警钟"栏目：已导入 19 条反腐案例素材（分类：反腐案例）
- 可自行导入：新闻案例、历史事件、个人经历等

### 蒸馏流程

1. 将素材录入素材库（`materials add` 或文件导入）
2. 运行蒸馏器，选择卡牌类型（角色/事件/隐患）
3. 校验生成的 card_data 是否符合 schema
4. 激活自定义卡牌，下一局自动合并入默认池

### 剧情库与自然语言选择

游戏开始时，Agent 自动从剧情库中展示可用剧情线供玩家选择：

| 输入方式 | 说明 |
|---------|------|
| 编号选择 | 输入"1""2"等直接映射到剧情列表序号 |
| 关键词匹配 | 输入"围猎""采购"等匹配剧情标题 |
| 自然语言描述 | 输入"我想体验权力腐蚀"等，Agent 语义匹配 |
| 自由模式 | 输入"自由""随机"等，跳过剧情线 |

> 完整规则见 `darkoffice-skill.md` 第14章（素材库与蒸馏器）、第15章（定制剧情线）。

后续可扩展文档：

1. `status-library.md`
2. `hazard-library.md`
3. `project-library.md`
