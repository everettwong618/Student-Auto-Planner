# Deploy Auto-Planner

This app runs on Streamlit and uses Supabase for student accounts and cloud saves.

## 1. Create Supabase

1. Create a free project at https://supabase.com.
2. Go to Authentication -> Sign In / Providers.
3. Under User Signups, keep `Allow new users to sign up` enabled.
4. For faster testing, turn off `Confirm email`. If it stays on, new users must
   confirm their email before they can log in.
5. Open SQL Editor and run:

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

6. Copy the Project URL and anon public key from Settings -> API.

## 2. Run Locally

Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "your-anon-public-key"
```

For the easiest private test, double-click:

```text
Start Auto-Planner.bat
```

That opens:

```text
http://localhost:8600
```

This mode is computer-only. It does not show your Wi-Fi IP address and it does
not publish the app to the internet.

If you prefer the command line, run:

```bash
streamlit run student_auto_planner.py
```

The app is configured to use port `8600`.

To test from an iPhone on the same Wi-Fi, double-click:

```text
Start Auto-Planner for iPhone.bat
```

That launcher prints the iPhone URL:

```text
http://YOUR-IPV4-ADDRESS:8600
```

That IP address is your computer's private Wi-Fi address, not a public website
address. It is only shown so your phone can reach the app running on your
computer.

If the phone cannot connect, allow Python/Streamlit through Windows Firewall or
deploy to Streamlit Community Cloud and test the public URL.

To install it like an app on iPhone, open the local or deployed URL in Safari,
tap Share, then tap `Add to Home Screen`.

## 3. Deploy To Streamlit Community Cloud

1. Push this folder to GitHub.
2. Create a new Streamlit app from the repo.
3. Set the main file to `student_auto_planner.py`.
4. In the Streamlit app settings, paste the two secrets:

```toml
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "your-anon-public-key"
```

5. Deploy.

## 4. Smoke Test

1. Open the deployed URL.
2. Click `Try as guest` and confirm the demo planner loads.
3. Create an account, add or edit one assignment, then log out.
4. Log back in and confirm the change persists.
5. Create a second test account and confirm it starts with its own planner.
