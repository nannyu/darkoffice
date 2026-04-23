#!/usr/bin/env python3
from __future__ import annotations

import json
import argparse
from html import escape
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from runtime.mechanics import build_mechanics_snapshot  # noqa: E402


OUTPUT_PATH = ROOT / "docs" / "visualizations" / "game-mechanics.html"


def _esc(value: object) -> str:
    return escape(str(value))


def _effect_badges(effect: dict[str, int]) -> str:
    ordered_keys = ["hp", "en", "st", "kpi", "risk", "cor"]
    labels = {"hp": "HP", "en": "EN", "st": "ST", "kpi": "KPI", "risk": "RISK", "cor": "COR"}
    badges = []
    for key in ordered_keys:
        value = int(effect.get(key, 0))
        if value == 0:
            continue
        polarity = "negative" if value < 0 or key in {"risk", "cor"} and value > 0 else "positive"
        prefix = "+" if value > 0 else ""
        badges.append(
            f'<span class="delta-pill {polarity}">{_esc(labels[key])} {prefix}{value}</span>'
        )
    return "".join(badges) or '<span class="delta-pill neutral">无直接数值变化</span>'


def _metric_cards(summary: dict) -> str:
    cards = [
        ("角色池", summary["character_count"]),
        ("事件池", summary["event_count"]),
        ("行动策略", summary["action_count"]),
        ("隐患来源", summary["hazard_count"]),
        ("流程节点", summary["turn_flow_step_count"]),
        ("失败线", summary["failure_rule_count"]),
    ]
    return "".join(
        f"""
        <article class="metric-card">
            <div class="metric-label">{_esc(label)}</div>
            <div class="metric-value">{_esc(value)}</div>
        </article>
        """
        for label, value in cards
    )


def _turn_flow_cards(turn_flow: list[dict]) -> str:
    return "".join(
        f"""
        <article class="flow-card">
            <div class="flow-index">{index:02d}</div>
            <div class="flow-phase">{_esc(step['phase'])}</div>
            <h3>{_esc(step['label'])}</h3>
            <p>{_esc(step['summary'])}</p>
            <div class="flow-id">{_esc(step['id'])}</div>
        </article>
        """
        for index, step in enumerate(turn_flow, start=1)
    )


def _settlement_ladder(steps: list[dict]) -> str:
    return "".join(
        f"""
        <article class="ladder-item">
            <div class="ladder-rank">{int(step['order']):02d}</div>
            <div class="ladder-copy">
                <h3>{_esc(step['label'])}</h3>
                <p>{_esc(step['summary'])}</p>
            </div>
        </article>
        """
        for step in steps
    )


def _resource_cards(resources: list[dict]) -> str:
    return "".join(
        f"""
        <article class="resource-card">
            <div class="eyebrow">{_esc(item['track'])}</div>
            <h3>{_esc(item['label'])}</h3>
            <p>{_esc(item['direction'])}</p>
            <div class="failure-chip">{_esc(item['failure_condition'])} · {_esc(item['failure_outcome'])}</div>
        </article>
        """
        for item in resources
    )


def _time_period_cards(periods: list[dict]) -> str:
    cards = []
    for period in periods:
        badge = '<span class="period-state active">运行中</span>' if period.get("enabled", True) else '<span class="period-state reserved">预留</span>'
        cards.append(
            f"""
            <article class="period-card">
                <div class="period-header">
                    <div>
                        <div class="eyebrow">{_esc(period['window'])}</div>
                        <h3>{_esc(period['id'])}</h3>
                    </div>
                    {badge}
                </div>
                <p class="period-mood">{_esc(period['mood'])}</p>
                <p>{_esc(period['summary'])}</p>
            </article>
            """
        )
    return "".join(cards)


