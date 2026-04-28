"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CHARACTER_NAME_MAP = exports.CHARACTERS = void 0;
exports.CHARACTERS = [
    { character_id: 'CHR_01', name: 'PUA上司', base_weight: 20 },
    { character_id: 'CHR_02', name: '推活同事', base_weight: 18 },
    { character_id: 'CHR_03', name: '甲方金主', base_weight: 15 },
    { character_id: 'CHR_04', name: 'HR笑面虎', base_weight: 10 },
    { character_id: 'CHR_05', name: '财务关键人', base_weight: 12 },
    { character_id: 'CHR_06', name: '派系总监', base_weight: 8 },
];
exports.CHARACTER_NAME_MAP = Object.fromEntries(exports.CHARACTERS.map(c => [c.character_id, c.name]));
