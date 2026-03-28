"""
IRONLOG — Motor de Automação Autônoma
Agentes que executam ações sem interação do usuário.
"""
import json, threading, time as _time, uuid
from typing import Optional
from datetime import datetime, date, timedelta
from pathlib import Path
import streamlit as st

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

_AUTO_FILE = DATA_DIR / "automations.json"
_LOG_FILE  = DATA_DIR / "automation_logs.json"
_FLAG_FILE = DATA_DIR / "automation_pending.json"  # UI notification flag

# ── AUTOMATION TEMPLATES ──────────────────────────────────────────────────────
TEMPLATES = [
    {
        "id": "briefing_matinal",
        "name": "☀️ Briefing Matinal",
        "description": "Todo dia às 7h: análise do dia, treino recomendado e motivação.",
        "agent": "athena",
        "trigger_type": "daily",
        "trigger_hour": 7,
        "prompt": (
            "Faça meu briefing matinal completo. "
            "Analise meu histórico de treinos e veja há quanto tempo não treino certos grupos musculares. "
            "Recomende o treino ideal para hoje. "
            "Verifique minhas metas e diga como estão. "
            "Termine com uma mensagem de motivação personalizada."
        ),
        "enabled": False,
        "last_run": None,
    },
    {
        "id": "alerta_inatividade",
        "name": "⚠️ Alerta de Inatividade",
        "description": "Após 3 dias sem treinar, cria e salva um plano de retorno.",
        "agent": "zeus",
        "trigger_type": "inactivity",
        "trigger_days": 3,
        "prompt": (
            "Analise meu histórico. Detectei inatividade de vários dias. "
            "Crie e SALVE um plano de retorno progressivo para esta semana (3 treinos, menor volume). "
            "Seja direto e motivador."
        ),
        "enabled": False,
        "last_run": None,
    },
    {
        "id": "relatorio_semanal",
        "name": "📊 Relatório Semanal",
        "description": "Toda segunda-feira: análise da semana anterior + plano para a próxima.",
        "agent": "oracle",
        "trigger_type": "weekly",
        "trigger_weekday": 0,  # Segunda
        "trigger_hour": 8,
        "prompt": (
            "Analise minha semana completa: "
            "frequência de treinos, volume total, PRs alcançados, grupos musculares trabalhados. "
            "Identifique pontos fracos. "
            "Crie uma meta nova para esta semana baseada nos dados."
        ),
        "enabled": False,
        "last_run": None,
    },
    {
        "id": "progressao_carga",
        "name": "📈 Progressão Inteligente",
        "description": "Após treinos: detecta quando é hora de aumentar carga e cria plano atualizado.",
        "agent": "hercules",
        "trigger_type": "daily",
        "trigger_hour": 21,
        "condition": "has_recent_workout",
        "prompt": (
            "Analise meus últimos 5 treinos. "
            "Identifique exercícios onde completei todas as séries e estou pronto para progredir. "
            "Me dê recomendações específicas de novos pesos. "
            "Se houver padrão claro de progressão, crie e SALVE um plano atualizado."
        ),
        "enabled": False,
        "last_run": None,
    },
    {
        "id": "check_metas",
        "name": "🎯 Check Semanal de Metas",
        "description": "Toda sexta-feira: status das metas + cria novas se necessário.",
        "agent": "athena",
        "trigger_type": "weekly",
        "trigger_weekday": 4,  # Sexta
        "trigger_hour": 18,
        "prompt": (
            "Verifique TODAS as minhas metas atuais. "
            "Para as atrasadas: crie um plano de ação e SALVE uma meta ajustada. "
            "Para as no prazo: sugira como acelerar o progresso. "
            "Se não tiver metas, analise meu histórico e CRIE 2 metas realistas."
        ),
        "enabled": False,
        "last_run": None,
    },
    {
        "id": "plano_nutricao",
        "name": "🥗 Plano Nutricional Diário",
        "description": "Ao meio-dia: se sem registro nutricional, sugere e loga refeições.",
        "agent": "apollo",
        "trigger_type": "daily",
        "trigger_hour": 12,
        "condition": "no_nutrition_today",
        "prompt": (
            "Veja o que já registrei para comer hoje. "
            "Se não tiver nada: REGISTRE 3 refeições balanceadas (café, almoço e jantar) "
            "baseadas em um objetivo de 2500 kcal com 180g proteína. "
            "Explique brevemente as escolhas."
        ),
        "enabled": False,
        "last_run": None,
    },
    {
        "id": "coach_pos_treino",
        "name": "🏁 Coach Pós-Treino",
        "description": "Após finalizar um treino: feedback, sugestão de recuperação e próximos passos.",
        "agent": "zeus",
        "trigger_type": "after_workout",
        "prompt": (
            "Analise meu treino mais recente: exercícios, séries, cargas. "
            "Dê feedback sobre o desempenho comparado com treinos anteriores. "
            "Sugira o que fazer amanhã (descanso ativo ou treino específico). "
            "Dê 1 dica de recuperação (nutrição, sono ou mobilidade)."
        ),
        "enabled": False,
        "last_run": None,
    },
]

