# Auto-Planner — Project Handoff / Context

> **Purpose of this file:** a complete, self-contained briefing so any AI coding
> assistant (or developer) can continue this project without the original chat
> history. Paste this whole file in as context. Last updated while adding
> multi-user accounts (Supabase).

---

## 1. What this is

**Auto-Planner** is a self-organizing study planner for busy college students.
Unlike a to-do list, it **builds the study plan for you**: you enter/import your
classes, work shifts, clubs, and assignments, and it automatically scores
priorities, breaks big assignments into tasks, and time-blocks study sessions into
the free gaps in your real schedule (around classes and meals). It reschedules
missed work, warns when you're overloaded, and exports to your calendar.

**Target user:** a student juggling classes, homework, exams, clubs and a part-time
job. **Value prop:** "Your classes, deadlines & study time — automatically
organized into a plan that fits your week."

## 2. Tech stack & how to run

- **Language/Framework:** Python + **Streamlit** (single-file app).
- **Main file:** `student_auto_planner.py` (~1,380 lines).
- **Dependencies:** `requirements.txt` — streamlit, pandas, icalendar, requests,
  python-dateutil (and **supabase** once accounts land).
- **Run locally:**
  - Double-click `Start Auto-Planner.bat`, **or**
  - `streamlit run student_auto_planner.py`
- **Port:** 8600 (set in `.streamlit/config.toml`; 8501 was taken on the dev
  machine). The default launcher binds to `localhost` for computer-only testing.
  `Start Auto-Planner for iPhone.bat` intentionally binds to `0.0.0.0` so phones
  on the same Wi-Fi can use the computer's private Wi-Fi address. Theme (calm
  indigo `#5b6ef5`) is also in that config.
- **Today's date:** the app uses the real `dt.date.today()`; demo data is relative
  to it so it always looks populated.

## 3. File map

```
student_auto_planner.py   # the entire app (logic + UI)
Start Auto-Planner.bat    # computer-only double-click launcher
Start Auto-Planner for iPhone.bat # same-Wi-Fi iPhone test launcher
requirements.txt          # pip deps
.streamlit/config.toml    # port 8600, computer-only default bind + theme
static/                   # manifest + icons for Home Screen / installable web app
README.md                 # user-facing overview
HANDOFF.md                # THIS FILE
MOBILE_APP.md             # iPhone local testing + Add to Home Screen instructions
TESTING.md                # simple testing guide
index.html                # original standalone mobile mockup (not the real app)
samples/                  # sample import files (CSV, .ics)
data/                     # legacy local JSON saves / backups; git-ignored
```

## 4. Complete feature inventory (all built & working)

- **Priority scoring** — `priority_score()`:
  `importance·0.40 + urgency·0.38 + difficulty·0.14 + effort·0.08` → High/Med/Low.
  Importance (1–5) is auto-detected by `detect_type()` so **exams/finals rank high
  even when weeks away** (this was a real bug fix — they used to show as Low).
- **Auto task breakdown** — `breakdown()` / `classify()` / `STAGES`: splits an
  assignment into ~1.5h milestone tasks by type (exam → review/practice/summary/
  final review; paper → outline/draft/…; project; pset; quiz).
- **Auto time-blocking** — `generate_plan()`: schedules over a **30-day horizon**
  (`HORIZON_DAYS`). Sorts tasks by priority, places each into the earliest free
  slot **before its due date**, keyed by real dates. Inserts a **15-min break**
  (`BREAK`) between back-to-back blocks. Overdue work is scheduled today. Anything
  that can't fit is collected in `st.session_state.unscheduled` and surfaced as an
  **⚠️ overload warning** on the Dashboard and Plan pages.
- **Free-slot detection** — `free_slots()`: open windows (8am–10pm) left after
  fixed commitments **and meal breaks**.
- **Meal breaks** — `DEFAULT_MEALS` (breakfast/lunch/dinner) reserved so study is
  never scheduled over meals; editable in the sidebar (`meal_windows()`).
- **Auto-reschedule** — `reschedule()`: a missed block moves to the next open slot.
- **Smart reminders** — `reminders()`: deadline + today's-block reminders, plus a
  **live study streak** (`compute_streak()` from `history`).
- **Import assignments** — `page_import()` + parsers, all feeding a review table
  (`st.data_editor`) before anything is created:
  - `parse_text()` — paste a syllabus/notes; regex+dateutil pulls due dates.
  - `parse_ics()` — upload any .ics (Google/Apple/Outlook/Canvas).
  - `fetch_feed()` — paste a live Canvas/Google calendar feed URL.
  - `parse_csv()` — upload a spreadsheet.
  - `commit_import()` — creates `Assignment`s and replans.
- **Calendar export** — `build_ics()` (study blocks + due dates, with alarms) and
  `gcal_link()` (one-click "Add to Google Calendar").
- **12-month calendar view** — `page_calendar()`: month-by-month browsing from the
  current month through 11 months ahead. Month cells show due dates first, then
  generated study blocks, then recurring classes/work/clubs, with compact overflow
  markers; day details add meals when enabled.
- **Installable mobile web app** — static manifest/icons plus injected iOS/Android
  metadata let users add Auto-Planner to the iPhone Home Screen from Safari.
- **Edit / delete assignments** — `page_tasks()`: each assignment has an ✏️ popover
  to edit fields or 🗑️ delete (delete snapshots first so Restore can undo).
- **Persistence (account-aware)** — `snapshot()` / `restore_snapshot()` serialize the
  inputs. Signed-in users autosave changed snapshots to Supabase; guests stay in
  memory unless they download a JSON copy. Clear keeps a backup; signed-in users
  also carry that backup in the Supabase JSON snapshot for durable undo.
