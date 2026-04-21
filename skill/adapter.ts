import { spawnSync } from "node:child_process";

type Command =
  | "health"
  | "init"
  | "create"
  | "show"
  | "turn"
  | "history"
  | "stats"
  | "prompt"
  | "play";

function runPython(args: string[]): string {
  const result = spawnSync("python3", ["scripts/game_state_cli.py", ...args], {
    cwd: process.cwd(),
    encoding: "utf-8",
  });

  if (result.error) {
    throw new Error(`python spawn error: ${result.error.message}`);
  }
  if (result.status !== 0) {
    throw new Error(result.stderr || `python exit code ${result.status}`);
  }
  return result.stdout.trim();
}

function parseJsonOutput(raw: string): unknown {
  try {
    return JSON.parse(raw);
  } catch {
    return { message: raw };
  }
}

function renderStatusBar(state: Record<string, unknown>): string {
  const hp = state.hp ?? "?";
  const en = state.en ?? "?";
  const st = state.st ?? "?";
  const kpi = state.kpi ?? "?";
  const risk = state.risk ?? "?";
  const cor = state.cor ?? "?";
  const day = state.day ?? "?";
  const turn = state.turn_index ?? "?";
  return `📊 第 ${day} 天｜第 ${turn} 回合\n生命 ${hp}/100 | 精力 ${en}/100 | 体力 ${st}/100 | 绩效 ${kpi} | 风险 ${risk} | 污染 ${cor}`;
}

function renderTurnOutput(payload: Record<string, unknown>): void {
  const state = (payload.state as Record<string, unknown>) || {};
  // day 和 turn_index 在 payload 根级别
  const displayState = {
    ...state,
    day: payload.day ?? state.day ?? "?",
    turn_index: payload.turn_index ?? state.turn_index ?? "?",
  };
  const delta = (payload.delta as Record<string, unknown>) || {};
  const tier = String(payload.result_tier ?? "?");
  const roll = payload.roll_value ?? "?";
  const score = payload.total_score ?? "?";
  const failure = payload.failure_type as string | null;
  const next = (payload.next_prompt as Record<string, unknown>) || {};
  const options = (next.options as Array<Record<string, unknown>>) || [];

  console.log("\n═══════════════════════════════════════");
  console.log(renderStatusBar(displayState));
  console.log("───────────────────────────────────────");
  console.log(`🎲 骰子: ${roll} | 总分: ${score} | 结果: ${tier}`);
  if (failure) {
    console.log(`💀 失败: ${failure}`);
  }
  console.log(`📉 Delta: HP ${delta.hp ?? 0} | EN ${delta.en ?? 0} | ST ${delta.st ?? 0} | KPI ${delta.kpi ?? 0} | RISK ${delta.risk ?? 0} | COR ${delta.cor ?? 0}`);
  const ending = payload.ending as Record<string, unknown> | null;
  if (ending) {
    const endingType = String(ending.ending_type ?? "");
    const icon = endingType === "good" ? "✨" : endingType === "black" ? "🖤" : "💀";
    console.log(`───────────────────────────────────────`);
    console.log(`${icon} 结局：${ending.name}`);
    console.log(`   ${ending.description}`);
  }
  console.log("───────────────────────────────────────");

  if (options.length > 0 && !failure && !ending) {
    console.log("📋 下一回合选项:");
    for (const opt of options) {
      console.log(`  ${opt.index}. ${opt.title} — ${opt.summary}`);
    }
    console.log(`\n💡 提示: ${next.input_hint ?? "回复编号或行动名称"}`);
  }
  console.log("═══════════════════════════════════════\n");
}

function doHealth(): void {
  const py = spawnSync("python3", ["--version"], { encoding: "utf-8" });
  const ok = py.status === 0;
  const initCheck = spawnSync("python3", ["scripts/game_state_cli.py", "init"], {
    cwd: process.cwd(),
    encoding: "utf-8",
  });
  const dbOk = initCheck.status === 0;

  console.log(
    JSON.stringify(
      {
        ok: ok && dbOk,
        runtime: "python3",
        version: (py.stdout || py.stderr).trim(),
        db_ready: dbOk,
        cwd: process.cwd(),
      },
      null,
      2
    )
  );
  process.exit(ok && dbOk ? 0 : 1);
}

function doPlay(sessionId: string, args: string[]): void {
  let action = "DIRECT_EXECUTE";
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--action" && args[i + 1]) {
      action = args[i + 1];
      break;
    }
  }

  const raw = runPython(["turn", sessionId, "--action", action]);
  const payload = parseJsonOutput(raw) as Record<string, unknown>;
  const wrapped = {
    ok: true,
    command: "turn",
    payload,
  };
  console.log(JSON.stringify(wrapped, null, 2));

  // 同时输出人类可读格式到 stderr，方便交互
  renderTurnOutput(payload);
}

function main(): void {
  const [cmd, ...rest] = process.argv.slice(2) as [Command | undefined, ...string[]];

  if (!cmd) {
    console.log(
      JSON.stringify(
        {
          ok: false,
          error: "missing command",
          usage:
            "health | init [--db path] | create <session_id> [--db path] | show <session_id> [--db path] | turn <session_id> [--action ACTION] [--mod N] [--db path] | history <session_id> [--limit N] [--db path] | stats <session_id> [--db path] | prompt <session_id> [--db path] | play <session_id> [--action ACTION]",
        },
        null,
        2
      )
    );
    process.exit(1);
  }

  if (cmd === "health") {
    doHealth();
    return;
  }

  if (cmd === "play") {
    const sessionId = rest[0];
    if (!sessionId) {
      console.log(JSON.stringify({ ok: false, error: "play requires session_id" }, null, 2));
      process.exit(1);
    }
    doPlay(sessionId, rest.slice(1));
    return;
  }

  const raw = runPython([cmd, ...rest]);
  const payload = parseJsonOutput(raw);
  console.log(
    JSON.stringify(
      {
        ok: true,
        command: cmd,
        payload,
      },
      null,
      2
    )
  );
}

main();
