import { AnalyticsAgent } from "./analytics-agent.js";
import { ExecutionAgent } from "./execution-agent.js";
import { GameAgent } from "./game-agent.js";
import { RiskAgent } from "./risk-agent.js";
import type { AgentContext, DecisionRun } from "./types.js";

export class DarkOfficeAgentOrchestrator {
  private readonly gameAgent = new GameAgent();
  private readonly analyticsAgent = new AnalyticsAgent();
  private readonly riskAgent = new RiskAgent();
  private readonly executionAgent = new ExecutionAgent();

  async run(context: AgentContext): Promise<DecisionRun> {
    const analyticsPromise = context.goal.domain === "business" ? this.analyticsAgent.run(context) : undefined;
    const [game, risk, analytics] = await Promise.all([
      this.gameAgent.run(context),
      this.riskAgent.run(context),
      analyticsPromise,
    ]);

    const execution = this.executionAgent.run(
      context.goal,
      game.signal,
      risk.signal,
      analytics?.signal
    );

    return {
      goal: context.goal,
      game: game.signal,
      analytics: analytics?.signal,
      risk: risk.signal,
      execution,
    };
  }
}
