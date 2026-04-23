from __future__ import annotations

from copy import deepcopy

from runtime.content import CHARACTERS, EVENTS_BY_CHARACTER
from runtime.materials import (
    load_active_custom_characters,
    load_active_custom_events,
    load_active_custom_hazards,
    merge_characters,
    merge_events,
)
from runtime.rules import (
    ACTION_HAZARD_MAP,
    ACTION_RULES,
    CHARACTER_WEIGHT_RULES,
    EVENT_HAZARD_MAP,
    FAILURE_RULES,
    RESOURCE_ORDER,
    RESOLUTION_TIER_RULES,
    ROLL_TRIGGER_SCENARIOS,
    SETTLEMENT_ORDER,
    STATUS_RULES,
    TIME_PERIOD_RULES,
    TURN_FLOW_STEPS,
    default_project,
    rules_catalog,
)


def _character_rule_index() -> dict[str, list[dict]]:
    rules: dict[str, list[dict]] = {}
    for rule in CHARACTER_WEIGHT_RULES:
        character_id = rule.get("character_id")
        if character_id:
            rules.setdefault(str(character_id), []).append(deepcopy(rule))
    return rules


def build_mechanics_snapshot(db_path: str | None = None, include_custom: bool = False) -> dict:
    """构建一份供 CLI、可视化与文档复用的机制快照。"""
    rule_catalog = rules_catalog()
    if include_custom:
        custom_characters = load_active_custom_characters(db_path)
        custom_events = load_active_custom_events(db_path)
        custom_hazards = load_active_custom_hazards(db_path)
    else:
        custom_characters = []
        custom_events = {}
        custom_hazards = {}

    all_characters = merge_characters(CHARACTERS, custom_characters)
    all_events = merge_events(EVENTS_BY_CHARACTER, custom_events)
    combined_event_hazards = {**EVENT_HAZARD_MAP, **custom_hazards}
    character_rule_map = _character_rule_index()

    character_cards = []
    total_event_count = 0
    for character in all_characters:
        events = []
        for event in all_events.get(character.character_id, []):
            hazard = combined_event_hazards.get(event.event_id)
            events.append(
                {
                    "event_id": event.event_id,
                    "name": event.name,
                    "base_effect": deepcopy(event.base_effect),
                    "event_category": event.event_category,
                    "pressure_level": event.pressure_level,
                    "tags": list(event.tags or []),
                    "hazard": deepcopy(hazard) if hazard else None,
                }
            )
        total_event_count += len(events)

        time_bias = []
        for period in TIME_PERIOD_RULES:
            weight = float(period.get("weight_modifiers", {}).get(character.character_id, 1.0))
            if weight != 1.0:
                time_bias.append(
                    {
                        "time_period": period["id"],
                        "weight": weight,
                    }
                )

        character_cards.append(
            {
                "character_id": character.character_id,
                "name": character.name,
                "base_weight": character.base_weight,
                "role_type": character.role_type,
                "faction": character.faction,
                "tags": list(character.tags or []),
                "passive_effect": character.passive_effect,
                "speech_style": character.speech_style,
                "time_bias": time_bias,
                "weight_rules": character_rule_map.get(character.character_id, []),
                "events": events,
            }
        )

    hazard_sources = [
        {
            "source_type": "event",
            "source_id": source_id,
            "source_name": source_id,
            "hazard": deepcopy(hazard),
        }
        for source_id, hazard in combined_event_hazards.items()
    ]
    hazard_sources.extend(
        {
            "source_type": "action",
            "source_id": action_id,
            "source_name": str(ACTION_RULES.get(action_id, {}).get("title", action_id)),
            "hazard": deepcopy(hazard),
        }
        for action_id, hazard in ACTION_HAZARD_MAP.items()
    )

    return {
        "summary": {
            "character_count": len(character_cards),
            "event_count": total_event_count,
            "action_count": len(ACTION_RULES),
            "hazard_count": len(hazard_sources),
            "turn_flow_step_count": len(TURN_FLOW_STEPS),
            "status_rule_count": len(STATUS_RULES),
            "failure_rule_count": len(FAILURE_RULES),
        },
        "rules": rule_catalog,
        "resource_cards": [
            {
                "resource_id": resource_id,
                **deepcopy(rule_catalog["resources"][resource_id]),
            }
            for resource_id in RESOURCE_ORDER
        ],
        "turn_flow": deepcopy(TURN_FLOW_STEPS),
        "settlement_order": deepcopy(SETTLEMENT_ORDER),
        "roll_triggers": deepcopy(ROLL_TRIGGER_SCENARIOS),
        "resolution_tiers": deepcopy(RESOLUTION_TIER_RULES),
        "actions": [
            {"action_id": action_id, **deepcopy(rule)}
            for action_id, rule in ACTION_RULES.items()
        ],
        "statuses": deepcopy(STATUS_RULES),
        "time_periods": deepcopy(TIME_PERIOD_RULES),
        "character_weight_rules": deepcopy(CHARACTER_WEIGHT_RULES),
        "characters": character_cards,
        "hazard_sources": hazard_sources,
        "default_project": default_project(),
        "failure_rules": deepcopy(FAILURE_RULES),
    }
