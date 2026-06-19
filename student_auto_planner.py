from __future__ import annotations

import calendar
import datetime as dt
import hashlib
import html
import json
import re
import urllib.parse
from dataclasses import asdict, dataclass

import pandas as pd
import streamlit as st

try:
    from supabase import create_client
except ImportError:  # guest mode still works without auth installed
    create_client = None


st.set_page_config(page_title="Auto-Planner", page_icon="AP", layout="wide")

TODAY = dt.date.today()
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
TODAY_IDX = TODAY.weekday()
DAY_START, DAY_END = 8.0, 22.0
FOCUS_BLOCK = 1.5
BREAK = 0.25
HORIZON_DAYS = 30
CALENDAR_MONTHS = 12

BRAND = "#01696f"
ACCENT = "#4157c8"
SURFACE = "#f7f6f2"
SECONDARY = "#edeae5"
TEXT = "#28251d"
DANGER = "#d94b4b"
AMBER = "#b7791f"
SUCCESS = "#2f855a"
FIXED_DOT = "#5b5563"
COLORS = [BRAND, ACCENT, AMBER, DANGER, "#7c5cff", SUCCESS]
KIND_COLORS = {"class": BRAND, "work": TEXT, "club": "#7c5cff", "meal": SUCCESS}
KIND_LABELS = {"class": "Class", "work": "Work", "club": "Club", "meal": "Meal"}
STATUSES = ["Not Started", "In Progress", "Done"]
PAGES = ["Dashboard", "Schedule", "Calendar", "Calendar Sync", "Assignments", "Import", "Study Plan", "Reminders", "Progress", "Account"]
DEFAULT_MEALS = [(8.0, 8.5, "Breakfast"), (12.0, 13.0, "Lunch"), (18.0, 19.0, "Dinner")]


@dataclass
class Fixed:
    day: str
    start: float
    end: float
    title: str
    kind: str


@dataclass
class Assignment:
    id: int
    title: str
    course: str
    due: dt.date
    hours: float
    diff: int
    color: str
    weight: int = 3
    status: str = "Not Started"
    source: str = ""
    external_id: str = ""


@dataclass
class Task:
    id: int
    assign_id: int
    title: str
    course: str
    color: str
    hours: float
    due: dt.date
    order: int
    done: bool = False


@dataclass
class Block:
    day: str
    start: float
    end: float
    title: str
    course: str
    color: str
    task_id: int
    date: dt.date


