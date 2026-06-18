# Auto-Planner Project Status

## Current Build Status

Auto-Planner is a Streamlit MVP with accounts, cloud saving, smart scheduling,
calendar browsing, mobile-friendly navigation, and installable web-app metadata.

Important note: on June 18, 2026 the source file was rebuilt cleanly after an
encoding/write failure damaged the previous `student_auto_planner.py`. The app is
again editable UTF-8 source and compiles successfully.

## Done

- Email/password sign up and login through Supabase.
- Guest mode for trying the app without saving.
- Per-user planner saves in Supabase using `snapshot()` / `restore_snapshot()`.
- Account-aware autosave for signed-in users.
- Password reset trigger from the login screen.
- Minimal Account page for email/password updates.
- 30-day rolling auto-study plan.
- 12-month Calendar page with Agenda and Month grid views.
- Recurring weekly classes/work/clubs in the sidebar.
- Assignment status tracking: Not Started, In Progress, Done.
- Persisted completed task IDs so progress survives replans and saves.
- Single-level undo for common edits, deletes, imports, clears, and schedule changes.
- One-tap "Missed? Reschedule" on today's study blocks.
- Loud overload banner when work cannot fit before deadlines.
- Friendlier CSV/ICS import errors.
- `.ics` export for generated study blocks and all assignment due dates.
- Mobile-friendly Quick jump navigation.
- Larger touch targets and custom Inter-based styling.
- Warm off-white/teal/indigo theme in `.streamlit/config.toml`.
- PWA manifest/icons for iPhone Home Screen install.
- Safer testing launchers:
  - `Start Auto-Planner.bat` for computer-only local testing.
  - `Start Auto-Planner for iPhone.bat` for same-Wi-Fi phone testing.

## What The App Should Do

Auto-Planner should help students turn assignments, classes, work, clubs, and
meals into a realistic study plan.

Core behavior:

- Let a student add assignments with due dates, effort, difficulty, importance,
  and status.
- Import assignments from pasted text, `.ics` calendar files, calendar feed URLs,
  and CSV files.
- Score work by urgency, importance, effort, and difficulty.
- Break large assignments into smaller study tasks.
- Schedule study blocks into free time around fixed commitments and meal breaks
  for the next 30 days.
- Browse the current month through 11 months ahead.
- Show overload warnings when work cannot fit before deadlines.
- Let students mark a block missed and reschedule it.
- Export the study plan as an `.ics` calendar file.
- Save each signed-in student's planner privately.

## Still Open

- True stay-signed-in persistence across hard browser refresh still needs a
  browser cookie/local-storage component. Current refresh-token handling only
  helps while Streamlit session state remains alive.
- Real-world feed testing should still be done with live Canvas, Google Calendar,
  and Outlook feeds.
- Native App Store app is not built; current mobile install is a Home Screen web
  app.
- Streamlit Community Cloud deployment and multi-account smoke testing still need
  to be done after pushing the repo.
