/**
 * 暗黑职场 — 规则汇总导出
 */

export { RESOURCE_ORDER, INITIAL_STATE, RESOURCE_DEFINITIONS, TURNS_PER_DAY, DEFAULT_PROJECT, defaultProject } from './resources';
export { RESOLUTION_TIER_RULES, resolutionTierForScore, tierByRoll } from './resolution';
export { TIME_PERIOD_RULES, timePeriodForTurn, timePeriodWeightModifiers } from './time-period';
export { ACTION_RULES, ACTION_MODIFIERS, ACTION_DISPLAY, ACTION_OPTION_POLICY, buildOptions } from './actions';
export { EVENT_HAZARD_MAP, ACTION_HAZARD_MAP, STATUS_RULES, FAILURE_RULES, CHARACTER_WEIGHT_RULES } from './hazards';
