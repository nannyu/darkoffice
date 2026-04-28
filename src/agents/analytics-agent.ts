import type {
  Agent,
  AgentContext,
  AgentResult,
  AnalyticsSignal,
  BusinessRecord,
  FactorInsight,
  StrategyOption,
} from "./types.js";

const FACTORS: Array<keyof BusinessRecord> = ["inventory", "sales", "footTraffic", "discountRate", "laborCost"];

function numberValues(records: BusinessRecord[], key: keyof BusinessRecord): number[] {
  return records.map((record) => record[key]).filter((value): value is number => typeof value === "number");
}

function correlation(xs: number[], ys: number[]): number {
  if (xs.length !== ys.length || xs.length < 2) {
    return 0;
  }

  const xMean = xs.reduce((sum, value) => sum + value, 0) / xs.length;
  const yMean = ys.reduce((sum, value) => sum + value, 0) / ys.length;
  let numerator = 0;
  let xDenominator = 0;
  let yDenominator = 0;

  for (let i = 0; i < xs.length; i += 1) {
    const xDelta = xs[i] - xMean;
    const yDelta = ys[i] - yMean;
    numerator += xDelta * yDelta;
    xDenominator += xDelta * xDelta;
    yDenominator += yDelta * yDelta;
  }

  const denominator = Math.sqrt(xDenominator * yDenominator);
  return denominator === 0 ? 0 : numerator / denominator;
}

function buildRecommendation(factor: keyof BusinessRecord, corr: number): string {
  const direction = corr >= 0 ? "提升" : "控制";
  const labels: Record<string, string> = {
    inventory: "库存水位",
    sales: "销量",
    footTraffic: "客流",
    discountRate: "折扣率",
    laborCost: "人工成本",
  };
  return `${direction}${labels[String(factor)] ?? String(factor)}，并在 7 天内复盘利润变化。`;
}

function toInsight(records: BusinessRecord[], factor: keyof BusinessRecord): FactorInsight | null {
  const profits = records.map((record) => record.profit);
  const xs = numberValues(records, factor);
  if (xs.length !== profits.length) {
    return null;
  }

  const corr = correlation(xs, profits);
  const abs = Math.abs(corr);
  return {
    factor,
    correlationToProfit: Number(corr.toFixed(3)),
    direction: abs < 0.2 ? "neutral" : corr > 0 ? "positive" : "negative",
    confidence: Number(Math.min(0.95, 0.35 + abs * 0.6).toFixed(2)),
    recommendation: buildRecommendation(factor, corr),
  };
}

function suggestionFromInsight(insight: FactorInsight): StrategyOption {
  const isPositive = insight.direction === "positive";
  const label = String(insight.factor);
  return {
    id: `analytics-${label}`,
    title: `${isPositive ? "放大" : "压降"} ${label}`,
    action: insight.recommendation,
    upside: Math.round(55 + insight.confidence * 35),
    risk: insight.direction === "neutral" ? 45 : Math.round(55 - insight.confidence * 25),
    cost: insight.factor === "laborCost" ? 60 : 40,
    evidence: [`${label} 与 profit 的相关系数为 ${insight.correlationToProfit}`, `置信度 ${insight.confidence}`],
  };
}

export class AnalyticsAgent implements Agent<AnalyticsSignal> {
  id = "analytics" as const;

  async run(context: AgentContext): Promise<AgentResult<AnalyticsSignal>> {
    const records = context.businessData ?? [];
    const insights = FACTORS.map((factor) => toInsight(records, factor))
      .filter((insight): insight is FactorInsight => insight !== null)
      .sort((a, b) => Math.abs(b.correlationToProfit) - Math.abs(a.correlationToProfit));

    return {
      generatedAt: new Date().toISOString(),
      signal: {
        agentId: this.id,
        recordsAnalyzed: records.length,
        targetMetric: "profit",
        factorInsights: insights,
        strategySuggestions: insights.slice(0, 3).map(suggestionFromInsight),
      },
    };
  }
}
