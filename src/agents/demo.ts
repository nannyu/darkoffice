import { readFileSync } from "node:fs";
import { DarkOfficeAgentOrchestrator } from "./orchestrator.js";
import type { AgentContext, BusinessRecord, StrategyDomain, UserGoal } from "./types.js";

function parseDomain(value: string | undefined): StrategyDomain {
  return value === "workplace" ? "workplace" : "business";
}

function loadBusinessData(path: string | undefined): BusinessRecord[] | undefined {
  if (!path) {
    return undefined;
  }
  return JSON.parse(readFileSync(path, "utf-8")) as BusinessRecord[];
}

async function main(): Promise<void> {
  const domain = parseDomain(process.argv[2]);
  const dataPath = process.argv[3];
  const goal: UserGoal = domain === "business"
    ? {
        id: "goal-profit-demo",
        domain,
        title: "提升门店利润",
        description: "在不显著增加人员成本的前提下，找出影响利润的关键经营因子并形成一周试点策略。",
        successMetric: "单店日利润",
        horizonDays: 14,
      }
    : {
        id: "goal-promotion-demo",
        domain,
        title: "设计职场晋升路径",
        description: "在复杂协作关系中提升可见度、降低背锅风险，并拿到可被评价的阶段性成果。",
        successMetric: "晋升项目认可度",
        horizonDays: 45,
      };

  const context: AgentContext = {
    goal,
    businessData: loadBusinessData(dataPath),
  };
  const result = await new DarkOfficeAgentOrchestrator().run(context);
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
