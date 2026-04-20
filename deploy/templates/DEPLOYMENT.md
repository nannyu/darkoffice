# DarkOffice Skill Deployment

## 1) Prerequisites

- `python3 --version` must be >= 3.10
- `node --version` must be >= 20
- `npm --version` must be >= 10

## 2) Local bootstrap

```bash
npm ci
npm run skill:health
npm run skill:init
npm run skill:create -- demo
npm run skill:turn -- demo --action EMAIL_TRACE
npm run skill:show -- demo
```

## 3) Platform mapping

- OpenClaw: use `deploy/manifests/openclaw.skill.json`
- WorkBuddy: use `deploy/manifests/workbuddy.skill.json`
- Qclaw: use `deploy/manifests/qclaw.skill.json`

## 4) Release verification

```bash
python3 scripts/simulate_balance.py --runs 20 --turns 30
```

Verify report:

- `docs/project/balance-report.md`
