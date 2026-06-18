# Auto-Planner

Your classes, deadlines, and study time automatically organized into a plan that
actually fits your week, with export to Google, Apple, or Outlook Calendar.

Auto-Planner is a self-organizing study planner for busy students. It scores
assignments by priority, breaks big work into study tasks, and places study
blocks into open time around classes, work, clubs, meals, and breaks.

## Easiest Way To Test

Double-click:

```text
Start Auto-Planner.bat
```

It opens the app on this computer:

```text
http://localhost:8600
```

This is the safest local test. It does not show your Wi-Fi IP address and it
does not publish the app to the internet. Close the black window to stop the app.

## Test On iPhone

Only use this when you want to test from your iPhone on the same Wi-Fi:

```text
Start Auto-Planner for iPhone.bat
```

That launcher shows an iPhone URL like:

```text
http://192.168.x.x:8600
```

That number is your computer's private Wi-Fi address. It is only shown so your
iPhone can reach the app running on your computer. It is not a public website
address.

For public testing away from your Wi-Fi, deploy to Streamlit Community Cloud.
That gives you a normal HTTPS link.

Auto-Planner also includes Home Screen app metadata. Open it in Safari, tap
Share, then tap **Add to Home Screen**. See `TESTING.md` and `MOBILE_APP.md`.

## Import Assignments

Open the **Import** page and use any of four ways. Each one drops into a review
table where you confirm dates and set effort before importing:

- **Paste text**: paste a syllabus chunk, email, or notes. The app detects dates
  like `June 22`, `6/18`, and `2026-07-01`.
- **Upload .ics**: import calendar exports from Google, Apple, Outlook, Canvas,
  or other school systems.
- **Calendar feed URL**: paste a live ICS feed from Canvas, Google Calendar, or
  Outlook.
- **Upload CSV**: columns `title, course, due, hours`; only title and due are
  required.

## Calendar Sync

- **Export plan (.ics)** downloads due dates and generated study blocks.
- **Add to Google Calendar** creates a quick-add link for the next suggested
  study block.

Study blocks import as timed events with reminders. Due dates import as all-day
calendar items.

## Accounts And Saving

Sign up with email and password and your planner saves automatically to your
Supabase account. Guest mode lets you try everything without an account, but
guest changes are not saved.

The sidebar includes:

- **Download my data** for a portable JSON copy.
- **Restore from a downloaded file** to load a saved copy.
- **Clear whole calendar** with a confirm step and undo backup.
- **Restore last backup** to undo a clear.
- **Reset to demo data** to start over with sample data.

Note: this Streamlit MVP may ask you to log in again after a hard browser
refresh. Your signed-in planner data is still saved to your account.

## Navigation

Use the top **Quick jump** selector to move between pages quickly, especially on
phones where the sidebar is tucked behind the menu. The sidebar still contains
the full controls for adding assignments, schedule commitments, export, and data.

## Main Features

- Dashboard overview.
- Schedule view for the next 7 days.
- Calendar page with agenda view and 12-month month-by-month browsing.
- Assignment management with edit and delete.
- Auto Study Plan for the next 30 days.
- Reminders and progress charts.
- Meal breaks, rest breaks, and recurring classes/work/clubs.
- Import from text, CSV, ICS upload, or ICS feed URL.
- Export to `.ics`.
- Installable Home Screen web app behavior on iPhone.

## How It Works

| Feature | What it does | Code |
|---|---|---|
| Priority scoring | Ranks assignments by importance, urgency, difficulty, and effort | `priority_score()`, `detect_type()` |
| Task breakdown | Splits exams, papers, projects, problem sets, and quizzes into focus tasks | `classify()`, `breakdown()` |
| Auto time-blocking | Plans the next 30 days into available schedule gaps | `free_slots()`, `generate_plan()` |
| 12-month calendar | Shows due dates, study blocks, and recurring commitments | `page_calendar()` |
| Auto reschedule | Moves missed blocks to the next open slot | `reschedule()` |
| Smart reminders | Builds reminders from deadlines and upcoming blocks | `reminders()` |
| Calendar export | Creates iCalendar files and Google Calendar quick-add links | `build_ics()`, `gcal_link()` |
| Smart import | Parses pasted text, ICS files, ICS feeds, and CSV files | `parse_text()`, `parse_ics()`, `fetch_feed()`, `parse_csv()` |

## Files

- `student_auto_planner.py`: the Streamlit app.
- `Start Auto-Planner.bat`: computer-only test launcher.
- `Start Auto-Planner for iPhone.bat`: same-Wi-Fi iPhone test launcher.
- `TESTING.md`: simple testing guide.
- `MOBILE_APP.md`: iPhone Home Screen instructions.
- `.streamlit/config.toml`: local server, static files, and theme settings.
- `.streamlit/secrets.toml.example`: Supabase secrets template.
- `DEPLOY.md`: Supabase setup and Streamlit Community Cloud deployment.
- `PROJECT_STATUS.md`: current build status and expected behavior.
- `requirements.txt`: Python dependencies.
- `index.html`: original standalone mobile UI mockup.

## Production Direction

The current app is a polished Streamlit MVP. A full native mobile version would
likely use React Native or Expo, Supabase, push notifications, and deeper Canvas
or Google Calendar sync. The current `.ics` export is the first practical bridge
to real calendar tools.