def inject_ui() -> None:
    st.html(
        """
        <script>
        const head = window.parent.document.head;
        function meta(name, content) {
          let el = head.querySelector(`meta[name="${name}"]`);
          if (!el) { el = window.parent.document.createElement("meta"); el.setAttribute("name", name); head.appendChild(el); }
          el.setAttribute("content", content);
        }
        function link(rel, href, attrs = {}) {
          let el = head.querySelector(`link[rel="${rel}"]`);
          if (!el) { el = window.parent.document.createElement("link"); el.setAttribute("rel", rel); head.appendChild(el); }
          el.setAttribute("href", href);
          Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
        }
        meta("theme-color", "#01696f");
        meta("mobile-web-app-capable", "yes");
        meta("apple-mobile-web-app-capable", "yes");
        meta("apple-mobile-web-app-title", "Auto-Planner");
        meta("apple-mobile-web-app-status-bar-style", "default");
        link("manifest", "/app/static/manifest.webmanifest");
        link("icon", "/app/static/icon-192.png", {type: "image/png"});
        link("apple-touch-icon", "/app/static/icon-180.png");
        </script>
        """,
        unsafe_allow_javascript=True,
    )
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"], .stApp {font-family:"Inter", system-ui, -apple-system, "Segoe UI", sans-serif;}
        .stApp {background:#f7f6f2;color:#28251d;}
        .block-container {padding-top:1.15rem; max-width:1080px;}
        h1,h2,h3 {letter-spacing:0;font-weight:800;color:#28251d;}
        .hero {background:linear-gradient(145deg,#01696f,#4157c8);color:white;border-radius:14px;padding:20px;margin-bottom:14px;box-shadow:0 12px 28px rgba(1,105,111,.22);}
        .hero .k {font-size:13px;font-weight:700;opacity:.88;text-transform:uppercase;}
        .hero .b {font-size:30px;font-weight:800;line-height:1.05;margin:4px 0;}
        .hero .s {font-size:13px;opacity:.94;}
        .card {background:white;border:1px solid rgba(40,37,29,.08);border-radius:12px;padding:16px 18px;margin:10px 0;box-shadow:0 6px 18px rgba(40,37,29,.07);}
        .pill {display:inline-block;border-radius:999px;padding:4px 10px;font-size:11px;font-weight:800;line-height:1.1;white-space:nowrap;}
        .hi {background:#fde8e8;color:#d94b4b;} .med {background:#fff4db;color:#b7791f;} .lo {background:#e7f4ee;color:#2f855a;}
        .status-not {background:#eeeae2;color:#655f51;} .status-progress {background:#e4eef8;color:#01696f;} .status-done {background:#e7f4ee;color:#2f855a;}
        .muted {color:#5f5a4d;} .faint {color:#837d70;font-size:12px;}
        .danger-banner {background:#fff1f1;border:1px solid rgba(217,75,75,.32);border-left:6px solid #d94b4b;border-radius:12px;padding:14px 16px;margin:12px 0;box-shadow:0 6px 18px rgba(217,75,75,.08);}
        .empty-note {background:#fbfaf7;border:1px dashed rgba(40,37,29,.18);border-radius:12px;padding:16px;margin:10px 0;color:#5f5a4d;}
        .study-card {background:white;border:1px solid rgba(40,37,29,.08);border-radius:12px;padding:12px 14px;margin:0 0 8px;box-shadow:0 5px 14px rgba(40,37,29,.06);}
        .study-card.done {text-decoration:line-through;opacity:.58;}
        .study-title {border-left:4px solid var(--task-color,#01696f);padding-left:8px;font-weight:800;color:#28251d;}
        .study-meta {display:flex;gap:6px;align-items:center;flex-wrap:wrap;margin-top:6px;}
        .study-links {display:flex;gap:8px;flex-wrap:wrap;margin-top:8px;}
        .study-links a {font-size:12px;font-weight:800;color:#01696f;text-decoration:none;background:#e7f4ee;border:1px solid rgba(1,105,111,.14);border-radius:999px;padding:6px 10px;}
        .assignment-links {display:flex;gap:8px;flex-wrap:wrap;margin-top:10px;}
        .assignment-links a {font-size:12px;font-weight:800;color:#4157c8;text-decoration:none;background:#e4eef8;border:1px solid rgba(65,87,200,.14);border-radius:999px;padding:6px 10px;}
        .assignment-card {background:white;border:1px solid rgba(40,37,29,.08);border-radius:12px;padding:14px 16px;margin:10px 0;box-shadow:0 6px 18px rgba(40,37,29,.07);}
        .assignment-head {display:flex;justify-content:space-between;gap:10px;align-items:flex-start;}
        .assignment-title {font-weight:800;color:#28251d;line-height:1.25;}
        .assignment-badges {display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end;}
        .mini-progress {height:7px;background:#eeeae2;border-radius:999px;overflow:hidden;margin-top:10px;}
        .mini-progress span {display:block;height:100%;background:linear-gradient(90deg,#01696f,#4157c8);border-radius:999px;}
        .page-head {background:linear-gradient(145deg,#ffffff,#fbfaf7);border:1px solid rgba(40,37,29,.08);border-left:5px solid #01696f;border-radius:12px;padding:14px 16px;margin:2px 0 14px;box-shadow:0 5px 16px rgba(40,37,29,.05);}
        .page-head .eyebrow {font-size:11px;font-weight:800;color:#01696f;text-transform:uppercase;letter-spacing:.02em;}
        .page-head .title {font-size:24px;font-weight:800;line-height:1.1;color:#28251d;margin-top:2px;}
        .page-head .sub {font-size:13px;color:#5f5a4d;margin-top:4px;}
        .quick-nav {display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;margin:8px 0 16px;}
        .quick-nav a {background:white;border:1px solid rgba(40,37,29,.08);border-radius:12px;min-height:52px;padding:8px 6px;text-align:center;box-shadow:0 4px 12px rgba(40,37,29,.05);text-decoration:none;color:#28251d;display:flex;flex-direction:column;align-items:center;justify-content:center;}
        .quick-nav a.active {background:#e7f4ee;border-color:rgba(1,105,111,.28);box-shadow:0 6px 18px rgba(1,105,111,.10);}
        .quick-nav .nav-icon {width:22px;height:22px;border-radius:8px;display:grid;place-items:center;background:#f4f1ea;color:#01696f;font-size:12px;font-weight:900;margin-bottom:3px;}
        .quick-nav a.active .nav-icon {background:#01696f;color:white;}
        .quick-nav b {display:block;font-size:12px;color:#28251d;line-height:1.05;}
        .stat-grid {display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:12px 0;}
        .stat-card {background:white;border:1px solid rgba(40,37,29,.08);border-radius:12px;padding:12px;box-shadow:0 4px 12px rgba(40,37,29,.05);}
        .stat-card b {font-size:20px;color:#28251d;}
        .stat-card span {display:block;font-size:12px;color:#837d70;margin-top:2px;}
        .stButton>button, .stDownloadButton>button, .stForm button, [role="tab"] {min-height:44px;border-radius:10px;}
        input, textarea, select {font-size:16px !important;}
        .stProgress > div > div > div {background:#01696f;}
        /* compact month calendar that fits any width (incl. phones) */
        table.cal {width:100%;border-collapse:separate;border-spacing:4px;table-layout:fixed;margin:8px 0 6px;}
        table.cal th {font-size:11px;color:#837d70;font-weight:800;padding:3px 0;text-align:center;}
        table.cal td {height:46px;vertical-align:top;text-align:center;padding:0;border-radius:9px;background:#ffffff;border:1px solid rgba(40,37,29,.08);box-shadow:0 2px 8px rgba(40,37,29,.04);}
        table.cal td.empty {background:transparent;border-color:transparent;box-shadow:none;}
        table.cal td.today {background:#e7f4ee;}
        table.cal td.sel {outline:2px solid #01696f;outline-offset:-2px;}
        table.cal a.day-link {display:block;min-height:46px;padding:5px 2px;text-decoration:none;color:#28251d;border-radius:9px;}
        table.cal .dnum {font-size:12px;font-weight:800;line-height:1.1;}
        table.cal .dots {display:flex;flex-wrap:wrap;gap:2px;justify-content:center;margin-top:4px;min-height:8px;}
        table.cal .dot {width:6px;height:6px;border-radius:50%;display:inline-block;}
        .section-title {display:flex;align-items:center;gap:10px;margin:16px 0 8px;}
        .section-title .icon {width:28px;height:28px;border-radius:9px;display:grid;place-items:center;background:#e7f4ee;color:#01696f;font-weight:900;}
        .section-title b {font-size:18px;}
        div[data-testid="stHorizontalBlock"]:has(button[kind]) {gap:5px;}
        .selected-day-note {background:linear-gradient(145deg,#ffffff,#f5fbf9);border:1px solid rgba(1,105,111,.16);border-left:5px solid #01696f;border-radius:12px;padding:12px 14px;margin:8px 0 12px;box-shadow:0 6px 18px rgba(1,105,111,.08);}
        @media (max-width: 700px) {
          .block-container {padding-left:.6rem;padding-right:.6rem;padding-top:.8rem;}
          .hero {padding:16px;border-radius:12px;}
          .hero .b {font-size:24px;}
          .card {padding:13px 14px;}
          .study-card {padding:11px 12px;}
          .assignment-card {padding:13px 14px;}
          .assignment-head {display:block;}
          .assignment-badges {justify-content:flex-start;margin-top:8px;}
          .page-head {padding:13px 14px;margin-bottom:12px;}
          .page-head .title {font-size:21px;}
          .quick-nav {grid-template-columns:repeat(3,minmax(0,1fr));gap:7px;}
          .quick-nav a {min-height:48px;border-radius:11px;padding:7px 5px;}
          .stat-grid {grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;}
          table.cal {border-spacing:3px;}
          table.cal td {height:39px;border-radius:8px;}
          table.cal a.day-link {min-height:39px;padding:4px 1px;}
          table.cal .dnum {font-size:11px;}
          table.cal .dot {width:5px;height:5px;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_ui()


def fmt_time(h: float) -> str:
    hr = int(h)
    minute = round((h - hr) * 60)
    ap = "PM" if hr >= 12 else "AM"
    h12 = ((hr + 11) % 12) + 1
    return f"{h12}:{minute:02d} {ap}" if minute else f"{h12} {ap}"


def _d(days: int) -> dt.date:
    return TODAY + dt.timedelta(days=days)


def secret(name: str) -> str:
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def supabase_credentials() -> tuple[str, str]:
    return secret("SUPABASE_URL"), secret("SUPABASE_ANON_KEY")


def supabase_ready() -> bool:
    url, key = supabase_credentials()
    return bool(create_client and url and key)


def get_sb():
    if create_client is None:
        raise RuntimeError("Supabase package is not installed.")
    if "sb" not in st.session_state:
        url, key = supabase_credentials()
        if not url or not key:
            raise RuntimeError("Supabase secrets are not configured.")
        st.session_state.sb = create_client(url, key)
    token = st.session_state.get("auth", {}).get("access_token")
    if token and hasattr(st.session_state.sb, "postgrest"):
        auth = getattr(st.session_state.sb.postgrest, "auth", None)
        if callable(auth):
            auth(token)
    return st.session_state.sb


def obj_get(obj, name: str):
    return obj.get(name) if isinstance(obj, dict) else getattr(obj, name, None)


def store_auth_response(response, fallback_email: str) -> bool:
    session = obj_get(response, "session")
    user = obj_get(response, "user") or obj_get(session, "user")
    token = obj_get(session, "access_token")
    uid = obj_get(user, "id")
    if not uid or not token:
        return False
    st.session_state.auth = {
        "id": uid,
        "email": obj_get(user, "email") or fallback_email,
        "access_token": token,
        "refresh_token": obj_get(session, "refresh_token"),
    }
    st.session_state.guest = False
    st.session_state._loaded_uid = None
    st.session_state._last_saved = None
    return True


# --- Stay signed in across a browser refresh: remember the refresh token in a
#     cookie and restore the Supabase session on load. All guarded so a failure
#     just falls back to the normal login screen; guests are never affected. ---
try:
    import extra_streamlit_components as stx
except Exception:  # pragma: no cover - component optional
    stx = None

AUTH_COOKIE = "ap_refresh"


def _cookies():
    if stx is None:
        return None
    if "cookie_mgr" not in st.session_state:
        try:
            st.session_state.cookie_mgr = stx.CookieManager(key="ap_cookies")
        except Exception:
            st.session_state.cookie_mgr = None
    return st.session_state.cookie_mgr


def remember_session() -> None:
    cm = _cookies()
    token = (st.session_state.get("auth") or {}).get("refresh_token")
    if not cm or not token:
        return
    try:
        cm.set(AUTH_COOKIE, token,
               expires_at=dt.datetime.now() + dt.timedelta(days=30), key="ap_cookie_set")
    except Exception:
        pass


def forget_session() -> None:
    cm = _cookies()
    if not cm:
        return
    try:
        cm.delete(AUTH_COOKIE, key="ap_cookie_del")
    except Exception:
        pass


def try_restore_session() -> None:
    if st.session_state.get("auth") or st.session_state.get("guest") or not supabase_ready():
        return
    cm = _cookies()
    if not cm:
        return
    try:
        token = cm.get(AUTH_COOKIE)
    except Exception:
        token = None
    if not token:
        return
    try:
        if store_auth_response(get_sb().auth.refresh_session(token), ""):
            remember_session()
            st.rerun()
        else:
            forget_session()
    except Exception:
        forget_session()


def sign_in(email: str, password: str) -> bool:
    return store_auth_response(get_sb().auth.sign_in_with_password({"email": email.strip(), "password": password}), email)


def sign_up(email: str, password: str) -> bool:
    return store_auth_response(get_sb().auth.sign_up({"email": email.strip(), "password": password}), email)


def sign_out() -> None:
    forget_session()
    try:
        if "sb" in st.session_state:
            st.session_state.sb.auth.sign_out()
    except Exception:
        pass
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def send_password_reset(email: str) -> None:
    get_sb().auth.reset_password_for_email(email.strip())


def update_account(email: str | None = None, password: str | None = None) -> None:
    attrs = {}
    if email:
        attrs["email"] = email.strip()
    if password:
        attrs["password"] = password
    if attrs:
        get_sb().auth.update_user(attrs)


def load_user_data(uid: str) -> dict | None:
    response = get_sb().table("planners").select("data").eq("user_id", uid).limit(1).execute()
    rows = obj_get(response, "data") or []
    return rows[0].get("data") if rows else None


def save_user_data(uid: str) -> None:
    data = snapshot()
    if st.session_state.get("backup"):
        data["_backup"] = st.session_state.backup
    payload = {"user_id": uid, "data": data, "updated_at": dt.datetime.now(dt.timezone.utc).isoformat()}
    get_sb().table("planners").upsert(payload, on_conflict="user_id").execute()


TYPE_DEFAULTS = {
    "final": (5, 10.0, 3),
    "exam": (5, 8.0, 3),
    "project": (4, 6.0, 3),
    "paper": (4, 6.0, 3),
    "quiz": (2, 1.5, 1),
    "homework": (2, 2.0, 2),
    "other": (3, 3.0, 2),
}


def detect_type(title: str, course: str = "") -> str:
    text = f"{title} {course}".lower()
    if "final" in text:
        return "final"
    if any(k in text for k in ("midterm", "exam", "test")):
        return "exam"
    if "quiz" in text:
        return "quiz"
    if any(k in text for k in ("project", "build", "app")):
        return "project"
    if any(k in text for k in ("paper", "essay", "research")):
        return "paper"
    if any(k in text for k in ("homework", "assignment", "problem set", "pset", "reading", "hw")):
        return "homework"
    return "other"


STAGES = {
    "exam": ["Review key chapters", "Work practice problems", "Make a summary sheet", "Final review"],
    "paper": ["Research and outline", "Draft introduction", "Write body sections", "Revise and cite", "Final proofread"],
    "project": ["Plan and set up", "Build core logic", "Add features", "Test and debug", "Polish and submit"],
    "pset": ["Attempt first half", "Finish remaining", "Check and review"],
    "quiz": ["Review notes", "Practice questions"],
    "generic": ["Get started", "Make progress", "Review", "Finish and submit"],
}


def priority_score(a: Assignment) -> int:
    days_left = max(0, (a.due - TODAY).days)
    urgency = max(0.0, min(1.0, (21 - days_left) / 21))
    raw = 0.40 * (a.weight / 5) + 0.38 * urgency + 0.14 * (a.diff / 3) + 0.08 * min(1, a.hours / 10)
    return round(raw * 100)


def pri_label(score: int) -> tuple[str, str]:
    if score >= 66:
        return "hi", "High"
    if score >= 40:
        return "med", "Medium"
    return "lo", "Low"


def breakdown(a: Assignment) -> list[Task]:
    group = {"final": "exam", "exam": "exam", "paper": "paper", "project": "project", "quiz": "quiz", "homework": "pset"}.get(detect_type(a.title, a.course), "generic")
    stages = STAGES[group]
    n = max(2, min(len(stages), int((a.hours + 1.49) // 1.5)))
    per = round(a.hours / n, 1)
    return [Task(a.id * 100 + i, a.id, stages[min(i, len(stages) - 1)], a.course, a.color, per, a.due, i) for i in range(n)]


def meal_windows() -> list[tuple[float, float]]:
    return [(s, e) for s, e, _ in st.session_state.get("meals", DEFAULT_MEALS)] if st.session_state.get("meals_on", True) else []


def free_slots() -> dict[str, list[tuple[float, float]]]:
    slots = {}
    for day in DAYS:
        busy = sorted([(f.start, f.end) for f in st.session_state.fixed if f.day == day] + meal_windows())
        open_slots, cursor = [], DAY_START
        for start, end in busy:
            if start - cursor >= 1:
                open_slots.append((cursor, start))
            cursor = max(cursor, end)
        if DAY_END - cursor >= 1:
            open_slots.append((cursor, DAY_END))
        slots[day] = open_slots
    return slots


def generate_plan() -> None:
    done_ids = {int(x) for x in st.session_state.get("task_done_ids", [])}
    done_ids.update(t.id for t in st.session_state.get("tasks", []) if t.done)
    tasks = []
    for a in st.session_state.assignments:
        for t in breakdown(a):
            t.done = t.id in done_ids or getattr(a, "status", "") == "Done"
            tasks.append(t)
    score = {a.id: priority_score(a) for a in st.session_state.assignments}
    tasks.sort(key=lambda t: (-score.get(t.assign_id, 0), t.order))
    slots = free_slots()
    used: dict[tuple[int, float], float] = {}
    blocks, unscheduled = [], []
    for t in [x for x in tasks if not x.done]:
        due_off = (t.due - TODAY).days
        placed = False
        for off in range(HORIZON_DAYS):
            if due_off >= 0 and off > due_off:
                break
            day = DAYS[(TODAY_IDX + off) % 7]
            date = TODAY + dt.timedelta(days=off)
            for start, end in slots.get(day, []):
                key = (off, start)
                consumed = used.get(key, 0)
                gap = BREAK if consumed else 0
                s = start + consumed + gap
                length = min(t.hours, FOCUS_BLOCK, end - s)
                if length >= 1:
                    blocks.append(Block(day, s, s + length, t.title, t.course, t.color, t.id, date))
                    used[key] = consumed + gap + length
                    placed = True
                    break
            if placed:
                break
        if not placed:
            unscheduled.append(t)
    st.session_state.tasks = tasks
    st.session_state.blocks = blocks
    st.session_state.unscheduled = unscheduled
    st.session_state.task_done_ids = sorted(t.id for t in tasks if t.done)


def seed_state() -> None:
    st.session_state.user = "Student"
    st.session_state.streak = 3
    st.session_state.history = [1, 2, 0, 3, 1.5, 2.5, 0]
    st.session_state.next_id = 100
    st.session_state.meals_on = True
    st.session_state.meals = list(DEFAULT_MEALS)
    st.session_state.fixed = [
        Fixed("Mon", 9, 10.5, "CS 201 Lecture", "class"),
        Fixed("Tue", 11, 12.5, "Psychology Lecture", "class"),
        Fixed("Wed", 13, 14.5, "Math Lecture", "class"),
        Fixed("Thu", 15, 18, "Work shift", "work"),
        Fixed("Fri", 9, 10.5, "CS 201 Lecture", "class"),
    ]
    st.session_state.assignments = [
        Assignment(1, "Psychology Research Paper", "PSY 201", _d(4), 8, 3, COLORS[3], 4),
        Assignment(2, "Calculus Problem Set", "MATH 240", _d(1), 3, 2, COLORS[2], 2),
        Assignment(3, "CS Project", "CS 201", _d(6), 6, 3, COLORS[0], 4),
    ]
    st.session_state.task_done_ids = []
    st.session_state.feed_sources = []
    st.session_state.feed_auto_refresh = True
    generate_plan()


def snapshot() -> dict:
    return {
        "user": st.session_state.user,
        "streak": st.session_state.streak,
        "history": st.session_state.history,
        "next_id": st.session_state.next_id,
        "meals_on": st.session_state.meals_on,
        "meals": st.session_state.meals,
        "fixed": [asdict(f) for f in st.session_state.fixed],
        "assignments": [{**asdict(a), "due": a.due.isoformat()} for a in st.session_state.assignments],
        "task_done_ids": st.session_state.get("task_done_ids", []),
        "feed_sources": st.session_state.get("feed_sources", []),
        "feed_auto_refresh": st.session_state.get("feed_auto_refresh", True),
    }


def restore_snapshot(snap: dict) -> None:
    st.session_state.user = snap.get("user", "Student")
    st.session_state.streak = snap.get("streak", 0)
    st.session_state.history = snap.get("history", [0] * 7)
    st.session_state.next_id = snap.get("next_id", 100)
    st.session_state.meals_on = snap.get("meals_on", True)
    st.session_state.meals = [tuple(m) for m in snap.get("meals", DEFAULT_MEALS)]
    st.session_state.fixed = [Fixed(**f) for f in snap.get("fixed", [])]
    st.session_state.assignments = []
    allowed = set(Assignment.__dataclass_fields__)
    for raw in snap.get("assignments", []):
        data = {k: v for k, v in raw.items() if k in allowed}
        data["due"] = dt.date.fromisoformat(raw["due"])
        data.setdefault("status", "Not Started")
        st.session_state.assignments.append(Assignment(**data))
    st.session_state.task_done_ids = [int(x) for x in snap.get("task_done_ids", [])]
    st.session_state.feed_sources = snap.get("feed_sources", [])
    st.session_state.feed_auto_refresh = snap.get("feed_auto_refresh", True)
    generate_plan()


def push_undo(label: str) -> None:
    st.session_state.undo_snapshot = snapshot()
    st.session_state.undo_label = label


def undo_last_change() -> bool:
    snap = st.session_state.get("undo_snapshot")
    if not snap:
        return False
    now = snapshot()
    restore_snapshot(snap)
    st.session_state.undo_snapshot = now
    st.session_state.undo_label = "last change"
    return True


def set_task_done(task: Task, done: bool) -> None:
    task.done = done
    st.session_state.task_done_ids = sorted(t.id for t in st.session_state.tasks if t.done)


def assignment_tasks(aid: int) -> list[Task]:
    return [t for t in st.session_state.tasks if t.assign_id == aid]


def assignment_status(a: Assignment) -> str:
    tasks = assignment_tasks(a.id)
    if tasks and all(t.done for t in tasks):
        return "Done"
    if tasks and any(t.done for t in tasks) and a.status == "Not Started":
        return "In Progress"
    return a.status if a.status in STATUSES else "Not Started"


def status_class(status: str) -> str:
    return {"Done": "status-done", "In Progress": "status-progress", "Not Started": "status-not"}.get(status, "status-not")


def set_assignment_status(a: Assignment, status: str) -> None:
    a.status = status
    for t in assignment_tasks(a.id):
        if status == "Done":
            t.done = True
        elif status == "Not Started":
            t.done = False
    st.session_state.task_done_ids = sorted(t.id for t in st.session_state.tasks if t.done)


def compute_streak() -> int:
    hist = st.session_state.get("history", [])
    idx = len(hist) - 1
    if idx >= 0 and hist[idx] == 0:
        idx -= 1
    count = 0
    while idx >= 0 and hist[idx] > 0:
        count += 1
        idx -= 1
    return count


def unscheduled_titles() -> list[str]:
    ids = {t.assign_id for t in st.session_state.get("unscheduled", [])}
    return [a.title for a in st.session_state.assignments if a.id in ids]


def add_months(base: dt.date, months: int) -> dt.date:
    idx = base.month - 1 + months
    return dt.date(base.year + idx // 12, idx % 12 + 1, 1)


def month_offset_for(day: dt.date) -> int:
    start = TODAY.replace(day=1)
    return max(0, min(CALENDAR_MONTHS - 1, (day.year - start.year) * 12 + day.month - start.month))


def init_state() -> None:
    # Shared UI state — must exist for BOTH guests and signed-in users
    # (sidebar()/pages read these every run).
    st.session_state.setdefault("calendar_month_offset", 0)
    st.session_state.setdefault("calendar_selected_date", TODAY)
    st.session_state.setdefault("active_page", PAGES[0])
    st.session_state.setdefault("sidebar_page", st.session_state.active_page)
    st.session_state.setdefault("top_page", st.session_state.active_page)
    st.session_state.setdefault("feed_sources", [])
    st.session_state.setdefault("feed_auto_refresh", True)

    if st.session_state.get("auth"):
        uid = st.session_state.auth["id"]
        if st.session_state.get("_loaded_uid") != uid:
            snap = load_user_data(uid)
            if snap:
                st.session_state.backup = snap.get("_backup")
                restore_snapshot(snap)
            elif st.session_state.get("pending_guest_snapshot"):
                restore_snapshot(st.session_state.pop("pending_guest_snapshot"))
            else:
                seed_state()
            st.session_state._loaded_uid = uid
        return
    if "assignments" not in st.session_state:
        seed_state()


def sync_page_from_sidebar() -> None:
    st.session_state.active_page = st.session_state.sidebar_page
    st.query_params["page"] = st.session_state.active_page


def sync_page_from_top() -> None:
    st.session_state.active_page = st.session_state.top_page
    st.query_params["page"] = st.session_state.active_page


def go_page(page: str) -> None:
    st.session_state.active_page = page
    st.query_params["page"] = page
    st.rerun()


def sync_page_from_query() -> None:
    page = st.query_params.get("page")
    if page in PAGES:
        st.session_state.active_page = page
    if st.query_params.get("add") == "assignment":
        st.session_state.show_add_assignment = True


def render_action_bar() -> None:
    actions = [
        ("Dashboard", "Today", "T"),
        ("Schedule", "Week", "W"),
        ("Calendar", "Calendar", "C"),
        ("Assignments", "Add", "+"),
        ("Calendar Sync", "Sync", "S"),
        ("Study Plan", "Plan", "P"),
    ]
    st.markdown(
        """<div class="section-title" style="margin-top:4px">
        <div class="icon">Q</div><b>Quick actions</b></div>""",
        unsafe_allow_html=True,
    )
    links = []
    active = st.session_state.get("active_page", "Dashboard")
    for page, label, icon in actions:
        cls = "active" if page == active else ""
        href = f"?page={urllib.parse.quote(page)}"
        if page == "Calendar":
            href += "&cal_view=Month%20grid"
        elif page == "Assignments":
            href += "&add=assignment"
        links.append(
            f"<a class='{cls}' href='{href}' target='_self'>"
            f"<span class='nav-icon'>{html.escape(icon)}</span>"
            f"<b>{html.escape(label)}</b></a>"
        )
    st.markdown(f"<div class='quick-nav'>{''.join(links)}</div>", unsafe_allow_html=True)


def page_header(title: str, subtitle: str, eyebrow: str = "Auto-Planner") -> None:
    st.markdown(
        f"""<div class="page-head">
        <div class="eyebrow">{html.escape(eyebrow)}</div>
        <div class="title">{html.escape(title)}</div>
        <div class="sub">{html.escape(subtitle)}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def login_gate() -> None:
    if st.session_state.get("auth") or st.session_state.get("guest"):
        return
    st.markdown("""<div class="hero" style="text-align:center"><div class="b">Auto-Planner</div><div class="s">Your deadlines and study time organized into a realistic plan.</div></div>""", unsafe_allow_html=True)
    if not supabase_ready():
        st.info("Accounts need Supabase secrets. Guest mode works now.")
    tab_login, tab_signup, tab_reset = st.tabs(["Log in", "Sign up", "Forgot password"])
    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in", type="primary", use_container_width=True, disabled=not supabase_ready()):
            try:
                if sign_in(email, password):
                    remember_session()
                    st.rerun()
            except Exception as exc:
                st.error(f"Could not log in: {exc}")
    with tab_signup:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        if st.button("Create account", type="primary", use_container_width=True, disabled=not supabase_ready()):
            try:
                if len(password) < 6:
                    st.warning("Use at least 6 characters.")
                elif sign_up(email, password):
                    remember_session()
                    st.rerun()
                else:
                    st.info("Check your email to confirm the account, then log in.")
            except Exception as exc:
                st.error(f"Could not create account: {exc}")
    with tab_reset:
        reset_email = st.text_input("Account email", key="reset_email")
        if st.button("Send password reset", use_container_width=True, disabled=not supabase_ready()):
            try:
                send_password_reset(reset_email)
                st.success("Password reset email sent if that account exists.")
            except Exception as exc:
                st.error(f"Could not send reset: {exc}")
    st.divider()
    if st.button("Try as guest", use_container_width=True):
        st.session_state.guest = True
        st.rerun()
    st.caption("Guest mode is temporary. Log in to save automatically.")
    st.stop()


try_restore_session()
login_gate()
init_state()


def autosave() -> None:
    auth = st.session_state.get("auth")
    if not auth:
        return
    encoded = json.dumps(snapshot(), sort_keys=True)
    if encoded == st.session_state.get("_last_saved"):
        return
    try:
        save_user_data(auth["id"])
        st.session_state._last_saved = encoded
        st.session_state._save_error = ""
    except Exception as exc:
        st.session_state._save_error = str(exc)


def build_ics() -> str:
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Auto-Planner//EN", "CALSCALE:GREGORIAN", "X-WR-CALNAME:Auto-Planner"]
    esc = lambda s: str(s).replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")
    for i, b in enumerate(st.session_state.blocks):
        sh, sm = divmod(round(b.start * 60), 60)
        eh, em = divmod(round(b.end * 60), 60)
        lines += ["BEGIN:VEVENT", f"UID:study-{b.task_id}-{i}@auto-planner", f"DTSTAMP:{stamp}", f"DTSTART:{b.date:%Y%m%d}T{sh:02d}{sm:02d}00", f"DTEND:{b.date:%Y%m%d}T{eh:02d}{em:02d}00", f"SUMMARY:Study: {esc(b.title)} ({esc(b.course)})", "DESCRIPTION:Auto-scheduled study block.", "BEGIN:VALARM", "TRIGGER:-PT15M", "ACTION:DISPLAY", "DESCRIPTION:Study block starting soon", "END:VALARM", "END:VEVENT"]
    for a in st.session_state.assignments:
        lines += ["BEGIN:VEVENT", f"UID:due-{a.id}@auto-planner", f"DTSTAMP:{stamp}", f"DTSTART;VALUE=DATE:{a.due:%Y%m%d}", f"DTEND;VALUE=DATE:{(a.due + dt.timedelta(days=1)):%Y%m%d}", f"SUMMARY:DUE: {esc(a.title)} ({esc(a.course)})", f"DESCRIPTION:{esc(a.title)} is due. Status: {esc(a.status)}.", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def gcal_link(title: str, day: dt.date, start: float, end: float) -> str:
    sh, sm = divmod(round(start * 60), 60)
    eh, em = divmod(round(end * 60), 60)
    dates = f"{day:%Y%m%d}T{sh:02d}{sm:02d}00/{day:%Y%m%d}T{eh:02d}{em:02d}00"
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode({"action": "TEMPLATE", "text": title, "dates": dates, "details": "Scheduled by Auto-Planner"})


def gcal_due_link(a: Assignment) -> str:
    dates = f"{a.due:%Y%m%d}/{(a.due + dt.timedelta(days=1)):%Y%m%d}"
    return "https://calendar.google.com/calendar/render?" + urllib.parse.urlencode({
        "action": "TEMPLATE",
        "text": f"DUE: {a.title}",
        "dates": dates,
        "details": f"{a.title} is due. Course: {a.course}. Scheduled by Auto-Planner.",
    })


def render_overload_banner() -> None:
    over = unscheduled_titles()
    if over:
        shown = ", ".join(over[:4]) + ("..." if len(over) > 4 else "")
        st.markdown(f"""<div class="danger-banner"><b>{len(over)} assignment(s) do not fit before the deadline.</b><div class="muted">Affected: {html.escape(shown)}. Free up time, reduce estimated hours, or start now.</div></div>""", unsafe_allow_html=True)


def due_text(days: int) -> str:
    if days < 0:
        return f"{abs(days)}d overdue"
    if days == 0:
        return "due today"
    if days == 1:
        return "due tomorrow"
    return f"due in {days}d"


def render_assignment_card(a: Assignment, score: int | None = None, compact: bool = False) -> None:
    tasks = assignment_tasks(a.id)
    done = sum(t.done for t in tasks)
    total = len(tasks)
    pct = round(done / total * 100) if total else 0
    days = (a.due - TODAY).days
    cls, lbl = ("hi", "Overdue") if days < 0 else pri_label(score if score is not None else priority_score(a))
    status = assignment_status(a)
    progress = "" if compact else f"<div class='mini-progress'><span style='width:{pct}%'></span></div>"
    calendar_link = "" if compact else (
        f"<div class='assignment-links'><a href='{html.escape(gcal_due_link(a), quote=True)}' "
        f"target='_blank' rel='noopener'>Add due date to Google Calendar</a></div>"
    )
    st.markdown(
        f"""<div class="assignment-card">
        <div class="assignment-head">
          <div>
            <div class="assignment-title">{html.escape(a.title)}</div>
            <div class="faint">{html.escape(a.course)} - {due_text(days)} - {done}/{total} tasks</div>
          </div>
          <div class="assignment-badges">
            <span class="pill {cls}">{lbl}</span>
            <span class="pill {status_class(status)}">{status}</span>
          </div>
        </div>{progress}{calendar_link}</div>""",
        unsafe_allow_html=True,
    )


def render_block(b: Block, today_view: bool = False) -> None:
    task = next((t for t in st.session_state.tasks if t.id == b.task_id), None)
    if not task:
        return
    c1, c2 = st.columns([0.16, 0.84])
    checked = c1.checkbox("Done", value=task.done, key=f"blk-{b.task_id}-{b.date}-{b.start}", label_visibility="collapsed")
    if checked != task.done:
        push_undo("update task")
        set_task_done(task, checked)
        st.session_state.history[-1] = max(0, st.session_state.history[-1] + (0.3 if checked else -0.3))
        st.rerun()
    done_class = "done" if task.done else ""
    status = "Done" if task.done else "Study"
    calendar_url = html.escape(gcal_link(f"Study: {b.title}", b.date, b.start, b.end), quote=True)
    c2.markdown(
        f"""<div class="study-card {done_class}" style="--task-color:{b.color}">
        <div class="study-title">{html.escape(b.title)}</div>
        <div class="study-meta">
        <span class="faint">{html.escape(b.course)}</span>
        <span class="pill status-progress">{fmt_time(b.start)}-{fmt_time(b.end)}</span>
        <span class="pill {status_class('Done' if task.done else 'In Progress')}">{status}</span>
        </div>
        <div class="study-links"><a href="{calendar_url}" target="_blank" rel="noopener">Add to Google Calendar</a></div>
        </div>""",
        unsafe_allow_html=True,
    )
    if today_view and not task.done:
        if st.button("Missed? Reschedule this block", key=f"miss-{b.task_id}-{b.start}", use_container_width=True):
            push_undo("reschedule block")
            reschedule(b.task_id)
            st.rerun()


def reschedule(task_id: int) -> None:
    task = next((t for t in st.session_state.tasks if t.id == task_id), None)
    if not task:
        return
    st.session_state.blocks = [b for b in st.session_state.blocks if b.task_id != task_id]
    slots = free_slots()
    for off in range(1, HORIZON_DAYS):
        day = DAYS[(TODAY_IDX + off) % 7]
        date = TODAY + dt.timedelta(days=off)
        for start, end in slots.get(day, []):
            if end - start >= 1:
                st.session_state.blocks.append(Block(day, start, min(end, start + FOCUS_BLOCK), task.title, task.course, task.color, task.id, date))
                st.toast(f"Moved to {date:%a, %b %d} at {fmt_time(start)}")
                return
    st.warning("No open slot found in the 30-day planning window.")


def render_data_tools(auth: dict | None, prefix: str = "data") -> None:
    st.markdown("**Save and data**")
    st.caption("Auto-saving to your account." if auth else "Guest mode: changes and backups are temporary. Log in to save automatically.")
    st.download_button(
        "Download my data",
        json.dumps(snapshot(), indent=2),
        "autoplanner_data.json",
        "application/json",
        use_container_width=True,
        key=f"{prefix}-download-data",
    )
    upload = st.file_uploader("Restore from file", type=["json"], key=f"{prefix}-restore-file")
    if upload:
        try:
            push_undo("restore file")
            restore_snapshot(json.load(upload))
            st.rerun()
        except Exception as exc:
            st.error(f"Could not restore that file: {exc}")
    if st.session_state.get("undo_snapshot") and st.button(f"Undo {st.session_state.get('undo_label', 'last change')}", use_container_width=True, key=f"{prefix}-undo"):
        undo_last_change()
        st.rerun()
    confirm_key = f"{prefix}_confirm_clear"
    if st.session_state.get(confirm_key):
        st.warning("This will remove all assignments, commitments, and study blocks from this planner.")
        c1, c2 = st.columns(2)
        if c1.button("Yes, clear it", use_container_width=True, key=f"{prefix}-clear-confirm"):
            push_undo("clear calendar")
            st.session_state.backup = snapshot()
            st.session_state.assignments = []
            st.session_state.fixed = []
            st.session_state.task_done_ids = []
            st.session_state[confirm_key] = False
            generate_plan()
            st.rerun()
        if c2.button("Cancel", use_container_width=True, key=f"{prefix}-clear-cancel"):
            st.session_state[confirm_key] = False
            st.rerun()
    elif st.button("Clear whole calendar", use_container_width=True, key=f"{prefix}-clear-start"):
        st.session_state[confirm_key] = True
        st.rerun()
    if st.session_state.get("backup"):
        if not auth:
            st.caption("Restore is available now, but guest backups disappear after closing or refreshing.")
        if st.button("Restore last backup", use_container_width=True, key=f"{prefix}-restore-backup"):
            restore_snapshot(st.session_state.backup)
            st.rerun()


def render_schedule_setup(prefix: str = "setup") -> None:
    with st.expander("Classes, work, and clubs"):
        st.caption("These repeat every week. Add class twice if it meets Tuesday and Thursday.")
        with st.form(f"{prefix}-fixed-form", clear_on_submit=True):
            name = st.text_input("Name", placeholder="CHEM 101 Lecture", key=f"{prefix}-fixed-name")
            kind = st.selectbox("Type", ["class", "work", "club"], key=f"{prefix}-fixed-kind")
            day = st.selectbox("Day", DAYS, key=f"{prefix}-fixed-day")
            a, b = st.columns(2)
            start = a.number_input("Start", 6.0, 21.5, 10.0, 0.5, key=f"{prefix}-fixed-start")
            end = b.number_input("End", 6.5, 22.0, 11.5, 0.5, key=f"{prefix}-fixed-end")
            if st.form_submit_button("Add weekly commitment", use_container_width=True):
                if name and end > start:
                    push_undo("add commitment")
                    st.session_state.fixed.append(Fixed(day, start, end, name, kind))
                    generate_plan()
                    st.rerun()
                else:
                    st.warning("Add a name and make sure end is after start.")
        for idx, f in enumerate(st.session_state.fixed):
            c1, c2 = st.columns([0.75, 0.25])
            c1.caption(f"{f.day} {fmt_time(f.start)}-{fmt_time(f.end)} - {f.title}")
            if c2.button("Remove", key=f"{prefix}-rmfixed-{idx}", use_container_width=True):
                push_undo("remove commitment")
                st.session_state.fixed.pop(idx)
                generate_plan()
                st.rerun()
    with st.expander("Meal breaks"):
        on = st.checkbox("Reserve meal times", value=st.session_state.meals_on, key=f"{prefix}-meals-on")
        breakfast = st.slider("Breakfast", 6.0, 10.0, st.session_state.meals[0][0], 0.5, key=f"{prefix}-breakfast")
        lunch = st.slider("Lunch", 11.0, 14.0, st.session_state.meals[1][0], 0.5, key=f"{prefix}-lunch")
        dinner = st.slider("Dinner", 16.0, 20.0, st.session_state.meals[2][0], 0.5, key=f"{prefix}-dinner")
        if (on, breakfast, lunch, dinner) != (st.session_state.meals_on, st.session_state.meals[0][0], st.session_state.meals[1][0], st.session_state.meals[2][0]):
            push_undo("change meals")
            st.session_state.meals_on = on
            st.session_state.meals = [(breakfast, breakfast + .5, "Breakfast"), (lunch, lunch + 1, "Lunch"), (dinner, dinner + 1, "Dinner")]
            generate_plan()
            st.rerun()


def sidebar() -> None:
    with st.sidebar:
        auth = st.session_state.get("auth")
        if auth:
            st.caption(f"Signed in as {auth.get('email')}")
            if st.button("Log out", use_container_width=True):
                sign_out()
                st.rerun()
        else:
            st.caption("Guest mode: not saved.")
            if st.button("Sign up to save", use_container_width=True):
                st.session_state.pending_guest_snapshot = snapshot()
                st.session_state.guest = False
                st.rerun()
        st.markdown("### Auto-Planner")
        st.caption(f"Hi {st.session_state.user} - {TODAY:%A, %b %d}")
        st.session_state.sidebar_page = st.session_state.active_page
        st.radio("Go to", PAGES, key="sidebar_page", on_change=sync_page_from_sidebar)
        st.divider()
        add_assignment_form("side")
        st.divider()
        st.download_button("Export plan (.ics)", build_ics(), "auto-planner.ics", "text/calendar", use_container_width=True)
        render_schedule_setup("side-schedule")
        st.divider()
        render_data_tools(auth, "side-data")


def add_assignment_form(prefix: str) -> None:
    with st.form(f"add-{prefix}", clear_on_submit=True):
        st.markdown("**Add assignment**")
        title = st.text_input("Title", key=f"{prefix}-title")
        course = st.text_input("Course", key=f"{prefix}-course")
        kind = st.selectbox("Type", list(TYPE_DEFAULTS), key=f"{prefix}-kind")
        due = st.date_input("Due date", value=_d(5), key=f"{prefix}-due")
        weight, hours_default, diff_default = TYPE_DEFAULTS[kind]
        hours = st.number_input("Estimated hours", 0.5, 60.0, hours_default, 0.5, key=f"{prefix}-hours")
        diff = st.select_slider("Difficulty", [1, 2, 3], value=diff_default, key=f"{prefix}-diff")
        if st.form_submit_button("Add and auto-plan", use_container_width=True):
            if not title.strip():
                st.warning("Add a title first.")
                return
            push_undo("add assignment")
            st.session_state.next_id += 1
            st.session_state.assignments.append(Assignment(st.session_state.next_id, title.strip(), course.strip() or "General", due, hours, diff, COLORS[len(st.session_state.assignments) % len(COLORS)], weight))
            generate_plan()
            st.rerun()


def page_dashboard() -> None:
    if not st.session_state.assignments:
        st.markdown("""<div class="hero"><div class="k">Welcome</div><div class="b">Build your first plan</div><div class="s">Add an assignment or import a syllabus, and Auto-Planner will schedule the work.</div></div>""", unsafe_allow_html=True)
        st.info("No assignments yet.")
        c1, c2 = st.columns(2)
        if c1.button("Add first assignment", type="primary", use_container_width=True):
            st.session_state.show_add_assignment = True
            go_page("Assignments")
        if c2.button("Import calendar or syllabus", use_container_width=True):
            go_page("Import")
        return
    blocks = sorted([b for b in st.session_state.blocks if b.date == TODAY], key=lambda b: b.start)
    done = sum(1 for b in blocks if any(t.id == b.task_id and t.done for t in st.session_state.tasks))
    planned = sum(b.end - b.start for b in blocks)
    total = len(blocks)
    due_week = sum(1 for a in st.session_state.assignments if 0 <= (a.due - TODAY).days <= 7)
    all_tasks = len(st.session_state.tasks)
    done_tasks = sum(t.done for t in st.session_state.tasks)
    plan_pct = round(done_tasks / all_tasks * 100) if all_tasks else 0
    st.markdown(f"""<div class="hero"><div class="k">Today's focus</div><div class="b">{done}/{total} tasks done</div><div class="s">{planned:g}h planned today - {compute_streak()} day streak</div></div>""", unsafe_allow_html=True)
    st.progress(done / total if total else 0)
    st.markdown(
        f"""<div class="stat-grid">
        <div class="stat-card"><b>{planned:g}h</b><span>planned today</span></div>
        <div class="stat-card"><b>{due_week}</b><span>due this week</span></div>
        <div class="stat-card"><b>{plan_pct}%</b><span>plan complete</span></div>
        <div class="stat-card"><b>{compute_streak()}d</b><span>study streak</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    render_overload_banner()
    with st.expander("Quick add assignment"):
        add_assignment_form("dash")
    left, right = st.columns([0.58, 0.42])
    with left:
        st.markdown("#### Today")
        if not blocks:
            st.markdown("""<div class="empty-note">Nothing due today -- enjoy the break or get ahead.</div>""", unsafe_allow_html=True)
        for b in blocks:
            render_block(b, today_view=True)
    with right:
        st.markdown("#### Upcoming")
        for a in sorted(st.session_state.assignments, key=lambda a: a.due)[:7]:
            render_assignment_card(a, priority_score(a), compact=True)


def page_schedule() -> None:
    page_header("Schedule", "A quick 7-day look at study blocks, meals, classes, work, and clubs.", "Week view")
    choices = [TODAY + dt.timedelta(days=i) for i in range(7)]
    selected = st.selectbox("Day", choices, format_func=lambda d: f"{d:%a, %b %d}" + (" - Today" if d == TODAY else ""))
    items = [(f.start, "fixed", f) for f in st.session_state.fixed if f.day == DAYS[selected.weekday()]]
    if st.session_state.meals_on:
        items += [(s, "fixed", Fixed(DAYS[selected.weekday()], s, e, label, "meal")) for s, e, label in st.session_state.meals]
    items += [(b.start, "study", b) for b in st.session_state.blocks if b.date == selected]
    items.sort(key=lambda x: x[0])
    render_overload_banner()
    if not items:
        st.markdown("""<div class="empty-note">Nothing scheduled here.</div>""", unsafe_allow_html=True)
    for _, typ, item in items:
        if typ == "study":
            render_block(item, today_view=(selected == TODAY))
        else:
            color = KIND_COLORS.get(item.kind, TEXT)
            st.markdown(f"""<div class="card" style="border-left:5px solid {color}"><b>{html.escape(item.title)}</b><div class="faint">{KIND_LABELS.get(item.kind, item.kind)} - {fmt_time(item.start)}-{fmt_time(item.end)}</div></div>""", unsafe_allow_html=True)
    st.markdown("""<div class="section-title"><div class="icon">S</div><b>Schedule settings</b></div>""", unsafe_allow_html=True)
    render_schedule_setup("main-schedule")


def calendar_items(day: dt.date) -> dict[str, list]:
    return {
        "due": [a for a in st.session_state.assignments if a.due == day],
        "study": [b for b in st.session_state.blocks if b.date == day],
        "fixed": [f for f in st.session_state.fixed if f.day == DAYS[day.weekday()]],
        "meals": [Fixed(DAYS[day.weekday()], s, e, label, "meal") for s, e, label in st.session_state.meals] if st.session_state.meals_on else [],
    }


def render_day_details(day: dt.date) -> None:
    items = calendar_items(day)
    st.markdown(
        f"""<div class="card"><div class="faint">{day:%A}</div>
        <div style="font-size:24px;font-weight:800">{day:%B %d, %Y}</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:10px">
        <span class="pill hi">{len(items['due'])} due</span>
        <span class="pill status-progress">{len(items['study'])} study</span>
        <span class="pill status-not">{len(items['fixed'])} fixed</span>
        </div></div>""",
        unsafe_allow_html=True,
    )
    if day > TODAY + dt.timedelta(days=HORIZON_DAYS - 1):
        st.caption("Study blocks will be generated closer to this date.")
    if not (items["due"] or items["study"] or items["fixed"] or items["meals"]):
        st.markdown("""<div class="empty-note">Nothing due today -- enjoy the break.</div>""", unsafe_allow_html=True)
    if items["due"]:
        st.markdown("""<div class="section-title"><div class="icon">!</div><b>Due</b></div>""", unsafe_allow_html=True)
        for a in items["due"]:
            st.markdown(f"""<div class="card" style="border-left:5px solid {DANGER}"><b>{html.escape(a.title)}</b><div class="faint">{html.escape(a.course)} - ~{a.hours:g}h - {assignment_status(a)}</div></div>""", unsafe_allow_html=True)
    if items["study"]:
        st.markdown("""<div class="section-title"><div class="icon">S</div><b>Study plan</b></div>""", unsafe_allow_html=True)
        for b in sorted(items["study"], key=lambda x: x.start):
            render_block(b, today_view=(day == TODAY))
    elif day <= TODAY + dt.timedelta(days=HORIZON_DAYS - 1):
        st.markdown("""<div class="empty-note">No study blocks scheduled for this day.</div>""", unsafe_allow_html=True)
    if items["fixed"]:
        st.markdown("""<div class="section-title"><div class="icon">C</div><b>Commitments</b></div>""", unsafe_allow_html=True)
        for f in sorted(items["fixed"], key=lambda x: x.start):
            color = KIND_COLORS.get(f.kind, TEXT)
            st.markdown(f"""<div class="card" style="border-left:5px solid {color}"><b>{html.escape(f.title)}</b><div class="faint">{KIND_LABELS.get(f.kind, f.kind)} - {fmt_time(f.start)}-{fmt_time(f.end)}</div></div>""", unsafe_allow_html=True)
    if items["meals"]:
        st.markdown("""<div class="section-title"><div class="icon">M</div><b>Meals</b></div>""", unsafe_allow_html=True)
        for f in sorted(items["meals"], key=lambda x: x.start):
            color = KIND_COLORS.get(f.kind, TEXT)
            st.markdown(f"""<div class="card" style="border-left:5px solid {color}"><b>{html.escape(f.title)}</b><div class="faint">{fmt_time(f.start)}-{fmt_time(f.end)}</div></div>""", unsafe_allow_html=True)


def render_month_grid(month_start: dt.date, selected: dt.date) -> str:
    """A compact HTML month grid that fits phone widths (display + dots)."""
    weeks = calendar.Calendar(firstweekday=calendar.MONDAY).monthdayscalendar(
        month_start.year, month_start.month)
    head = "".join(f"<th>{d}</th>" for d in DAYS)
    rows = ""
    for week in weeks:
        cells = ""
        for num in week:
            if not num:
                cells += "<td class='empty'></td>"
                continue
            d = dt.date(month_start.year, month_start.month, num)
            items = calendar_items(d)
            dots = ""
            for color, n in ((DANGER, len(items["due"])), (BRAND, len(items["study"])),
                             (FIXED_DOT, len(items["fixed"]))):
                dots += f"<span class='dot' style='background:{color}'></span>" * min(n, 4)
            cls = " ".join(c for c, on in (("today", d == TODAY), ("sel", d == selected)) if on)
            href = (
                f"?page=Calendar"
                f"&cal_date={d.isoformat()}"
                f"&cal_view=Month%20grid"
                f"&calendar_month_offset={month_offset_for(d)}"
            )
            cells += (f"<td class='{cls}'><a class='day-link' href='{href}' target='_self'>"
                      f"<div class='dnum'>{num}</div>"
                      f"<div class='dots'>{dots}</div></a></td>")
        rows += f"<tr>{cells}</tr>"
    return f"<table class='cal'><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"


def page_calendar() -> None:
    page_header("Calendar", "Browse the next 12 months and tap any day to see the plan.", "Month view")
    if st.button("Connect calendars / sync feeds", use_container_width=True, key="calendar-open-sync"):
        go_page("Calendar Sync")
    query_view = st.query_params.get("cal_view")
    if query_view in ("Agenda", "Month grid"):
        st.session_state.cal_view = query_view
    query_date = st.query_params.get("cal_date")
    if query_date:
        try:
            clicked = dt.date.fromisoformat(query_date)
            st.session_state.calendar_selected_date = clicked
            st.session_state.calendar_month_offset = month_offset_for(clicked)
            st.session_state.cal_view = "Month grid"
        except ValueError:
            pass
    offset = max(0, min(CALENDAR_MONTHS - 1, int(st.session_state.get("calendar_month_offset", 0))))
    month_start = add_months(TODAY.replace(day=1), offset)
    c1, c2, c3, c4 = st.columns([.18, .44, .18, .20])
    if c1.button("Prev", disabled=offset == 0, use_container_width=True):
        st.session_state.calendar_month_offset = offset - 1
        st.session_state.calendar_selected_date = add_months(TODAY.replace(day=1), offset - 1)
        st.rerun()
    c2.markdown(f"#### {month_start:%B %Y}")
    if c3.button("Today", use_container_width=True):
        st.session_state.calendar_month_offset = 0
        st.session_state.calendar_selected_date = TODAY
        st.rerun()
    if c4.button("Next", disabled=offset == CALENDAR_MONTHS - 1, use_container_width=True):
        st.session_state.calendar_month_offset = offset + 1
        st.session_state.calendar_selected_date = add_months(TODAY.replace(day=1), offset + 1)
        st.rerun()
    # Read the view from session_state (not the widget return) so it never
    # diverges from what the toggle shows after Prev/Next/Today reruns.
    st.session_state.setdefault("cal_view", "Agenda")
    if hasattr(st, "segmented_control"):
        st.segmented_control("View", ["Agenda", "Month grid"], key="cal_view")
    else:
        st.radio("View", ["Agenda", "Month grid"], horizontal=True, key="cal_view")
    view = st.session_state.cal_view or "Agenda"
    selected = st.session_state.get("calendar_selected_date", TODAY)
    if isinstance(selected, str):
        selected = dt.date.fromisoformat(selected)
    if selected.month != month_start.month or selected.year != month_start.year:
        selected = month_start
        st.session_state.calendar_selected_date = selected
    if view == "Agenda":
        render_day_details(selected)
        st.markdown("#### This month")
        for day in range(1, calendar.monthrange(month_start.year, month_start.month)[1] + 1):
            d = dt.date(month_start.year, month_start.month, day)
            items = calendar_items(d)
            if items["due"] or items["study"] or items["fixed"]:
                row, action = st.columns([.74, .26])
                row.markdown(f"**{d:%a, %b %d}**  <span class='faint'>{len(items['due'])} due - {len(items['study'])} study - {len(items['fixed'])} fixed</span>", unsafe_allow_html=True)
                if action.button("Open", key=f"open-{d}", use_container_width=True):
                    st.session_state.calendar_selected_date = d
                    st.rerun()
        return
    st.markdown(
        f"""<div class="selected-day-note"><b>{selected:%A, %B %d}</b>
        <div class="faint">Tap any day below to open that day's plan.</div></div>""",
        unsafe_allow_html=True,
    )
    render_day_details(selected)
    st.markdown(
        """<div class="section-title"><div class="icon">M</div><b>Month grid</b></div>""",
        unsafe_allow_html=True,
    )
    st.markdown(render_month_grid(month_start, selected), unsafe_allow_html=True)
    st.markdown(
        f"<div class='faint' style='margin:2px 0 6px'>"
        f"<span style='color:{DANGER};font-size:15px'>&bull;</span> due &nbsp;&nbsp;"
        f"<span style='color:{BRAND};font-size:15px'>&bull;</span> study &nbsp;&nbsp;"
        f"<span style='color:{FIXED_DOT};font-size:15px'>&bull;</span> class / work / club</div>",
        unsafe_allow_html=True)
    with st.expander("Jump to a date"):
        last_day = calendar.monthrange(month_start.year, month_start.month)[1]
        picked = st.date_input(
            "Show a day's details", value=selected,
            min_value=dt.date(month_start.year, month_start.month, 1),
            max_value=dt.date(month_start.year, month_start.month, last_day))
        if picked != selected:
            st.session_state.calendar_selected_date = picked
            st.rerun()


COURSE_RE = re.compile(r"\b([A-Z]{2,4})\s?[- ]?(\d{2,3}[A-Z]?)\b")
DATE_RE = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{1,2}(?:,?\s*\d{4})?)", re.I)


def course_from(text: str) -> str:
    m = COURSE_RE.search(text)
    return f"{m.group(1)} {m.group(2)}" if m else "General"


def candidate(title: str, due: dt.date, course: str = "", source: str = "", external_id: str = "") -> dict:
    kind = detect_type(title, course)
    weight, hours, diff = TYPE_DEFAULTS[kind]
    return {
        "title": title.strip()[:90] or "Untitled assignment",
        "course": course or course_from(title),
        "due": due,
        "hours": hours,
        "diff": diff,
        "weight": weight,
        "source": source,
        "external_id": external_id,
    }


def parse_text(text: str) -> list[dict]:
    from dateutil import parser
    out = []
    for line in text.splitlines():
        match = DATE_RE.search(line)
        if not match:
            continue
        try:
            parsed = parser.parse(match.group(0), fuzzy=True, default=dt.datetime(TODAY.year, 1, 1)).date()
            if not re.search(r"\d{4}", match.group(0)) and parsed < TODAY:
                parsed = parsed.replace(year=parsed.year + 1)
        except Exception:
            continue
        title = re.sub(r"\b(due|by|deadline|submit)\b", "", line[:match.start()] + line[match.end():], flags=re.I)
        out.append(candidate(title, parsed))
    return out


def parse_ics(data, source: str = "") -> list[dict]:
    from icalendar import Calendar
    if isinstance(data, bytes):
        data = data.decode("utf-8", "ignore")
    try:
        cal = Calendar.from_ical(data)
    except Exception as exc:
        raise ValueError("That calendar file could not be read. Try exporting it again as .ics.") from exc
    out = []
    for event in cal.walk("VEVENT"):
        summary = str(event.get("SUMMARY", "")).strip()
        start = event.get("DTSTART")
        if not summary or not start:
            continue
        value = start.dt
        due = value.date() if isinstance(value, dt.datetime) else value
        if isinstance(due, dt.date):
            uid = str(event.get("UID", "")).strip()
            external_id = uid or hashlib.sha1(f"{summary}|{due.isoformat()}".encode("utf-8")).hexdigest()
            out.append(candidate(summary, due, course_from(summary), source, external_id))
    return out


def fetch_feed(url: str) -> str:
    import requests
    url = url.strip()
    if url.startswith("webcal://"):
        url = "https://" + url[len("webcal://"):]
    if not url.startswith(("http://", "https://")):
        raise ValueError("Paste a full calendar URL that starts with http, https, or webcal.")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text


def feed_key(source_name: str, external_id: str) -> tuple[str, str]:
    return source_name.strip().lower(), external_id.strip()


def sync_feed_source(source: dict) -> dict:
    """Fetch one saved ICS feed and upsert its events into assignments."""
    name = (source.get("name") or "Calendar feed").strip()
    url = (source.get("url") or "").strip()
    if not url:
        raise ValueError("Missing feed URL.")

    parsed = parse_ics(fetch_feed(url), source=name)
    existing = {
        feed_key(a.source, a.external_id): a
        for a in st.session_state.assignments
        if getattr(a, "source", "") and getattr(a, "external_id", "")
    }

    added = 0
    updated = 0
    for row in parsed:
        external_id = row.get("external_id") or hashlib.sha1(
            f"{name}|{row['title']}|{row['due'].isoformat()}".encode("utf-8")
        ).hexdigest()
        key = feed_key(name, external_id)
        if key in existing:
            a = existing[key]
            changed = (
                a.title != row["title"]
                or a.course != row["course"]
                or a.due != row["due"]
            )
            a.title = row["title"]
            a.course = row["course"]
            a.due = row["due"]
            a.source = name
            a.external_id = external_id
            if changed:
                updated += 1
        else:
            st.session_state.next_id += 1
            st.session_state.assignments.append(
                Assignment(
                    st.session_state.next_id,
                    row["title"],
                    row.get("course") or "General",
                    row["due"],
                    float(row.get("hours") or 3),
                    int(row.get("diff") or 2),
                    COLORS[len(st.session_state.assignments) % len(COLORS)],
                    int(row.get("weight") or 3),
                    source=name,
                    external_id=external_id,
                )
            )
            added += 1

    source["last_sync"] = dt.datetime.now(dt.timezone.utc).isoformat()
    source["last_count"] = len(parsed)
    source["last_error"] = ""
    generate_plan()
    return {"added": added, "updated": updated, "seen": len(parsed)}


def refresh_connected_feeds(force: bool = False) -> dict:
    """Refresh saved feeds once per app session, or on demand."""
    sources = st.session_state.get("feed_sources", [])
    if not sources:
        return {"added": 0, "updated": 0, "errors": 0}
    if not force and st.session_state.get("_feeds_refreshed_this_session"):
        return {"added": 0, "updated": 0, "errors": 0}

    totals = {"added": 0, "updated": 0, "errors": 0}
    for source in sources:
        try:
            result = sync_feed_source(source)
            totals["added"] += result["added"]
            totals["updated"] += result["updated"]
        except Exception as exc:
            source["last_error"] = str(exc)
            totals["errors"] += 1
    st.session_state._feeds_refreshed_this_session = True
    return totals


def maybe_auto_refresh_feeds() -> None:
    if not st.session_state.get("feed_auto_refresh", True):
        return
    if not st.session_state.get("feed_sources"):
        return
    if st.session_state.get("_feeds_refreshed_this_session"):
        return
    totals = refresh_connected_feeds(force=False)
    if totals["added"] or totals["updated"]:
        st.toast(
            f"Calendar feeds updated: {totals['added']} added, {totals['updated']} changed."
        )


def parse_csv(file) -> list[dict]:
    try:
        df = pd.read_csv(file)
    except Exception as exc:
        raise ValueError("That CSV could not be read. Export it again as comma-separated values.") from exc
    cols = {str(c).lower().strip(): c for c in df.columns}
    title_col = next((cols[x] for x in ("title", "name", "assignment", "task") if x in cols), None)
    due_col = next((cols[x] for x in ("due", "due date", "date", "deadline") if x in cols), None)
    if title_col is None or due_col is None:
        raise ValueError("CSV needs at least a title column and a due/date column.")
    course_col = next((cols[x] for x in ("course", "class", "subject") if x in cols), None)
    hours_col = next((cols[x] for x in ("hours", "hrs", "effort") if x in cols), None)
    out = []
    for _, row in df.iterrows():
        if pd.isna(row[title_col]) or pd.isna(row[due_col]):
            continue
        try:
            due = pd.to_datetime(row[due_col]).date()
        except Exception:
            continue
        cand = candidate(str(row[title_col]), due, str(row[course_col]) if course_col and not pd.isna(row[course_col]) else "")
        if hours_col and not pd.isna(row[hours_col]):
            cand["hours"] = float(row[hours_col])
        out.append(cand)
    return out


def commit_import(rows: list[dict]) -> int:
    push_undo("import assignments")
    count = 0
    for row in rows:
        st.session_state.next_id += 1
        st.session_state.assignments.append(
            Assignment(
                st.session_state.next_id,
                str(row["title"]),
                str(row.get("course") or "General"),
                row["due"],
                float(row.get("hours") or 3),
                int(row.get("diff") or 2),
                COLORS[len(st.session_state.assignments) % len(COLORS)],
                int(row.get("weight") or 3),
                source=str(row.get("source") or ""),
                external_id=str(row.get("external_id") or ""),
            )
        )
        count += 1
    generate_plan()
    return count


def page_import() -> None:
    page_header("Import assignments", "Bring in syllabus text, calendar files, CSVs, or connected calendar feeds.", "Setup")
    st.markdown(
        """<div class="card"><b>Want automatic updates?</b>
        <div class="faint">Use Calendar Sync to connect Canvas, Google, Outlook, iCal, or webcal feeds once and refresh them later.</div></div>""",
        unsafe_allow_html=True,
    )
    if st.button("Open Calendar Sync", type="primary", use_container_width=True, key="import-open-calendar-sync"):
        go_page("Calendar Sync")
    found = None
    t1, t2, t3, t4, t5 = st.tabs(["Paste text", "Upload .ics", "Calendar feed", "Upload CSV", "Connected feeds"])
    with t1:
        text = st.text_area("Paste syllabus text", height=160)
        if st.button("Detect due dates", use_container_width=True):
            found = parse_text(text)
            if not found:
                st.warning("No dates found. Try lines like 'Essay due June 22'.")
    with t2:
        upload = st.file_uploader("Upload .ics", type=["ics"])
        if upload:
            try:
                found = parse_ics(upload.read())
            except Exception as exc:
                st.error(str(exc))
    with t3:
        st.markdown("#### Calendar feed sync")
        st.caption("Use Canvas Calendar Feed, Google Calendar secret iCal URL, Outlook published ICS, or any webcal link.")
        feed_name = st.text_input("Feed name", placeholder="Canvas / School Calendar")
        url = st.text_input("Feed URL", placeholder="https://...ics or webcal://...")
        c1, c2 = st.columns(2)
        if c1.button("Preview feed", use_container_width=True):
            try:
                found = parse_ics(fetch_feed(url), source=feed_name or "Calendar feed")
                if not found:
                    st.warning("Feed loaded, but no dated events were found.")
            except Exception as exc:
                st.error(f"Could not fetch that feed: {exc}")
        if c2.button("Save and sync automatically", type="primary", use_container_width=True):
            if not url.strip():
                st.warning("Paste a feed URL first.")
            else:
                push_undo("connect calendar feed")
                source = {
                    "name": feed_name.strip() or "Calendar feed",
                    "url": url.strip(),
                    "last_sync": "",
                    "last_count": 0,
                    "last_error": "",
                }
                st.session_state.feed_sources.append(source)
                try:
                    result = sync_feed_source(source)
                    st.success(f"Connected. Added {result['added']} and updated {result['updated']} assignment(s).")
                except Exception as exc:
                    source["last_error"] = str(exc)
                    st.error(f"Saved the feed, but could not sync yet: {exc}")
                st.rerun()
        sources = st.session_state.get("feed_sources", [])
        if sources:
            st.markdown("##### Connected feeds")
            if st.button("Refresh saved feeds", use_container_width=True, key="feed-tab-refresh"):
                push_undo("refresh calendar feeds")
                totals = refresh_connected_feeds(force=True)
                st.toast(
                    f"Feeds refreshed: {totals['added']} added, "
                    f"{totals['updated']} updated, {totals['errors']} error(s)."
                )
                st.rerun()
            for idx, source in enumerate(sources):
                st.caption(
                    f"{source.get('name', 'Calendar feed')} - "
                    f"{source.get('last_count', 0)} events seen"
                )
    with t4:
        csv = st.file_uploader("Upload CSV", type=["csv"])
        if csv:
            try:
                found = parse_csv(csv)
            except Exception as exc:
                st.error(str(exc))
    with t5:
        st.caption("Saved feeds refresh once when the app opens, and anytime you tap Refresh all.")
        st.session_state.feed_auto_refresh = st.checkbox(
            "Refresh connected feeds when the app opens",
            value=st.session_state.get("feed_auto_refresh", True),
        )
        sources = st.session_state.get("feed_sources", [])
        if not sources:
            st.info("No connected feeds yet. Add one from the Calendar feed tab.")
        else:
            if st.button("Refresh all feeds now", type="primary", use_container_width=True):
                push_undo("refresh calendar feeds")
                totals = refresh_connected_feeds(force=True)
                st.toast(
                    f"Feeds refreshed: {totals['added']} added, "
                    f"{totals['updated']} updated, {totals['errors']} error(s)."
                )
                st.rerun()
            for idx, source in enumerate(list(sources)):
                last = source.get("last_sync") or "Never"
                if last != "Never":
                    try:
                        last = dt.datetime.fromisoformat(last).strftime("%b %d, %I:%M %p").replace(" 0", " ")
                    except Exception:
                        pass
                st.markdown(
                    f"""<div class="card"><b>{html.escape(source.get('name', 'Calendar feed'))}</b>
                    <div class="faint">{html.escape(source.get('url', ''))}</div>
                    <div class="faint">Last sync: {html.escape(str(last))} - events seen: {source.get('last_count', 0)}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if source.get("last_error"):
                    st.warning(source["last_error"])
                if st.button("Remove feed", key=f"remove-feed-{idx}", use_container_width=True):
                    push_undo("remove calendar feed")
                    st.session_state.feed_sources.pop(idx)
                    st.rerun()
    if found is not None:
        st.session_state.import_candidates = found
    cands = st.session_state.get("import_candidates")
    if cands:
        st.markdown("#### Review and import")
        df = pd.DataFrame([{
            "Import": True,
            "Title": c["title"],
            "Course": c["course"],
            "Due": c["due"],
            "Hours": c["hours"],
            "Difficulty": c["diff"],
            "Importance": c["weight"],
            "Source": c.get("source", ""),
            "External ID": c.get("external_id", ""),
        } for c in cands])
        edited = st.data_editor(df, hide_index=True, use_container_width=True)
        chosen = edited[edited["Import"]]
        if st.button(f"Import {len(chosen)} selected", type="primary", use_container_width=True, disabled=len(chosen) == 0):
            rows = [{
                "title": row["Title"],
                "course": row["Course"],
                "due": row["Due"] if isinstance(row["Due"], dt.date) else pd.to_datetime(row["Due"]).date(),
                "hours": row["Hours"],
                "diff": row["Difficulty"],
                "weight": row["Importance"],
                "source": row.get("Source", ""),
                "external_id": row.get("External ID", ""),
            } for row in chosen.to_dict("records")]
            commit_import(rows)
            st.session_state.import_candidates = None
            st.rerun()


def page_calendar_sync() -> None:
    page_header("Calendar Sync", "Connect Canvas, Google Calendar, Outlook, iCal, or webcal feeds once.", "Connected calendars")
    st.markdown(
        """<div class="card"><b>Connect your school calendars once.</b>
        <div class="faint">Canvas, Google Calendar, Outlook, iCloud/iCal, and webcal links can refresh into Auto-Planner automatically.</div></div>""",
        unsafe_allow_html=True,
    )

    with st.expander("What link do I paste here?", expanded=False):
        st.markdown(
            "- **Canvas:** Calendar -> Calendar Feed -> copy the feed link.\n"
            "- **Google Calendar:** Calendar settings -> Secret address in iCal format.\n"
            "- **Outlook:** Calendar sharing/publish settings -> ICS link.\n"
            "- **iPhone / iCloud Calendar:** use a public/shared iCal subscription link if available. Direct private Apple Calendar access needs a separate Apple integration."
        )

    with st.form("calendar-sync-form", clear_on_submit=True):
        feed_name = st.text_input("Calendar name", placeholder="Canvas / School Calendar")
        feed_url = st.text_input("Calendar feed URL", placeholder="https://...ics or webcal://...")
        submitted = st.form_submit_button("Connect and sync", type="primary", use_container_width=True)

    if submitted:
        if not feed_url.strip():
            st.warning("Paste a calendar feed URL first.")
        else:
            push_undo("connect calendar feed")
            source = {
                "name": feed_name.strip() or "Calendar feed",
                "url": feed_url.strip(),
                "last_sync": "",
                "last_count": 0,
                "last_error": "",
            }
            st.session_state.feed_sources.append(source)
            try:
                result = sync_feed_source(source)
                st.success(
                    f"Connected. Added {result['added']} and updated {result['updated']} assignment(s)."
                )
            except Exception as exc:
                source["last_error"] = str(exc)
                st.error(f"Saved the feed, but could not sync yet: {exc}")
            st.rerun()

    st.divider()
    st.markdown("#### Connected calendars")
    st.session_state.feed_auto_refresh = st.checkbox(
        "Refresh connected feeds when the app opens",
        value=st.session_state.get("feed_auto_refresh", True),
        key="sync-auto-refresh",
    )

    sources = st.session_state.get("feed_sources", [])
    if not sources:
        st.info("No calendars connected yet.")
        return

    if st.button("Refresh all feeds now", type="primary", use_container_width=True, key="sync-refresh-all"):
        push_undo("refresh calendar feeds")
        totals = refresh_connected_feeds(force=True)
        st.toast(
            f"Feeds refreshed: {totals['added']} added, "
            f"{totals['updated']} updated, {totals['errors']} error(s)."
        )
        st.rerun()

    for idx, source in enumerate(list(sources)):
        last = source.get("last_sync") or "Never"
        if last != "Never":
            try:
                last = dt.datetime.fromisoformat(last).strftime("%b %d, %I:%M %p").replace(" 0", " ")
            except Exception:
                pass
        st.markdown(
            f"""<div class="card"><b>{html.escape(source.get('name', 'Calendar feed'))}</b>
            <div class="faint">{html.escape(source.get('url', ''))}</div>
            <div class="faint">Last sync: {html.escape(str(last))} - events seen: {source.get('last_count', 0)}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if source.get("last_error"):
            st.warning(source["last_error"])
        if st.button("Remove feed", key=f"sync-remove-feed-{idx}", use_container_width=True):
            push_undo("remove calendar feed")
            st.session_state.feed_sources.pop(idx)
            st.rerun()


def page_tasks() -> None:
    page_header("Assignments", "Track deadlines, status, priority, and the smaller tasks inside each assignment.", "Work list")
    add_open = bool(st.session_state.pop("show_add_assignment", False))
    with st.expander("Add an assignment", expanded=add_open):
        add_assignment_form("main")
    flt = st.segmented_control("Filter", ["Active", "All", "Done"], default="Active") if hasattr(st, "segmented_control") else st.radio("Filter", ["Active", "All", "Done"], horizontal=True)
    if not st.session_state.assignments:
        st.info("No assignments yet.")
        return
    score = {a.id: priority_score(a) for a in st.session_state.assignments}
    for a in sorted(st.session_state.assignments, key=lambda x: -score[x.id]):
        tasks = assignment_tasks(a.id)
        visible = tasks if flt == "All" else [t for t in tasks if t.done] if flt == "Done" else [t for t in tasks if not t.done]
        if not visible and flt != "All":
            continue
        status = assignment_status(a)
        render_assignment_card(a, score[a.id])
        c1, c2 = st.columns([.7, .3])
        new_status = c1.selectbox("Status", STATUSES, index=STATUSES.index(status), key=f"status-{a.id}", label_visibility="collapsed")
        if new_status != status:
            push_undo("change assignment status")
            set_assignment_status(a, new_status)
            st.rerun()
        with c2.popover("Edit", use_container_width=True):
            title = st.text_input("Title", a.title, key=f"title-{a.id}")
            course = st.text_input("Course", a.course, key=f"course-{a.id}")
            due = st.date_input("Due", a.due, key=f"due-{a.id}")
            hours = st.number_input("Hours", .5, 60.0, float(a.hours), .5, key=f"hours-{a.id}")
            diff = st.select_slider("Difficulty", [1, 2, 3], value=a.diff, key=f"diff-{a.id}")
            weight = st.slider("Importance", 1, 5, a.weight, key=f"weight-{a.id}")
            ecol1, ecol2 = st.columns(2)
            if ecol1.button("Save", key=f"save-{a.id}", use_container_width=True):
                push_undo("edit assignment")
                a.title, a.course, a.due, a.hours, a.diff, a.weight = title or a.title, course or "General", due, hours, diff, weight
                generate_plan()
                st.rerun()
            delete_key = f"confirm_delete_assignment_{a.id}"
            if st.session_state.get(delete_key):
                st.warning("Delete this assignment and its study blocks?")
                d1, d2 = st.columns(2)
                if d1.button("Yes, delete", key=f"delete-yes-{a.id}", use_container_width=True):
                    push_undo("delete assignment")
                    st.session_state.backup = snapshot()
                    st.session_state.assignments = [x for x in st.session_state.assignments if x.id != a.id]
                    st.session_state[delete_key] = False
                    generate_plan()
                    st.rerun()
                if d2.button("Cancel", key=f"delete-no-{a.id}", use_container_width=True):
                    st.session_state[delete_key] = False
                    st.rerun()
            elif ecol2.button("Delete", key=f"delete-{a.id}", use_container_width=True):
                st.session_state[delete_key] = True
                st.rerun()
        for t in visible:
            checked = st.checkbox(f"{t.title} - ~{t.hours:g}h", value=t.done, key=f"task-{t.id}")
            if checked != t.done:
                push_undo("update task")
                set_task_done(t, checked)
                st.session_state.history[-1] = max(0, st.session_state.history[-1] + (.3 if checked else -.3))
                st.rerun()


def page_plan() -> None:
    page_header("Auto Study Plan", "Review the rolling 30-day study blocks Auto-Planner generated for you.", "Plan")
    total_h = sum(b.end - b.start for b in st.session_state.blocks)
    st.markdown(f"""<div class="card"><b>Generated for the next {HORIZON_DAYS} days</b><div class="faint">{len(st.session_state.blocks)} study blocks - {total_h:g} planned hours</div></div>""", unsafe_allow_html=True)
    render_overload_banner()
    if st.button("Build / refresh my study plan", type="primary", use_container_width=True):
        push_undo("refresh plan")
        generate_plan()
        st.rerun()
    st.download_button("Export this plan (.ics)", build_ics(), "auto-planner.ics", "text/calendar", use_container_width=True)
    by_date: dict[dt.date, list[Block]] = {}
    for b in st.session_state.blocks:
        by_date.setdefault(b.date, []).append(b)
    if not by_date:
        st.info("Add an assignment to generate study blocks.")
    for date in sorted(by_date):
        st.markdown(f"#### {date:%A, %b %d}")
        for b in sorted(by_date[date], key=lambda x: x.start):
            render_block(b, today_view=(date == TODAY))


def page_reminders() -> None:
    page_header("Reminders", "See urgent deadlines and overload warnings before they sneak up.", "Focus")
    render_overload_banner()
    active = [a for a in st.session_state.assignments if assignment_status(a) != "Done"]
    groups = [
        ("Overdue", [a for a in active if (a.due - TODAY).days < 0]),
        ("Due today", [a for a in active if (a.due - TODAY).days == 0]),
        ("Next 3 days", [a for a in active if 1 <= (a.due - TODAY).days <= 3]),
    ]
    shown = any(items for _, items in groups)
    if not shown:
        st.markdown("""<div class="empty-note">No urgent reminders right now.</div>""", unsafe_allow_html=True)
        return
    for title, items in groups:
        if not items:
            continue
        icon = "!" if title == "Overdue" else "T" if title == "Due today" else "3"
        st.markdown(f"""<div class="section-title"><div class="icon">{icon}</div><b>{title}</b></div>""", unsafe_allow_html=True)
        for a in sorted(items, key=lambda x: x.due):
            render_assignment_card(a, priority_score(a), compact=True)


def page_progress() -> None:
    page_header("Progress", "Watch completion, streaks, and study hours build over the week.", "Momentum")
    done = sum(t.done for t in st.session_state.tasks)
    total = len(st.session_state.tasks)
    pct = done / total if total else 0
    active_assignments = sum(1 for a in st.session_state.assignments if assignment_status(a) != "Done")
    due_week = sum(1 for a in st.session_state.assignments if assignment_status(a) != "Done" and 0 <= (a.due - TODAY).days <= 7)
    planned_week = sum(b.end - b.start for b in st.session_state.blocks if 0 <= (b.date - TODAY).days <= 7)
    done_assignments = sum(1 for a in st.session_state.assignments if assignment_status(a) == "Done")
    st.markdown(f"""<div class="hero"><div class="k">This plan</div><div class="b">{done}/{total} tasks - {pct:.0%}</div><div class="s">{compute_streak()} day streak - {sum(st.session_state.history):g}h this week</div></div>""", unsafe_allow_html=True)
    st.progress(pct)
    st.markdown(
        f"""<div class="stat-grid">
        <div class="stat-card"><b>{active_assignments}</b><span>active assignments</span></div>
        <div class="stat-card"><b>{due_week}</b><span>due this week</span></div>
        <div class="stat-card"><b>{planned_week:g}h</b><span>planned next 7 days</span></div>
        <div class="stat-card"><b>{done_assignments}</b><span>assignments done</span></div>
        </div>""",
        unsafe_allow_html=True,
    )
    if active_assignments:
        st.markdown("""<div class="section-title"><div class="icon">N</div><b>Next up</b></div>""", unsafe_allow_html=True)
        for a in sorted([a for a in st.session_state.assignments if assignment_status(a) != "Done"], key=lambda x: (x.due, -priority_score(x)))[:3]:
            render_assignment_card(a, priority_score(a), compact=True)
    labels = [(TODAY - dt.timedelta(days=6 - i)).strftime("%a") for i in range(7)]
    st.markdown("""<div class="section-title"><div class="icon">H</div><b>Study hours</b></div>""", unsafe_allow_html=True)
    st.bar_chart(pd.DataFrame({"hours": st.session_state.history}, index=labels), color=BRAND, height=220)


def page_account() -> None:
    page_header("Account", "Manage sign-in and saving so your planner follows you.", "Settings")
    auth = st.session_state.get("auth")
    if not auth:
        st.info("You are in guest mode. Sign up to save your planner automatically.")
        if st.button("Sign up / log in", type="primary", use_container_width=True):
            st.session_state.pending_guest_snapshot = snapshot()
            st.session_state.guest = False
            st.rerun()
        st.divider()
        render_data_tools(auth, "account-data")
        return
    st.caption(f"Signed in as {auth.get('email')}")
    with st.form("account_form"):
        new_email = st.text_input("New email", placeholder="leave blank to keep current")
        new_password = st.text_input("New password", type="password", placeholder="leave blank to keep current")
        if st.form_submit_button("Update account", use_container_width=True):
            try:
                update_account(new_email or None, new_password or None)
                st.success("Account update submitted. Email changes may need confirmation.")
            except Exception as exc:
                st.error(f"Could not update account: {exc}")
    st.divider()
    render_data_tools(auth, "account-data")
    if st.button("Log out", use_container_width=True):
        sign_out()
        st.rerun()


sync_page_from_query()
sidebar()
maybe_auto_refresh_feeds()
st.session_state.top_page = st.session_state.active_page
st.selectbox("Quick jump", PAGES, key="top_page", on_change=sync_page_from_top)
render_action_bar()

ROUTES = {
    "Dashboard": page_dashboard,
    "Schedule": page_schedule,
    "Calendar": page_calendar,
    "Calendar Sync": page_calendar_sync,
    "Assignments": page_tasks,
    "Import": page_import,
    "Study Plan": page_plan,
    "Reminders": page_reminders,
    "Progress": page_progress,
    "Account": page_account,
}

ROUTES[st.session_state.active_page]()
autosave()
if st.session_state.get("_save_error"):
    st.warning(f"Auto-save could not reach Supabase: {st.session_state._save_error}")
elif st.session_state.get("auth"):
    st.caption("Auto-Planner - saved to your account.")
else:
    st.caption("Auto-Planner - guest mode, not saved.")
