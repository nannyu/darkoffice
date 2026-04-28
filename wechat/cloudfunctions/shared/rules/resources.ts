/**
 * 暗黑职场 — 资源定义 & 基础常量
 *
 * 转译自 Python runtime/rules.py + engine.py
 */

import type { ResourceType, ResourceDefinition, ResourceState, Project } from '../types/game';

export { RESOURCE_ORDER, INITIAL_STATE } from '../types/game';

/** 资源元数据定义 */
export const RESOURCE_DEFINITIONS: Readonly<Record<ResourceType, ResourceDefinition>> = {
  hp: { label: '生命', track: '生存线', direction: '越高越安全', failure_condition: 'HP <= 0', failure_outcome: '崩溃出局' },
  en: { label: '精力', track: '心智线', direction: '越高越稳定', failure_condition: 'EN <= 0', failure_outcome: '精神崩溃' },
  st: { label: '体力', track: '耐久线', direction: '越高越能硬扛', failure_condition: 'ST <= 0', failure_outcome: '体力耗尽' },
  kpi: { label: '绩效', track: '组织评价线', direction: '越高越能苟住岗位', failure_condition: 'KPI <= 0', failure_outcome: '被开除' },
  risk: { label: '风险', track: '暴雷线', direction: '越低越安全', failure_condition: 'RISK >= 100', failure_outcome: '暴雷结局' },
  cor: { label: '污染', track: '黑化线', direction: '越低越干净', failure_condition: 'COR >= 100', failure_outcome: '黑化结局' },
};

/** 每 24 回合为 1 个工作日 */
export const TURNS_PER_DAY = 24;

/** 默认项目模板 */
export const DEFAULT_PROJECT: Readonly<Project> = {
  id: 'PRJ_WEEKLY', name: '本周交付', progress: 0, target: 5, pressure: 2,
};

/** 返回一份可安全修改的默认项目 */
export function defaultProject(): Project {
  return { ...DEFAULT_PROJECT };
}
