# Maintenance Page & Nginx Example

If Odoo is down (HTTP 500 / registry failure) it's better to display a friendly maintenance page via the fronting web server (nginx) rather than exposing raw 500 pages.

## Simple static maintenance page
Create a static `maintenance.html` and configure nginx to serve it for your site when the upstream is down.

### Example `maintenance.html`
Saved in `/srv/www/maintenance/maintenance.html` (example):

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Site Maintenance</title>
  <style>
    body { font-family: Arial, sans-serif; text-align: center; padding: 6rem; background:#f5f6f8 }
    .card { max-width: 680px; margin: 3rem auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.08) }
    h1 { color:#333 }
    p { color:#666 }
    .time { margin-top: 1.25rem; font-size: .95rem; color:#999 }
  </style>
</head>
<body>
  <div class="card">
    <h1>We’re performing maintenance</h1>
    <p>Thanks for your patience — our services are temporarily unavailable while we apply important fixes. Please try again in a few minutes.</p>
    <div class="time">Last updated: 2025-12-23</div>
  </div>
</body>
</html>
```

### Example nginx config snippet that serves maintenance when Odoo is down
Place this in your server block; it uses `proxy_next_upstream off` to let nginx detect backend failure and fall back to static maintenance file for 502/504/500.

```nginx
server {
  listen 80;
  server_name example.com;

  root /srv/www/maintenance;

  location / {
    proxy_pass http://127.0.0.1:8069;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;

    # Failover to static maintenance page on upstream error
    proxy_next_upstream error timeout http_500 http_502 http_503 http_504;
    proxy_intercept_errors on;
    error_page 500 502 503 504 = /maintenance.html;
  }

  location = /maintenance.html {
    internal;
    root /srv/www/maintenance;
  }
}
```

## Deploy steps
1. Create `/srv/www/maintenance/maintenance.html` with the content above.
2. Add config snippet to your nginx server block and test: `sudo nginx -t`.
3. Reload nginx: `sudo systemctl reload nginx`.

This does not fix the underlying KeyError but provides a clean visual for users until the registry is repaired. Combine this with the emergency containment steps to bring Odoo back online quickly.
