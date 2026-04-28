import type { Agent, AgentContext, AgentResult, RiskSignal } from "./types.js";

export class RiskAgent implements Agent<RiskSignal> {
  id = "risk" as const;

  async run(context: AgentContext): Promise<AgentResult<RiskSignal>> {
    const hasData = Boolean(context.businessData?.length);
    const horizonPenalty = context.goal.horizonDays < 14 ? 18 : context.goal.horizonDays > 90 ? 10 : 5;
    const dataPenalty = context.goal.domain === "business" && !hasData ? 35 : 8;
    const ambiguityPenalty = context.goal.description.length < 20 ? 18 : 6;
    const riskScore = Math.min(100, horizonPenalty + dataPenalty + ambiguityPenalty + 20);

    return {
      generatedAt: new Date().toISOString(),
      signal: {
        agentId: this.id,
        riskScore,
        riskLevel: riskScore >= 70 ? "high" : riskScore >= 45 ? "medium" : "low",
        assumptions: [
          "目标指标可以被周期性观测。",
          "用户能拿到关键行动的执行反馈。",
          hasData ? "经营数据样本可用于初步归因。" : "当前缺少结构化经营数据，分析结论以假设为主。",
        ],
        mitigations: [
          "所有策略先做小范围试点。",
          "关键沟通动作保留书面记录。",
          "每轮反馈只调整一个主要参数，避免无法归因。",
        ],
      },
    };
  }
}
