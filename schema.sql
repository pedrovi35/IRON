-- ═══════════════════════════════════════════════
-- IRONLOG — Schema do banco de dados (Supabase)
-- Cole este SQL no SQL Editor do Supabase e execute
-- ═══════════════════════════════════════════════

-- Planos de treino
CREATE TABLE IF NOT EXISTS plans (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  exercises   JSONB DEFAULT '[]'::jsonb,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Sessões de treino (histórico)
CREATE TABLE IF NOT EXISTS sessions (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date        DATE NOT NULL,
  plan_name   TEXT DEFAULT 'Treino Livre',
  duration    INT DEFAULT 0,
  exercises   JSONB DEFAULT '[]'::jsonb,
  notes       TEXT DEFAULT '',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Medidas corporais
CREATE TABLE IF NOT EXISTS measurements (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date        DATE NOT NULL,
  peso        FLOAT DEFAULT 0,
  altura      FLOAT DEFAULT 0,
  bf          FLOAT DEFAULT 0,
  bmi         FLOAT DEFAULT 0,
  peito       FLOAT DEFAULT 0,
  cintura     FLOAT DEFAULT 0,
  quadril     FLOAT DEFAULT 0,
  braco_d     FLOAT DEFAULT 0,
  braco_e     FLOAT DEFAULT 0,
  coxa        FLOAT DEFAULT 0,
  panturrilha FLOAT DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Metas
CREATE TABLE IF NOT EXISTS goals (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  type        TEXT DEFAULT '',
  unit        TEXT DEFAULT '',
  current     FLOAT DEFAULT 0,
  target      FLOAT NOT NULL,
  deadline    DATE,
  notes       TEXT DEFAULT '',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Registro de nutrição
CREATE TABLE IF NOT EXISTS nutrition_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  date        DATE NOT NULL,
  meal        TEXT NOT NULL,
  type        TEXT DEFAULT '',
  kcal        INT DEFAULT 0,
  prot        FLOAT DEFAULT 0,
  carb        FLOAT DEFAULT 0,
  fat         FLOAT DEFAULT 0,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Recordes pessoais manuais
CREATE TABLE IF NOT EXISTS manual_prs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  exercise    TEXT NOT NULL,
  date        DATE NOT NULL,
  weight      FLOAT DEFAULT 0,
  reps        INT DEFAULT 1,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Exercícios personalizados
CREATE TABLE IF NOT EXISTS custom_exercises (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  muscle      TEXT DEFAULT '',
  eq          TEXT DEFAULT '',
  lvl         TEXT DEFAULT 'Iniciante',
  descr       TEXT DEFAULT '',
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ── Row Level Security (RLS) ──────────────────────────────
ALTER TABLE plans            ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions         ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurements     ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals            ENABLE ROW LEVEL SECURITY;
ALTER TABLE nutrition_logs   ENABLE ROW LEVEL SECURITY;
ALTER TABLE manual_prs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE custom_exercises ENABLE ROW LEVEL SECURITY;

-- Remove políticas antigas (se existirem) e recria
DROP POLICY IF EXISTS "allow_all_plans"            ON plans;
DROP POLICY IF EXISTS "allow_all_sessions"         ON sessions;
DROP POLICY IF EXISTS "allow_all_measurements"     ON measurements;
DROP POLICY IF EXISTS "allow_all_goals"            ON goals;
DROP POLICY IF EXISTS "allow_all_nutrition_logs"   ON nutrition_logs;
DROP POLICY IF EXISTS "allow_all_manual_prs"       ON manual_prs;
DROP POLICY IF EXISTS "allow_all_custom_exercises" ON custom_exercises;

-- Políticas abertas (acesso total via anon key)
CREATE POLICY "allow_all_plans"            ON plans            FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_sessions"         ON sessions         FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_measurements"     ON measurements     FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_goals"            ON goals            FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_nutrition_logs"   ON nutrition_logs   FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_manual_prs"       ON manual_prs       FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "allow_all_custom_exercises" ON custom_exercises FOR ALL USING (true) WITH CHECK (true);
