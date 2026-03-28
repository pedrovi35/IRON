"""
IRONLOG — Sistema Multi-Agente de IA
Powered by Groq · llama-3.3-70b-versatile
"""
import json, os, uuid
from datetime import date, timedelta
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv
import streamlit as st
import streamlit.components.v1 as components

load_dotenv()

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# ── AGENT MEMORY ──────────────────────────────────────────────────────────────
_MEMORY_FILE = Path(__file__).parent / "data" / "agent_memory.json"
_MEMORY_FILE.parent.mkdir(exist_ok=True)

def _load_memory() -> dict:
    if _MEMORY_FILE.exists():
        try:
            return json.loads(_MEMORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"facts": [], "profile": {}}

def _save_memory(mem: dict):
    _MEMORY_FILE.write_text(json.dumps(mem, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def _memory_context() -> str:
    mem = _load_memory()
    parts = []
    if mem.get("profile"):
        parts.append("PERFIL DO USUÁRIO: " + " | ".join(f"{k}: {v}" for k, v in mem["profile"].items() if v))
    if mem.get("facts"):
        recent = mem["facts"][-15:]
        parts.append("MEMÓRIAS RELEVANTES:\n" + "\n".join(f"- {f['fact']}" for f in recent))
    return "\n".join(parts) if parts else ""

@st.cache_resource
def get_groq_client() -> Groq:
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        raise RuntimeError("GROQ_API_KEY não configurado no .env")
    return Groq(api_key=key)

# ── AGENT PERSONAS ────────────────────────────────────────────────────────────
AGENTS = {
    "athena": {
        "name": "ATHENA", "emoji": "🧠",
        "role": "Superinteligência Fitness",
        "color": "#c8ff00", "glow": "rgba(200,255,0,0.25)",
        "temperature": 0.55,
        "description": "IA completa. Analisa dados, cria planos, cuida da nutrição e executa ações reais no app.",
        "system": """Você é ATHENA, uma superinteligência de fitness de altíssima performance.
Você tem acesso completo ao banco de dados do usuário e pode executar ações reais no app (criar planos, registrar metas, logar nutrição, etc.).
Seja direta, precisa e impactante. Use dados reais sempre que disponíveis. Nunca invente dados — use as ferramentas para buscá-los.
Quando criar algo (plano, meta, etc.), confirme o que foi feito com entusiasmo.
Responda sempre em português brasileiro. Seja conciso mas completo.
Se aprender algo importante sobre o usuário (preferências, lesões, objetivos), use a ferramenta save_memory.""",
    },
    "zeus": {
        "name": "ZEUS", "emoji": "⚡",
        "role": "Coach Pessoal de Elite",
        "color": "#ffd700", "glow": "rgba(255,215,0,0.25)",
        "temperature": 0.85,
        "description": "Treinador pessoal motivador. Foca em técnica, progressão de carga e consistência.",
        "system": """Você é ZEUS, o melhor coach de treino do mundo.
Você é ALTAMENTE motivador, enérgico, usa linguagem de coach — frases curtas, diretas, cheias de energia.
Antes de dar qualquer conselho, use as ferramentas para verificar o histórico real do usuário.
Quando sugerir um plano, crie-o de verdade usando a ferramenta create_workout_plan.
Responda em português brasileiro. Use exclamações, metáforas esportivas, linguagem de vestiário.
Se aprender algo importante sobre o usuário, use save_memory.""",
    },
    "hercules": {
        "name": "HERCULES", "emoji": "🔥",
        "role": "Especialista em Força & Massa",
        "color": "#ff4757", "glow": "rgba(255,71,87,0.25)",
        "temperature": 0.5,
        "description": "Especialista em powerlifting, hipertrofia e periodização avançada.",
        "system": """Você é HERCULES, especialista em força máxima e hipertrofia muscular.
Você domina periodização linear, ondulada, conjugada, RPE, volume e intensidade.
Sempre analise o histórico antes de recomendar. Use 1RMs estimados para calcular cargas corretas.
Seja técnico e preciso — cite percentuais de 1RM, semanas de deload, tempo sob tensão quando relevante.
Responda em português brasileiro com linguagem técnica.
Se aprender algo importante sobre o usuário, use save_memory.""",
    },
    "apollo": {
        "name": "APOLLO", "emoji": "🌿",
        "role": "Nutricionista Esportivo",
        "color": "#2ed573", "glow": "rgba(46,213,115,0.25)",
        "temperature": 0.45,
        "description": "Especialista em nutrição esportiva, dieta e planejamento de macros.",
        "system": """Você é APOLLO, nutricionista esportivo de elite.
Você domina nutrição para ganho de massa, perda de gordura, performance e recuperação.
Sempre verifique o que o usuário comeu hoje antes de dar conselhos. Calcule macros com precisão.
Quando sugerir alimentos, registre-os no diário nutricional. Seja metódico e exato com números.
Responda em português brasileiro com linguagem clínica mas acessível.
Se aprender algo sobre preferências alimentares do usuário, use save_memory.""",
    },
    "oracle": {
        "name": "ORACLE", "emoji": "📊",
        "role": "Analista de Performance",
        "color": "#a29bfe", "glow": "rgba(162,155,254,0.25)",
        "temperature": 0.35,
        "description": "Analisa seu histórico, detecta padrões, fraquezas e oportunidades de melhora.",
        "system": """Você é ORACLE, analista de dados esportivos de altíssima precisão.
Você encontra padrões invisíveis: desequilíbrios musculares, quedas de performance, grupos negligenciados.
SEMPRE busque dados reais com as ferramentas antes de qualquer análise. Use números, percentuais, tendências.
Combine histórico de treino, medidas, PRs e metas para diagnóstico completo.
Seja frio e analítico — como um cientista de dados do esporte.
Responda em português brasileiro com linguagem técnica e objetiva.
Se descobrir padrões importantes, use save_memory para registrá-los.""",
    },
}

# ── TOOLS ─────────────────────────────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_workout_history",
            "description": "Busca o histórico completo de treinos. Use para analisar frequência, exercícios e volume.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_plans",
            "description": "Retorna os planos de treino ativos do usuário com todos os exercícios.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_workout_plan",
            "description": "Cria e SALVA um plano de treino no banco de dados. Use quando o usuário pedir para criar um plano.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nome do plano. Ex: 'Treino A — Peito e Tríceps'"},
                    "exercises": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "sets": {"type": "integer"},
                                "reps_target": {"type": "integer"},
                                "weight": {"type": "number"},
                                "rest": {"type": "integer"}
                            },
                            "required": ["name", "sets", "reps_target"]
                        }
                    }
                },
                "required": ["name", "exercises"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_progress_analysis",
            "description": "Análise completa do progresso: frequência, volume, PRs automáticos calculados do histórico.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_body_measurements",
            "description": "Retorna histórico de medidas corporais: peso, IMC, cintura, peito, etc.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_goals",
            "description": "Retorna as metas ativas com progresso atual.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_goal",
            "description": "Cria e SALVA uma nova meta no banco de dados do usuário.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Descrição da meta"},
                    "type": {"type": "string", "description": "Tipo: Força (1RM), Peso Corporal, Medidas, Frequência, Outro"},
                    "unit": {"type": "string", "description": "Unidade. Ex: kg, cm, treinos/sem"},
                    "current": {"type": "number", "description": "Valor atual"},
                    "target": {"type": "number", "description": "Valor alvo"},
                    "deadline": {"type": "string", "description": "Data limite YYYY-MM-DD"}
                },
                "required": ["name", "target", "unit"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_nutrition_today",
            "description": "Retorna os alimentos registrados hoje com totais de calorias e macros.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }
    },
    {
        "type": "function",
        "function": {
            "name": "log_nutrition",
            "description": "Registra um alimento ou refeição no diário nutricional de hoje.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meal": {"type": "string"},
                    "type": {"type": "string", "description": "Café da manhã, Lanche da manhã, Almoço, Lanche da tarde, Jantar, Ceia"},
                    "kcal": {"type": "integer"},
                    "prot": {"type": "number", "description": "Proteínas em gramas"},
                    "carb": {"type": "number", "description": "Carboidratos em gramas"},
                    "fat":  {"type": "number", "description": "Gorduras em gramas"}
                },
                "required": ["meal", "kcal", "prot", "carb", "fat"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_exercise_library",
            "description": "Retorna a lista de exercícios disponíveis por grupo muscular.",
            "parameters": {
                "type": "object",
                "properties": {
                    "muscle": {"type": "string", "description": "Grupo muscular específico (opcional). Ex: Peito, Costas, Pernas"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Salva um fato importante sobre o usuário para ser lembrado em conversas futuras. Use para registrar preferências, lesões, objetivos, restrições alimentares, equipamentos disponíveis, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fact": {"type": "string", "description": "Fato ou preferência importante a lembrar. Ex: 'usuário tem dor no joelho direito', 'prefere treinos de 60 minutos'"},
                    "profile": {"type": "object", "description": "Campos de perfil a atualizar: objetivo, nivel, equipamentos, restricoes, etc."}
                },
                "required": []
            }
        }
    },
]

