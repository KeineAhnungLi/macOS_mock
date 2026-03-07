# Shared Browser Access

If you do not have a Mac for native packaging yet, the fastest way to let Mac users use TEM8Practice is to host the site on a Windows machine and let them open it in a browser.

## Start shared access

```powershell
.\start_share.ps1
```

This binds the site to `0.0.0.0` and prints the reachable LAN URLs.

## What Mac users should open

```text
http://YOUR_WINDOWS_LAN_IP:PORT/?progress=local
```

Example:

```text
http://192.168.1.23:8000/?progress=local
```

## Why `?progress=local`

- each browser keeps its own progress
- users do not overwrite each other when sharing one server
- no Mac packaging is required

## Browser requirement

- Safari works
- Chrome works
- if Chrome is missing, the site still works in the default browser
