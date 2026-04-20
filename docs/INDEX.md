# Dark Office Documentation Index

本文档是《暗黑职场》项目的内部文档导航中枢。它负责说明该看什么、先看什么、哪个文档对哪个问题负责，但不承担大段规则细节的定义职责。

## 当前文档状态

- 项目处于文档建设阶段
- 技术栈尚未定案
- 开发实现尚未启动
- 当前优先目标是把玩法、系统、内容和协作边界打磨成熟

## 阅读顺序

1. [README.md](/Users/niunan/project/darkoffice/README.md)
2. [docs/collaboration/development-guidelines.md](/Users/niunan/project/darkoffice/docs/collaboration/development-guidelines.md)
3. [project/README.md](/Users/niunan/project/darkoffice/docs/project/README.md)
4. [design/README.md](/Users/niunan/project/darkoffice/docs/design/README.md)
5. [systems/README.md](/Users/niunan/project/darkoffice/docs/systems/README.md)
6. [content/README.md](/Users/niunan/project/darkoffice/docs/content/README.md)
7. [archive/legacy-docs.md](/Users/niunan/project/darkoffice/docs/archive/legacy-docs.md)

## 文档分区

### `project/`

定义项目定位、设计目标、版本边界、阶段目标与术语表。

- [project/README.md](/Users/niunan/project/darkoffice/docs/project/README.md)
- [project/positioning.md](/Users/niunan/project/darkoffice/docs/project/positioning.md)
- [project/scope-and-milestones.md](/Users/niunan/project/darkoffice/docs/project/scope-and-milestones.md)
- [project/glossary.md](/Users/niunan/project/darkoffice/docs/project/glossary.md)
- [project/design-pillars.md](/Users/niunan/project/darkoffice/docs/project/design-pillars.md)

### `design/`

定义玩家体验、核心循环、进程推进、结局方向等玩法设计内容。

- [design/README.md](/Users/niunan/project/darkoffice/docs/design/README.md)
- [design/core-loop.md](/Users/niunan/project/darkoffice/docs/design/core-loop.md)
- [design/game-overview.md](/Users/niunan/project/darkoffice/docs/design/game-overview.md)
- [design/progression.md](/Users/niunan/project/darkoffice/docs/design/progression.md)
- [design/endings.md](/Users/niunan/project/darkoffice/docs/design/endings.md)

### `systems/`

定义卡牌系统、数值规则、回合流程、事件生成、角色与状态等正式规则。

- [systems/README.md](/Users/niunan/project/darkoffice/docs/systems/README.md)
- [systems/card-system.md](/Users/niunan/project/darkoffice/docs/systems/card-system.md)
- [systems/turn-flow.md](/Users/niunan/project/darkoffice/docs/systems/turn-flow.md)
- [systems/stats-and-resources.md](/Users/niunan/project/darkoffice/docs/systems/stats-and-resources.md)
- [systems/event-generation.md](/Users/niunan/project/darkoffice/docs/systems/event-generation.md)
- [systems/character-system.md](/Users/niunan/project/darkoffice/docs/systems/character-system.md)
- [systems/status-hazard-project.md](/Users/niunan/project/darkoffice/docs/systems/status-hazard-project.md)
- [systems/rules-and-resolution.md](/Users/niunan/project/darkoffice/docs/systems/rules-and-resolution.md)
- [systems/conversation-interaction.md](/Users/niunan/project/darkoffice/docs/systems/conversation-interaction.md)

### `content/`

定义角色池、事件库、卡牌模板、文本风格与内容生产规范。

- [content/README.md](/Users/niunan/project/darkoffice/docs/content/README.md)
- [content/card-templates.md](/Users/niunan/project/darkoffice/docs/content/card-templates.md)
- [content/tone-and-writing.md](/Users/niunan/project/darkoffice/docs/content/tone-and-writing.md)
- [content/card-taxonomy.md](/Users/niunan/project/darkoffice/docs/content/card-taxonomy.md)
- [content/character-roster.md](/Users/niunan/project/darkoffice/docs/content/character-roster.md)
- [content/event-library.md](/Users/niunan/project/darkoffice/docs/content/event-library.md)
- [content/response-library.md](/Users/niunan/project/darkoffice/docs/content/response-library.md)
- [content/sample-card-set.md](/Users/niunan/project/darkoffice/docs/content/sample-card-set.md)

### `collaboration/`

定义开发规范、文档规范、交接方式与 AI/Agent 协作规则。

- [collaboration/README.md](/Users/niunan/project/darkoffice/docs/collaboration/README.md)
- [collaboration/development-guidelines.md](/Users/niunan/project/darkoffice/docs/collaboration/development-guidelines.md)
- [collaboration/source-of-truth.md](/Users/niunan/project/darkoffice/docs/collaboration/source-of-truth.md)
- [collaboration/doc-style-guide.md](/Users/niunan/project/darkoffice/docs/collaboration/doc-style-guide.md)
- [collaboration/agent-handoff.md](/Users/niunan/project/darkoffice/docs/collaboration/agent-handoff.md)
- [collaboration/change-log.md](/Users/niunan/project/darkoffice/docs/collaboration/change-log.md)

### `archive/`

保留历史文档、迁移说明与废弃文档映射，不再承担现行事实源职责。

- [archive/legacy-docs.md](/Users/niunan/project/darkoffice/docs/archive/legacy-docs.md)
- [archive/initial-design-source-compendium.md](/Users/niunan/project/darkoffice/docs/archive/initial-design-source-compendium.md)

## 当前事实源优先级

1. 结构化子文档中的最新定义
2. `docs/collaboration/development-guidelines.md` 中的协作与开发规则
3. `docs/INDEX.md` 中的导航与阅读顺序说明
4. 根目录历史策划文档中的未迁移内容

当多个文档表述冲突时，以结构化子文档中的最新定义为准；历史总案只用于追溯，不用于覆盖现行规则。

## 文档迁移原则

- 先建立主题文档，再迁移历史内容
- 迁移时优先去重，不做机械复制
- 新共识只写入目标子文档，不再回填到历史总案中
- 历史文档一旦被正式拆分，应在 `archive/` 中补充映射关系

## 后续可扩展文档

以下文档不是当前阶段的必需事实源，但后续深入内容生产或技术预研时可以继续补充：

1. `docs/systems/data-structure-spec.md`
2. `docs/content/status-library.md`
3. `docs/content/hazard-library.md`
4. `docs/content/project-library.md`
5. `docs/collaboration/review-checklist.md`
