# Local API-Sports Widget Scripts (Dev-Only)

If your browser blocks the CDN script with `net::ERR_BLOCKED_BY_ORB`, you can serve the widget script locally from the React dev server to avoid the cross-origin filter.

Place the files below under `frontend/public/vendor/api-sports/3.1.0/`:

- `player.js` (from <https://widgets.api-sports.io/3.1.0/player>)
- `team.js`   (from <https://widgets.api-sports.io/3.1.0/team>)

Quick download commands (PowerShell):

```powershell
# Run from repository root (Windows PowerShell)
New-Item -ItemType Directory -Force -Path .\frontend\public\vendor\api-sports\3.1.0 | Out-Null
Invoke-WebRequest -Uri https://widgets.api-sports.io/3.1.0/player -OutFile .\frontend\public\vendor\api-sports\3.1.0\player.js
Invoke-WebRequest -Uri https://widgets.api-sports.io/3.1.0/team -OutFile .\frontend\public\vendor\api-sports\3.1.0\team.js
```

How it works

- During development on localhost, the app tries the local files first.
- If a local file is missing or fails to load, it falls back to the CDN 3.1.0 path, and then to legacy 3.0.4.

Note: Do not commit the downloaded JS files if you do not have permission to redistribute them. Keep them local for development.