def _action_cards(actions: list[dict]) -> str:
    return "".join(
        f"""
        <article class="action-card">
            <div class="action-top">
                <div>
                    <div class="eyebrow">{_esc(action['action_id'])}</div>
                    <h3>{_esc(action['title'])}</h3>
                </div>
                <div class="mod-badge">{int(action['modifier']):+d}</div>
            </div>
            <div class="action-category">{_esc(action['category'])}</div>
            <p>{_esc(action['summary'])}</p>
            <div class="tradeoff">{_esc(action['tradeoff'])}</div>
        </article>
        """
        for action in actions
    )


def _tier_cards(tiers: list[dict]) -> str:
    return "".join(
        f"""
        <article class="tier-card">
            <div class="tier-range">{_esc(tier['range'])}</div>
            <h3>{_esc(tier['label'])}</h3>
            <div class="tier-multiplier">倍率 {float(tier['multiplier']):.1f}</div>
            <p>{_esc(tier['summary'])}</p>
        </article>
        """
        for tier in tiers
    )


def _character_cards(characters: list[dict]) -> str:
    cards = []
    for character in characters:
        time_bias = "".join(
            f'<span class="mini-chip">{_esc(item["time_period"])} × {float(item["weight"]):.1f}</span>'
            for item in character.get("time_bias", [])
        ) or '<span class="mini-chip muted">无额外时段偏置</span>'
        weight_rules = "".join(
            f'<li><strong>{_esc(rule["label"])}:</strong> {_esc(rule["condition"])} -> {_esc(rule["effect"])}</li>'
            for rule in character.get("weight_rules", [])
        ) or '<li>当前没有额外条件权重。</li>'
        events = "".join(
            f"""
            <article class="event-card">
                <div class="event-head">
                    <h4>{_esc(event['name'])}</h4>
                    <span class="event-id">{_esc(event['event_id'])}</span>
                </div>
                <div class="event-deltas">{_effect_badges(event['base_effect'])}</div>
                {f'<div class="hazard-link">连锁隐患：{_esc(event["hazard"]["name"])} · 倒计时 {int(event["hazard"]["countdown"])} · 严重度 {int(event["hazard"]["severity"])}</div>' if event.get("hazard") else '<div class="hazard-link quiet">当前未直接生成隐患</div>'}
            </article>
            """
            for event in character.get("events", [])
        ) or '<p class="empty-copy">当前没有挂载事件。</p>'

        cards.append(
            f"""
            <details class="character-card" open>
                <summary>
                    <div>
                        <div class="eyebrow">{_esc(character['character_id'])}</div>
                        <h3>{_esc(character['name'])}</h3>
                    </div>
                    <div class="weight-badge">基础权重 {_esc(character['base_weight'])}</div>
                </summary>
                <div class="character-meta">
                    <div class="meta-block">
                        <div class="meta-label">时段偏置</div>
                        <div class="chip-row">{time_bias}</div>
                    </div>
                    <div class="meta-block">
                        <div class="meta-label">额外加压规则</div>
                        <ul class="rule-list">{weight_rules}</ul>
                    </div>
                </div>
                <div class="event-grid">{events}</div>
            </details>
            """
        )
    return "".join(cards)


def _hazard_rows(hazards: list[dict]) -> str:
    return "".join(
        f"""
        <article class="hazard-row">
            <div class="hazard-source">
                <div class="eyebrow">{_esc(item['source_type'])}</div>
                <h3>{_esc(item['source_name'])}</h3>
                <div class="source-id">{_esc(item['source_id'])}</div>
            </div>
            <div class="hazard-arrow">-></div>
            <div class="hazard-card-mini">
                <h4>{_esc(item['hazard']['name'])}</h4>
                <p>倒计时 {int(item['hazard']['countdown'])} / 严重度 {int(item['hazard']['severity'])}</p>
            </div>
        </article>
        """
        for item in hazards
    )


def _failure_cards(failures: list[dict]) -> str:
    return "".join(
        f"""
        <article class="failure-card">
            <div class="failure-rank">P{int(item['priority'])}</div>
            <h3>{_esc(item['label'])}</h3>
            <p>{_esc(item['condition'])}</p>
        </article>
        """
        for item in failures
    )


