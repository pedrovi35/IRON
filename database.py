import os
from dotenv import load_dotenv
from supabase import create_client, Client
import streamlit as st

load_dotenv()

@st.cache_resource
def get_sb() -> Client:
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL e SUPABASE_KEY não configurados no .env")
    return create_client(url, key)

def _db():
    return get_sb()

def _clear():
    """Invalida todos os caches de leitura após uma escrita."""
    get_plans.clear()
    get_sessions.clear()
    get_measurements.clear()
    get_goals.clear()
    get_nutrition.clear()
    get_manual_prs.clear()
    get_custom_exercises.clear()

# ── PLANS ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_plans():
    return _db().table("plans").select("*").order("created_at").execute().data

def add_plan(plan: dict):
    _db().table("plans").insert(plan).execute()
    get_plans.clear()

def delete_plan(plan_id: str):
    _db().table("plans").delete().eq("id", plan_id).execute()
    get_plans.clear()

def update_plan(plan_id: str, plan: dict):
    _db().table("plans").update(plan).eq("id", plan_id).execute()
    get_plans.clear()

# ── SESSIONS (histórico) ──────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_sessions():
    return _db().table("sessions").select("*").order("date", desc=True).execute().data

def add_session(session: dict):
    _db().table("sessions").insert(session).execute()
    get_sessions.clear()

def delete_session(session_id: str):
    _db().table("sessions").delete().eq("id", session_id).execute()
    get_sessions.clear()

# ── MEASUREMENTS ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_measurements():
    return _db().table("measurements").select("*").order("date", desc=True).execute().data

def add_measurement(m: dict):
    _db().table("measurements").insert(m).execute()
    get_measurements.clear()

# ── GOALS ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_goals():
    return _db().table("goals").select("*").order("created_at").execute().data

def add_goal(g: dict):
    _db().table("goals").insert(g).execute()
    get_goals.clear()

def update_goal_current(goal_id: str, current: float):
    _db().table("goals").update({"current": current}).eq("id", goal_id).execute()
    get_goals.clear()

def delete_goal(goal_id: str):
    _db().table("goals").delete().eq("id", goal_id).execute()
    get_goals.clear()

# ── NUTRITION ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_nutrition():
    return _db().table("nutrition_logs").select("*").order("created_at", desc=True).execute().data

def add_nutrition(log: dict):
    _db().table("nutrition_logs").insert(log).execute()
    get_nutrition.clear()

def delete_nutrition(log_id: str):
    _db().table("nutrition_logs").delete().eq("id", log_id).execute()
    get_nutrition.clear()

# ── MANUAL PRs ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_manual_prs():
    return _db().table("manual_prs").select("*").order("date", desc=True).execute().data

def add_manual_pr(pr: dict):
    _db().table("manual_prs").insert(pr).execute()
    get_manual_prs.clear()

# ── CUSTOM EXERCISES ──────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def get_custom_exercises():
    return _db().table("custom_exercises").select("*").order("name").execute().data

def add_custom_exercise(ex: dict):
    _db().table("custom_exercises").insert(ex).execute()
    get_custom_exercises.clear()

def delete_custom_exercise(ex_id: str):
    _db().table("custom_exercises").delete().eq("id", ex_id).execute()
    get_custom_exercises.clear()
