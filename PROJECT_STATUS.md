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
- Account page exposes data download/restore/undo/backup tools so mobile users
  do not need the sidebar for planner data management.
- Clearing the whole calendar now requires a confirmation step before deleting
  assignments, commitments, and generated blocks.
- Deleting a single assignment now requires confirmation inside the edit popover
  to prevent accidental taps on mobile.
- One-tap "Missed? Reschedule" on today's study blocks.
- Loud overload banner when work cannot fit before deadlines.
- Friendlier CSV/ICS import errors.
- Top-level Calendar Sync page for Canvas, Google Calendar, Outlook, iCal, and
  `webcal://` links. Saved feeds can refresh automatically once per app session
  and can be refreshed manually from the Calendar Sync page.
- Feed-created assignments track their source/event ID so refreshed calendar
  events update instead of duplicating.
- `.ics` export for generated study blocks and all assignment due dates.
- Mobile-friendly Quick jump navigation.
- Mobile action bar for Today, Calendar, Add, and Plan so phone users do not need
  the sidebar for common navigation.
- Mobile action bar includes a Sync shortcut so students do not need the sidebar
  to connect calendar feeds.
- Compact quick-nav strip for Today, Week, Calendar, Add, Sync, and Plan with
  URL-backed page links that work on mobile and desktop.
- Add quick action opens directly to the assignment form, Calendar quick action
  opens the month grid, and empty Dashboard users get clear Add/Import starts.
- Larger touch targets and custom Inter-based styling.
- Warm off-white/teal/indigo theme in `.streamlit/config.toml`.
- Polished dashboard stat cards and a quick-add assignment panel.
- Compact phone-friendly month grid with persistent Agenda/Month view state,
  visible due/study/fixed color legend, and compressed tappable day cells.
  Selected-day details appear above the grid immediately after tapping a date.
- Clean tapped-day plan panel with summary badges and separate Due, Study Plan,
  Commitments, and Meals sections.
- More touch-friendly study block cards with clearer status/time badges and a
  full-width missed/reschedule action on today's blocks.
- Study block cards include an "Add to Google Calendar" link for quickly copying
  an individual block into Google Calendar.
- Cleaner assignment cards on Dashboard and Assignments with responsive badges,
  due timing, and task progress bars.
- Reminders page groups active work into Overdue, Due today, and Next 3 days,
  while completed assignments stay out of urgent reminders.
- Consistent polished page headers across the main app pages with short
  subtitles explaining each section's purpose.
- Progress page now includes active assignment, due-this-week, planned-hours,
  completed-assignment stats plus a compact Next up list.
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
  saved calendar feed URLs, and CSV files.
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
- Direct private iPhone/Apple Calendar sync is not built yet. The current path is
  connecting a shareable/subscribed iCloud/Google/Outlook/Canvas iCal feed URL.
- Swipe-to-open sidebar was removed because Streamlit on iPhone reformatted the
  layout instead of reliably opening/closing the menu. The app relies on visible
  Quick jump/action-bar navigation instead.
- Native App Store app is not built; current mobile install is a Home Screen web
  app.
- Streamlit Community Cloud deployment and multi-account smoke testing still need
  to be done after pushing the repo.