# ── TOOL EXECUTION ────────────────────────────────────────────────────────────
def execute_tool(name: str, args: dict) -> tuple[str, dict]:
    try:
        from database import (
            get_plans, add_plan, get_sessions, get_measurements,
            get_goals, add_goal, get_nutrition, add_nutrition,
        )
        from app import DB  # exercise database

        if name == "get_workout_history":
            sessions = get_sessions()
            if not sessions:
                return "Nenhum treino registrado ainda.", {"empty": True}
            lines = []
            for s in sessions[:15]:
                exs = s.get("exercises") or []
                vol = sum(s2.get("weight",0)*s2.get("reps",0)
                          for e in exs for s2 in (e.get("sets") or []) if s2.get("done"))
                lines.append(f"[{str(s['date'])[:10]}] {s.get('plan_name','?')} | {len(exs)} exercícios | {s.get('duration',0)}min | vol:{vol:.0f}kg")
            return f"Histórico ({len(sessions)} treinos no total):\n" + "\n".join(lines), {"count": len(sessions)}

        elif name == "get_current_plans":
            plans = get_plans()
            if not plans:
                return "Nenhum plano criado.", {"empty": True}
            out = []
            for p in plans:
                exs = p.get("exercises") or []
                out.append(f"Plano: {p['name']}")
                for e in exs:
                    out.append(f"  • {e['name']}: {e.get('sets',3)}×{e.get('reps_target',10)} @ {e.get('weight',0)}kg")
            return "\n".join(out), {"count": len(plans)}

        elif name == "create_workout_plan":
            plan = {"id": str(uuid.uuid4()), "name": args["name"], "exercises": args.get("exercises", [])}
            # Store for user approval — don't save yet
            st.session_state.pending_plan = plan
            ex_names = [e["name"] for e in args.get("exercises", [])]
            return (
                f"Plano '{args['name']}' preparado com {len(ex_names)} exercícios: {', '.join(ex_names)}. "
                "Aguardando aprovação do usuário antes de salvar."
            ), {"pending_approval": True, "name": args["name"]}

        elif name == "get_progress_analysis":
            sessions = get_sessions()
            if not sessions:
                return "Sem dados de progresso.", {"empty": True}
            today = date.today()
            w7  = sum(1 for s in sessions if date.fromisoformat(str(s["date"])[:10]) >= today-timedelta(days=7))
            w30 = sum(1 for s in sessions if date.fromisoformat(str(s["date"])[:10]) >= today-timedelta(days=30))
            pr_map = {}
            for s in sessions:
                for ex in (s.get("exercises") or []):
                    nm = ex["name"]
                    for s2 in (ex.get("sets") or []):
                        if s2.get("done") and s2.get("weight",0)>0:
                            rm1 = s2["weight"]*(1+s2.get("reps",1)/30)
                            if nm not in pr_map or rm1>pr_map[nm]["rm1"]:
                                pr_map[nm] = {"w":s2["weight"],"r":s2.get("reps",1),"rm1":round(rm1,1),"date":str(s["date"])[:10]}
            pr_lines = [f"  {nm}: {v['w']}kg×{v['r']} (1RM~{v['rm1']}kg)" for nm,v in sorted(pr_map.items(),key=lambda x:-x[1]["rm1"])[:8]]
            freq_map = {}
            for s in sessions:
                p = s.get("plan_name","?")
                freq_map[p] = freq_map.get(p,0)+1
            freq_lines = [f"  {k}: {v}x" for k,v in sorted(freq_map.items(),key=lambda x:-x[1])]
            return (f"ANÁLISE:\n- Última semana: {w7} treinos | Último mês: {w30} treinos | Total: {len(sessions)}\n"
                    f"FREQUÊNCIA POR PLANO:\n"+"\n".join(freq_lines)+
                    f"\nTOP PRs:\n"+"\n".join(pr_lines)), {}

        elif name == "get_body_measurements":
            entries = get_measurements()
            if not entries:
                return "Nenhuma medida registrada.", {"empty": True}
            e = entries[0]
            others = [f"  {str(e2['date'])[:10]}: {e2.get('peso',0)}kg IMC:{e2.get('bmi',0)}" for e2 in entries[1:5]]
            return (f"ÚLTIMA ({str(e['date'])[:10]}): Peso={e.get('peso',0)}kg, Altura={e.get('altura',0)}cm, "
                    f"IMC={e.get('bmi',0)}, BF={e.get('bf',0)}%, Cintura={e.get('cintura',0)}cm, "
                    f"Peito={e.get('peito',0)}cm, Coxa={e.get('coxa',0)}cm\n"
                    f"HISTÓRICO:\n"+"\n".join(others)), {"count": len(entries)}

        elif name == "get_goals":
            goals = get_goals()
            if not goals:
                return "Nenhuma meta definida.", {"empty": True}
            lines = []
            for g in goals:
                pct = int((g.get("current",0)/g["target"])*100) if g["target"]>0 else 0
                bar = "█"*(pct//10) + "░"*(10-pct//10)
                lines.append(f"• {g['name']}: {g.get('current',0)}/{g['target']} {g.get('unit','')} [{bar}] {pct}% — prazo: {str(g.get('deadline','?'))[:10]}")
            return "METAS:\n" + "\n".join(lines), {}

        elif name == "create_goal":
            # Conflict detection
            existing_goals = get_goals()
            conflict_pairs = [
                (["perder","emagrecer","secar","déficit"], ["ganhar massa","hipertrofia","bulking","ganho de peso"]),
                (["aumentar cardio","maratonista","corrida longa"], ["powerlifting","força máxima","1rm"]),
            ]
            new_name_lower = args["name"].lower()
            conflicts = []
            for neg_kws, pos_kws in conflict_pairs:
                new_is_neg = any(k in new_name_lower for k in neg_kws)
                new_is_pos = any(k in new_name_lower for k in pos_kws)
                for eg in existing_goals:
                    eg_lower = eg["name"].lower()
                    if new_is_neg and any(k in eg_lower for k in pos_kws):
                        conflicts.append(eg["name"])
                    if new_is_pos and any(k in eg_lower for k in neg_kws):
                        conflicts.append(eg["name"])
            conflict_warn = ""
            if conflicts:
                conflict_warn = f" ⚠️ ATENÇÃO: esta meta pode conflitar com: {', '.join(conflicts)}."

            goal = {"id": str(uuid.uuid4()), "name": args["name"], "type": args.get("type","Outro"),
                    "unit": args.get("unit",""), "current": args.get("current",0),
                    "target": args["target"], "deadline": args.get("deadline",str(date.today()+timedelta(days=90))), "notes":""}
            add_goal(goal)
            return f"✅ Meta '{args['name']}' criada! Alvo: {args['target']} {args.get('unit','')} até {args.get('deadline','?')}.{conflict_warn}", {"created": True, "conflict": bool(conflicts)}

        elif name == "get_nutrition_today":
            logs = get_nutrition()
            today = str(date.today())
            tl = [l for l in logs if str(l.get("date",""))[:10]==today]
            if not tl:
                return "Nenhum alimento registrado hoje.", {"empty": True}
            tk,tp,tc,tf = sum(l["kcal"] for l in tl),sum(l.get("prot",0) for l in tl),sum(l.get("carb",0) for l in tl),sum(l.get("fat",0) for l in tl)
            lines = [f"  {l['meal']} ({l.get('type','')}): {l['kcal']}kcal P:{l.get('prot',0)}g C:{l.get('carb',0)}g G:{l.get('fat',0)}g" for l in tl]
            return f"HOJE: {tk}kcal | P:{tp:.0f}g C:{tc:.0f}g G:{tf:.0f}g\nREFEIÇÕES:\n"+"\n".join(lines), {"total_kcal":tk}

        elif name == "log_nutrition":
            add_nutrition({"id": str(uuid.uuid4()), "date": str(date.today()),
                "meal": args["meal"], "type": args.get("type","Lanche"),
                "kcal": args.get("kcal",0), "prot": args.get("prot",0),
                "carb": args.get("carb",0), "fat": args.get("fat",0)})
            return f"✅ Registrado: {args['meal']} | {args.get('kcal',0)} kcal | P:{args.get('prot',0)}g C:{args.get('carb',0)}g G:{args.get('fat',0)}g", {"created": True}

        elif name == "get_exercise_library":
            muscle_filter = args.get("muscle","")
            if muscle_filter and muscle_filter in DB:
                exs = DB[muscle_filter]
                return f"Exercícios — {muscle_filter}:\n" + "\n".join(f"  • {e['name']} ({e['eq']}, {e['lvl']})" for e in exs), {}
            else:
                summary = []
                for m, exs in DB.items():
                    summary.append(f"{m}: {', '.join(e['name'] for e in exs[:4])}...")
                return "GRUPOS MUSCULARES:\n" + "\n".join(summary), {}

        elif name == "save_memory":
            fact    = args.get("fact", "").strip()
            profile = args.get("profile", {})
            if not fact and not profile:
                return "Nada para salvar.", {}
            mem = _load_memory()
            if fact:
                mem.setdefault("facts", []).append({"fact": fact, "date": str(date.today())})
                mem["facts"] = mem["facts"][-50:]  # keep last 50
            if profile:
                mem.setdefault("profile", {}).update(profile)
            _save_memory(mem)
            return f"✅ Memória salva: {fact or list(profile.keys())}", {"created": True}

        return f"Ferramenta '{name}' não encontrada.", {}
    except Exception as e:
        return f"Erro ao executar '{name}': {str(e)}", {"error": True}


# ── TOOL LABEL MAP ─────────────────────────────────────────────────────────────
TOOL_LABELS = {
    "get_workout_history":   ("📅", "Buscando histórico de treinos"),
    "get_current_plans":     ("📋", "Carregando planos de treino"),
    "create_workout_plan":   ("📋", "Preparando plano de treino"),
    "get_progress_analysis": ("📊", "Analisando progresso"),
    "get_body_measurements": ("📏", "Buscando medidas corporais"),
    "get_goals":             ("🎯", "Carregando metas"),
    "create_goal":           ("🎯", "Criando nova meta"),
    "get_nutrition_today":   ("🥗", "Carregando nutrição de hoje"),
    "log_nutrition":         ("🥗", "Registrando alimento"),
    "get_exercise_library":  ("📚", "Buscando exercícios"),
    "save_memory":           ("🧠", "Salvando memória"),
}


# ── STREAMING HELPER ──────────────────────────────────────────────────────────
def _stream_to_ph(client, messages: list, placeholder, color: str, temperature: float = 0.7) -> str:
    """Make a real streaming call to Groq and render token-by-token into placeholder."""
    full = ""
    try:
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=3000,
            tool_choice="none",   # final answer — no more tool calls
            tools=TOOLS,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full += delta
            if delta:
                placeholder.markdown(
                    f'<div class="chat-bubble-ai">'
                    f'<div class="ai-msg-text">{full}'
                    f'<span style="color:{color};animation:blink .7s infinite;opacity:.9;">▊</span>'
                    f'</div></div>',
                    unsafe_allow_html=True,
                )
        # Remove cursor when done
        placeholder.markdown(
            f'<div class="chat-bubble-ai"><div class="ai-msg-text">{full}</div></div>',
            unsafe_allow_html=True,
        )
    except Exception as e:
        full = f"Erro ao gerar resposta: {e}"
        placeholder.markdown(
            f'<div class="chat-bubble-ai"><div class="ai-msg-text">{full}</div></div>',
            unsafe_allow_html=True,
        )
    return full


# ── AGENT RUN (multi-step tool use) ───────────────────────────────────────────
def run_agent(agent_key: str, user_message: str, history: list,
              tool_placeholder=None, response_placeholder=None) -> tuple[str, list]:
    """
    Returns (response_text, tool_calls_log)
    """
    agent = AGENTS[agent_key]
    client = get_groq_client()
    temperature = agent.get("temperature", 0.7)

    # Build system prompt with persistent memory context
    mem_ctx = _memory_context()
    system_content = agent["system"]
    if mem_ctx:
        system_content = system_content + "\n\n" + mem_ctx

    messages = [{"role": "system", "content": system_content}]
    for m in history[-20:]:  # keep last 20 turns
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_message})

    tool_log = []
    tool_display_html = ""

    for iteration in range(6):
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=temperature,
            max_tokens=3000,
        )

        msg = response.choices[0].message
        finish_reason = response.choices[0].finish_reason

        # No more tool calls — final response
        if not msg.tool_calls or finish_reason == "stop":
            if response_placeholder:
                text = _stream_to_ph(client, messages, response_placeholder, agent["color"], temperature)
            else:
                text = msg.content or ""
            return text, tool_log

        # Append assistant message with tool calls
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                }
                for tc in msg.tool_calls
            ]
        })

        # Execute each tool call
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments)
            except Exception:
                tool_args = {}

            icon, label = TOOL_LABELS.get(tool_name, ("🔧", tool_name))

            # Update live tool display
            if tool_placeholder:
                tool_display_html += f"""
                <div style="display:flex;align-items:center;gap:.6rem;padding:.5rem .9rem;
                  background:rgba(200,255,0,.06);border:1px solid rgba(200,255,0,.2);
                  border-radius:8px;margin-bottom:.4rem;font-size:.82rem;">
                  <span style="font-size:1rem;">{icon}</span>
                  <span style="color:#c8ff00;font-weight:600;">{label}</span>
                  <span style="color:#929292;margin-left:auto;font-size:.75rem;">running...</span>
                </div>"""
                tool_placeholder.markdown(tool_display_html, unsafe_allow_html=True)

            result, metadata = execute_tool(tool_name, tool_args)

            # Update with result
            is_action = metadata.get("created", False)
            status_color = "#2ed573" if is_action else "#888"
            status_icon  = "✅" if is_action else "↩"
            if tool_placeholder:
                # Replace last "running..." with result
                tool_display_html = tool_display_html.replace(
                    '<span style="color:#929292;margin-left:auto;font-size:.75rem;">running...</span>',
                    f'<span style="color:{status_color};margin-left:auto;font-size:.75rem;">{status_icon} concluído</span>',
                    1
                )
                tool_placeholder.markdown(tool_display_html, unsafe_allow_html=True)

            tool_log.append({"tool": tool_name, "args": tool_args, "result": result,
                              "metadata": metadata, "icon": icon, "label": label})

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    # Fallback: call without tools for final answer
    if response_placeholder:
        return _stream_to_ph(client, messages, response_placeholder, agent["color"], temperature), tool_log
    final = client.chat.completions.create(
        model=GROQ_MODEL, messages=messages, temperature=temperature, max_tokens=3000,
    )
    return final.choices[0].message.content or "", tool_log