- **"Feel real" layer** — editable display name, live streak, honest dashboard copy
  (real free-hours, "all done 🎉"), friendly empty state, ⚠️ overdue flags,
  `st.balloons()` when the day is finished, study-hours that decrement on uncheck.

## 5. Architecture map

**Data model (dataclasses):**
- `Fixed(day, start, end, title, kind)` — a class/work/club/meal (recurring by
  weekday; `start`/`end` are 24h floats, e.g. 14.5 = 2:30pm).
- `Assignment(id, title, course, due, hours, diff, color, weight)` — `weight` is
  importance 1–5.
- `Task(id, assign_id, title, course, color, hours, due, order, done)` — a
  milestone sub-task (derived from an Assignment).
- `Block(day, start, end, title, course, color, task_id, date)` — a scheduled study
  session on a specific `date` (derived).

**State:** everything lives in `st.session_state` (`assignments`, `fixed`, `tasks`,
`blocks`, `meals`, `history`, `unscheduled`, `user`, etc.). `tasks`/`blocks` are
**derived** — `generate_plan()` rebuilds them; only inputs are persisted.

**Pages / routing:** synced sidebar and top "Quick jump" navigation set
`st.session_state.active_page`; `ROUTES` maps label → `page_*()` function
(`page_dashboard`, `page_schedule`, `page_tasks`, `page_import`, `page_calendar`,
`page_plan`, `page_reminders`, `page_progress`). `render_block()` is the shared
study-block row (checkbox + reschedule).

**Execution order (top to bottom):** config/theme → dataclasses → logic functions →
persistence helpers → `Init` block (seed or load) → `with st.sidebar:` (nav + add
forms + data controls) → `ROUTES[page]()` → `autosave()`.

## 6. CURRENT TASK — multi-user sign-up (Supabase). Status: CODE ADDED

Goal: let other students **sign up / log in** and have their **own saved plan**,
keep a **guest demo** (unsaved), and deploy on Streamlit Community Cloud. Approach
keeps Streamlit (no rewrite); only swaps the storage target from a local file to a
**per-user Supabase row**, wrapped in a login gate. Reuses `snapshot()` /
`restore_snapshot()`.

**Backend:** Supabase (Auth + Postgres). **Sign-in:** email + password. **Guest:**
in-memory demo, not saved.

**Supabase setup the owner must do once** (then paste URL + anon key into
`.streamlit/secrets.toml`):
```sql
create table public.planners (
  user_id uuid primary key references auth.users(id) on delete cascade,
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz default now()
);
alter table public.planners enable row level security;
create policy "own planner" on public.planners
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
```

**Implementation status:**
The app now includes Supabase helpers, a login/sign-up/guest gate, account-aware
init/autosave, sidebar account controls, deployment docs, a secrets template, and
`PROJECT_STATUS.md`. The owner still needs to create the Supabase project, run the
SQL below, and paste secrets before live account testing.

**Implementation outline:**
1. `requirements.txt` += `supabase>=2.0`; `.streamlit/secrets.toml` (git-ignored)
   with `SUPABASE_URL`/`SUPABASE_ANON_KEY` (+ a `.example`); `.gitignore`.
2. Backend helpers: `get_sb()` (per-session client in `st.session_state.sb` — NOT a
   global cached resource, to avoid sharing auth tokens), `sign_up`, `sign_in`
   (store `st.session_state.auth = {id,email,token}`, set `postgrest.auth(token)`),
   `sign_out`, `load_user_data(uid)`, `save_user_data(uid)` (upsert jsonb snapshot).
3. Login gate after the CSS block: tabs Log in / Sign up + "Try as guest"; `st.stop()`
   until authed or guest.
4. Init + autosave become account-aware: logged-in loads/saves Supabase
   (save only when `json.dumps(snapshot())` changed vs `st.session_state._last_saved`);
   guests in-memory only.
5. Sidebar account UI: email + Log out, or guest "sign up to save" nudge.
6. `DEPLOY.md` + README update.

**Security:** only the **anon** key client-side; RLS enforces per-user isolation;
passwords handled by Supabase (never stored by us). Per-session client prevents
cross-user token bleed.

## 7. Known decisions & constraints

- **Why Streamlit:** the app already exists in it and ships fast; good for personal
  use + portfolio. A real consumer product with polished mobile UX would eventually
  be a Next.js + Supabase rewrite — deliberately deferred.
- **Why Supabase:** Streamlit Cloud's filesystem is ephemeral, so local JSON won't
  persist there; Supabase gives hosted Postgres + Auth on a free tier.
- **Streamlit caveat:** a hard browser refresh resets `st.session_state`, so a user
  is logged out on refresh until "stay logged in" cookies are added (a planned
  follow-up via `extra-streamlit-components`).

## 8. Follow-ups / backlog (not yet built)

- Stay-logged-in across refresh (cookie-stored Supabase session).
- Password reset + email verification UX; optional Google sign-in.
- Real push notifications (needs a hosted backend/worker).
- Stay-logged-in across hard refresh; richer analytics.
- Possible eventual Next.js + Supabase rewrite for a true mobile app feel.

## 9. How to verify after changes

- `python -m py_compile student_auto_planner.py` → must be clean.
- Headless render test of all pages via `streamlit.testing.v1.AppTest` (set
  `guest=True` to avoid needing network).
- `streamlit run student_auto_planner.py` → load http://localhost:8600 → HTTP 200.
- For auth: sign up, add an assignment, log out, log back in → data persists;
  second user sees a fresh plan (RLS working).
