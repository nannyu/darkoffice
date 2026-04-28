#!/usr/bin/env bash
set -euo pipefail

DB="runtime/verify_$(date +%s).sqlite3"
SESSION="verify_session"
FAILED=0

pass() { echo "  ✓ $1"; }
fail() { echo "  ✗ $1"; FAILED=$((FAILED + 1)); }

echo "== DarkOffice Skill 功能验证 =="
echo "db: $DB"
echo "session: $SESSION"
echo ""

# 1. 健康检查
echo "[1/9] 健康检查"
if npm run -s skill:health > /dev/null 2>&1; then
  pass "healthcheck"
else
  fail "healthcheck"
fi

# 2. 初始化临时数据库
echo "[2/9] 初始化数据库"
rm -f "$DB"
if python3 scripts/game_state_cli.py --db "$DB" init > /dev/null 2>&1; then
  pass "init"
else
  fail "init"
fi

# 3. 创建会话
echo "[3/9] 创建会话"
CREATE_OUT=$(python3 scripts/game_state_cli.py --db "$DB" create "$SESSION" 2>&1)
if echo "$CREATE_OUT" | grep -q '"session_id"'; then
  pass "create session"
else
  fail "create session"
fi

# 4. 查看状态
echo "[4/9] 查看状态"
SHOW_OUT=$(python3 scripts/game_state_cli.py --db "$DB" show "$SESSION" 2>&1)
if echo "$SHOW_OUT" | grep -q '"hp": 100'; then
  pass "show state"
else
  fail "show state"
fi

# 5. 执行回合
echo "[5/9] 执行回合"
TURN_OUT=$(python3 scripts/game_state_cli.py --db "$DB" turn "$SESSION" --action DIRECT_EXECUTE 2>&1)
if echo "$TURN_OUT" | grep -q '"result_tier"'; then
  pass "turn resolution"
else
  fail "turn resolution"
fi

# 6. 获取提示
echo "[6/9] 获取提示"
PROMPT_OUT=$(python3 scripts/game_state_cli.py --db "$DB" prompt "$SESSION" 2>&1)
if echo "$PROMPT_OUT" | grep -q '"status_bar"'; then
  pass "next prompt"
else
  fail "next prompt"
fi

# 7. 查看历史
echo "[7/9] 查看历史"
HIST_OUT=$(python3 scripts/game_state_cli.py --db "$DB" history "$SESSION" 2>&1)
if echo "$HIST_OUT" | grep -q '"turn_index"'; then
  pass "history"
else
  fail "history"
fi

# 8. 查看统计
echo "[8/9] 查看统计"
STATS_OUT=$(python3 scripts/game_state_cli.py --db "$DB" stats "$SESSION" 2>&1)
if echo "$STATS_OUT" | grep -q '"action_type"'; then
  pass "stats"
else
  fail "stats"
fi

# 9. play 模式（使用主数据库的已有会话，避免重复创建）
echo "[9/9] play 模式"
PLAY_OUT=$(npm run -s skill:play -- test_0421_001 --action EMAIL_TRACE 2>&1)
if echo "$PLAY_OUT" | grep -q '"ok": true'; then
  pass "play mode"
else
  fail "play mode"
fi

# 清理临时数据库
rm -f "$DB"

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "✅ 所有验证通过"
  exit 0
else
  echo "❌ $FAILED 项验证失败"
  exit 1
fi