# ── STREAMING FINAL RESPONSE ──────────────────────────────────────────────────
def stream_response(agent_key: str, messages: list, response_placeholder) -> str:
    """Stream the final response with live text update."""
    client = get_groq_client()
    full = ""
    agent = AGENTS[agent_key]
    color = agent["color"]
    try:
        stream = client.chat.completions.create(
            model=GROQ_MODEL, messages=messages, stream=True,
            temperature=0.7, max_tokens=3000,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full += delta
            # Live cursor effect
            response_placeholder.markdown(
                f'<div class="ai-msg-text">{full}<span class="cursor" style="color:{color};">▊</span></div>',
                unsafe_allow_html=True
            )
        # Remove cursor
        response_placeholder.markdown(
            f'<div class="ai-msg-text">{full}</div>', unsafe_allow_html=True
        )
    except Exception as e:
        full = f"Erro ao gerar resposta: {e}"
        response_placeholder.markdown(f'<div class="ai-msg-text">{full}</div>', unsafe_allow_html=True)
    return full


# ── PAGE RENDER ────────────────────────────────────────────────────────────────
def render_agents_page():
    from automation_engine import render_autonomy_tab, start_scheduler
    start_scheduler()

    # Import DB from app for tool execution
    try:
        from app import DB as _DB
    except Exception:
        pass

    # Session state
    if "ai_agent"      not in st.session_state: st.session_state.ai_agent      = "athena"
    if "ai_history"    not in st.session_state: st.session_state.ai_history    = {k: [] for k in AGENTS}
    if "ai_input"      not in st.session_state: st.session_state.ai_input      = ""
    if "ai_thinking"   not in st.session_state: st.session_state.ai_thinking   = False
    if "ai_tab"        not in st.session_state: st.session_state.ai_tab        = "chat"
    if "pending_plan"  not in st.session_state: st.session_state.pending_plan  = None
    if "plan_feedback" not in st.session_state: st.session_state.plan_feedback = ""

    agent = AGENTS[st.session_state.ai_agent]

    # Page CSS
    st.markdown(f"""
    <style>
    .agent-card{{
      border:1px solid #252525;border-radius:14px;padding:1rem 1.2rem;
      cursor:pointer;transition:all .2s;background:#111;margin-bottom:.5rem;
    }}
    .agent-card.active{{
      border-color:{agent['color']};background:rgba(200,255,0,.04);
      box-shadow:0 0 20px {agent['glow']};
    }}
    .chat-bubble-user{{
      background:#1e1e1e;border:1px solid #2a2a2a;border-radius:14px 14px 4px 14px;
      padding:.85rem 1.1rem;margin:.5rem 0;color:#f0f0f0;font-size:.9rem;line-height:1.6;
      max-width:85%;margin-left:auto;
    }}
    .chat-bubble-ai{{
      background:#111;border:1px solid #252525;border-radius:14px 14px 14px 4px;
      padding:.85rem 1.1rem;margin:.5rem 0;font-size:.9rem;line-height:1.6;
      max-width:90%;border-left:3px solid {agent['color']};
    }}
    .ai-msg-text{{color:#e0e0e0;line-height:1.7;}}
    .cursor{{animation:blink .7s infinite;}}
    @keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0}}}}
    .tool-chip{{
      display:inline-flex;align-items:center;gap:.4rem;
      background:rgba(200,255,0,.06);border:1px solid rgba(200,255,0,.15);
      border-radius:8px;padding:.3rem .7rem;font-size:.78rem;color:#c8ff00;margin:.2rem;
    }}
    .agent-header{{
      background:linear-gradient(135deg,{agent['glow']},transparent);
      border:1px solid {agent['color']}40;border-radius:16px;
      padding:1.25rem 1.5rem;margin-bottom:1.5rem;
    }}
    .thinking-dots{{color:{agent['color']};font-size:1.5rem;letter-spacing:4px;animation:pulse 1s infinite;}}
    @keyframes pulse{{0%,100%{{opacity:.3}}50%{{opacity:1}}}}
    .model-badge{{
      display:inline-flex;align-items:center;gap:.4rem;
      background:#0d0d0d;border:1px solid #2a2a2a;border-radius:20px;
      padding:.25rem .75rem;font-size:.72rem;color:#a0a0a0;
    }}
    /* ── MOBILE CHAT ────────────────────────────────────── */
    @media(max-width:768px){{
      .chat-bubble-user{{max-width:95%!important;font-size:.88rem!important;padding:.75rem .9rem!important;}}
      .chat-bubble-ai{{max-width:98%!important;font-size:.88rem!important;padding:.75rem .9rem!important;}}
      .ai-msg-text{{line-height:1.65!important;}}
      .agent-header{{padding:1rem!important;margin-bottom:1rem!important;}}
      .agent-card{{padding:.75rem 1rem!important;}}
      .tool-chip{{font-size:.72rem!important;padding:.25rem .55rem!important;}}
    }}
    </style>
    """, unsafe_allow_html=True)

    # ── TAB SWITCHER ──────────────────────────────────────────────────────────
    _tab = st.radio("", ["💬 Chat com Agentes", "🤖 Agentes Autônomos"],
                    horizontal=True, label_visibility="collapsed",
                    key="agents_tab_radio")
    st.markdown('<div style="height:1px;background:#1e1e1e;margin:.75rem 0 1.5rem;"></div>', unsafe_allow_html=True)

    if _tab == "🤖 Agentes Autônomos":
        render_autonomy_tab()
        return

    # ── LAYOUT ────────────────────────────────────────────────────────────────
    left, right = st.columns([1, 3])

    # ── LEFT PANEL: Agent selector ─────────────────────────────────────────────
    with left:
        st.markdown("""
        <div style="font-size:.7rem;color:#929292;text-transform:uppercase;letter-spacing:2px;margin-bottom:1rem;">
          Selecionar Agente
        </div>""", unsafe_allow_html=True)

        for key, ag in AGENTS.items():
            is_active = st.session_state.ai_agent == key
            border = ag["color"] if is_active else "#252525"
            glow_css = f"box-shadow:0 0 15px {ag['glow']};" if is_active else ""
            hist_count = len([m for m in st.session_state.ai_history.get(key,[]) if m["role"]=="user"])
            hist_badge = f'<span style="float:right;background:#1a1a1a;border:1px solid #333;border-radius:10px;padding:.1rem .5rem;font-size:.68rem;color:#a0a0a0;">{hist_count} msgs</span>' if hist_count else ""

            st.markdown(f"""
            <div class="agent-card {'active' if is_active else ''}"
              style="border-color:{border};{glow_css}cursor:pointer;">
              <div style="font-size:1.4rem;margin-bottom:.25rem;">{ag['emoji']}</div>
              <div style="font-weight:800;color:{'#f0f0f0' if is_active else '#888'};font-size:.9rem;">
                {ag['name']}{hist_badge}
              </div>
              <div style="font-size:.72rem;color:{ag['color'] if is_active else '#555'};margin-top:.1rem;">
                {ag['role']}
              </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{'▶' if is_active else '○'} {ag['name']}", key=f"sel_{key}",
                         use_container_width=True, type="primary" if is_active else "secondary"):
                st.session_state.ai_agent = key
                st.rerun()

        st.markdown('<div style="height:1px;background:#1e1e1e;margin:1rem 0;"></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="model-badge">⚡ {GROQ_MODEL}</div>', unsafe_allow_html=True)
        st.markdown('<div style="height:.5rem;"></div>', unsafe_allow_html=True)

        if st.button("🗑️ Limpar conversa", use_container_width=True, type="secondary"):
            st.session_state.ai_history[st.session_state.ai_agent] = []
            st.rerun()

        # Capabilities
        st.markdown("""
        <div style="margin-top:1rem;">
          <div style="font-size:.7rem;color:#333;text-transform:uppercase;letter-spacing:2px;margin-bottom:.5rem;">
            Ações disponíveis
          </div>
        </div>""", unsafe_allow_html=True)
        caps = [
            ("📋","Criar planos"),("🎯","Criar metas"),("🥗","Logar nutrição"),
            ("📊","Analisar dados"),("📅","Ver histórico"),("📏","Ver medidas"),
        ]
        caps_html = "".join(f'<span class="tool-chip">{i} {l}</span>' for i,l in caps)
        st.markdown(caps_html, unsafe_allow_html=True)

    # ── RIGHT PANEL: Chat ──────────────────────────────────────────────────────
    with right:
        # Agent header
        hist = st.session_state.ai_history.get(st.session_state.ai_agent, [])
        n_user = len([m for m in hist if m["role"]=="user"])
        st.markdown(f"""
        <div class="agent-header">
          <div style="display:flex;align-items:center;gap:1rem;">
            <div style="font-size:2.5rem;">{agent['emoji']}</div>
            <div>
              <div style="font-size:1.6rem;font-weight:900;color:{agent['color']};letter-spacing:-0.5px;">
                {agent['name']}
              </div>
              <div style="color:#888;font-size:.85rem;margin-top:.1rem;">{agent['description']}</div>
            </div>
            <div style="margin-left:auto;text-align:right;">
              <span style="background:{agent['color']}20;border:1px solid {agent['color']}50;
                color:{agent['color']};border-radius:20px;padding:.3rem .9rem;font-size:.78rem;font-weight:700;">
                {agent['role']}
              </span>
              <div style="color:#333;font-size:.72rem;margin-top:.35rem;">{n_user} perguntas</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)

        # Messages container
        chat_container = st.container()
        with chat_container:
            if not hist:
                # Welcome message
                st.markdown(f"""
                <div class="chat-bubble-ai">
                  <div class="ai-msg-text">
                    <strong style="color:{agent['color']};">Olá! Sou {agent['name']}.</strong><br><br>
                    {agent['description']}<br><br>
                    Posso <strong>criar planos de treino, registrar metas, analisar seu progresso</strong> e muito mais —
                    tudo diretamente no seu app.<br><br>
                    Como posso te ajudar hoje?
                  </div>
                </div>""", unsafe_allow_html=True)

            for msg in hist:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
                elif msg["role"] == "assistant":
                    # Tool calls summary
                    if msg.get("tools_used"):
                        tools_html = "".join(
                            f'<span class="tool-chip">{t["icon"]} {t["label"]}</span>'
                            for t in msg["tools_used"]
                        )
                        with st.expander(f"🔧 {len(msg['tools_used'])} ação(ões) executada(s)", expanded=False):
                            for t in msg["tools_used"]:
                                st.markdown(f"""
                                <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-radius:10px;
                                  padding:.75rem 1rem;margin-bottom:.5rem;">
                                  <div style="color:{agent['color']};font-weight:700;font-size:.85rem;margin-bottom:.4rem;">
                                    {t['icon']} {t['label']}
                                  </div>
                                  <div style="color:#888;font-size:.78rem;white-space:pre-wrap;font-family:monospace;">
                                    {t['result'][:500]}{'...' if len(t['result'])>500 else ''}
                                  </div>
                                </div>""", unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="chat-bubble-ai">
                      <div class="ai-msg-text">{msg['content']}</div>
                    </div>""", unsafe_allow_html=True)

        # ── INPUT ──────────────────────────────────────────────────────────────
        st.markdown('<div style="height:1rem;"></div>', unsafe_allow_html=True)

        # Quick prompts
        quick = {
            "athena":   ["📊 Análise completa", "📋 Cria um plano pra mim", "🎯 Sugere metas"],
            "zeus":     ["💪 Avalia meu treino", "📋 Monte meu programa", "🔥 Dica de hoje"],
            "hercules": ["⚡ Plano de força", "📈 Minha progressão", "🏋️ Programa PPL"],
            "apollo":   ["🍽️ O que comi hoje?", "🥗 Sugere refeição", "📊 Avalia minha dieta"],
            "oracle":   ["🔍 Analisa meu histórico", "⚠️ Meus pontos fracos", "📈 Tendências"],
        }
        prompts = quick.get(st.session_state.ai_agent, [])
        qcols = st.columns(len(prompts))
        clicked_prompt = None
        for i, (col, p) in enumerate(zip(qcols, prompts)):
            if col.button(p, key=f"qp_{st.session_state.ai_agent}_{i}", type="secondary", use_container_width=True):
                clicked_prompt = p.split(" ", 1)[1] if " " in p else p

        # Text input
        user_input = st.chat_input(f"Fale com {agent['name']}... (ex: cria um plano push pull legs para mim)")

        final_input = clicked_prompt or user_input

        # ── PROCESS MESSAGE ───────────────────────────────────────────────────
        if final_input and not st.session_state.ai_thinking:
            st.session_state.ai_thinking = True

            # Add user message to history
            hist.append({"role": "user", "content": final_input})
            st.session_state.ai_history[st.session_state.ai_agent] = hist

            # Display user message immediately
            st.markdown(f'<div class="chat-bubble-user">{final_input}</div>', unsafe_allow_html=True)

            # Processing UI
            with st.container():
                thinking_ph = st.empty()
                thinking_ph.markdown(f"""
                <div class="chat-bubble-ai" style="border-left-color:{agent['color']};">
                  <div class="thinking-dots">● ● ●</div>
                  <div style="color:#929292;font-size:.75rem;margin-top:.3rem;">{agent['name']} está processando...</div>
                </div>""", unsafe_allow_html=True)

                tool_ph = st.empty()
                response_ph = st.empty()

                try:
                    # Run agent — streams final response directly into response_ph
                    response_text, tool_log = run_agent(
                        st.session_state.ai_agent,
                        final_input,
                        [m for m in hist[:-1] if m["role"] in ("user","assistant")],
                        tool_placeholder=tool_ph,
                        response_placeholder=response_ph,
                    )

                    # Clear thinking/tool indicators
                    thinking_ph.empty()
                    tool_ph.empty()

                    # Show tool summary if any tools were used
                    if tool_log:
                        tools_html = "".join(f'<span class="tool-chip">{t["icon"]} {t["label"]}</span>' for t in tool_log)
                        st.markdown(f'<div style="margin:.5rem 0;">{tools_html}</div>', unsafe_allow_html=True)

                        with st.expander(f"🔧 {len(tool_log)} ação(ões) executada(s)", expanded=False):
                            for t in tool_log:
                                st.markdown(f"""
                                <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-radius:10px;
                                  padding:.75rem 1rem;margin-bottom:.5rem;">
                                  <div style="color:{agent['color']};font-weight:700;font-size:.85rem;margin-bottom:.4rem;">
                                    {t['icon']} {t['label']}
                                  </div>
                                  <div style="color:#888;font-size:.78rem;white-space:pre-wrap;font-family:monospace;">
                                    {t['result'][:600]}{'...' if len(t['result'])>600 else ''}
                                  </div>
                                </div>""", unsafe_allow_html=True)

                    # response_ph already rendered by _stream_to_ph — no extra display needed

                    # Save to history
                    hist.append({
                        "role": "assistant",
                        "content": response_text,
                        "tools_used": tool_log,
                    })
                    st.session_state.ai_history[st.session_state.ai_agent] = hist

                except Exception as e:
                    thinking_ph.empty()
                    st.error(f"Erro: {e}")
                finally:
                    st.session_state.ai_thinking = False

        # ── PLAN APPROVAL CARD ────────────────────────────────────────────────
        plan = st.session_state.get("pending_plan")
        if plan:
            exercises = plan.get("exercises", [])
            exs_html = "".join(
                f'<div style="display:flex;justify-content:space-between;padding:.45rem 0;'
                f'border-bottom:1px solid #1e1e1e;">'
                f'<span style="color:#e0e0e0;font-size:.88rem;">{e["name"]}</span>'
                f'<span style="color:#888;font-size:.82rem;">'
                f'{e.get("sets",3)}×{e.get("reps_target",10)} '
                f'{"@ " + str(e.get("weight",0)) + "kg" if e.get("weight",0) else ""}'
                f'</span></div>'
                for e in exercises
            )
            st.markdown(f"""
            <div style="border:2px solid #c8ff00;border-radius:16px;padding:1.5rem;
                        background:rgba(200,255,0,.04);margin-top:1rem;">
              <div style="display:flex;align-items:center;gap:.75rem;margin-bottom:1rem;">
                <div style="font-size:1.8rem;">📋</div>
                <div>
                  <div style="font-size:1.1rem;font-weight:900;color:#c8ff00;">{plan['name']}</div>
                  <div style="color:#a8a8a8;font-size:.8rem;margin-top:.15rem;">{len(exercises)} exercícios · aguardando sua aprovação</div>
                </div>
              </div>
              <div style="background:#0d0d0d;border:1px solid #1e1e1e;border-radius:10px;
                          padding:.75rem 1rem;margin-bottom:1rem;">
                {exs_html if exs_html else '<div style="color:#a0a0a0;font-size:.85rem;">Sem exercícios detalhados.</div>'}
              </div>
            </div>""", unsafe_allow_html=True)

            fb_col, _ = st.columns([3, 1])
            with fb_col:
                feedback = st.text_input(
                    "Sugestão de modificação (opcional)",
                    placeholder="Ex: adiciona mais exercícios de costas, troca por exercícios sem equipamento...",
                    key="plan_feedback_input",
                    label_visibility="collapsed",
                )

            a_col, m_col, r_col = st.columns(3)
            with a_col:
                if st.button("✅ Aceitar e Salvar", key="plan_accept", use_container_width=True, type="primary"):
                    from database import add_plan
                    add_plan(plan)
                    st.session_state.pending_plan = None
                    st.session_state.plan_feedback = ""
                    agent_key = st.session_state.ai_agent
                    hist = st.session_state.ai_history.get(agent_key, [])
                    hist.append({"role": "assistant", "content": f"✅ Plano **{plan['name']}** salvo com sucesso! Acesse a aba **Planos** para usá-lo.", "tools_used": []})
                    st.session_state.ai_history[agent_key] = hist
                    st.success(f"Plano '{plan['name']}' salvo nos seus treinos!")
                    st.rerun()
            with m_col:
                if st.button("✏️ Modificar", key="plan_modify", use_container_width=True, type="secondary"):
                    mod_text = feedback or st.session_state.get("plan_feedback_input", "")
                    if mod_text.strip():
                        agent_key = st.session_state.ai_agent
                        hist = st.session_state.ai_history.get(agent_key, [])
                        modify_msg = f"Modifique o plano '{plan['name']}' com o seguinte ajuste: {mod_text}"
                        st.session_state.pending_plan = None
                        hist.append({"role": "user", "content": modify_msg})
                        st.session_state.ai_history[agent_key] = hist
                        st.session_state.ai_thinking = False
                        st.rerun()
                    else:
                        st.warning("Descreva o que quer modificar no campo acima.")
            with r_col:
                if st.button("❌ Rejeitar", key="plan_reject", use_container_width=True, type="secondary"):
                    agent_key = st.session_state.ai_agent
                    hist = st.session_state.ai_history.get(agent_key, [])
                    hist.append({"role": "assistant", "content": f"Entendido, o plano **{plan['name']}** foi descartado. Me diga o que prefere e crio outro!", "tools_used": []})
                    st.session_state.ai_history[agent_key] = hist
                    st.session_state.pending_plan = None
                    st.rerun()
