# Install Auto-Planner On iPhone

Auto-Planner is currently an installable web app. It runs in Safari like an app
and can be added to your iPhone Home Screen.

## Local Testing On This Computer

For the easiest test, double-click:

```text
Start Auto-Planner.bat
```

That opens `http://localhost:8600` on your computer only. It does not show your
Wi-Fi IP address.

## Local Testing On iPhone

1. Make sure your computer and iPhone are on the same Wi-Fi.
2. Double-click `Start Auto-Planner for iPhone.bat` on the computer.
3. In the launcher window, look for the iPhone URL. It looks like:

```text
http://192.168.x.x:8600
```

4. Open that URL in Safari on the iPhone.

Do not use `localhost` on the iPhone. On the phone, `localhost` means the phone
itself, not your computer.

The Wi-Fi IP is not a public website address. It is only shown so your iPhone can
reach the app running on your computer.

## Add To Home Screen

1. Open Auto-Planner in Safari.
2. Tap the Share button.
3. Tap `Add to Home Screen`.
4. Name it `Auto-Planner`.
5. Tap `Add`.

The icon will open Auto-Planner in a standalone app-style window.

## Best Public Test

For classmates or testing away from your Wi-Fi, deploy to Streamlit Community
Cloud and add the deployed HTTPS URL to the Home Screen instead of the local IP.

## Current Limits

- This is not an App Store native app yet.
- It needs internet/network access to load.
- A hard browser refresh may ask you to log in again, but signed-in planner data
  remains saved in Supabase.
