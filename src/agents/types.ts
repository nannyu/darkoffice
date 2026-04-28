export type AgentId = "game" | "analytics" | "execution" | "risk";

export type StrategyDomain = "workplace" | "business";

export interface UserGoal {
  id: string;
  domain: StrategyDomain;
  title: string;
  description: string;
  successMetric: string;
  horizonDays: number;
}

export interface SimulationRole {
  id: string;
  name: string;
  role: "boss" | "peer" | "client" | "user" | "system";
  incentives: string[];
  riskTolerance: number;
  influence: number;
}

export interface StrategyOption {
  id: string;
  title: string;
  action: string;
  upside: number;
  risk: number;
  cost: number;
  evidence: string[];
}

export interface GameSignal {
  agentId: "game";
  scenario: string;
  roles: SimulationRole[];
  options: StrategyOption[];
  recommendedOptionId: string;
  behavioralForecast: string[];
}

export interface BusinessRecord {
  period: string;
  profit: number;
  inventory: number;
  sales: number;
  footTraffic?: number;
  discountRate?: number;
  laborCost?: number;
}

export interface FactorInsight {
  factor: keyof BusinessRecord;
  correlationToProfit: number;
  direction: "positive" | "negative" | "neutral";
  confidence: number;
  recommendation: string;
}

export interface AnalyticsSignal {
  agentId: "analytics";
  recordsAnalyzed: number;
  targetMetric: "profit";
  factorInsights: FactorInsight[];
  strategySuggestions: StrategyOption[];
}

export interface RiskSignal {
  agentId: "risk";
  riskScore: number;
  riskLevel: "low" | "medium" | "high";
  assumptions: string[];
  mitigations: string[];
}

export interface ActionStep {
  id: string;
  owner: "user" | "manager" | "team" | "system";
  title: string;
  detail: string;
  dueInDays: number;
  successSignal: string;
}

export interface ExecutionPlan {
  agentId: "execution";
  strategyTitle: string;
  decisionSummary: string;
  rationaleChain: string[];
  actionPath: ActionStep[];
  feedbackSignals: string[];
  modelUpdates: ModelUpdate[];
}

export interface ModelUpdate {
  parameter: string;
  currentValue: number;
  adjustmentRule: string;
}

export interface AgentContext {
  goal: UserGoal;
  businessData?: BusinessRecord[];
}

export interface AgentResult<TSignal> {
  signal: TSignal;
  generatedAt: string;
}

export interface Agent<TSignal> {
  id: AgentId;
  run(context: AgentContext): Promise<AgentResult<TSignal>>;
}

export interface DecisionRun {
  goal: UserGoal;
  game: GameSignal;
  analytics?: AnalyticsSignal;
  risk: RiskSignal;
  execution: ExecutionPlan;
}
