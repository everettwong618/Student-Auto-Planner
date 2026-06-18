# Simple Testing Guide

## Fastest Test

Double-click:

```text
Start Auto-Planner.bat
```

That opens the app on this computer only:

```text
http://localhost:8600
```

This is the safest local test. It does not show your Wi-Fi IP address and it
does not publish the app to the internet.

## iPhone Test

Only use this when you want to test from your iPhone on the same Wi-Fi:

```text
Start Auto-Planner for iPhone.bat
```

That window shows an iPhone URL like:

```text
http://192.168.x.x:8600
```

That number is your computer's Wi-Fi address on your private network. It is only
shown so your phone can connect to the app running on your computer. It is not a
public website address.

If the iPhone cannot connect:

1. Make sure the computer and iPhone are on the same Wi-Fi.
2. Keep the launcher window open.
3. Allow Python or Streamlit through Windows Firewall if Windows asks.
4. Try again with the newest iPhone URL shown in the launcher.

## Public Test

For testing away from home Wi-Fi, use Streamlit Community Cloud. That gives you a
normal public HTTPS link, and students do not need your home Wi-Fi IP address.
