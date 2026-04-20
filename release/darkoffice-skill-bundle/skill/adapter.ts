import { spawnSync } from "node:child_process";

type Command = "health" | "init" | "create" | "show" | "turn" | "history" | "stats";

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

function main(): void {
  const [cmd, ...rest] = process.argv.slice(2) as [Command | undefined, ...string[]];

  if (!cmd) {
    console.log(
      JSON.stringify(
        {
          ok: false,
          error: "missing command",
          usage:
            "health | init [--db path] | create <session_id> [--db path] | show <session_id> [--db path] | turn <session_id> [--action ACTION] [--mod N] [--db path] | history <session_id> [--limit N] [--db path] | stats <session_id> [--db path]",
        },
        null,
        2
      )
    );
    process.exit(1);
  }

  if (cmd === "health") {
    const py = spawnSync("python3", ["--version"], {
      encoding: "utf-8",
    });
    const ok = py.status === 0;
    console.log(
      JSON.stringify(
        {
          ok,
          runtime: "python3",
          version: (py.stdout || py.stderr).trim(),
          cwd: process.cwd(),
        },
        null,
        2
      )
    );
    process.exit(ok ? 0 : 1);
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
