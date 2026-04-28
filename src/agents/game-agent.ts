import type { Agent, AgentContext, AgentResult, GameSignal, SimulationRole, StrategyOption } from "./types.js";

const workplaceRoles: SimulationRole[] = [
  {
    id: "boss",
    name: "直属老板",
    role: "boss",
    incentives: ["降低风险外溢", "获得可汇报结果", "控制团队资源"],
    riskTolerance: 0.45,
    influence: 0.9,
  },
  {
    id: "peer",
    name: "协作同事",
    role: "peer",
    incentives: ["避免背锅", "争取可见功劳", "维持关系"],
    riskTolerance: 0.55,
    influence: 0.55,
  },
  {
    id: "client",
    name: "内部客户",
    role: "client",
    incentives: ["更快交付", "更少约束", "把压力转移给执行方"],
    riskTolerance: 0.7,
    influence: 0.7,
  },
];

const businessRoles: SimulationRole[] = [
  {
    id: "store_manager",
    name: "门店负责人",
    role: "boss",
    incentives: ["提升利润", "减少损耗", "稳定排班"],
    riskTolerance: 0.5,
    influence: 0.85,
  },
  {
    id: "frontline",
    name: "一线员工",
    role: "peer",
    incentives: ["降低操作复杂度", "减少临时加班", "拿到清晰指令"],
    riskTolerance: 0.4,
    influence: 0.5,
  },
  {
    id: "customer",
    name: "顾客",
    role: "client",
    incentives: ["买到合适商品", "获得即时优惠", "减少等待"],
    riskTolerance: 0.6,
    influence: 0.75,
  },
];

function buildWorkplaceOptions(): StrategyOption[] {
  return [
    {
      id: "visible-alignment",
      title: "先对齐目标，再争取资源",
      action: "把晋升目标拆成可汇报成果，主动约老板确认优先级和评价口径。",
      upside: 82,
      risk: 38,
      cost: 45,
      evidence: ["老板最在意可汇报结果", "提前定义口径能降低隐性考核不确定性"],
    },
    {
      id: "silent-execution",
      title: "低调执行，等待结果说话",
      action: "减少沟通成本，把时间投入交付质量。",
      upside: 58,
      risk: 64,
      cost: 35,
      evidence: ["交付质量有价值", "但低可见度会让功劳分配失真"],
    },
    {
      id: "coalition-building",
      title: "建立跨团队支持面",
      action: "先帮助关键协作者解决一个小痛点，再借势推动晋升项目。",
      upside: 74,
      risk: 48,
      cost: 62,
      evidence: ["同事会避免背锅", "互惠关系能提高复杂项目推进率"],
    },
  ];
}

function buildBusinessOptions(): StrategyOption[] {
  return [
    {
      id: "inventory-profit-sprint",
      title: "库存利润联动冲刺",
      action: "把高库存低动销 SKU 列为本周清理对象，配合小幅折扣与陈列调整。",
      upside: 80,
      risk: 42,
      cost: 50,
      evidence: ["库存占压会拖累利润", "销量改善通常比单纯涨价更稳"],
    },
    {
      id: "traffic-conversion",
      title: "客流转化提升",
      action: "在高客流时段安排强销售人员，并记录转化率变化。",
      upside: 70,
      risk: 35,
      cost: 55,
      evidence: ["客流是收入入口", "排班调整成本低于大促活动"],
    },
    {
      id: "discount-guardrail",
      title: "折扣护栏",
      action: "设置最低毛利线，只允许对临期或滞销品打折。",
      upside: 65,
      risk: 28,
      cost: 30,
      evidence: ["无差别折扣会侵蚀利润", "折扣应绑定库存和动销目标"],
    },
  ];
}

function scoreOption(option: StrategyOption): number {
  return option.upside - option.risk * 0.7 - option.cost * 0.25;
}

export class GameAgent implements Agent<GameSignal> {
  id = "game" as const;

  async run(context: AgentContext): Promise<AgentResult<GameSignal>> {
    const isBusiness = context.goal.domain === "business";
    const options = isBusiness ? buildBusinessOptions() : buildWorkplaceOptions();
    const recommended = [...options].sort((a, b) => scoreOption(b) - scoreOption(a))[0];

    return {
      generatedAt: new Date().toISOString(),
      signal: {
        agentId: this.id,
        scenario: isBusiness
          ? "门店利润提升：库存、销量、客流、折扣与人效相互牵制。"
          : "职场晋升路径：可见度、资源、联盟、风险归因相互牵制。",
        roles: isBusiness ? businessRoles : workplaceRoles,
        options,
        recommendedOptionId: recommended.id,
        behavioralForecast: [
          `${recommended.title} 会优先改变高影响角色的激励结构。`,
          "若行动缺少留痕，风险会从业务问题转化为责任归因问题。",
          "先做低成本试点，再扩展到更高风险动作。",
        ],
      },
    };
  }
}
