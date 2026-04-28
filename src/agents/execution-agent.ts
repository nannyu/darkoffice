import type { AnalyticsSignal, ExecutionPlan, GameSignal, RiskSignal, StrategyOption, UserGoal } from "./types.js";

function optionScore(option: StrategyOption): number {
  return option.upside - option.risk * 0.8 - option.cost * 0.2;
}

function pickStrategy(game: GameSignal, analytics?: AnalyticsSignal): StrategyOption {
  const candidates = [...game.options, ...(analytics?.strategySuggestions ?? [])];
  return candidates.sort((a, b) => optionScore(b) - optionScore(a))[0];
}

export class ExecutionAgent {
  id = "execution" as const;

  run(goal: UserGoal, game: GameSignal, risk: RiskSignal, analytics?: AnalyticsSignal): ExecutionPlan {
    const strategy = pickStrategy(game, analytics);
    const topInsight = analytics?.factorInsights[0];

    return {
      agentId: this.id,
      strategyTitle: strategy.title,
      decisionSummary: `围绕「${goal.title}」，优先执行「${strategy.title}」。`,
      rationaleChain: [
        `目标指标：${goal.successMetric}，周期：${goal.horizonDays} 天。`,
        `行为模拟建议：${game.behavioralForecast[0]}`,
        topInsight
          ? `数据证据：${String(topInsight.factor)} 与利润相关系数 ${topInsight.correlationToProfit}。`
          : "数据证据：当前以行为模拟和风险假设为主。",
        `风险等级：${risk.riskLevel}，先用低成本试点验证。`,
      ],
      actionPath: [
        {
          id: "step-1",
          owner: "user",
          title: "定义试点边界",
          detail: `把「${strategy.action}」限定在一个团队、一个门店或一个关键项目内。`,
          dueInDays: 1,
          successSignal: "试点范围、负责人、目标指标被写入记录。",
        },
        {
          id: "step-2",
          owner: "user",
          title: "执行关键动作",
          detail: strategy.action,
          dueInDays: Math.min(7, Math.max(2, Math.floor(goal.horizonDays / 4))),
          successSignal: "行动完成并收集至少一条定量或定性反馈。",
        },
        {
          id: "step-3",
          owner: "system",
          title: "复盘并修正参数",
          detail: "比较试点前后指标，更新风险权重、角色反应和经营因子权重。",
          dueInDays: Math.min(14, Math.max(7, Math.floor(goal.horizonDays / 2))),
          successSignal: `${goal.successMetric} 出现方向性变化，或明确识别阻塞原因。`,
        },
      ],
      feedbackSignals: [
        goal.successMetric,
        "关键角色态度变化",
        "执行成本偏差",
        "风险事件数量",
      ],
      modelUpdates: [
        {
          parameter: "behavioralRiskWeight",
          currentValue: risk.riskScore / 100,
          adjustmentRule: "若负反馈多于正反馈，上调 0.05；否则下调 0.03。",
        },
        {
          parameter: topInsight ? `${String(topInsight.factor)}Weight` : "evidenceConfidence",
          currentValue: topInsight?.confidence ?? 0.4,
          adjustmentRule: "根据试点结果与目标指标的同向程度更新。",
        },
      ],
    };
  }
}
