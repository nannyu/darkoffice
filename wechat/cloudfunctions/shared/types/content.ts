/**
 * 暗黑职场 — 卡牌内容类型
 *
 * 补充 game.ts 中 Character/Event 的扩展字段类型
 */

import type { HazardMapEntry } from './game';

// ---------------------------------------------------------------------------
// 卡牌类型枚举
// ---------------------------------------------------------------------------

export type CardType = 'CHARACTER' | 'EVENT' | 'HAZARD' | 'PROJECT' | 'MECHANIC';

/** 卡牌发布状态 */
export type CardStatus = 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';

// ---------------------------------------------------------------------------
// 卡牌通用结构
// ---------------------------------------------------------------------------

export interface Card {
  card_id: string;
  card_type: CardType;
  card_name: string;
  status: CardStatus;
  version: string;
  payload: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// 自定义角色卡扩展（女娲蒸馏产物）
// ---------------------------------------------------------------------------

export interface DistilledCharacter {
  character_id: string;
  name: string;
  base_weight: number;
  role_type?: string;
  faction?: string;
  tags?: string[];
  passive_effect?: string;
  speech_style?: string;
  // 女娲蒸馏扩展
  mind_model?: string;
  decision_heuristics?: string[];
  inner_tension?: string;
  anti_pattern?: string;
  vulnerability?: string;
}

// ---------------------------------------------------------------------------
// 自定义事件卡扩展（女娲蒸馏产物）
// ---------------------------------------------------------------------------

export interface DistilledEvent {
  event_id: string;
  character_id: string;
  name: string;
  base_effect: Record<string, number>;
  event_category?: string;
  pressure_level?: string;
  tags?: string[];
  flavor_text?: string;
  possible_followups?: string[];
  dice_dc?: number;
  // 女娲蒸馏扩展
  structural_trap?: string;
  hidden_cost?: string;
  hazard_hook?: string;
}

// ---------------------------------------------------------------------------
// 自定义隐患卡扩展（女娲蒸馏产物）
// ---------------------------------------------------------------------------

export interface DistilledHazard extends HazardMapEntry {
  origin_story?: string;
  explosion_scene?: string;
  chain_reaction?: string;
  intervention_chance?: string;
}

// ---------------------------------------------------------------------------
// 剧情线扩展
// ---------------------------------------------------------------------------

export interface DistilledStorylineAct {
  act_index: number;
  title: string;
  character_id: string;
  event_ids: string[];
  completion_condition: string;
  branches: unknown[];
  theme?: string;
  power_arc?: string;
  power_shift?: string;
}