def build_html(snapshot: dict) -> str:
    snapshot_json = json.dumps(snapshot, ensure_ascii=False)
    snapshot_script = snapshot_json.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>暗黑职场 · 游戏机制总览</title>
  <style>
    :root {{
      --paper: #f6f0e7;
      --paper-strong: #fff9f2;
      --ink: #1f1714;
      --muted: #6f625a;
      --ember: #b44524;
      --ember-deep: #6b1e10;
      --gold: #d4951f;
      --steel: #33424f;
      --line: rgba(31, 23, 20, 0.12);
      --shadow: 0 20px 40px rgba(36, 18, 11, 0.12);
      --radius: 22px;
    }}

    * {{
      box-sizing: border-box;
    }}

    html {{
      scroll-behavior: smooth;
    }}

    body {{
      margin: 0;
      font-family: "Avenir Next", "PingFang SC", "Hiragino Sans GB", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top right, rgba(212, 149, 31, 0.24), transparent 32%),
        radial-gradient(circle at left 15% bottom 10%, rgba(180, 69, 36, 0.16), transparent 28%),
        linear-gradient(180deg, #f8f4ed 0%, #f1e7d9 100%);
      min-height: 100vh;
    }}

    body::before {{
      content: "";
      position: fixed;
      inset: 0;
      background:
        linear-gradient(rgba(31, 23, 20, 0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(31, 23, 20, 0.04) 1px, transparent 1px);
      background-size: 24px 24px;
      opacity: 0.45;
      pointer-events: none;
    }}

    .shell {{
      position: relative;
      max-width: 1440px;
      margin: 0 auto;
      padding: 32px 20px 80px;
    }}

    .hero {{
      display: grid;
      grid-template-columns: 1.3fr 0.8fr;
      gap: 28px;
      align-items: stretch;
      margin-bottom: 28px;
    }}

    .hero-panel,
    .hero-aside,
    section {{
      background: rgba(255, 249, 242, 0.78);
      backdrop-filter: blur(18px);
      border: 1px solid rgba(31, 23, 20, 0.1);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }}

    .hero-panel {{
      padding: 40px;
      position: relative;
    }}

    .hero-panel::after {{
      content: "规则引擎";
      position: absolute;
      right: 24px;
      top: 20px;
      padding: 8px 14px;
      border: 1px solid rgba(180, 69, 36, 0.28);
      border-radius: 999px;
      color: var(--ember);
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }}

    .hero h1,
    section h2,
    .character-card h3,
    .action-card h3,
    .resource-card h3,
    .period-card h3,
    .tier-card h3,
    .failure-card h3 {{
      font-family: "Baskerville", "Songti SC", "STSong", serif;
      font-weight: 700;
      letter-spacing: 0.01em;
    }}

    .hero h1 {{
      font-size: clamp(46px, 7vw, 88px);
      line-height: 0.95;
      margin: 0 0 18px;
      max-width: 10ch;
    }}

    .hero .subtitle {{
      font-size: 18px;
      line-height: 1.75;
      color: var(--muted);
      max-width: 55ch;
      margin-bottom: 22px;
    }}

    .eyebrow {{
      display: inline-block;
      font-size: 12px;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      color: var(--ember);
      margin-bottom: 10px;
    }}

    .hero-stamps {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
    }}

    .stamp {{
      border: 1px solid rgba(31, 23, 20, 0.12);
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 13px;
      background: rgba(255, 255, 255, 0.45);
    }}

    .hero-aside {{
      display: grid;
      grid-template-rows: auto auto;
    }}

    .aside-top,
    .aside-bottom {{
      padding: 26px 28px;
    }}

    .aside-top {{
      border-bottom: 1px solid var(--line);
    }}

    .aside-top p,
    .aside-bottom p {{
      color: var(--muted);
      line-height: 1.7;
      margin: 0;
    }}

    .nav-pills {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}

    .nav-pills a {{
      text-decoration: none;
      color: var(--ink);
      border: 1px solid rgba(31, 23, 20, 0.12);
      padding: 10px 14px;
      border-radius: 999px;
      font-size: 13px;
      background: rgba(255, 255, 255, 0.46);
    }}

    .metrics {{
      display: grid;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      gap: 14px;
      margin-bottom: 28px;
    }}

    .metric-card {{
      background: rgba(255, 249, 242, 0.76);
      border: 1px solid rgba(31, 23, 20, 0.1);
      border-radius: 18px;
      padding: 18px;
      box-shadow: var(--shadow);
    }}

    .metric-label {{
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}

    .metric-value {{
      font-family: "Baskerville", "Songti SC", serif;
      font-size: 34px;
      color: var(--ember-deep);
    }}

    section {{
      padding: 28px;
      margin-bottom: 28px;
    }}

    section h2 {{
      margin: 0 0 8px;
      font-size: clamp(30px, 4vw, 48px);
    }}

    section .lead {{
      margin: 0 0 22px;
      color: var(--muted);
      line-height: 1.75;
      max-width: 72ch;
    }}

    .flow-grid,
    .resource-grid,
    .period-grid,
    .action-grid,
    .tier-grid,
    .failure-grid {{
      display: grid;
      gap: 16px;
    }}

    .flow-grid {{
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }}

    .flow-card,
    .resource-card,
    .period-card,
    .action-card,
    .tier-card,
    .failure-card {{
      border: 1px solid rgba(31, 23, 20, 0.1);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.52);
      padding: 18px;
      min-height: 180px;
    }}

    .flow-card {{
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }}

    .flow-index {{
      width: 42px;
      height: 42px;
      border-radius: 50%;
      border: 1px solid rgba(180, 69, 36, 0.25);
      display: grid;
      place-items: center;
      color: var(--ember);
      font-size: 13px;
      font-weight: 700;
    }}

    .flow-phase,
    .action-category,
    .period-mood,
    .tier-multiplier,
    .failure-rank,
    .mod-badge,
    .weight-badge,
    .period-state,
    .failure-chip,
    .hazard-link {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      width: fit-content;
      border-radius: 999px;
      font-size: 12px;
      padding: 7px 10px;
    }}

    .flow-phase,
    .action-category,
    .period-state.active {{
      background: rgba(212, 149, 31, 0.15);
      color: #8a5a07;
    }}

    .period-state.reserved,
    .hazard-link.quiet,
    .mini-chip.muted {{
      background: rgba(51, 66, 79, 0.08);
      color: var(--steel);
    }}

    .flow-id,
    .event-id,
    .source-id {{
      margin-top: auto;
      font-size: 12px;
      color: var(--muted);
      letter-spacing: 0.08em;
    }}

    .ladder {{
      display: grid;
      grid-template-columns: 1fr 0.9fr;
      gap: 24px;
      align-items: start;
    }}

    .ladder-stack {{
      display: grid;
      gap: 12px;
    }}

    .ladder-item {{
      display: grid;
      grid-template-columns: 64px 1fr;
      gap: 14px;
      align-items: center;
      border: 1px solid rgba(31, 23, 20, 0.1);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.5);
    }}

    .ladder-rank {{
      width: 50px;
      height: 50px;
      border-radius: 14px;
      background: linear-gradient(135deg, rgba(180, 69, 36, 0.14), rgba(212, 149, 31, 0.16));
      display: grid;
      place-items: center;
      color: var(--ember);
      font-weight: 800;
    }}

    .ladder-copy h3,
    .event-card h4,
    .hazard-card-mini h4 {{
      margin: 0 0 6px;
    }}

    .ladder-copy p,
    .flow-card p,
    .resource-card p,
    .period-card p,
    .action-card p,
    .tier-card p,
    .failure-card p,
    .hero-aside p,
    .event-card p {{
      margin: 0;
      line-height: 1.7;
      color: var(--muted);
    }}

    .side-note {{
      border: 1px dashed rgba(31, 23, 20, 0.18);
      border-radius: 18px;
      padding: 18px;
      background: rgba(255, 255, 255, 0.36);
    }}

    .side-note ul,
    .rule-list {{
      margin: 12px 0 0;
      padding-left: 18px;
      color: var(--muted);
      line-height: 1.75;
    }}

    .resource-grid {{
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }}

    .period-grid,
    .action-grid,
    .tier-grid,
    .failure-grid {{
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }}

    .action-top,
    .period-header,
    .event-head,
    .character-card summary {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: flex-start;
    }}

    .mod-badge,
    .weight-badge,
    .failure-rank {{
      background: rgba(180, 69, 36, 0.12);
      color: var(--ember-deep);
      font-weight: 700;
    }}

    .tradeoff {{
      margin-top: 12px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
      color: var(--steel);
      line-height: 1.7;
    }}

    .character-stack {{
      display: grid;
      gap: 16px;
    }}

    .character-card {{
      border: 1px solid rgba(31, 23, 20, 0.12);
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.56);
      padding: 18px 18px 20px;
    }}

    .character-card summary {{
      list-style: none;
      cursor: pointer;
    }}

    .character-card summary::-webkit-details-marker {{
      display: none;
    }}

    .character-meta {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin: 18px 0;
    }}

    .meta-block {{
      padding: 16px;
      border-radius: 16px;
      background: rgba(246, 240, 231, 0.74);
      border: 1px solid rgba(31, 23, 20, 0.08);
    }}

    .meta-label {{
      font-size: 12px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 12px;
    }}

    .chip-row,
    .event-deltas {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}

    .mini-chip,
    .delta-pill {{
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      background: rgba(255, 255, 255, 0.85);
      border: 1px solid rgba(31, 23, 20, 0.08);
    }}

    .delta-pill.negative {{
      background: rgba(180, 69, 36, 0.12);
      color: var(--ember-deep);
    }}

    .delta-pill.positive {{
      background: rgba(45, 122, 87, 0.12);
      color: #226145;
    }}

    .delta-pill.neutral {{
      background: rgba(51, 66, 79, 0.08);
      color: var(--steel);
    }}

    .event-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}

    .event-card,
    .hazard-card-mini {{
      border: 1px solid rgba(31, 23, 20, 0.1);
      border-radius: 16px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.72);
    }}

    .hazard-link {{
      margin-top: 12px;
      background: rgba(180, 69, 36, 0.08);
      color: var(--ember-deep);
    }}

    .hazard-list {{
      display: grid;
      gap: 12px;
    }}

    .hazard-row {{
      display: grid;
      grid-template-columns: 1fr 60px 1fr;
      gap: 16px;
      align-items: center;
      border: 1px solid rgba(31, 23, 20, 0.1);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255, 255, 255, 0.58);
    }}

    .hazard-arrow {{
      text-align: center;
      font-size: 24px;
      color: var(--ember);
    }}

    .footer-note {{
      padding: 22px;
      border-radius: 18px;
      background: rgba(255, 249, 242, 0.74);
      border: 1px solid rgba(31, 23, 20, 0.1);
      box-shadow: var(--shadow);
    }}

    .footer-note code {{
      font-family: "SFMono-Regular", "Menlo", monospace;
      font-size: 13px;
      background: rgba(31, 23, 20, 0.06);
      padding: 2px 6px;
      border-radius: 6px;
    }}

    .empty-copy {{
      color: var(--muted);
      margin: 0;
    }}

    @media (max-width: 1100px) {{
      .hero,
      .ladder {{
        grid-template-columns: 1fr;
      }}

      .metrics,
      .flow-grid,
      .resource-grid,
      .period-grid,
      .action-grid,
      .tier-grid,
      .failure-grid,
      .event-grid,
      .character-meta {{
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }}
    }}

    @media (max-width: 720px) {{
      .shell {{
        padding: 16px 14px 60px;
      }}

      .hero-panel,
      .aside-top,
      .aside-bottom,
      section {{
        padding: 20px;
      }}

      .metrics,
      .flow-grid,
      .resource-grid,
      .period-grid,
      .action-grid,
      .tier-grid,
      .failure-grid,
      .event-grid,
      .character-meta {{
        grid-template-columns: 1fr;
      }}

      .hazard-row {{
        grid-template-columns: 1fr;
      }}

      .hazard-arrow {{
        transform: rotate(90deg);
      }}
    }}
  </style>
