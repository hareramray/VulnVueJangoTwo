# VulnShop — deliberately vulnerable Vue + Django training lab

> ⚠️ **Every bug in this repository is intentional.** It exists to practise
> finding and fixing the OWASP-style issues below in a safe, local sandbox —
> the same idea as DVWA / OWASP Juice Shop / WebGoat. **Never deploy it on a
> public or shared network, and only test against your own instance.**

A Django REST-ish backend and a Vue 3 frontend, each endpoint/panel mapped to
one test area. The full break-and-fix walkthrough is in
[`docs/Break_and_Fix_Guide.pdf`](docs/Break_and_Fix_Guide.pdf).

## Coverage

| # | Test area | Where | Marker |
|---|-----------|-------|--------|
| 1 | Authentication (weak hash, no policy, bad reset) | `views.register/login/forgot_password/reset_password` | `[VULN-01-AUTH]` |
| 2 | Access control (IDOR) | `views.get_order/delete_order` | `[VULN-02-ACCESS]` |
| 3 | Session management (no server-side logout) | `views.logout_view`, cookie settings | `[VULN-03-SESSION]` |
| 4 | SQL injection (raw string query) | `views.search_orders` | `[VULN-04-SQLI]` |
| 5 | XSS — stored & reflected | `views.comments/greet`, `v-html` in frontend | `[VULN-05-XSS]` |
| 6 | CSRF (disabled middleware) | `views.change_email`, `docs/csrf-poc.html` | `[VULN-06-CSRF]` |
| 7 | File upload & path traversal | `views.upload/download` | `[VULN-07-FILES]` |
| 8 | SSRF (import from URL) | `views.import_url` | `[VULN-08-SSRF]` |
| 9 | Business logic (client-set price, reusable coupon) | `views.checkout` | `[VULN-09-LOGIC]` |
| 10 | API over-exposure (hidden fields) | `views.list_users` | `[VULN-10-API]` |
| 11 | Config / info disclosure (DEBUG, headers, CORS, debug endpoint) | `settings.py`, `middleware.py`, `views.debug_info` | `[VULN-11-CONFIG]` |

## Run it

### Backend (Django)
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python seed.py                      # demo users: alice/123456, bob/password, admin/admin
python manage.py runserver 127.0.0.1:8000
```

### Frontend (Vue 3, no build step)
The frontend is a single CDN-based page. Serve it over http (not file://) so
cookies behave:
```bash
cd frontend
python -m http.server 5173
# open http://127.0.0.1:5173
```

## How to use the lab
1. Open the frontend, read each card, and try the suggested payload.
2. Open `docs/Break_and_Fix_Guide.pdf` for the exploit steps **and the fix** for
   every item (frontend and backend).
3. Try to apply the fixes yourself — each `[VULN-...]` comment describes the
   secure pattern right next to the vulnerable code.

## Resetting
Delete `backend/db.sqlite3` and the `backend/media/` folder, then re-run
`migrate` + `seed.py`.