# ── STORAGE ───────────────────────────────────────────────────────────────────
def _load_automations() -> list:
    if _AUTO_FILE.exists():
        saved = json.loads(_AUTO_FILE.read_text(encoding="utf-8"))
        # Merge saved state into templates
        saved_map = {a["id"]: a for a in saved}
        result = []
        for t in TEMPLATES:
            merged = dict(t)
            if t["id"] in saved_map:
                merged["enabled"]  = saved_map[t["id"]].get("enabled", False)
                merged["last_run"] = saved_map[t["id"]].get("last_run")
            result.append(merged)
        return result
    return [dict(t) for t in TEMPLATES]

def _save_automations(automations: list):
    _AUTO_FILE.write_text(json.dumps(automations, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def _load_logs() -> list:
    if _LOG_FILE.exists():
        return json.loads(_LOG_FILE.read_text(encoding="utf-8"))
    return []

def _append_log(entry: dict):
    logs = _load_logs()
    logs.insert(0, entry)
    logs = logs[:100]  # keep last 100
    _LOG_FILE.write_text(json.dumps(logs, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def _set_pending_flag(automation_name: str):
    pending = []
    if _FLAG_FILE.exists():
        pending = json.loads(_FLAG_FILE.read_text(encoding="utf-8"))
    pending.insert(0, {"name": automation_name, "at": datetime.now().isoformat()})
    pending = pending[:10]
    _FLAG_FILE.write_text(json.dumps(pending, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def get_pending_notifications() -> list:
    if _FLAG_FILE.exists():
        data = json.loads(_FLAG_FILE.read_text(encoding="utf-8"))
        _FLAG_FILE.write_text("[]", encoding="utf-8")  # clear after reading
        return data
    return []

# ── CONDITION CHECKERS ────────────────────────────────────────────────────────
def _check_condition(condition: Optional[str]) -> bool:
    if not condition:
        return True
    try:
        from database import get_sessions, get_nutrition
        if condition == "no_nutrition_today":
            logs = get_nutrition()
            today = str(date.today())
            return not any(str(l.get("date",""))[:10] == today for l in logs)
        if condition == "has_recent_workout":
            sessions = get_sessions()
            if not sessions:
                return False
            last = date.fromisoformat(str(sessions[0]["date"])[:10])
            return (date.today() - last).days <= 1
    except Exception:
        pass
    return True

def _is_due(auto: dict) -> bool:
    """Check if an automation should run now."""
    if not auto.get("enabled"):
        return False

    now = datetime.now()
    last_run = auto.get("last_run")
    if last_run:
        last_dt = datetime.fromisoformat(str(last_run))
        # Avoid re-running within 1 hour
        if (now - last_dt).total_seconds() < 3600:
            return False

    ttype = auto.get("trigger_type")

    if ttype == "daily":
        hour = auto.get("trigger_hour", 7)
        if now.hour != hour:
            return False
        # Check not already run today
        if last_run and datetime.fromisoformat(str(last_run)).date() == now.date():
            return False
        return _check_condition(auto.get("condition"))

    elif ttype == "weekly":
        wday = auto.get("trigger_weekday", 0)
        hour = auto.get("trigger_hour", 8)
        if now.weekday() != wday or now.hour != hour:
            return False
        if last_run and datetime.fromisoformat(str(last_run)).date() == now.date():
            return False
        return True

    elif ttype == "inactivity":
        days = auto.get("trigger_days", 3)
        try:
            from database import get_sessions
            sessions = get_sessions()
            if not sessions:
                return True
            last = date.fromisoformat(str(sessions[0]["date"])[:10])
            inactive_days = (date.today() - last).days
            if inactive_days < days:
                return False
            # Don't re-trigger if already ran today
            if last_run and datetime.fromisoformat(str(last_run)).date() == now.date():
                return False
            return True
        except Exception:
            return False

    elif ttype == "after_workout":
        try:
            from database import get_sessions
            sessions = get_sessions()
            if not sessions:
                return False
            last_session_date = date.fromisoformat(str(sessions[0]["date"])[:10])
            if last_session_date != date.today():
                return False
            if last_run and datetime.fromisoformat(str(last_run)).date() == date.today():
                return False
            return True
        except Exception:
            return False

    return False

# ── RUN ONE AUTOMATION ────────────────────────────────────────────────────────
def run_automation(auto_id: str) -> Optional[dict]:
    """Run an automation by ID. Returns log entry or None."""
    from agents import run_agent, AGENTS

    automations = _load_automations()
    auto = next((a for a in automations if a["id"] == auto_id), None)
    if not auto:
        return None

    agent_key = auto.get("agent", "athena")
    prompt    = auto.get("prompt", "")

    try:
        response, tool_log = run_agent(agent_key, prompt, [])
        entry = {
            "id":        str(uuid.uuid4()),
            "auto_id":   auto_id,
            "auto_name": auto["name"],
            "agent":     agent_key,
            "agent_emoji": AGENTS[agent_key]["emoji"],
            "prompt":    prompt[:200],
            "response":  response,
            "tools_used": [{"tool": t["tool"], "label": t["label"], "icon": t["icon"]} for t in tool_log],
            "ran_at":    datetime.now().isoformat(),
            "success":   True,
        }
    except Exception as e:
        entry = {
            "id":        str(uuid.uuid4()),
            "auto_id":   auto_id,
            "auto_name": auto["name"],
            "agent":     agent_key,
            "agent_emoji": "🤖",
            "prompt":    prompt[:200],
            "response":  f"Erro: {e}",
            "tools_used": [],
            "ran_at":    datetime.now().isoformat(),
            "success":   False,
        }

    # Update last_run
    for a in automations:
        if a["id"] == auto_id:
            a["last_run"] = datetime.now().isoformat()
    _save_automations(automations)
    _append_log(entry)
    _set_pending_flag(auto["name"])
    return entry

# ── BACKGROUND SCHEDULER ──────────────────────────────────────────────────────
_scheduler_lock = threading.Lock()
_scheduler_running = False

def _scheduler_loop():
    """Background thread: checks automations every 60s."""
    while True:
        try:
            automations = _load_automations()
            for auto in automations:
                if _is_due(auto):
                    run_automation(auto["id"])
        except Exception:
            pass
        _time.sleep(60)

@st.cache_resource
def start_scheduler():
    """Start the background scheduler once per server session."""
    global _scheduler_running
    with _scheduler_lock:
        if not _scheduler_running:
            _scheduler_running = True
            t = threading.Thread(target=_scheduler_loop, daemon=True)
            t.start()
    return True

# ── CHECK ON STARTUP ──────────────────────────────────────────────────────────
def check_startup_automations():
    """Called on app startup to check + run any due automations."""
    start_scheduler()  # ensure scheduler is running

    automations = _load_automations()
    ran = []
    for auto in automations:
        if _is_due(auto):
            entry = run_automation(auto["id"])
            if entry:
                ran.append(entry)
    return ran

# ── RENDER UI ─────────────────────────────────────────────────────────────────
def render_autonomy_tab():
    """Streamlit UI for managing autonomous agents."""
    from agents import AGENTS

    automations = _load_automations()
    logs = _load_logs()

    st.markdown("""
    <div style="margin-bottom:1.5rem;">
      <div style="font-size:1.5rem;font-weight:900;color:#f0f0f0;letter-spacing:-.5px;">
        🤖 Agentes Autônomos
      </div>
      <div style="color:#555;font-size:.85rem;margin-top:.25rem;">
        Ative automações para que os agentes tomem ações sem você precisar pedir.
        Rodam em segundo plano enquanto o app está aberto.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── AUTOMATION CARDS ─────────────────────────────────────────────────────
    for auto in automations:
        agent   = AGENTS.get(auto["agent"], {})
        color   = agent.get("color", "#c8ff00")
        emoji   = agent.get("emoji", "🤖")
        last    = auto.get("last_run")
        last_str = datetime.fromisoformat(str(last)).strftime("%d/%m %H:%M") if last else "Nunca executou"

        trigger_map = {
            "daily":         f"⏰ Diário às {auto.get('trigger_hour','?')}h",
            "weekly":        f"📅 Semanal (dia {['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'][auto.get('trigger_weekday',0)]} às {auto.get('trigger_hour','?')}h)",
            "inactivity":    f"😴 Inatividade > {auto.get('trigger_days','?')} dias",
            "after_workout": f"🏁 Após cada treino",
        }
        trigger_label = trigger_map.get(auto["trigger_type"], auto["trigger_type"])

        col1, col2 = st.columns([4, 1])

        with col1:
            st.markdown(f"""
            <div style="background:#111;border:1px solid {''+color+'40' if auto['enabled'] else '#252525'};
              border-radius:14px;padding:1.1rem 1.25rem;
              {'box-shadow:0 0 20px '+agent.get('glow','rgba(0,0,0,0)')+';' if auto['enabled'] else ''}">
              <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.5rem;">
                <span style="font-size:1.4rem;">{emoji}</span>
                <div>
                  <div style="font-weight:800;color:{'#f0f0f0' if auto['enabled'] else '#666'};font-size:.95rem;">
                    {auto['name']}
                    {'<span style="background:'+color+'20;color:'+color+';border:1px solid '+color+'40;border-radius:10px;padding:.1rem .5rem;font-size:.68rem;font-weight:700;margin-left:.5rem;">ATIVO</span>' if auto['enabled'] else ''}
                  </div>
                  <div style="color:#555;font-size:.78rem;margin-top:.15rem;">{auto['description']}</div>
                </div>
              </div>
              <div style="display:flex;gap:1rem;font-size:.75rem;color:#444;">
                <span>🎯 {agent.get('name','?')}</span>
                <span>{trigger_label}</span>
                <span>🕐 Último: {last_str}</span>
              </div>
            </div>""", unsafe_allow_html=True)

        with col2:
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
            toggle_label = "🔴 Desativar" if auto["enabled"] else "🟢 Ativar"
            if st.button(toggle_label, key=f"tog_{auto['id']}", use_container_width=True,
                         type="secondary"):
                for a in automations:
                    if a["id"] == auto["id"]:
                        a["enabled"] = not a["enabled"]
                _save_automations(automations)
                st.rerun()

            if st.button("▶ Rodar Agora", key=f"run_{auto['id']}", use_container_width=True):
                with st.spinner(f"{emoji} {auto['name']} executando..."):
                    entry = run_automation(auto["id"])
                if entry and entry["success"]:
                    st.success("✅ Concluído!")
                    with st.expander("Ver resultado", expanded=True):
                        st.markdown(f"""
                        <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-radius:10px;
                          padding:1rem;font-size:.88rem;color:#ccc;line-height:1.7;">
                          {entry['response']}
                        </div>""", unsafe_allow_html=True)
                        if entry["tools_used"]:
                            tools_html = " ".join(f'<span style="background:rgba(200,255,0,.07);border:1px solid rgba(200,255,0,.2);color:#c8ff00;border-radius:8px;padding:.2rem .6rem;font-size:.75rem;">{t["icon"]} {t["label"]}</span>' for t in entry["tools_used"])
                            st.markdown(tools_html, unsafe_allow_html=True)
                else:
                    st.error(f"Erro: {entry['response'] if entry else 'desconhecido'}")
                st.rerun()

    # ── LOG DE AÇÕES AUTÔNOMAS ────────────────────────────────────────────────
    st.markdown('<div style="height:1px;background:#1e1e1e;margin:2rem 0 1.5rem;"></div>', unsafe_allow_html=True)
    st.markdown("### 📋 Histórico de Ações Autônomas")

    if not logs:
        st.markdown("""
        <div style="background:#111;border:1px solid #1e1e1e;border-radius:14px;
          padding:2.5rem;text-align:center;color:#333;">
          Nenhuma ação autônoma executada ainda.<br>
          <span style="font-size:.8rem;">Ative automações acima e elas aparecerão aqui.</span>
        </div>""", unsafe_allow_html=True)
        return

    for log in logs[:15]:
        ran_dt = datetime.fromisoformat(log["ran_at"]).strftime("%d/%m/%Y às %H:%M")
        tools_html = " ".join(
            f'<span style="background:rgba(200,255,0,.06);border:1px solid rgba(200,255,0,.15);color:#c8ff00;border-radius:6px;padding:.15rem .5rem;font-size:.72rem;">{t["icon"]} {t["label"]}</span>'
            for t in log.get("tools_used", [])
        )
        success_color = "#2ed573" if log.get("success") else "#ff4757"
        success_icon  = "✅" if log.get("success") else "❌"

        with st.expander(f"{log['agent_emoji']} **{log['auto_name']}** — {ran_dt} {success_icon}"):
            if tools_html:
                st.markdown(f'<div style="margin-bottom:.75rem;">{tools_html}</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-radius:10px;
              padding:1rem;font-size:.87rem;color:#ccc;line-height:1.7;
              border-left:3px solid {success_color};">
              {log['response']}
            </div>""", unsafe_allow_html=True)