</head>
<body>
  <main class="shell">
    <header class="hero">
      <section class="hero-panel" id="top">
        <div class="eyebrow">Dark Office Mechanics Atlas</div>
        <h1>不是你在上班，是系统在结算你。</h1>
        <p class="subtitle">这张图把《暗黑职场》当前规则引擎拆成同一张版图：回合状态机、正式结算链、资源红线、动作取舍、角色事件池、隐患延迟爆炸，以及多条失败结局如何互相咬合。</p>
        <div class="hero-stamps">
          <span class="stamp">确定性优先，关键节点随机</span>
          <span class="stamp">事件压力 -> 行动应对 -> 延迟后果</span>
          <span class="stamp">共享规则源驱动页面</span>
        </div>
      </section>
      <aside class="hero-aside">
        <div class="aside-top">
          <div class="eyebrow">阅读方式</div>
          <p>先看回合流程，再看正式结算顺序，然后去对照资源红线和动作策略。角色与隐患区会告诉你，为什么“眼前最优”经常会变成“几回合后的爆炸”。</p>
          <nav class="nav-pills">
            <a href="#flow">回合流程</a>
            <a href="#resources">资源红线</a>
            <a href="#actions">行动策略</a>
            <a href="#pressure">角色事件池</a>
            <a href="#hazards">隐患链</a>
          </nav>
        </div>
        <div class="aside-bottom">
          <div class="eyebrow">引擎现状</div>
          <p>当前页面基于运行时快照生成。文档中的“深夜”时段已保留为预留档位，但在现有 <strong>24 回合日制</strong> 下尚未启用，这里会明确标识，避免把规划误认为已生效机制。</p>
        </div>
      </aside>
    </header>

    <section class="metrics">{_metric_cards(snapshot["summary"])}</section>

    <section id="flow">
      <div class="eyebrow">Turn State Machine</div>
      <h2>回合状态机</h2>
      <p class="lead">引擎把每回合拆成维护、施压、决策、结算、后果和准备六层。玩家在聊天界面只看到“状态栏 + 事件 + 选项”，但背后其实跑着这条更完整的状态链。</p>
      <div class="flow-grid">{_turn_flow_cards(snapshot["turn_flow"])}</div>
    </section>

    <section id="resolution">
      <div class="eyebrow">Resolution Pipeline</div>
      <h2>正式结算顺序</h2>
      <p class="lead">这条顺序决定了“为什么留痕能保命、为什么硬扛会透支、为什么有些代价不是当场结算”。越靠后的环节，越像系统把账记在未来。</p>
      <div class="ladder">
        <div class="ladder-stack">{_settlement_ladder(snapshot["settlement_order"])}</div>
        <aside class="side-note">
          <div class="eyebrow">触发骰子的时候</div>
          <ul>
            {"".join(f"<li><strong>{_esc(item['label'])}:</strong> {_esc(item['summary'])}</li>" for item in snapshot["roll_triggers"])}
          </ul>
        </aside>
      </div>
    </section>

    <section id="resources">
      <div class="eyebrow">Pressure Tracks</div>
      <h2>资源红线与失败线</h2>
      <p class="lead">六个数值不是同类条。`HP/EN/ST/KPI` 是你撑住系统的底盘，`RISK/COR` 则是系统反过来吞掉你的黑箱计数器。它们共同定义了“活着”和“变脏”之间的张力。</p>
      <div class="resource-grid">{_resource_cards(snapshot["resource_cards"])}</div>
    </section>

    <section id="time">
      <div class="eyebrow">Time Pressure</div>
      <h2>时间段压力分布</h2>
      <p class="lead">时间段决定谁更容易找上门。当前实现已经启用了上午、午休、下午、加班四档，深夜档位仍然保留在规则表里，方便后续扩展更长的工作日节奏。</p>
      <div class="period-grid">{_time_period_cards(snapshot["time_periods"])}</div>
    </section>

    <section id="actions">
      <div class="eyebrow">Action Deck</div>
      <h2>行动策略面板</h2>
      <p class="lead">动作不是技能树，而是生存姿态。修正值只说明“这条路容易成功多少”，真正的差异在于它把代价推向哪条线：透支、背锅、拖延、黑化，还是暂时苟住。</p>
      <div class="action-grid">{_action_cards(snapshot["actions"])}</div>
    </section>

    <section id="tiers">
      <div class="eyebrow">Outcome Quality</div>
      <h2>结果档位</h2>
      <p class="lead">当前引擎用总分档位映射倍率。惩罚项会随倍率缩放，正向收益则按反向逻辑保留，所以大成功不只是“少掉点血”，而是会真正提升你从这一轮里拿到的好处。</p>
      <div class="tier-grid">{_tier_cards(snapshot["resolution_tiers"])}</div>
    </section>

    <section id="pressure">
      <div class="eyebrow">Character Event Pools</div>
      <h2>角色事件池与加压规则</h2>
      <p class="lead">这里展示“谁会来”“为什么会来”“来了之后会把你推向哪条后果链”。展开角色卡可以直接看到事件效果和它可能引爆的隐患。</p>
      <div class="character-stack">{_character_cards(snapshot["characters"])}</div>
    </section>

    <section id="hazards">
      <div class="eyebrow">Delayed Consequences</div>
      <h2>隐患延迟爆炸链</h2>
      <p class="lead">隐患系统是这套机制最阴的部分。很多选项不会立刻杀死你，而是先把问题埋起来，等倒计时归零再一次性炸回 `HP / KPI / RISK`。</p>
      <div class="hazard-list">{_hazard_rows(snapshot["hazard_sources"])}</div>
    </section>

    <section id="failure">
      <div class="eyebrow">Fail States</div>
      <h2>失败结局优先级</h2>
      <p class="lead">如果多条失败线同时触发，引擎会按优先级裁定最终结局。也就是说，暴雷和黑化并不是你唯一需要怕的东西；在那之前，你可能已经先因为崩溃、体力耗尽或绩效归零被系统清出局。</p>
      <div class="failure-grid">{_failure_cards(snapshot["failure_rules"])}</div>
    </section>

    <div class="footer-note">
      这张页面由 <code>python3 scripts/render_mechanics_visual.py</code> 生成，底层数据来自 <code>python3 scripts/game_state_cli.py mechanics</code>。如果规则表更新，重新运行一次渲染脚本即可同步页面。
    </div>
  </main>
  <script type="application/json" id="mechanics-snapshot">{snapshot_script}</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Dark Office mechanics visualization")
    parser.add_argument("--db", default="runtime/darkoffice.sqlite3")
    parser.add_argument("--with-custom", action="store_true", help="包含当前数据库中激活的自定义卡牌")
    args = parser.parse_args()

    snapshot = build_mechanics_snapshot(args.db, include_custom=args.with_custom)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(build_html(snapshot), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "output": str(OUTPUT_PATH),
                "character_count": snapshot["summary"]["character_count"],
                "event_count": snapshot["summary"]["event_count"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
