/**
 * 暗黑职场 — 内置角色
 */

import type { Character } from '../types/game';

export const CHARACTERS: readonly Character[] = [
  { character_id: 'CHR_01', name: 'PUA上司', base_weight: 20 },
  { character_id: 'CHR_02', name: '推活同事', base_weight: 18 },
  { character_id: 'CHR_03', name: '甲方金主', base_weight: 15 },
  { character_id: 'CHR_04', name: 'HR笑面虎', base_weight: 10 },
  { character_id: 'CHR_05', name: '财务关键人', base_weight: 12 },
  { character_id: 'CHR_06', name: '派系总监', base_weight: 8 },
];

export const CHARACTER_NAME_MAP: Readonly<Record<string, string>> = Object.fromEntries(
  CHARACTERS.map(c => [c.character_id, c.name])
);
