import streamlit as st
import json, math, random, uuid, time
from datetime import datetime, date, timedelta
import streamlit.components.v1 as components
from agents import render_agents_page
from automation_engine import start_scheduler, get_pending_notifications

from database import (
    get_plans, add_plan, delete_plan,
    get_sessions, add_session,
    get_measurements, add_measurement,
    get_goals, add_goal, update_goal_current, delete_goal,
    get_nutrition, add_nutrition, delete_nutrition,
    get_manual_prs, add_manual_pr,
    get_custom_exercises, add_custom_exercise, delete_custom_exercise,
)

try:
    import plotly.graph_objects as go
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

st.set_page_config(page_title="IRONLOG — Treino com IA", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# ── SEO / META TAGS ───────────────────────────────────────────────────────────
st.markdown("""
<meta name="description" content="IRONLOG — Registre treinos, acompanhe progresso e receba coaching com IA. O seu diário de academia inteligente.">
<meta name="keywords" content="treino, academia, musculação, fitness, diário de treino, coach IA, progresso, nutrição">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<meta name="theme-color" content="#080808">
<meta property="og:title" content="IRONLOG — Seu Parceiro de Treino com IA">
<meta property="og:description" content="Registre treinos, acompanhe progresso e receba coaching personalizado com inteligência artificial.">
<meta property="og:type" content="website">
<meta name="robots" content="index, follow">
""", unsafe_allow_html=True)

# ── EXERCISE DB ───────────────────────────────────────────────────────────────
DB = {
"Peito":[
  {"name":"Supino Reto com Barra","eq":"Barra","lvl":"Intermediário","descr":"Deitado no banco, desça a barra até o peito e empurre."},
  {"name":"Supino Inclinado com Barra","eq":"Barra","lvl":"Intermediário","descr":"Banco a 30–45°, empurre a barra para cima."},
  {"name":"Supino Declinado com Barra","eq":"Barra","lvl":"Intermediário","descr":"Banco declinado, foco na parte inferior do peitoral."},
  {"name":"Supino com Halter","eq":"Halter","lvl":"Iniciante","descr":"Halteres para maior amplitude de movimento."},
  {"name":"Supino Inclinado com Halter","eq":"Halter","lvl":"Iniciante","descr":"Halteres no banco inclinado."},
  {"name":"Crossover no Cabo","eq":"Cabo","lvl":"Iniciante","descr":"Cruce os cabos contraindo o peitoral."},
  {"name":"Flexão de Braço","eq":"Peso Corporal","lvl":"Iniciante","descr":"Posição de prancha, desça o peito ao chão."},
  {"name":"Mergulho em Paralelas","eq":"Peso Corporal","lvl":"Intermediário","descr":"Em paralelas, desça até cotovelos a 90°."},
  {"name":"Fly com Halter","eq":"Halter","lvl":"Iniciante","descr":"Deitado, abra e feche os braços como asas."},
  {"name":"Peck Deck","eq":"Máquina","lvl":"Iniciante","descr":"Sentado, feche os braços contraindo o peitoral."},
],
"Costas":[
  {"name":"Barra Fixa","eq":"Peso Corporal","lvl":"Intermediário","descr":"Puxe o corpo até o queixo ultrapassar a barra."},
  {"name":"Remada Curvada com Barra","eq":"Barra","lvl":"Intermediário","descr":"Inclinado, puxe a barra até o abdômen."},
  {"name":"Remada Unilateral com Halter","eq":"Halter","lvl":"Iniciante","descr":"Joelho no banco, puxe o halter até a cintura."},
  {"name":"Puxada Frontal no Pulley","eq":"Cabo","lvl":"Iniciante","descr":"Sentado, puxe a barra larga até o peito."},
  {"name":"Puxada Fechada no Pulley","eq":"Cabo","lvl":"Iniciante","descr":"Pegada neutra, puxe até o peito."},
  {"name":"Levantamento Terra","eq":"Barra","lvl":"Avançado","descr":"Barra no chão, puxe até a posição ereta."},
  {"name":"Pull-over com Halter","eq":"Halter","lvl":"Intermediário","descr":"Leve o halter para trás da cabeça e retorne."},
  {"name":"Remada Baixa no Cabo","eq":"Cabo","lvl":"Iniciante","descr":"Sentado, puxe o cabo até o abdômen."},
  {"name":"Hiperextensão Lombar","eq":"Máquina","lvl":"Iniciante","descr":"Eleve o tronco contraindo a lombar."},
  {"name":"Remada Cavalinho","eq":"Máquina","lvl":"Iniciante","descr":"Apoiado, puxe os cabos até a cintura."},
],
"Ombros":[
  {"name":"Desenvolvimento com Barra","eq":"Barra","lvl":"Intermediário","descr":"Em pé, empurre a barra acima da cabeça."},
  {"name":"Desenvolvimento com Halter","eq":"Halter","lvl":"Iniciante","descr":"Sentado, empurre halteres acima da cabeça."},
  {"name":"Elevação Lateral com Halter","eq":"Halter","lvl":"Iniciante","descr":"Eleve os braços lateralmente até os ombros."},
  {"name":"Elevação Frontal com Halter","eq":"Halter","lvl":"Iniciante","descr":"Eleve os braços para frente até os ombros."},
  {"name":"Elevação Posterior com Halter","eq":"Halter","lvl":"Iniciante","descr":"Inclinado, eleve os braços para trás."},
  {"name":"Arnold Press","eq":"Halter","lvl":"Intermediário","descr":"Inicie com halteres na frente, rotacione e pressione."},
  {"name":"Crucifixo Inverso na Máquina","eq":"Máquina","lvl":"Iniciante","descr":"Abra os braços contraindo o deltoide posterior."},
  {"name":"Elevação Lateral no Cabo","eq":"Cabo","lvl":"Iniciante","descr":"Puxe o cabo lateralmente."},
  {"name":"Encolhimento com Barra","eq":"Barra","lvl":"Iniciante","descr":"Eleve os ombros contraindo o trapézio."},
],
"Bíceps":[
  {"name":"Rosca Direta com Barra","eq":"Barra","lvl":"Iniciante","descr":"Flexione os cotovelos levando a barra aos ombros."},
  {"name":"Rosca Alternada com Halter","eq":"Halter","lvl":"Iniciante","descr":"Alterne a flexão dos braços."},
  {"name":"Rosca Martelo","eq":"Halter","lvl":"Iniciante","descr":"Pegada neutra, flexione os cotovelos."},
  {"name":"Rosca Concentrada","eq":"Halter","lvl":"Iniciante","descr":"Apoie o cotovelo na coxa e curve o braço."},
  {"name":"Rosca no Cabo","eq":"Cabo","lvl":"Iniciante","descr":"Puxe o cabo flexionando os cotovelos."},
  {"name":"Rosca Scott","eq":"Barra","lvl":"Intermediário","descr":"Braços apoiados no banco Scott."},
  {"name":"Rosca 21s","eq":"Barra","lvl":"Intermediário","descr":"7 baixo + 7 cima + 7 completas."},
  {"name":"Rosca Inversa","eq":"Barra","lvl":"Intermediário","descr":"Pegada pronada, flexione os cotovelos."},
],
"Tríceps":[
  {"name":"Tríceps no Pulley com Corda","eq":"Cabo","lvl":"Iniciante","descr":"Puxe a corda para baixo estendendo os cotovelos."},
  {"name":"Tríceps Francês","eq":"Barra","lvl":"Intermediário","descr":"Deitado, dobre cotovelos levando a barra à testa."},
  {"name":"Mergulho em Banco","eq":"Peso Corporal","lvl":"Iniciante","descr":"Mãos no banco, dobre e estenda os cotovelos."},
  {"name":"Tríceps com Halter Acima","eq":"Halter","lvl":"Iniciante","descr":"Halter acima da cabeça, dobre os cotovelos."},
  {"name":"Tríceps no Pulley com Barra","eq":"Cabo","lvl":"Iniciante","descr":"Puxe a barra para baixo."},
  {"name":"Kickback com Halter","eq":"Halter","lvl":"Iniciante","descr":"Inclinado, estenda o braço para trás."},
  {"name":"Supino Fechado","eq":"Barra","lvl":"Intermediário","descr":"Supino com pegada fechada, foco no tríceps."},
],
"Pernas":[
  {"name":"Agachamento Livre","eq":"Barra","lvl":"Intermediário","descr":"Barra nos ombros, desça até a coxa paralela ao chão."},
  {"name":"Leg Press 45°","eq":"Máquina","lvl":"Iniciante","descr":"Empurre a plataforma com os pés."},
  {"name":"Hack Squat","eq":"Máquina","lvl":"Intermediário","descr":"Agachamento na máquina inclinada."},
  {"name":"Extensão de Pernas","eq":"Máquina","lvl":"Iniciante","descr":"Sentado, estenda os joelhos."},
  {"name":"Flexão de Pernas Deitado","eq":"Máquina","lvl":"Iniciante","descr":"Deitado de bruços, flexione os joelhos."},
  {"name":"Flexão de Pernas em Pé","eq":"Máquina","lvl":"Iniciante","descr":"Em pé, flexione um joelho de cada vez."},
  {"name":"Cadeira Adutora","eq":"Máquina","lvl":"Iniciante","descr":"Feche as pernas contraindo os adutores."},
  {"name":"Cadeira Abdutora","eq":"Máquina","lvl":"Iniciante","descr":"Abra as pernas contraindo os abdutores."},
  {"name":"Panturrilha no Smith","eq":"Smith","lvl":"Iniciante","descr":"Eleve os calcanhares contraindo a panturrilha."},
  {"name":"Passada com Halter","eq":"Halter","lvl":"Intermediário","descr":"Passo à frente, dobre ambos os joelhos."},
  {"name":"Stiff com Barra","eq":"Barra","lvl":"Intermediário","descr":"Desça a barra pela frente da perna."},
  {"name":"Agachamento Búlgaro","eq":"Halter","lvl":"Avançado","descr":"Pé traseiro apoiado, agache com o pé da frente."},
  {"name":"Leg Press Unilateral","eq":"Máquina","lvl":"Intermediário","descr":"Leg press com uma perna de cada vez."},
  {"name":"Agachamento Goblet","eq":"Halter","lvl":"Iniciante","descr":"Halter na frente do peito, agache profundo."},
],
"Glúteos":[
  {"name":"Hip Thrust com Barra","eq":"Barra","lvl":"Intermediário","descr":"Apoiado no banco, empurre o quadril para cima."},
  {"name":"Glúteo no Cabo","eq":"Cabo","lvl":"Iniciante","descr":"De quatro, puxe o cabo com o pé para trás."},
  {"name":"Elevação Pélvica","eq":"Peso Corporal","lvl":"Iniciante","descr":"Deitado, eleve o quadril contraindo glúteos."},
  {"name":"Agachamento Sumo","eq":"Halter","lvl":"Iniciante","descr":"Pés abertos, halter entre as pernas."},
  {"name":"Coice no Cross","eq":"Cabo","lvl":"Iniciante","descr":"Preso ao tornozelo, coice para trás."},
  {"name":"Hip Thrust Unilateral","eq":"Peso Corporal","lvl":"Intermediário","descr":"Uma perna de cada vez no hip thrust."},
],
"Abdômen":[
  {"name":"Abdominal Crunch","eq":"Peso Corporal","lvl":"Iniciante","descr":"Eleve o tronco contraindo o abdômen."},
  {"name":"Abdominal com Roda","eq":"Roda","lvl":"Avançado","descr":"Estenda a roda à frente e retorne."},
  {"name":"Prancha","eq":"Peso Corporal","lvl":"Iniciante","descr":"No antebraço, mantenha o corpo reto."},
  {"name":"Elevação de Pernas","eq":"Peso Corporal","lvl":"Intermediário","descr":"Deitado, eleve as pernas retas a 90°."},
  {"name":"Abdominal no Cabo","eq":"Cabo","lvl":"Iniciante","descr":"De joelhos, puxe o cabo flexionando o tronco."},
  {"name":"Russian Twist","eq":"Peso Corporal","lvl":"Intermediário","descr":"Sentado, gire o tronco de lado a lado."},
  {"name":"Mountain Climber","eq":"Peso Corporal","lvl":"Intermediário","descr":"Posição de flexão, alterne joelhos ao peito."},
  {"name":"Abdominal Infra","eq":"Peso Corporal","lvl":"Intermediário","descr":"Deitado, eleve quadril trazendo joelhos ao peito."},
],
"Cardio":[
  {"name":"Esteira","eq":"Máquina","lvl":"Iniciante","descr":"Caminhada ou corrida."},
  {"name":"Bicicleta Ergométrica","eq":"Máquina","lvl":"Iniciante","descr":"Pedalada em intensidade variada."},
  {"name":"Elíptico","eq":"Máquina","lvl":"Iniciante","descr":"Movimento elíptico de baixo impacto."},
  {"name":"HIIT","eq":"Peso Corporal","lvl":"Avançado","descr":"Intervalos de alta intensidade."},
  {"name":"Pular Corda","eq":"Corda","lvl":"Intermediário","descr":"Pule em ritmo constante ou variado."},
  {"name":"Remo Ergométrico","eq":"Máquina","lvl":"Intermediário","descr":"Simule o movimento de remo."},
],
}

QUOTES = [
    "Sem dor, sem ganho.",
    "Disciplina é escolher entre o que você quer agora e o que mais quer.",
    "Cada rep te aproxima da sua melhor versão.",
    "A dor de hoje é a força de amanhã.",
    "Consistência bate intensidade. Todo. Maldito. Dia.",
    "Levante pesado, coma bem, descanse, repita.",
    "Seu único limite é você mesmo.",
    "O corpo consegue quase tudo. É a mente que precisa acreditar.",
    "Não conte os dias. Faça os dias contarem.",
    "Força não vem da capacidade física. Vem de uma vontade indomável.",
]

def all_exercises():
    out = []
    for muscle, exs in DB.items():
        for e in exs:
            out.append({**e, "muscle": muscle})
    try:
        for e in get_custom_exercises():
            out.append({**e, "descr": e.get("descr", "")})
    except Exception:
        pass
    return out

def ex_names():
    return [e["name"] for e in all_exercises()]

# ── SESSION STATE ─────────────────────────────────────────────────────────────
_ss_defaults = {
    "workout": None, "page": "dashboard",
    "rest_end_ts": 0.0,        # Unix timestamp when rest timer ends
    "rest_ex_name": "",        # exercise name for the active rest
    "confirm_action": None,    # {"type": str, "id": str, "label": str}
    "history_page": 0,         # pagination index for history
}
for k, v in _ss_defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

#MainMenu,footer,header,.stDeployButton{visibility:hidden!important;display:none!important;}

/* ── DESIGN TOKENS ─────────────────────────────────── */
:root{
  --bg:#080808;--bg2:#111;--card:#181818;--card2:#222;
  --acc:#c8ff00;--acc2:#ff4757;--acc3:#2ed573;--warn:#ffa502;
  --txt:#f0f0f0;--txt2:#b0b0b0;--txt3:#6a6a6a;--bdr:#2a2a2a;
  --radius:14px;--radius-sm:10px;
  --shadow:0 2px 12px rgba(0,0,0,.45);
}

/* ── BASE ──────────────────────────────────────────── */
.stApp{
  background:var(--bg)!important;
  font-family:'Inter',sans-serif!important;
  font-size:15px;
  line-height:1.6;
  color:var(--txt);
  -webkit-text-size-adjust:100%;
}
.main .block-container{padding:1.5rem 2.5rem 4rem!important;max-width:100%!important;}
*{box-sizing:border-box;}

/* ── SIDEBAR ───────────────────────────────────────── */
[data-testid="stSidebar"]{background:#0d0d0d!important;border-right:1px solid var(--bdr)!important;}
[data-testid="stSidebar"] *{color:var(--txt)!important;}
[data-testid="stSidebar"] .stButton button{
  background:transparent!important;color:var(--txt2)!important;
  border:none!important;text-align:left!important;padding:10px 14px!important;
  border-radius:8px!important;font-size:.9rem!important;font-weight:500!important;
  transition:all .15s!important;width:100%!important;letter-spacing:0!important;
}
[data-testid="stSidebar"] .stButton button:hover{
  background:rgba(200,255,0,.08)!important;color:var(--acc)!important;transform:none!important;box-shadow:none!important;
}

/* ── HEADINGS ──────────────────────────────────────── */
h1,h2,h3,h4,h5,h6{color:var(--txt)!important;font-family:'Inter',sans-serif!important;line-height:1.3!important;}
h2{font-size:1.25rem!important;font-weight:700!important;}
h3{font-size:1.1rem!important;font-weight:600!important;}
h4{font-size:1rem!important;font-weight:600!important;}

/* ── INPUTS ────────────────────────────────────────── */
.stTextInput input,.stNumberInput input,.stTextArea textarea{
  background:var(--card)!important;border:1px solid var(--bdr)!important;
  color:var(--txt)!important;border-radius:var(--radius-sm)!important;
  font-family:'Inter',sans-serif!important;font-size:15px!important;
  transition:border-color .15s,box-shadow .15s!important;
}
.stTextInput input:focus,.stNumberInput input:focus,.stTextArea textarea:focus{
  border-color:var(--acc)!important;box-shadow:0 0 0 3px rgba(200,255,0,.12)!important;outline:none!important;
}
.stTextInput label,.stNumberInput label,.stTextArea label,.stSelectbox label{
  color:var(--txt2)!important;font-size:.85rem!important;font-weight:500!important;margin-bottom:.3rem!important;
}

/* ── SELECTBOX ─────────────────────────────────────── */
.stSelectbox [data-baseweb="select"]{background:var(--card)!important;border-color:var(--bdr)!important;border-radius:var(--radius-sm)!important;}
.stSelectbox [data-baseweb="select"] *{background:var(--card)!important;color:var(--txt)!important;font-size:15px!important;}
.stSelectbox [data-baseweb="popover"] *{background:#1c1c1c!important;color:var(--txt)!important;}

/* ── BUTTONS ───────────────────────────────────────── */
.stButton button{
  background:linear-gradient(135deg,var(--acc),#b0e800)!important;
  color:#000!important;border:none!important;border-radius:var(--radius-sm)!important;
  font-weight:700!important;font-size:.9rem!important;padding:.6rem 1.5rem!important;
  transition:all .18s ease!important;letter-spacing:.2px!important;
  min-height:44px!important;
}
.stButton button:hover{
  transform:translateY(-1px)!important;
  box-shadow:0 6px 24px rgba(200,255,0,.3)!important;
}
.stButton button:active{transform:translateY(0)!important;}
.stButton button[kind="secondary"]{
  background:var(--card)!important;color:var(--txt)!important;
  border:1px solid var(--bdr)!important;
}
.stButton button[kind="secondary"]:hover{
  border-color:var(--acc)!important;color:var(--acc)!important;
  box-shadow:none!important;transform:none!important;
}

/* ── METRICS ───────────────────────────────────────── */
[data-testid="metric-container"]{
  background:var(--card)!important;border:1px solid var(--bdr)!important;
  border-radius:var(--radius)!important;padding:1.25rem!important;
  transition:border-color .15s!important;
}
[data-testid="metric-container"]:hover{border-color:#3a3a3a!important;}
[data-testid="metric-container"] label{
  color:var(--txt2)!important;font-size:.78rem!important;
  text-transform:uppercase;letter-spacing:1.2px;font-weight:600!important;
}
[data-testid="stMetricValue"]{color:var(--txt)!important;font-weight:800!important;font-size:1.75rem!important;}
[data-testid="stMetricDelta"]{font-size:.8rem!important;}

/* ── TABS ──────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"]{
  background:transparent!important;border-bottom:1px solid var(--bdr)!important;
  gap:0;overflow-x:auto;-webkit-overflow-scrolling:touch;
  scrollbar-width:none;
}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{display:none;}
.stTabs [data-baseweb="tab"]{
  color:var(--txt2)!important;background:transparent!important;border:none!important;
  font-weight:600!important;padding:.75rem 1.25rem!important;white-space:nowrap;
  font-size:.88rem!important;transition:color .15s!important;
}
.stTabs [aria-selected="true"]{color:var(--acc)!important;border-bottom:2px solid var(--acc)!important;}
.stTabs [data-baseweb="tab"]:hover{color:var(--txt)!important;}

/* ── PROGRESS ──────────────────────────────────────── */
.stProgress>div>div{background:var(--acc)!important;border-radius:4px!important;}
.stProgress>div{background:var(--card2)!important;border-radius:4px!important;}

/* ── EXPANDER ──────────────────────────────────────── */
.streamlit-expanderHeader{
  background:var(--card)!important;border:1px solid var(--bdr)!important;
  border-radius:var(--radius-sm)!important;color:var(--txt)!important;
  font-weight:600!important;font-size:.9rem!important;
  padding:1rem 1.25rem!important;
}
.streamlit-expanderContent{
  background:var(--card2)!important;border:1px solid var(--bdr)!important;
  border-top:none!important;border-radius:0 0 var(--radius-sm) var(--radius-sm)!important;
  padding:1rem 1.25rem!important;
}

/* ── SCROLLBAR ─────────────────────────────────────── */
::-webkit-scrollbar{width:5px;height:5px;}
::-webkit-scrollbar-track{background:var(--bg);}
::-webkit-scrollbar-thumb{background:#333;border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:var(--acc);}

/* ── CUSTOM COMPONENTS ─────────────────────────────── */
.card{
  background:var(--card);border:1px solid var(--bdr);
  border-radius:var(--radius);padding:1.5rem;margin-bottom:1rem;
  transition:border-color .2s;
}
.card:hover{border-color:#383838;}

.pghead{margin-bottom:1.75rem;}
.pgtitle{font-size:clamp(1.5rem,5vw,2rem);font-weight:900;color:var(--txt);letter-spacing:-1px;line-height:1.1;}
.pgsub{color:var(--txt2);font-size:.95rem;margin-top:.4rem;line-height:1.5;}

.section-label{
  font-size:.75rem;font-weight:700;text-transform:uppercase;
  letter-spacing:1.5px;color:var(--txt3);margin-bottom:.75rem;
}

.badge{display:inline-block;padding:.25rem .7rem;border-radius:20px;font-size:.72rem;font-weight:700;letter-spacing:.3px;}
.badge-g{background:rgba(46,213,115,.15);color:#2ed573;border:1px solid rgba(46,213,115,.35);}
.badge-y{background:rgba(255,165,2,.15);color:#ffa502;border:1px solid rgba(255,165,2,.35);}
.badge-r{background:rgba(255,71,87,.15);color:#ff4757;border:1px solid rgba(255,71,87,.35);}
.badge-a{background:rgba(200,255,0,.14);color:#c8ff00;border:1px solid rgba(200,255,0,.35);}

.divider{height:1px;background:var(--bdr);margin:1.25rem 0;}

.set-row{
  display:flex;align-items:center;gap:1rem;padding:.75rem 1rem;
  background:var(--card2);border-radius:var(--radius-sm);margin-bottom:.5rem;
  border:1px solid var(--bdr);transition:border-color .15s;
}
.set-row:hover{border-color:#3a3a3a;}
.set-done{border-color:rgba(46,213,115,.4)!important;background:rgba(46,213,115,.05)!important;}

.ex-chip{
  display:inline-block;background:var(--card2);border:1px solid var(--bdr);
  border-radius:20px;padding:.3rem .8rem;margin:.2rem;
  font-size:.8rem;color:var(--txt2);line-height:1.4;
}

.quote-box{
  border-left:3px solid var(--acc);padding:.9rem 1.25rem;
  background:rgba(200,255,0,.04);border-radius:0 12px 12px 0;
  font-style:italic;color:var(--txt);font-size:.95rem;line-height:1.6;
}

.pr-tag{
  background:linear-gradient(135deg,#ffd700,#ff8c00);color:#000;
  padding:.2rem .55rem;border-radius:12px;font-size:.68rem;font-weight:800;letter-spacing:.5px;
}

.db-badge{
  display:inline-flex;align-items:center;gap:.4rem;
  background:rgba(46,213,115,.1);border:1px solid rgba(46,213,115,.3);
  color:#2ed573;border-radius:20px;padding:.35rem 1rem;
  font-size:.8rem;font-weight:700;
}

/* Info text — better contrast than raw #888 */
.info-text{color:var(--txt2);font-size:.9rem;line-height:1.6;}
.muted{color:var(--txt3);font-size:.82rem;}

/* ── MOBILE RESPONSIVENESS ─────────────────────────── */
@media (max-width:768px) {
  /* Core layout — extra bottom padding for bottom nav */
  .main .block-container{padding:.75rem .75rem 5.5rem!important;}
  .stApp{font-size:15px;}

  /* Page header */
  .pgtitle{font-size:1.55rem!important;letter-spacing:-.5px!important;}
  .pgsub{font-size:.88rem!important;}
  .pghead{margin-bottom:1.25rem!important;}

  /* Cards */
  .card{padding:1rem 1.1rem!important;border-radius:12px!important;margin-bottom:.75rem!important;}

  /* Metrics — 2 per row naturally via Streamlit columns */
  [data-testid="stMetricValue"]{font-size:1.4rem!important;}
  [data-testid="metric-container"]{padding:.9rem 1rem!important;border-radius:10px!important;}
  [data-testid="metric-container"] label{font-size:.72rem!important;letter-spacing:.8px!important;}

  /* Buttons — larger touch targets */
  .stButton button{
    min-height:48px!important;font-size:.88rem!important;
    padding:.7rem 1rem!important;border-radius:10px!important;
  }

  /* Inputs — prevent iOS zoom (must be ≥16px) */
  .stTextInput input,.stNumberInput input,.stTextArea textarea{
    font-size:16px!important;min-height:46px!important;
  }
  .stSelectbox [data-baseweb="select"]{min-height:46px!important;}
  .stSelectbox [data-baseweb="select"] *{font-size:16px!important;}

  /* Tabs — horizontal scroll */
  .stTabs [data-baseweb="tab"]{padding:.65rem 1rem!important;font-size:.82rem!important;}

  /* Set rows */
  .set-row{flex-wrap:wrap!important;gap:.5rem!important;padding:.7rem .8rem!important;}

  /* Quote */
  .quote-box{padding:.75rem 1rem!important;font-size:.9rem!important;}

  /* Sidebar toggle */
  [data-testid="collapsedControl"]{
    top:.5rem!important;left:.5rem!important;
    width:44px!important;height:44px!important;
    background:#181818!important;border:1px solid #303030!important;
    border-radius:10px!important;
  }

  /* Expanders */
  .streamlit-expanderHeader{padding:.8rem 1rem!important;font-size:.88rem!important;}
  .streamlit-expanderContent{padding:.75rem 1rem!important;}

  /* Plotly — no overflow */
  .js-plotly-plot,.plot-container{max-width:100%!important;overflow:hidden!important;}

  /* Divider spacing */
  .divider{margin:.9rem 0!important;}

  /* Section label */
  .section-label{font-size:.7rem!important;}

  /* Headings on mobile */
  h2{font-size:1.1rem!important;}
  h3{font-size:1rem!important;}
  h4{font-size:.95rem!important;}
}

/* ── TABLET ────────────────────────────────────────── */
@media (min-width:769px) and (max-width:1024px) {
  .main .block-container{padding:1.25rem 1.75rem 3rem!important;}
  .pgtitle{font-size:1.85rem!important;}
  [data-testid="stMetricValue"]{font-size:1.6rem!important;}
}

</style>
""", unsafe_allow_html=True)

# ── CONNECTION CHECK ──────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def check_connection():
    try:
        from database import get_sb
        get_sb().table("plans").select("id").limit(1).execute()
        return True, None
    except Exception as e:
        return False, str(e)

conn_ok, conn_err = check_connection()

# ── START BACKGROUND SCHEDULER ───────────────────────────────────────────────
if conn_ok:
    start_scheduler()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
PAGES = [
    ("🏠","Dashboard","dashboard"),
    ("🤖","Agentes IA","agents"),
    ("▶️","Iniciar Treino","workout"),
    ("📋","Planos de Treino","plans"),
    ("📚","Exercícios","exercises"),
    ("📅","Histórico","history"),
    ("📊","Progresso","progress"),
    ("📏","Medidas","measurements"),
    ("🏆","Recordes","records"),
    ("🧮","Calculadoras","calculators"),
    ("⏱️","Timer","timer"),
    ("🥗","Nutrição","nutrition"),
    ("🎯","Metas","goals"),
]

with st.sidebar:
    st.markdown("""
    <div style="padding:1.5rem 1rem 1rem;text-align:center;">
      <div style="font-size:1.9rem;font-weight:900;color:#c8ff00;letter-spacing:-1px;">⚡ IRONLOG</div>
      <div style="font-size:.7rem;color:#888;letter-spacing:2px;text-transform:uppercase;margin-top:.2rem;">Seu parceiro de treino</div>
    </div>
    <div style="height:1px;background:#1e1e1e;margin:0 1rem .75rem;"></div>
    """, unsafe_allow_html=True)

    # DB status
    if conn_ok:
        st.markdown('<div style="text-align:center;margin-bottom:.75rem;"><span class="db-badge">🟢 Supabase conectado</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center;margin-bottom:.75rem;"><span class="badge badge-r">🔴 Sem conexão</span></div>', unsafe_allow_html=True)

    for icon, label, key in PAGES:
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.page = key
            st.rerun()

    if st.session_state.workout:
        elapsed = (datetime.now() - datetime.fromisoformat(st.session_state.workout["start"])).seconds // 60
        st.markdown(f"""
        <div style="margin:1rem;padding:.75rem;background:rgba(200,255,0,.07);border:1px solid rgba(200,255,0,.3);border-radius:10px;text-align:center;">
          <div style="color:#c8ff00;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;">🔥 Treino em Andamento</div>
          <div style="color:#888;font-size:.75rem;margin-top:.25rem;">{elapsed} min</div>
        </div>
        """, unsafe_allow_html=True)

# ── BLOCK IF NO CONNECTION ────────────────────────────────────────────────────
if not conn_ok and st.session_state.page not in ("calculators", "timer"):
    st.markdown(f"""
    <div class="card" style="border-color:#ff4757;text-align:center;padding:3rem;">
      <div style="font-size:3rem;">🔴</div>
      <div style="font-size:1.5rem;font-weight:800;margin:.75rem 0 .5rem;">Sem conexão com Supabase</div>
      <div style="color:#b0b0b0;font-size:.9rem;">{conn_err}</div>
      <div style="margin-top:1.5rem;color:#a0a0a0;font-size:.85rem;">
        Verifique o arquivo <code>.env</code> e rode o <code>schema.sql</code> no Supabase.
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── MOBILE QUICK-NAV BAR ─────────────────────────────────────────────────────
# Shows on mobile only — horizontal scrollable row of icon+label buttons
_mob_pages = [
    ("🏠", "dashboard", "Início"),
    ("🤖", "agents",    "IA"),
    ("🏋️", "workout",   "Treino"),
    ("📊", "progress",  "Stats"),
    ("📋", "plans",     "Planos"),
    ("🍽️", "nutrition", "Dieta"),
    ("🎯", "goals",     "Metas"),
]
_cur_page = st.session_state.get("page", "dashboard")

st.markdown("""
<style>
/* Hide the mob-nav wrapper on desktop */
.mob-nav-outer{display:none;}
@media(max-width:768px){
  .mob-nav-outer{
    display:flex!important;gap:.3rem;margin-bottom:1rem;
    overflow-x:auto;padding:.15rem .05rem;-webkit-overflow-scrolling:touch;
    scrollbar-width:none;
  }
  .mob-nav-outer::-webkit-scrollbar{display:none;}
  /* Each column inside the nav */
  .mob-nav-outer [data-testid="column"]{
    flex:0 0 auto!important;min-width:60px!important;
  }
  /* Default button style */
  .mob-nav-outer .stButton button{
    background:#1a1a1a!important;color:#7a7a7a!important;
    border:1px solid #2a2a2a!important;border-radius:10px!important;
    padding:.4rem .2rem .35rem!important;font-size:.75rem!important;
    min-height:52px!important;line-height:1.3!important;
    font-weight:600!important;display:flex!important;
    flex-direction:column!important;align-items:center!important;
    gap:.1rem!important;transform:none!important;box-shadow:none!important;
  }
  /* Active button */
  .mob-nav-active .stButton button{
    background:rgba(200,255,0,.1)!important;color:#c8ff00!important;
    border-color:rgba(200,255,0,.35)!important;
  }
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="mob-nav-outer">', unsafe_allow_html=True)
_mob_btn_cols = st.columns(len(_mob_pages))
for _col, (_icon, _key, _lbl) in zip(_mob_btn_cols, _mob_pages):
    _active = _cur_page == _key
    with _col:
        if _active:
            st.markdown('<div class="mob-nav-active">', unsafe_allow_html=True)
        if st.button(f"{_icon}\n{_lbl}", key=f"mobnav_{_key}", use_container_width=True):
            st.session_state.page = _key
            st.rerun()
        if _active:
            st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ── PAGES ─────────────────────────────────────────────────────────────────────

def page_dashboard():
    # ── Autonomous agent notifications (persistent in session_state) ──────────
    # Pull new ones from file and merge into session_state list
    if "agent_notifs" not in st.session_state:
        st.session_state.agent_notifs = []
    new_notifs = get_pending_notifications()
    if new_notifs:
        st.session_state.agent_notifs = new_notifs + st.session_state.agent_notifs
        st.session_state.agent_notifs = st.session_state.agent_notifs[:10]  # keep max 10

    notifs_to_remove = []
    for idx, n in enumerate(st.session_state.agent_notifs):
        auto_name = n.get("name", "Automação")
        ts_raw    = n.get("at", "")
        try:
            ts = datetime.fromisoformat(ts_raw).strftime("%d/%m/%Y às %H:%M")
        except Exception:
            ts = ts_raw
        nc1, nc2 = st.columns([10, 1])
        with nc1:
            st.markdown(f"""
            <div style="background:rgba(200,255,0,.07);border:1px solid rgba(200,255,0,.35);
                        border-radius:12px;padding:.9rem 1.25rem;margin-bottom:.5rem;display:flex;
                        align-items:flex-start;gap:.9rem;">
              <div style="font-size:1.4rem;line-height:1;">🤖</div>
              <div>
                <div style="color:#c8ff00;font-weight:700;font-size:.88rem;">
                  Agente Autônomo: {auto_name}
                </div>
                <div style="color:#a8a8a8;font-size:.75rem;margin-top:.2rem;">{ts}</div>
              </div>
            </div>""", unsafe_allow_html=True)
        with nc2:
            st.markdown("<div style='height:.6rem'></div>", unsafe_allow_html=True)
            if st.button("✕", key=f"dismiss_notif_{idx}", type="secondary"):
                notifs_to_remove.append(idx)
    for idx in sorted(notifs_to_remove, reverse=True):
        st.session_state.agent_notifs.pop(idx)
    if notifs_to_remove:
        st.rerun()

    sessions = get_sessions()
    plans = get_plans()
    today = date.today()
    week_ago = today - timedelta(days=7)

    week_sessions = [s for s in sessions if date.fromisoformat(str(s["date"])[:10]) >= week_ago]
    total_sessions = len(sessions)
    streak = 0
    seen = {str(s["date"])[:10] for s in sessions}
    d = today
    while str(d) in seen:
        streak += 1
        d -= timedelta(days=1)

    week_vol = 0
    for s in week_sessions:
        for ex in (s.get("exercises") or []):
            for st_ in (ex.get("sets") or []):
                if st_.get("done"):
                    week_vol += st_.get("weight", 0) * st_.get("reps", 0)

    st.markdown('<div class="pghead"><div class="pgtitle">Dashboard</div><div class="pgsub">Bem-vindo de volta. Vamos treinar? 💪</div></div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    c1.metric("🗓️ Treinos na Semana", len(week_sessions))
    c2.metric("📦 Total de Treinos", total_sessions)
    c3, c4 = st.columns(2)
    c3.metric("🔥 Sequência Atual", f"{streak} dias" if streak > 0 else "0 dias")
    c4.metric("💪 Volume Semana", f"{week_vol:,.0f} kg")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("#### 📈 Treinos nos Últimos 30 Dias")
        if HAS_PLOTLY:
            days_30 = [(today - timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
            counts = {d: 0 for d in days_30}
            for s in sessions:
                d = str(s["date"])[:10]
                if d in counts:
                    counts[d] += 1
            fig = go.Figure()
            fig.add_trace(go.Bar(x=list(counts.keys()), y=list(counts.values()),
                marker_color="#c8ff00", marker_line_width=0))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888", height=220, margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(showgrid=False, showticklabels=False),
                yaxis=dict(showgrid=True, gridcolor="#1e1e1e"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if sessions:
            st.markdown("#### 📅 Últimos Treinos")
            for s in sessions[:5]:
                d = date.fromisoformat(str(s["date"])[:10]).strftime("%d/%m/%Y")
                n_ex = len(s.get("exercises") or [])
                st.markdown(f"""
                <div class="card" style="padding:1rem 1.25rem;display:flex;justify-content:space-between;align-items:center;gap:.75rem;">
                  <div style="flex:1;min-width:0;">
                    <div style="font-weight:700;color:#f0f0f0;font-size:.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{s.get("plan_name","Treino Livre")}</div>
                    <div style="font-size:.82rem;color:#a8a8a8;margin-top:.25rem;">{d} &middot; {n_ex} exercícios &middot; {s.get("duration",0)} min</div>
                  </div>
                  <span class="badge badge-a" style="flex-shrink:0;">Concluído</span>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="card" style="text-align:center;color:#888;padding:2rem;">Nenhum treino registrado ainda.</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("#### 💡 Motivação")
        q = random.choice(QUOTES)
        st.markdown(f'<div class="quote-box"><div style="color:#f0f0f0;font-style:italic;">"{q}"</div></div>', unsafe_allow_html=True)

        st.markdown('<div style="margin-top:1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown("#### 📋 Seus Planos")
        if plans:
            for p in plans[:5]:
                n = len(p.get("exercises") or [])
                st.markdown(f"""
                <div class="card" style="padding:.9rem 1.1rem;">
                  <div style="font-weight:700;font-size:.9rem;">{p["name"]}</div>
                  <div style="color:#a8a8a8;font-size:.78rem;margin-top:.2rem;">{n} exercícios</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="card" style="color:#909090;font-size:.85rem;text-align:center;">Crie seu primeiro plano!</div>', unsafe_allow_html=True)

        if st.button("▶️ Iniciar Treino Agora", use_container_width=True):
            st.session_state.page = "workout"
            st.rerun()


def page_workout():
    st.markdown('<div class="pghead"><div class="pgtitle">Iniciar Treino</div><div class="pgsub">Registre seus sets em tempo real.</div></div>', unsafe_allow_html=True)

    if st.session_state.workout is None:
        plans = get_plans()
        plan_names = ["Treino Livre", "😴 Dia de Descanso"] + [p["name"] for p in plans]
        sel = st.selectbox("Selecionar Plano", plan_names)

        if sel == "😴 Dia de Descanso":
            st.markdown('<div class="card" style="text-align:center;padding:2rem;border-color:rgba(200,255,0,.2);">'
                        '<div style="font-size:2.5rem;">😴</div>'
                        '<div style="font-size:1.1rem;font-weight:700;margin:.5rem 0 .25rem;">Dia de Descanso</div>'
                        '<div style="color:#a8a8a8;font-size:.85rem;">Recuperação é parte do treino.</div>'
                        '</div>', unsafe_allow_html=True)
            rest_note = st.text_input("Anotação (opcional)", placeholder="Alongamento, caminhada leve...")
            if st.button("💾 Registrar Descanso", use_container_width=True):
                add_session({"id": str(uuid.uuid4()), "date": date.today().isoformat(),
                             "plan_name": "😴 Descanso", "duration": 0, "exercises": [],
                             "notes": rest_note})
                st.success("✅ Dia de descanso registrado!")
                st.session_state.page = "history"
                st.rerun()
        else:
            exercises_for_plan = []
            if sel != "Treino Livre":
                plan_obj = next((p for p in plans if p["name"] == sel), None)
                if plan_obj:
                    exercises_for_plan = plan_obj.get("exercises") or []

            if st.button("🚀 Começar Treino", use_container_width=True):
                exs = []
                for e in exercises_for_plan:
                    sets = [{"weight": float(e.get("weight", 0)), "reps": int(e.get("reps_target", 10)),
                             "done": False, "rpe": 0}
                            for _ in range(e.get("sets", 3))]
                    exs.append({"name": e["name"], "target_sets": e.get("sets", 3),
                                 "target_reps": str(e.get("reps_target", 10)),
                                 "rest": e.get("rest", 90), "sets": sets, "notes": ""})
                st.session_state.workout = {
                    "plan_name": sel, "start": datetime.now().isoformat(),
                    "exercises": exs, "notes": "",
                }
                st.session_state.rest_end_ts = 0.0
                st.rerun()
    else:
        w = st.session_state.workout
        elapsed = (datetime.now() - datetime.fromisoformat(w["start"])).seconds // 60
        total_sets_done = sum(1 for e in w["exercises"] for s in e["sets"] if s["done"])
        total_sets = sum(len(e["sets"]) for e in w["exercises"])

        hc1, hc2, hc3 = st.columns(3)
        hc1.metric("⏱️ Duração", f"{elapsed} min")
        hc2.metric("✅ Sets Concluídos", f"{total_sets_done}/{total_sets}")
        hc3.metric("💪 Exercícios", len(w["exercises"]))

        # ── REST TIMER BANNER ──────────────────────────────────────────────────
        now_ts = time.time()
        if st.session_state.rest_end_ts > now_ts:
            end_ts_ms = int(st.session_state.rest_end_ts * 1000)
            ex_name   = st.session_state.get("rest_ex_name", "")
            components.html(f"""
            <div id="rtb" style="background:#0d0d0d;border:2px solid #c8ff00;border-radius:14px;
              padding:1rem 1.5rem;display:flex;align-items:center;gap:1.5rem;margin-bottom:.5rem;
              font-family:Inter,sans-serif;">
              <div style="text-align:center;min-width:70px;">
                <div id="rcount" style="color:#c8ff00;font-size:2.8rem;font-weight:900;line-height:1;">0</div>
                <div style="color:#888;font-size:.7rem;text-transform:uppercase;letter-spacing:1px;">seg</div>
              </div>
              <div style="flex:1;">
                <div style="color:#888;font-size:.72rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:.2rem;">Descanso</div>
                <div style="color:#e0e0e0;font-size:.9rem;font-weight:600;">{ex_name}</div>
              </div>
              <button onclick="skipRest()" style="background:#1e1e1e;border:1px solid #333;color:#888;
                border-radius:8px;padding:.4rem .9rem;cursor:pointer;font-size:.8rem;">Pular ⏭</button>
            </div>
            <script>
            const endTs={end_ts_ms};
            const el=document.getElementById('rcount');
            let done=false;
            function tick(){{
              const rem=Math.max(0,Math.ceil((endTs-Date.now())/1000));
              el.textContent=rem;
              const pct=rem/((endTs-Date.now()+rem*1000)/1000);
              el.style.color=rem<=5?'#ff4757':'#c8ff00';
              if(rem>0){{setTimeout(tick,250);}}
              else if(!done){{done=true;beep();document.getElementById('rtb').style.opacity='.4';}}
            }}
            function beep(){{try{{const a=new AudioContext();const o=a.createOscillator();
              o.connect(a.destination);o.frequency.value=880;o.start();o.stop(a.currentTime+0.3);
              setTimeout(()=>{{const o2=a.createOscillator();o2.connect(a.destination);
              o2.frequency.value=1100;o2.start();o2.stop(a.currentTime+0.25);}},350);}}catch(e){{}}}}
            function skipRest(){{document.getElementById('rtb').style.display='none';}}
            tick();
            </script>
            """, height=110)

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        with st.expander("➕ Adicionar Exercício"):
            names = ex_names()
            ex_pick = st.selectbox("Exercício", names, key="wk_add_ex")
            c1, c2, c3 = st.columns(3)
            n_sets = c1.number_input("Sets", 1, 20, 3, key="wk_add_sets")
            reps_t = c2.number_input("Reps alvo", 1, 50, 10, key="wk_add_reps")
            rest_t = c3.number_input("Descanso (s)", 30, 300, 90, key="wk_add_rest")
            w_t = st.number_input("Peso (kg)", 0.0, 500.0, 0.0, 2.5, key="wk_add_w")
            if st.button("Adicionar"):
                sets = [{"weight": w_t, "reps": reps_t, "done": False, "rpe": 0} for _ in range(n_sets)]
                w["exercises"].append({"name": ex_pick, "target_sets": n_sets,
                    "target_reps": str(reps_t), "rest": rest_t, "sets": sets, "notes": ""})
                st.rerun()

        def _start_rest(ei, si):
            key = f"d_{ei}_{si}"
            if st.session_state.get(key):   # just checked as done
                ex = st.session_state.workout["exercises"][ei]
                rest_secs = ex.get("rest", 90)
                st.session_state.rest_end_ts  = time.time() + rest_secs
                st.session_state.rest_ex_name = ex["name"]

        for ei, ex in enumerate(w["exercises"]):
            with st.expander(f"**{ex['name']}** — {len(ex['sets'])} sets · alvo: {ex['target_reps']} reps", expanded=True):
                st.markdown(
                    "<div style='display:grid;grid-template-columns:40px 1fr 1fr 1fr 60px 50px;"
                    "gap:.4rem;align-items:center;padding:.3rem 0;"
                    "font-size:.72rem;color:#909090;text-transform:uppercase;letter-spacing:1px;'>"
                    "<div></div><div>Peso(kg)</div><div>Reps</div><div>RPE</div><div>Feito</div><div></div>"
                    "</div>", unsafe_allow_html=True)
                for si, s in enumerate(ex["sets"]):
                    cc = st.columns([1, 2, 2, 2, 1, 1])
                    cc[0].markdown(f"<div style='color:#909090;font-size:.82rem;padding-top:.55rem;'>S{si+1}</div>", unsafe_allow_html=True)
                    w_val  = cc[1].number_input("kg",   0.0, 500.0, float(s["weight"]), 2.5,  key=f"w_{ei}_{si}", label_visibility="collapsed")
                    r_val  = cc[2].number_input("reps", 0,   100,   int(s["reps"]),           key=f"r_{ei}_{si}", label_visibility="collapsed")
                    rpe_val= cc[3].number_input("RPE",  0,   10,    int(s.get("rpe", 0)),      key=f"rpe_{ei}_{si}", label_visibility="collapsed")
                    done   = cc[4].checkbox("✓",  value=s["done"], key=f"d_{ei}_{si}",
                                            on_change=_start_rest, args=(ei, si))
                    if cc[5].button("⏱", key=f"t_{ei}_{si}", help="Reiniciar descanso"):
                        st.session_state.rest_end_ts  = time.time() + ex.get("rest", 90)
                        st.session_state.rest_ex_name = ex["name"]
                        st.rerun()
                    s["weight"] = w_val; s["reps"] = r_val; s["done"] = done; s["rpe"] = rpe_val
                ex["notes"] = st.text_input("Anotações", value=ex.get("notes",""), key=f"note_{ei}", placeholder="Observações...")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        col_notes, col_finish = st.columns([2, 1])
        with col_notes:
            w["notes"] = st.text_area("Anotações do treino", value=w.get("notes",""), height=80, placeholder="Como foi o treino hoje?")
        with col_finish:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            if st.button("🏁 Finalizar Treino", use_container_width=True):
                dur = (datetime.now() - datetime.fromisoformat(w["start"])).seconds // 60
                try:
                    add_session({
                        "id": str(uuid.uuid4()),
                        "date": w["start"][:10],
                        "plan_name": w["plan_name"],
                        "duration": dur,
                        "exercises": w["exercises"],
                        "notes": w.get("notes", ""),
                    })
                    st.session_state.workout = None
                    st.session_state.rest_end_ts = 0.0
                    st.success("✅ Treino salvo!")
                    st.session_state.page = "history"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            # Confirm cancel
            if not st.session_state.get("confirm_cancel_workout"):
                if st.button("❌ Cancelar", use_container_width=True, type="secondary"):
                    st.session_state.confirm_cancel_workout = True
                    st.rerun()
            else:
                st.warning("Perderá o treino atual. Tem certeza?")
                cc1, cc2 = st.columns(2)
                if cc1.button("Sim, cancelar", use_container_width=True, type="secondary"):
                    st.session_state.workout = None
                    st.session_state.rest_end_ts = 0.0
                    st.session_state.confirm_cancel_workout = False
                    st.rerun()
                if cc2.button("Continuar", use_container_width=True):
                    st.session_state.confirm_cancel_workout = False
                    st.rerun()


def page_plans():
    st.markdown('<div class="pghead"><div class="pgtitle">Planos de Treino</div><div class="pgsub">Crie e gerencie seus programas.</div></div>', unsafe_allow_html=True)

    plans = get_plans()
    tab1, tab2 = st.tabs(["📋 Meus Planos", "➕ Novo Plano"])

    with tab1:
        if not plans:
            st.markdown('<div class="card" style="text-align:center;color:#909090;padding:3rem;">Nenhum plano criado ainda.</div>', unsafe_allow_html=True)
        for plan in plans:
            with st.expander(f"**{plan['name']}** — {len(plan.get('exercises') or [])} exercícios"):
                for ex in (plan.get("exercises") or []):
                    st.markdown(f"""
                    <div class="set-row">
                      <div style="flex:1;font-weight:600;">{ex['name']}</div>
                      <span class="badge badge-a">{ex.get('sets',3)}×{ex.get('reps_target',10)}</span>
                      <span class="badge badge-g">{ex.get('weight',0)} kg</span>
                      <span class="badge badge-y">⏱ {ex.get('rest',90)}s</span>
                    </div>""", unsafe_allow_html=True)
                conf_key = f"confirm_del_plan_{plan['id']}"
                if not st.session_state.get(conf_key):
                    if st.button("🗑️ Deletar Plano", key=f"del_{plan['id']}", type="secondary"):
                        st.session_state[conf_key] = True
                        st.rerun()
                else:
                    st.warning(f"Deletar **{plan['name']}**? Não pode ser desfeito.")
                    cc1, cc2 = st.columns(2)
                    if cc1.button("✅ Confirmar", key=f"conf_yes_{plan['id']}"):
                        delete_plan(plan["id"])
                        st.session_state.pop(conf_key, None)
                        st.rerun()
                    if cc2.button("❌ Cancelar", key=f"conf_no_{plan['id']}", type="secondary"):
                        st.session_state.pop(conf_key, None)
                        st.rerun()

    with tab2:
        plan_name = st.text_input("Nome do Plano", placeholder="Ex: Treino A — Peito e Tríceps")
        if "new_plan_ex" not in st.session_state:
            st.session_state.new_plan_ex = []

        all_ex_list = all_exercises()
        names = [e["name"] for e in all_ex_list]

        # ── Bulk add ──────────────────────────────────────────────────────────
        st.markdown("#### Adicionar Exercícios")
        bulk_picks = st.multiselect("Selecionar vários de uma vez", names, key="np_bulk",
                                    placeholder="Escolha 1 ou mais exercícios...")
        c1, c2, c3 = st.columns(3)
        np_sets   = c1.number_input("Sets (todos)", 1, 20, 3, key="np_sets")
        np_reps   = c2.number_input("Reps (todos)", 1, 50, 10, key="np_reps")
        np_rest   = c3.number_input("Descanso s (todos)", 30, 300, 90, key="np_rest")
        np_weight = st.number_input("Peso kg (todos)", 0.0, 500.0, 0.0, 2.5, key="np_weight")

        if st.button("➕ Adicionar Selecionados") and bulk_picks:
            existing = {e["name"] for e in st.session_state.new_plan_ex}
            for nm in bulk_picks:
                if nm not in existing:
                    st.session_state.new_plan_ex.append({"name": nm, "sets": np_sets,
                        "reps_target": np_reps, "weight": np_weight, "rest": np_rest})
            st.rerun()

        if st.session_state.new_plan_ex:
            st.markdown("#### Exercícios do Plano")
            for i, ex in enumerate(st.session_state.new_plan_ex):
                col1, col2 = st.columns([4, 1])
                col1.markdown(f"""<div class="set-row"><div style="flex:1;font-weight:600;">{ex['name']}</div>
                  <span class="badge badge-a">{ex['sets']}×{ex['reps_target']}</span>
                  <span class="badge badge-g">{ex['weight']} kg</span>
                  <span class="badge badge-y">⏱ {ex.get('rest',90)}s</span></div>""", unsafe_allow_html=True)
                if col2.button("✕", key=f"rm_{i}", type="secondary"):
                    st.session_state.new_plan_ex.pop(i)
                    st.rerun()

        if st.button("💾 Salvar Plano", use_container_width=True) and plan_name:
            if not st.session_state.new_plan_ex:
                st.warning("Adicione pelo menos um exercício.")
            else:
                try:
                    add_plan({"id": str(uuid.uuid4()), "name": plan_name,
                               "exercises": st.session_state.new_plan_ex.copy()})
                    st.session_state.new_plan_ex = []
                    st.success(f"✅ Plano '{plan_name}' salvo!")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))


def page_exercises():
    st.markdown('<div class="pghead"><div class="pgtitle">Exercícios</div><div class="pgsub">Biblioteca completa de exercícios.</div></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📚 Biblioteca", "➕ Exercício Personalizado"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        muscle_filter = c1.selectbox("Grupo Muscular", ["Todos"] + list(DB.keys()))
        search = c2.text_input("Buscar", placeholder="Nome do exercício...")

        all_ex = all_exercises()
        if muscle_filter != "Todos":
            all_ex = [e for e in all_ex if e.get("muscle") == muscle_filter]
        if search:
            all_ex = [e for e in all_ex if search.lower() in e["name"].lower()]

        for muscle in (list(DB.keys()) if muscle_filter == "Todos" else [muscle_filter]):
            exs = [e for e in all_ex if e.get("muscle") == muscle]
            if not exs:
                continue
            st.markdown(f"<div style='color:#c8ff00;font-weight:800;font-size:.9rem;text-transform:uppercase;letter-spacing:1px;margin:1.5rem 0 .5rem;'>{muscle}</div>", unsafe_allow_html=True)
            for e in exs:
                lvl = e.get("lvl", "")
                badge = "badge-g" if lvl=="Iniciante" else ("badge-y" if lvl=="Intermediário" else "badge-r")
                with st.expander(f"{e['name']} — {e.get('eq','')}"):
                    st.markdown(f"""
                    <div style="display:flex;gap:.5rem;margin-bottom:.75rem;">
                      <span class="badge {badge}">{lvl}</span>
                      <span class="badge badge-a">{e.get('muscle','')}</span>
                      <span class="ex-chip">🏋️ {e.get('eq','')}</span>
                    </div>
                    <div style="color:#aaa;font-size:.9rem;line-height:1.6;">{e.get('descr','')}</div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.markdown("#### Adicionar Exercício Personalizado")
        name_c = st.text_input("Nome")
        c1, c2 = st.columns(2)
        muscle_c = c1.selectbox("Grupo Muscular", list(DB.keys()), key="cus_muscle")
        eq_c = c2.text_input("Equipamento")
        lvl_c = st.radio("Dificuldade", ["Iniciante","Intermediário","Avançado"], horizontal=True)
        desc_c = st.text_area("Como executar", height=100)
        if st.button("Salvar Exercício") and name_c:
            try:
                add_custom_exercise({"id": str(uuid.uuid4()), "name": name_c,
                    "muscle": muscle_c, "eq": eq_c, "lvl": lvl_c, "descr": desc_c})
                st.success("✅ Adicionado!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

        custom = get_custom_exercises()
        if custom:
            st.markdown("#### Seus Exercícios")
            for e in custom:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"**{e['name']}** — {e.get('muscle','')}")
                if c2.button("🗑️", key=f"del_ce_{e['id']}", type="secondary"):
                    delete_custom_exercise(e["id"])
                    st.rerun()


def page_history():
    st.markdown('<div class="pghead"><div class="pgtitle">Histórico</div><div class="pgsub">Todos os seus treinos.</div></div>', unsafe_allow_html=True)

    sessions = get_sessions()
    if not sessions:
        st.markdown('<div class="card" style="text-align:center;color:#909090;padding:3rem;">Nenhum treino registrado ainda.</div>', unsafe_allow_html=True)
        return

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns(3)
    search_hist = fc1.text_input("🔍 Buscar plano", placeholder="Nome do treino...", key="hist_search")
    all_plan_names = sorted({s.get("plan_name","") for s in sessions if s.get("plan_name")})
    plan_filter = fc2.selectbox("Filtrar por plano", ["Todos"] + all_plan_names, key="hist_plan")
    date_options = ["Todos os tempos","Última semana","Último mês","Últimos 3 meses"]
    date_filter = fc3.selectbox("Período", date_options, key="hist_period")

    today = date.today()
    cutoffs = {"Última semana": today-timedelta(days=7), "Último mês": today-timedelta(days=30),
               "Últimos 3 meses": today-timedelta(days=90)}

    filtered = sessions
    if search_hist:
        filtered = [s for s in filtered if search_hist.lower() in (s.get("plan_name","")).lower()]
    if plan_filter != "Todos":
        filtered = [s for s in filtered if s.get("plan_name") == plan_filter]
    if date_filter in cutoffs:
        filtered = [s for s in filtered if date.fromisoformat(str(s["date"])[:10]) >= cutoffs[date_filter]]

    st.markdown(f"<div style='color:#909090;font-size:.8rem;margin:.5rem 0 1rem;'>{len(filtered)} treino(s)</div>", unsafe_allow_html=True)

    # ── Pagination ────────────────────────────────────────────────────────────
    PAGE_SIZE = 15
    total_pages = max(1, math.ceil(len(filtered) / PAGE_SIZE))
    pg = st.session_state.get("history_page", 0)
    pg = max(0, min(pg, total_pages - 1))
    page_sessions = filtered[pg * PAGE_SIZE:(pg + 1) * PAGE_SIZE]

    for s in page_sessions:
        plan_nm = s.get("plan_name", "Treino Livre")
        is_rest = plan_nm == "😴 Descanso"
        d = date.fromisoformat(str(s["date"])[:10]).strftime("%d/%m/%Y")
        n_ex = len(s.get("exercises") or [])
        total_vol = sum(
            s2.get("weight",0) * s2.get("reps",0)
            for e in (s.get("exercises") or [])
            for s2 in (e.get("sets") or [])
            if s2.get("done")
        )
        label = f"{'😴' if is_rest else '💪'} **{plan_nm}** — {d}" + (f"  ·  {s.get('duration',0)} min  ·  {n_ex} exercícios" if not is_rest else "")
        with st.expander(label):
            if is_rest:
                st.markdown('<div style="color:#888;font-size:.9rem;padding:.5rem 0;">Dia de recuperação registrado.</div>', unsafe_allow_html=True)
                if s.get("notes"):
                    st.markdown(f"<div style='color:#a8a8a8;font-size:.85rem;font-style:italic;'>📝 {s['notes']}</div>", unsafe_allow_html=True)
            else:
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Duração", f"{s.get('duration',0)} min")
                mc2.metric("Exercícios", n_ex)
                mc3.metric("Volume Total", f"{total_vol:,.0f} kg")
                for ex in (s.get("exercises") or []):
                    sets_done = [s2 for s2 in (ex.get("sets") or []) if s2.get("done")]
                    if not sets_done:
                        continue
                    st.markdown(f"<div style='font-weight:700;margin:.75rem 0 .4rem;color:#c8ff00;font-size:.9rem;'>{ex['name']}</div>", unsafe_allow_html=True)
                    for i, s2 in enumerate(sets_done):
                        rpe_txt = f" · RPE {s2.get('rpe',0)}" if s2.get("rpe") else ""
                        st.markdown(f"<div class='set-row set-done'><span style='color:#a8a8a8;font-size:.8rem;'>Set {i+1}</span>"
                                    f"<span>{s2.get('weight',0)} kg × {s2.get('reps',0)} reps{rpe_txt}</span></div>", unsafe_allow_html=True)
                if s.get("notes"):
                    st.markdown(f"<div style='color:#a8a8a8;font-size:.85rem;font-style:italic;'>📝 {s['notes']}</div>", unsafe_allow_html=True)

    # Pagination controls
    if total_pages > 1:
        st.markdown('<div style="height:.75rem;"></div>', unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        if pc1.button("← Anterior", disabled=(pg == 0), use_container_width=True, type="secondary"):
            st.session_state.history_page = pg - 1
            st.rerun()
        pc2.markdown(f"<div style='text-align:center;color:#909090;padding:.6rem;'>Página {pg+1} / {total_pages}</div>", unsafe_allow_html=True)
        if pc3.button("Próxima →", disabled=(pg >= total_pages-1), use_container_width=True, type="secondary"):
            st.session_state.history_page = pg + 1
            st.rerun()


def page_progress():
    st.markdown('<div class="pghead"><div class="pgtitle">Progresso</div><div class="pgsub">Sua evolução ao longo do tempo.</div></div>', unsafe_allow_html=True)

    if not HAS_PLOTLY:
        st.warning("Instale plotly: pip install plotly")
        return

    sessions = get_sessions()
    if not sessions:
        st.info("Nenhum treino registrado.")
        return

    ex_data = {}
    for s in sessions:
        d = str(s["date"])[:10]
        for ex in (s.get("exercises") or []):
            nm = ex["name"]
            for s2 in (ex.get("sets") or []):
                if s2.get("done") and s2.get("weight", 0) > 0:
                    ex_data.setdefault(nm, []).append({"date": d, "weight": s2["weight"], "reps": s2["reps"]})

    if not ex_data:
        st.info("Complete treinos para ver o progresso.")
        return

    tab1, tab2 = st.tabs(["💪 Por Exercício", "📊 Volume Semanal"])

    with tab1:
        sel_ex = st.selectbox("Exercício", sorted(ex_data.keys()))
        if sel_ex:
            data = sorted(ex_data[sel_ex], key=lambda x: x["date"])
            dates = [d["date"] for d in data]
            weights = [d["weight"] for d in data]
            rm1 = [round(w * (1 + r / 30), 1) for w, r in zip(weights, [d["reps"] for d in data])]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=weights, name="Peso (kg)",
                line=dict(color="#c8ff00", width=2), mode="lines+markers", marker=dict(size=6, color="#c8ff00")))
            fig.add_trace(go.Scatter(x=dates, y=rm1, name="1RM Estimado",
                line=dict(color="#ff4757", width=1, dash="dot"), mode="lines"))
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888", height=320, legend=dict(orientation="h", y=-0.2),
                margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(gridcolor="#1e1e1e"))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            if weights:
                c1, c2, c3 = st.columns(3)
                c1.metric("Peso Máximo", f"{max(weights)} kg")
                c2.metric("Último", f"{weights[-1]} kg")
                c3.metric("Evolução", f"{weights[-1]-weights[0]:+.1f} kg" if len(weights)>1 else "—")

    with tab2:
        from collections import defaultdict
        week_vol = defaultdict(float)
        for s in sessions:
            d = date.fromisoformat(str(s["date"])[:10])
            week = d.strftime("%Y-W%W")
            for ex in (s.get("exercises") or []):
                for s2 in (ex.get("sets") or []):
                    if s2.get("done"):
                        week_vol[week] += s2.get("weight",0) * s2.get("reps",0)
        if week_vol:
            wks = sorted(week_vol.keys())
            fig2 = go.Figure(go.Bar(x=wks, y=[week_vol[w] for w in wks],
                marker_color="#c8ff00", marker_line_width=0))
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888", height=300, margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(gridcolor="#1e1e1e", title="Volume (kg·reps)"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


def page_measurements():
    st.markdown('<div class="pghead"><div class="pgtitle">Medidas Corporais</div><div class="pgsub">Acompanhe sua composição corporal.</div></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["➕ Nova Medição", "📈 Histórico"])

    with tab1:
        med_date = st.date_input("Data", value=date.today())
        c1, c2, c3 = st.columns(3)
        peso    = c1.number_input("Peso (kg)", 0.0, 300.0, 70.0, 0.1)
        altura  = c2.number_input("Altura (cm)", 0.0, 250.0, 170.0, 0.5)
        bf      = c3.number_input("% Gordura", 0.0, 60.0, 0.0, 0.1)
        st.markdown("#### Medidas (cm)")
        c1, c2, c3 = st.columns(3)
        peit    = c1.number_input("Peito", 0.0, 200.0, 0.0, 0.5)
        cint    = c2.number_input("Cintura", 0.0, 200.0, 0.0, 0.5)
        quad    = c3.number_input("Quadril", 0.0, 200.0, 0.0, 0.5)
        c1, c2, c3 = st.columns(3)
        braco_d = c1.number_input("Braço D", 0.0, 100.0, 0.0, 0.5)
        braco_e = c2.number_input("Braço E", 0.0, 100.0, 0.0, 0.5)
        coxa    = c3.number_input("Coxa", 0.0, 100.0, 0.0, 0.5)
        panturrilha = st.number_input("Panturrilha", 0.0, 100.0, 0.0, 0.5)

        bmi = round(peso / ((altura/100)**2), 1) if altura > 0 and peso > 0 else 0
        if bmi > 0:
            cat = "Abaixo do peso" if bmi<18.5 else ("Normal" if bmi<25 else ("Sobrepeso" if bmi<30 else "Obesidade"))
            st.markdown(f'IMC: **<span style="color:#c8ff00;">{bmi}</span>** — {cat}', unsafe_allow_html=True)

        if st.button("💾 Salvar Medidas"):
            try:
                add_measurement({"id": str(uuid.uuid4()), "date": str(med_date),
                    "peso": peso, "altura": altura, "bf": bf, "bmi": bmi,
                    "peito": peit, "cintura": cint, "quadril": quad,
                    "braco_d": braco_d, "braco_e": braco_e, "coxa": coxa, "panturrilha": panturrilha})
                st.success("✅ Salvo!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    with tab2:
        entries = get_measurements()
        if not entries:
            st.info("Nenhuma medição registrada.")
            return

        sorted_e = sorted(entries, key=lambda x: str(x["date"]))
        dates_e   = [str(e["date"])[:10] for e in sorted_e]

        if HAS_PLOTLY and len(entries) > 1:
            chart_tab1, chart_tab2, chart_tab3 = st.tabs(["⚖️ Peso & BF%", "📏 Medidas", "📊 Individual"])

            with chart_tab1:
                fig = go.Figure()
                pesos = [e.get("peso", 0) for e in sorted_e]
                bfs   = [e.get("bf", 0)   for e in sorted_e]
                fig.add_trace(go.Scatter(x=dates_e, y=pesos, name="Peso (kg)",
                    line=dict(color="#c8ff00", width=2), mode="lines+markers", marker=dict(size=6),
                    yaxis="y1"))
                if any(b > 0 for b in bfs):
                    fig.add_trace(go.Scatter(x=dates_e, y=bfs, name="BF%",
                        line=dict(color="#ff4757", width=2, dash="dot"), mode="lines+markers",
                        marker=dict(size=5), yaxis="y2"))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#888", height=300, margin=dict(l=0,r=0,t=10,b=0),
                    legend=dict(orientation="h", y=-0.2),
                    xaxis=dict(gridcolor="#1e1e1e"),
                    yaxis=dict(gridcolor="#1e1e1e", title="kg"),
                    yaxis2=dict(overlaying="y", side="right", title="%", gridcolor="#1e1e1e",
                                showgrid=False, tickfont=dict(color="#ff4757")),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                if pesos:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Peso Inicial", f"{pesos[0]} kg")
                    c2.metric("Peso Atual", f"{pesos[-1]} kg")
                    c3.metric("Variação", f"{pesos[-1]-pesos[0]:+.1f} kg")

            with chart_tab2:
                metrics_circ = {"Peito":"peito","Cintura":"cintura","Quadril":"quadril",
                                "Coxa":"coxa","Braço D":"braco_d","Panturrilha":"panturrilha"}
                colors_circ  = ["#c8ff00","#ff4757","#2ed573","#ffa502","#a29bfe","#fd79a8"]
                fig2 = go.Figure()
                for (label, key), color in zip(metrics_circ.items(), colors_circ):
                    vals = [e.get(key, 0) for e in sorted_e]
                    if any(v > 0 for v in vals):
                        fig2.add_trace(go.Scatter(x=dates_e, y=vals, name=label,
                            line=dict(color=color, width=1.5), mode="lines+markers",
                            marker=dict(size=5)))
                fig2.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#888", height=320, margin=dict(l=0,r=0,t=10,b=0),
                    legend=dict(orientation="h", y=-0.25),
                    xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(gridcolor="#1e1e1e", title="cm"))
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            with chart_tab3:
                all_metrics = {"Peso":"peso","BF%":"bf","IMC":"bmi","Peito":"peito","Cintura":"cintura",
                               "Quadril":"quadril","Coxa":"coxa","Braço D":"braco_d","Panturrilha":"panturrilha"}
                m_pick = st.selectbox("Métrica", list(all_metrics.keys()))
                key_pick = all_metrics[m_pick]
                vals_pick = [e.get(key_pick, 0) for e in sorted_e]
                fig3 = go.Figure()
                fig3.add_trace(go.Scatter(x=dates_e, y=vals_pick, name=m_pick,
                    line=dict(color="#c8ff00", width=2), mode="lines+markers", fill="tozeroy",
                    fillcolor="rgba(200,255,0,.06)", marker=dict(size=7, color="#c8ff00")))
                fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#888", height=260, margin=dict(l=0,r=0,t=10,b=0),
                    xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(gridcolor="#1e1e1e"))
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        st.markdown("#### Histórico de Medições")
        for e in entries[:15]:
            st.markdown(f"""
            <div class="card" style="padding:1rem 1.25rem;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem;">
                <strong>{str(e['date'])[:10]}</strong><span class="badge badge-a">{e.get('peso',0)} kg</span>
              </div>
              <div style="display:flex;flex-wrap:wrap;gap:.4rem;">
                {'<span class="ex-chip">IMC: '+str(e.get("bmi",0))+'</span>' if e.get("bmi") else ""}
                {'<span class="ex-chip">BF: '+str(e.get("bf",0))+'%</span>' if e.get("bf") else ""}
                {'<span class="ex-chip">Cintura: '+str(e.get("cintura",0))+' cm</span>' if e.get("cintura") else ""}
                {'<span class="ex-chip">Peito: '+str(e.get("peito",0))+' cm</span>' if e.get("peito") else ""}
                {'<span class="ex-chip">Coxa: '+str(e.get("coxa",0))+' cm</span>' if e.get("coxa") else ""}
              </div>
            </div>""", unsafe_allow_html=True)


def page_records():
    st.markdown('<div class="pghead"><div class="pgtitle">Recordes Pessoais</div><div class="pgsub">Seus melhores resultados. 🏆</div></div>', unsafe_allow_html=True)

    sessions = get_sessions()
    pr_map = {}
    for s in sessions:
        for ex in (s.get("exercises") or []):
            nm = ex["name"]
            for s2 in (ex.get("sets") or []):
                if s2.get("done") and s2.get("weight",0) > 0:
                    rm1 = s2["weight"] * (1 + s2.get("reps",1)/30)
                    if nm not in pr_map or rm1 > pr_map[nm]["rm1"]:
                        pr_map[nm] = {"weight": s2["weight"], "reps": s2.get("reps",1),
                                      "rm1": round(rm1,1), "date": str(s["date"])[:10]}

    tab1, tab2 = st.tabs(["🏅 PRs Automáticos", "✏️ PR Manual"])

    with tab1:
        if not pr_map:
            st.info("Complete treinos para ver seus PRs automáticos.")
        else:
            all_ex_dict = {e["name"]: e.get("muscle","Outros") for e in all_exercises()}
            by_muscle = {}
            for nm, pr in pr_map.items():
                m = all_ex_dict.get(nm, "Outros")
                by_muscle.setdefault(m, []).append((nm, pr))
            for muscle, items in sorted(by_muscle.items()):
                st.markdown(f"<div style='color:#c8ff00;font-weight:800;font-size:.9rem;text-transform:uppercase;letter-spacing:1px;margin:1.25rem 0 .5rem;'>{muscle}</div>", unsafe_allow_html=True)
                for nm, pr in sorted(items, key=lambda x: x[1]["rm1"], reverse=True):
                    st.markdown(f"""
                    <div class="card" style="padding:1rem 1.25rem;display:flex;justify-content:space-between;align-items:center;">
                      <div><div style="font-weight:700;">{nm}</div><div style="color:#a8a8a8;font-size:.8rem;">{pr['date']}</div></div>
                      <div style="text-align:right;">
                        <div style="font-size:1.3rem;font-weight:900;">{pr['weight']} kg × {pr['reps']}</div>
                        <span class="pr-tag">1RM ~{pr['rm1']} kg</span>
                      </div>
                    </div>""", unsafe_allow_html=True)

    with tab2:
        manual_prs = get_manual_prs()
        c1, c2 = st.columns(2)
        pr_ex   = c1.selectbox("Exercício", ex_names(), key="pr_ex")
        pr_date = c2.date_input("Data", value=date.today(), key="pr_date")
        c1, c2 = st.columns(2)
        pr_w = c1.number_input("Peso (kg)", 0.0, 500.0, 100.0, 2.5)
        pr_r = c2.number_input("Reps", 1, 50, 1)
        if st.button("💾 Salvar PR"):
            try:
                add_manual_pr({"id": str(uuid.uuid4()), "exercise": pr_ex,
                    "date": str(pr_date), "weight": pr_w, "reps": pr_r})
                st.success("✅ PR salvo!")
                st.rerun()
            except Exception as e:
                st.error(str(e))
        for pr in manual_prs[:10]:
            rm = round(pr["weight"] * (1 + pr["reps"]/30), 1)
            st.markdown(f"""
            <div class="card" style="padding:.9rem 1.1rem;display:flex;justify-content:space-between;align-items:center;">
              <div><strong>{pr['exercise']}</strong><div style="color:#a8a8a8;font-size:.8rem;">{str(pr['date'])[:10]}</div></div>
              <div style="text-align:right;"><strong>{pr['weight']} kg × {pr['reps']}</strong><div><span class="pr-tag">~{rm} kg</span></div></div>
            </div>""", unsafe_allow_html=True)


def page_calculators():
    st.markdown('<div class="pghead"><div class="pgtitle">Calculadoras</div><div class="pgsub">Ferramentas para otimizar treino e dieta.</div></div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["💪 1RM", "🔥 TDEE & Macros", "⚖️ IMC", "🏋️ Anilhas"])

    with tab1:
        st.markdown("#### Estimativa de 1 Repetição Máxima")
        c1, c2 = st.columns(2)
        rm_w = c1.number_input("Peso levantado (kg)", 0.0, 500.0, 100.0, 2.5)
        rm_r = c2.number_input("Repetições", 1, 30, 8)
        epley   = rm_w * (1 + rm_r/30)
        brzycki = rm_w * (36/(37-rm_r)) if rm_r < 37 else 0
        mayhew  = (100*rm_w)/(52.2+41.9*math.exp(-0.055*rm_r))
        avg = (epley+brzycki+mayhew)/3
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Epley",   f"{epley:.1f} kg")
        c2.metric("Brzycki", f"{brzycki:.1f} kg")
        c3.metric("Mayhew",  f"{mayhew:.1f} kg")
        c4.metric("Média",   f"{avg:.1f} kg")
        st.markdown("#### Zonas de Treinamento")
        for pct, label in [(100,"1RM"),(95,"2–3 reps"),(90,"4–5 reps"),(85,"6 reps"),
                           (80,"8 reps"),(75,"10 reps"),(70,"12 reps"),(65,"15 reps"),(60,"20 reps")]:
            val = avg*pct/100
            st.markdown(f"""<div class="set-row" style="margin-bottom:.3rem;">
              <span style="color:#c8ff00;font-weight:700;width:3rem;">{pct}%</span>
              <span style="flex:1;color:#888;font-size:.85rem;">{label}</span>
              <strong>{val:.1f} kg</strong></div>""", unsafe_allow_html=True)

    with tab2:
        c1,c2 = st.columns(2)
        td_peso = c1.number_input("Peso (kg)", 30.0, 250.0, 75.0, 0.5, key="td_p")
        td_alt  = c2.number_input("Altura (cm)", 100.0, 250.0, 175.0, 0.5, key="td_a")
        c1,c2 = st.columns(2)
        td_age  = c1.number_input("Idade", 10, 100, 25, key="td_age")
        td_sex  = c2.radio("Sexo", ["Masculino","Feminino"], horizontal=True)
        td_act  = st.selectbox("Nível de Atividade", ["Sedentário","Levemente ativo (1–3x/sem)",
            "Moderadamente ativo (3–5x/sem)","Muito ativo (6–7x/sem)","Extremamente ativo (2x/dia)"])
        goal = st.radio("Objetivo", ["Perder Peso","Manter Peso","Ganhar Massa"], horizontal=True)
        act_mult = [1.2,1.375,1.55,1.725,1.9][["Sedentário","Levemente ativo (1–3x/sem)",
            "Moderadamente ativo (3–5x/sem)","Muito ativo (6–7x/sem)","Extremamente ativo (2x/dia)"].index(td_act)]
        bmr = (88.362+13.397*td_peso+4.799*td_alt-5.677*td_age) if td_sex=="Masculino" else \
              (447.593+9.247*td_peso+3.098*td_alt-4.330*td_age)
        tdee = bmr*act_mult
        adj = -500 if goal=="Perder Peso" else (300 if goal=="Ganhar Massa" else 0)
        target = tdee+adj
        c1,c2,c3 = st.columns(3)
        c1.metric("TMB (Basal)",f"{bmr:.0f} kcal")
        c2.metric("TDEE",       f"{tdee:.0f} kcal")
        c3.metric("Alvo",       f"{target:.0f} kcal")
        prot = td_peso*(2.2 if goal=="Ganhar Massa" else 2.0)
        fat  = target*0.25/9
        carb = max((target-prot*4-fat*9)/4, 0)
        c1,c2,c3 = st.columns(3)
        c1.metric("Proteínas",   f"{prot:.0f}g", f"{prot*4:.0f} kcal")
        c2.metric("Carboidratos",f"{carb:.0f}g",  f"{carb*4:.0f} kcal")
        c3.metric("Gorduras",    f"{fat:.0f}g",   f"{fat*9:.0f} kcal")

    with tab3:
        c1,c2 = st.columns(2)
        bmi_p = c1.number_input("Peso (kg)", 30.0, 250.0, 75.0, 0.5, key="bmi_p")
        bmi_h = c2.number_input("Altura (cm)", 100.0, 250.0, 175.0, 0.5, key="bmi_h")
        bmi_v = bmi_p/(bmi_h/100)**2
        bmi_cat = "Abaixo do peso" if bmi_v<18.5 else ("Normal" if bmi_v<25 else ("Sobrepeso" if bmi_v<30 else "Obesidade"))
        bmi_col = "#2ed573" if 18.5<=bmi_v<25 else ("#ffa502" if bmi_v<30 else "#ff4757")
        st.markdown(f"""<div class="card" style="text-align:center;padding:2rem;">
          <div style="font-size:4rem;font-weight:900;color:{bmi_col};">{bmi_v:.1f}</div>
          <div style="font-size:1.2rem;color:#aaa;margin-top:.5rem;">{bmi_cat}</div></div>""", unsafe_allow_html=True)

    with tab4:
        c1,c2 = st.columns(2)
        bar_w    = c1.selectbox("Barra", [20.0,15.0,10.0,7.5], format_func=lambda x: f"{x} kg")
        target_w = c2.number_input("Peso total (kg)", 0.0, 500.0, 100.0, 2.5)
        remaining = (target_w - bar_w) / 2
        used = []
        for p in [25.0,20.0,15.0,10.0,5.0,2.5,1.25]:
            while remaining >= p-0.001:
                used.append(p); remaining = round(remaining-p, 3)
        if used:
            st.markdown("**Por lado:**")
            for p in used:
                st.markdown(f'<span class="badge badge-a" style="margin:.2rem;font-size:.95rem;">{p} kg</span>', unsafe_allow_html=True)
            total_check = bar_w + sum(used)*2
            if abs(remaining) > 0.01:
                st.warning(f"⚠️ Total aproximado: {total_check} kg")
            else:
                st.success(f"✅ Total: {total_check} kg")
        else:
            st.info("Peso alvo menor que o peso da barra.")


def page_timer():
    st.markdown('<div class="pghead"><div class="pgtitle">Timer de Descanso</div><div class="pgsub">Cronômetro para intervalos entre séries.</div></div>', unsafe_allow_html=True)

    preset = st.radio("Preset", ["30s","45s","1 min","90s","2 min","3 min","5 min"], horizontal=True)
    preset_map = {"30s":30,"45s":45,"1 min":60,"90s":90,"2 min":120,"3 min":180,"5 min":300}
    final_s = st.number_input("Tempo personalizado (s)", 5, 600, preset_map[preset])

    components.html(f"""
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@900&display=swap');
      body{{margin:0;background:transparent;}}
      #wrap{{text-align:center;padding:1rem 0;}}
      #disp{{font-size:clamp(3.5rem,15vw,6rem);font-weight:900;color:#c8ff00;font-family:'Inter',sans-serif;letter-spacing:-3px;line-height:1;transition:color .3s;}}
      #msg{{font-size:.9rem;color:#909090;margin:.5rem 0 1.2rem;letter-spacing:1.5px;text-transform:uppercase;}}
      .btn{{background:linear-gradient(135deg,#c8ff00,#a0cc00);color:#000;border:none;
        border-radius:10px;font-weight:800;font-size:.95rem;padding:.6rem 1.8rem;
        cursor:pointer;margin:.3rem;transition:transform .15s;}}
      .btn-s{{background:#1a1a1a;color:#f0f0f0;border:1px solid #2a2a2a;}}
      .btn:hover{{transform:translateY(-1px);}}
      #prog{{width:100%;height:5px;background:#1a1a1a;border-radius:3px;margin-top:1.2rem;overflow:hidden;}}
      #bar{{height:5px;background:#c8ff00;border-radius:3px;width:100%;transition:width .8s linear,background .3s;}}
    </style>
    <div id="wrap">
      <div id="disp">00:00</div>
      <div id="msg">Pronto para descansar</div>
      <div>
        <button class="btn" onclick="startTimer()">▶ Iniciar</button>
        <button class="btn btn-s" onclick="pauseTimer()">⏸ Pausar</button>
        <button class="btn btn-s" onclick="resetTimer()">↺ Reset</button>
      </div>
      <div id="prog"><div id="bar"></div></div>
    </div>
    <script>
      var total={final_s}, left=total, iv=null, running=false;
      function fmt(s){{var m=Math.floor(s/60),sec=s%60;return String(m).padStart(2,'0')+':'+String(sec).padStart(2,'0');}}
      function update(){{
        document.getElementById('disp').textContent=fmt(left);
        document.getElementById('bar').style.width=((left/total)*100)+'%';
        if(left<=10){{document.getElementById('disp').style.color='#ff4757';document.getElementById('bar').style.background='#ff4757';}}
      }}
      update();
      function startTimer(){{
        if(running)return; running=true;
        document.getElementById('msg').textContent='Descansando...';
        iv=setInterval(function(){{
          if(left<=0){{clearInterval(iv);running=false;
            document.getElementById('msg').textContent='⚡ PRÓXIMA SÉRIE!';
            document.getElementById('disp').textContent='DONE!'; beep(); return;}}
          left--; update();
        }},1000);
      }}
      function pauseTimer(){{clearInterval(iv);running=false;document.getElementById('msg').textContent='Pausado';}}
      function resetTimer(){{
        clearInterval(iv);running=false;left=total;
        document.getElementById('disp').style.color='#c8ff00';
        document.getElementById('bar').style.background='#c8ff00';
        document.getElementById('msg').textContent='Pronto para descansar'; update();
      }}
      function beep(){{try{{
        var ctx=new(window.AudioContext||window.webkitAudioContext)();
        [[880,.15],[660,.35],[880,.55]].forEach(function(p){{
          var o=ctx.createOscillator(),g=ctx.createGain();
          o.connect(g);g.connect(ctx.destination);
          o.frequency.value=p[0];g.gain.value=.25;
          o.start(ctx.currentTime+p[1]);o.stop(ctx.currentTime+p[1]+.18);
        }});
      }}catch(e){{}}}}
    </script>
    """, height=280)


def page_nutrition():
    st.markdown('<div class="pghead"><div class="pgtitle">Nutrição</div><div class="pgsub">Controle calorias e macronutrientes.</div></div>', unsafe_allow_html=True)

    today = str(date.today())
    tab1, tab2, tab3 = st.tabs(["📝 Registrar", "📊 Hoje", "📅 Histórico"])

    with tab1:
        c1,c2 = st.columns(2)
        meal_name = c1.text_input("Alimento / Refeição", placeholder="Frango grelhado, arroz...")
        meal_type = c2.selectbox("Tipo", ["Café da manhã","Lanche da manhã","Almoço","Lanche da tarde","Jantar","Ceia"])
        c1,c2,c3,c4 = st.columns(4)
        kcal = c1.number_input("Kcal", 0, 5000, 300)
        prot = c2.number_input("Proteína (g)", 0.0, 500.0, 30.0, 0.5)
        carb = c3.number_input("Carb (g)", 0.0, 500.0, 30.0, 0.5)
        fat  = c4.number_input("Gordura (g)", 0.0, 200.0, 10.0, 0.5)
        if st.button("➕ Adicionar") and meal_name:
            try:
                add_nutrition({"id": str(uuid.uuid4()), "date": today, "meal": meal_name,
                    "type": meal_type, "kcal": kcal, "prot": prot, "carb": carb, "fat": fat})
                st.success("✅ Registrado!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    with tab2:
        logs = get_nutrition()
        today_logs = [l for l in logs if str(l.get("date",""))[:10] == today]
        if not today_logs:
            st.info("Nenhuma refeição registrada hoje.")
        else:
            tk = sum(l["kcal"] for l in today_logs)
            tp = sum(l["prot"] for l in today_logs)
            tc = sum(l["carb"] for l in today_logs)
            tf = sum(l["fat"]  for l in today_logs)
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Calorias",     f"{tk} kcal")
            c2.metric("Proteínas",    f"{tp:.1f}g")
            c3.metric("Carboidratos", f"{tc:.1f}g")
            c4.metric("Gorduras",     f"{tf:.1f}g")
            if HAS_PLOTLY:
                fig = go.Figure(go.Pie(labels=["Proteínas","Carboidratos","Gorduras"],
                    values=[tp*4,tc*4,tf*9], marker_colors=["#c8ff00","#2ed573","#ff4757"], hole=.55))
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#888",
                    height=200, margin=dict(l=0,r=0,t=0,b=0), showlegend=True,
                    legend=dict(orientation="h", y=-0.15))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            for l in today_logs:
                c1,c2 = st.columns([4,1])
                c1.markdown(f"""<div class="card" style="padding:.85rem 1.1rem;">
                  <div style="display:flex;justify-content:space-between;">
                    <div><strong>{l['meal']}</strong> <span class="ex-chip">{l['type']}</span></div>
                    <span class="badge badge-a">{l['kcal']} kcal</span>
                  </div>
                  <div style="font-size:.8rem;color:#a8a8a8;margin-top:.3rem;">P:{l['prot']}g · C:{l['carb']}g · G:{l['fat']}g</div>
                </div>""", unsafe_allow_html=True)
                if c2.button("🗑️", key=f"del_n_{l['id']}", type="secondary"):
                    delete_nutrition(l["id"]); st.rerun()

    with tab3:
        logs = get_nutrition()
        if not logs:
            st.info("Nenhum registro.")
        elif HAS_PLOTLY:
            from collections import defaultdict
            by_date = defaultdict(lambda: {"kcal":0})
            for l in logs:
                by_date[str(l["date"])[:10]]["kcal"] += l["kcal"]
            dates = sorted(by_date.keys())
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=dates, y=[by_date[d]["kcal"] for d in dates],
                name="Kcal", line=dict(color="#c8ff00",width=2), mode="lines+markers"))
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_color="#888", height=250, margin=dict(l=0,r=0,t=10,b=0),
                xaxis=dict(gridcolor="#1e1e1e"), yaxis=dict(gridcolor="#1e1e1e",title="kcal"))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


def page_goals():
    st.markdown('<div class="pghead"><div class="pgtitle">Metas</div><div class="pgsub">Defina objetivos e acompanhe seu progresso.</div></div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🎯 Minhas Metas", "➕ Nova Meta"])

    with tab1:
        goals = get_goals()
        if not goals:
            st.markdown('<div class="card" style="text-align:center;color:#909090;padding:3rem;">Nenhuma meta definida ainda.</div>', unsafe_allow_html=True)
        for g in goals:
            pct = min(100, int((g.get("current",0)/g["target"])*100)) if g["target"]>0 else 0
            badge_cls = "badge-g" if pct>=100 else ("badge-y" if pct>=50 else "badge-r")
            status = "✅ Concluída!" if pct>=100 else f"{pct}%"
            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:.75rem;">
                <div>
                  <div style="font-weight:700;">{g['name']}</div>
                  <div style="color:#a8a8a8;font-size:.8rem;">{g.get('type','')} · Prazo: {str(g.get('deadline','—'))[:10]}</div>
                </div>
                <span class="badge {badge_cls}">{status}</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:.85rem;color:#888;margin-bottom:.4rem;">
                <span>Atual: <strong style="color:#f0f0f0;">{g.get('current',0)} {g.get('unit','')}</strong></span>
                <span>Meta: <strong style="color:#c8ff00;">{g['target']} {g.get('unit','')}</strong></span>
              </div>
            </div>""", unsafe_allow_html=True)
            st.progress(pct/100)
            c1, c2, c3 = st.columns([2,1,1])
            new_cur = c1.number_input(f"Atualizar ({g.get('unit','')})", value=float(g.get("current",0)), key=f"gc_{g['id']}")
            if c2.button("Atualizar", key=f"gup_{g['id']}"):
                try:
                    update_goal_current(g["id"], new_cur)
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
            if c3.button("🗑️ Remover", key=f"gdel_{g['id']}", type="secondary"):
                delete_goal(g["id"]); st.rerun()

    with tab2:
        goal_name = st.text_input("Nome da Meta", placeholder="Ex: Supinar 100kg, Perder 5kg...")
        c1,c2 = st.columns(2)
        goal_type = c1.selectbox("Tipo", ["Força (1RM)","Peso Corporal","Medidas","Frequência","Outro"])
        goal_unit = c2.text_input("Unidade", placeholder="kg, cm, treinos/sem...")
        c1,c2,c3 = st.columns(3)
        goal_current  = c1.number_input("Valor Atual",  0.0, 9999.0, 0.0)
        goal_target   = c2.number_input("Valor Alvo",   0.0, 9999.0, 100.0)
        goal_deadline = c3.date_input("Prazo", value=date.today()+timedelta(days=90))
        goal_notes = st.text_area("Motivação", placeholder="Por que esta meta é importante?", height=80)
        if st.button("🎯 Salvar Meta") and goal_name:
            try:
                add_goal({"id": str(uuid.uuid4()), "name": goal_name, "type": goal_type,
                    "unit": goal_unit, "current": goal_current, "target": goal_target,
                    "deadline": str(goal_deadline), "notes": goal_notes})
                st.success("✅ Meta criada!")
                st.rerun()
            except Exception as e:
                st.error(str(e))


# ── ROUTER ────────────────────────────────────────────────────────────────────
{
    "dashboard":    page_dashboard,
    "agents":       render_agents_page,
    "workout":      page_workout,
    "plans":        page_plans,
    "exercises":    page_exercises,
    "history":      page_history,
    "progress":     page_progress,
    "measurements": page_measurements,
    "records":      page_records,
    "calculators":  page_calculators,
    "timer":        page_timer,
    "nutrition":    page_nutrition,
    "goals":        page_goals,
}.get(st.session_state.page, page_dashboard)()
