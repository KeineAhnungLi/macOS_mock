# Cloud Deployment

## Modes

- Local mode: unchanged. If `apiBaseUrl` is empty, the app keeps using the local bundled server and `data/user_progress.json`.
- Cloud mode: static files can be hosted on COS/CDN, while `/api/*` is served by your own server domain.

## What changed

- Frontend can now read `window.TEM8_CONFIG.apiBaseUrl`.
- When `apiBaseUrl` is set, the browser sends a stable per-browser `X-TEM8-Client-ID`.
- Backend now supports CORS and stores cloud progress per client in:
  - `data/clients/<client_id>.json`

## Static hosting on COS/CDN

Upload the contents of [app/static](c:\Users\HW\Desktop\专八练习网\app\static) to your COS bucket root.

Before uploading, edit:

- [config.js](c:\Users\HW\Desktop\专八练习网\app\static\assets\config.js)

Example:

```js
window.TEM8_CONFIG = {
  apiBaseUrl: "https://api.example.com",
  clientId: "",
};
```

Reference template:

- [config.example.js](c:\Users\HW\Desktop\专八练习网\app\static\assets\config.example.js)

Then let your CDN/domain serve:

- `https://learn.example.com/index.html`
- `https://learn.example.com/assets/...`

## API server deployment

Run the existing Python server on your own server and bind it behind your domain.

Important environment variable:

```bash
export TEM8_ALLOWED_ORIGINS="https://learn.example.com,https://cdn.example.com"
```

If you want to allow every origin during testing:

```bash
export TEM8_ALLOWED_ORIGINS="*"
```

Then start the server:

```bash
python run.py --host 0.0.0.0 --port 8000
```

Or:

```bash
python gateway.py --host 0.0.0.0 --port 8000 --no-browser
```

Your reverse proxy/domain should expose the API as:

- `https://api.example.com/api/exams`
- `https://api.example.com/api/progress`
- `https://api.example.com/api/events`

## How client progress works in cloud mode

- Each browser gets an automatic persistent client ID.
- Progress is saved in a separate file per client.
- Local browser cache is still kept as a fallback merge source.
- If you need one user to share progress across multiple devices, give them the same `clientId` explicitly in `config.js` or via query string `?client=...`.

## Quick test without uploading

You can test the split setup locally:

1. Run the API server on your machine.
2. Open the static page with a custom API base:

```text
file:///.../app/static/index.html?api=http://127.0.0.1:8000
```

Or after uploading to any static host:

```text
https://your-static-host/index.html?api=https://api.example.com
```

## Notes

- Local packaged exe/setup remains compatible.
- Cloud mode is opt-in. It only activates when `apiBaseUrl` is set.
- Event logs remain in:
  - `logs/events.jsonl`
