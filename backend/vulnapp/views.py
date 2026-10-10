"""
Vulnerable API views.  Every endpoint is annotated with the weakness it
demonstrates ([VULN-NN-...]) and, in a comment, the corresponding fix.

These are TRAINING TARGETS. The matching secure patterns are described in
docs/Break_and_Fix_Guide.pdf.  Do not copy these into real software.
"""
import json
import os
import socket
import urllib.request

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import connection
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Comment, Coupon, Order, PasswordResetToken, Profile


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def body_json(request):
    try:
        return json.loads(request.body.decode() or "{}")
    except Exception:
        return {}


def ok(data=None, **extra):
    payload = {"ok": True}
    if data is not None:
        payload["data"] = data
    payload.update(extra)
    return JsonResponse(payload)


def err(message, status=400):
    return JsonResponse({"ok": False, "error": message}, status=status)


# ==========================================================================
# 1. AUTHENTICATION
# ==========================================================================
@csrf_exempt
def register(request):
    data = body_json(request)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return err("username and password required")
    if User.objects.filter(username=username).exists():
        return err("user exists")
    # [VULN-01-AUTH] No password policy (validators disabled in settings) and
    #   passwords are stored with MD5. Fix: enforce validators + strong hasher.
    user = User.objects.create_user(username=username, password=password)
    Profile.objects.create(user=user, full_name=data.get("full_name", ""))
    return ok({"id": user.id, "username": user.username})


@csrf_exempt
def login_view(request):
    data = body_json(request)
    user = authenticate(
        request, username=data.get("username"), password=data.get("password")
    )
    if user is None:
        # [VULN-01-AUTH] No rate limiting / lockout -> unlimited credential
        #   stuffing & brute force. Fix: throttle + lockout + generic errors.
        return err("invalid credentials", status=401)
    login(request, user)
    return ok({"username": user.username})


@csrf_exempt
def forgot_password(request):
    """[VULN-01-AUTH] Issues a weak, non-expiring, reusable reset token AND
    returns it directly in the HTTP response (so no email control is needed).
    Fix: email a high-entropy token, store only its hash, expire it quickly
    and mark it single-use."""
    data = body_json(request)
    try:
        user = User.objects.get(username=data.get("username"))
    except User.DoesNotExist:
        return err("no such user", status=404)
    # Predictable token: just the user id reversed + fixed salt.
    token = f"{user.id}reset"
    PasswordResetToken.objects.create(user=user, token=token)
    return ok({"reset_token": token}, hint="use POST /api/reset-password")


@csrf_exempt
def reset_password(request):
    data = body_json(request)
    token = data.get("token", "")
    try:
        prt = PasswordResetToken.objects.filter(token=token).latest("created")
    except PasswordResetToken.DoesNotExist:
        return err("bad token", status=400)
    # [VULN-01-AUTH] 'used' and 'created' are never checked: the link works
    #   forever and can be replayed. Fix: verify not used and not expired,
    #   then set prt.used = True atomically.
    prt.user.set_password(data.get("new_password", ""))
    prt.user.save()
    return ok(msg="password changed")


def whoami(request):
    if not request.user.is_authenticated:
        return err("not logged in", status=401)
    return ok({"username": request.user.username, "id": request.user.id})


# ==========================================================================
# 2. ACCESS CONTROL  (IDOR)
# ==========================================================================
def get_order(request, order_id):
    """[VULN-02-ACCESS] Returns any order by id with no ownership check, so
    customer A can read customer B's order by changing the id (IDOR).
    Fix: filter by owner=request.user (or verify ownership) and 404 otherwise."""
    try:
        o = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return err("not found", status=404)
    return ok({
        "id": o.id, "owner": o.owner.username, "item": o.item,
        "price_cents": o.price_cents, "quantity": o.quantity, "status": o.status,
    })


@csrf_exempt
def delete_order(request, order_id):
    """[VULN-02-ACCESS] Any authenticated user can delete anyone's order.
    Fix: require ownership (or an admin role) before mutating."""
    Order.objects.filter(id=order_id).delete()
    return ok(msg="deleted")


# ==========================================================================
# 3. SESSION MANAGEMENT
# ==========================================================================
@csrf_exempt
def logout_view(request):
    """[VULN-03-SESSION] Pretends to log out but does NOT call Django's
    logout(), so the server-side session stays valid and the cookie keeps
    working. Fix: call logout(request) to flush the session server-side."""
    # logout(request)   # <-- intentionally commented out
    resp = ok(msg="logged out (client thinks so)")
    return resp


# ==========================================================================
# 4. SQL INJECTION
# ==========================================================================
def search_orders(request):
    """[VULN-04-SQLI] Builds a raw SQL string from the 'q' query param.
    Try:  /api/search?q=x' OR '1'='1
    Fix: use parameterised queries / the ORM, never string concatenation."""
    q = request.GET.get("q", "")
    sql = (
        "SELECT id, item, status FROM vulnapp_order "
        f"WHERE item LIKE '%{q}%'"
    )
    rows = []
    with connection.cursor() as cur:
        try:
            cur.execute(sql)
            rows = [
                {"id": r[0], "item": r[1], "status": r[2]} for r in cur.fetchall()
            ]
        except Exception as e:
            # [VULN-11-CONFIG] Leaks the raw SQL error (and thus the query) to
            #   the client. Fix: log server-side, return a generic message.
            return err(f"SQL error: {e} :: query was: {sql}", status=500)
    return ok(rows, executed_sql=sql)


# ==========================================================================
# 5. CROSS-SITE SCRIPTING (stored + reflected)
# ==========================================================================
@csrf_exempt
def comments(request):
    if request.method == "POST":
        data = body_json(request)
        # [VULN-05-XSS] Stores raw HTML/JS with no sanitisation. The Vue
        #   frontend renders it with v-html -> stored XSS for every viewer.
        #   Fix: sanitise on input (allow-list) AND escape on output.
        c = Comment.objects.create(
            author=data.get("author", "anon"),
            body=data.get("body", ""),
        )
        return ok({"id": c.id})
    items = [
        {"id": c.id, "author": c.author, "body": c.body,
         "created": c.created.isoformat()}
        for c in Comment.objects.order_by("-created")[:50]
    ]
    return ok(items)


def greet(request):
    """[VULN-05-XSS] Reflected XSS: echoes the 'name' param into an HTML
    response unescaped.  Try: /api/greet?name=<script>alert(1)</script>
    Fix: escape output (Django templates autoescape) / set correct content
    type / add a Content-Security-Policy."""
    name = request.GET.get("name", "guest")
    html = f"<h1>Hello, {name}!</h1>"
    return HttpResponse(html)  # text/html, unescaped


# ==========================================================================
# 6. CSRF
# ==========================================================================
@csrf_exempt
def change_email(request):
    """[VULN-06-CSRF] State-changing POST with csrf_exempt (and CSRF middleware
    disabled globally). Any site can forge this using the victim's cookie.
    Fix: remove csrf_exempt, enable CsrfViewMiddleware, require the token,
    and re-authenticate for sensitive changes."""
    if not request.user.is_authenticated:
        return err("not logged in", status=401)
    data = body_json(request)
    request.user.email = data.get("email", "")
    request.user.save()
    return ok(msg=f"email set to {request.user.email}")


# ==========================================================================
# 7. FILE UPLOADS & PATH TRAVERSAL
# ==========================================================================
@csrf_exempt
def upload(request):
    """[VULN-07-FILES] Accepts any file, keeps the client-supplied name, and
    writes it under MEDIA_ROOT with no type/size/extension checks, so a
    '.html'/'.svg' (stored XSS) or a traversal name like '../../x' is honoured.
    Fix: validate type/size, generate a random server-side name, store outside
    the web root and serve with Content-Disposition: attachment."""
    f = request.FILES.get("file")
    if not f:
        return err("no file")
    os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
    dest = os.path.join(settings.MEDIA_ROOT, f.name)  # client controls f.name
    with open(dest, "wb") as out:
        for chunk in f.chunks():
            out.write(chunk)
    return ok({"stored_as": f.name, "url": f"/api/download?path={f.name}"})


def download(request):
    """[VULN-07-FILES] Path traversal: joins a user-supplied path to MEDIA_ROOT
    with no normalisation check.  Try: /api/download?path=../db.sqlite3
    Fix: resolve the path and confirm it stays within MEDIA_ROOT; serve only
    allow-listed files."""
    rel = request.GET.get("path", "")
    full = os.path.join(settings.MEDIA_ROOT, rel)
    if not os.path.exists(full):
        return err("not found", status=404)
    return FileResponse(open(full, "rb"))


# ==========================================================================
# 8. SSRF
# ==========================================================================
@csrf_exempt
def import_url(request):
    """[VULN-08-SSRF] Fetches any URL the client supplies, including internal
    addresses (http://127.0.0.1, http://169.254.169.254/ cloud metadata,
    file://). Fix: allow-list schemes+hosts, resolve DNS and block private/
    link-local ranges, disable redirects, set timeouts."""
    data = body_json(request) if request.method == "POST" else request.GET
    target = data.get("url", "")
    try:
        with urllib.request.urlopen(target, timeout=5) as r:  # noqa: S310
            content = r.read(4096)
        return ok({"fetched": target, "preview": content.decode(errors="replace")})
    except Exception as e:
        return err(f"fetch failed: {e}", status=502)


# ==========================================================================
# 9. BUSINESS LOGIC
# ==========================================================================
@csrf_exempt
def checkout(request):
    """[VULN-09-LOGIC] Trusts client-supplied price and quantity, allows
    negative quantities, and applies coupons that are never marked redeemed.
    Fix: compute totals server-side from catalogue prices, validate ranges,
    and enforce single-use coupons transactionally."""
    data = body_json(request)
    item = data.get("item", "widget")
    price_cents = int(data.get("price_cents", 0))     # client sets the price!
    quantity = int(data.get("quantity", 1))           # may be negative
    coupon_code = data.get("coupon")

    total = price_cents * quantity
    applied = None
    if coupon_code:
        try:
            c = Coupon.objects.get(code=coupon_code)
            total = int(total * (100 - c.percent_off) / 100)
            applied = c.code
            # c.redeemed never set -> unlimited reuse
        except Coupon.DoesNotExist:
            pass

    owner = request.user if request.user.is_authenticated else User.objects.first()
    o = Order.objects.create(
        owner=owner, item=item, price_cents=price_cents,
        quantity=quantity, status="paid",
    )
    return ok({"order_id": o.id, "total_cents": total, "coupon": applied})


# ==========================================================================
# 10. API SECURITY  (excessive data exposure)
# ==========================================================================
def list_users(request):
    """[VULN-10-API] No auth required and returns sensitive fields (ssn,
    internal_notes, is_admin, email, password hash) that the UI never shows.
    Fix: require auth+authorisation and serialise only public fields."""
    out = []
    for u in User.objects.all():
        p = getattr(u, "profile", None)
        out.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "password_hash": u.password,          # leaks the hash
            "ssn": getattr(p, "ssn", ""),
            "internal_notes": getattr(p, "internal_notes", ""),
            "is_admin": getattr(p, "is_admin", False),
        })
    return ok(out)


# ==========================================================================
# 11. CONFIGURATION / INFO DISCLOSURE
# ==========================================================================
def debug_info(request):
    """[VULN-11-CONFIG] Exposes a debug endpoint dumping settings + env.
    Fix: never ship debug endpoints; DEBUG=False; remove backup files."""
    return ok({
        "DEBUG": settings.DEBUG,
        "SECRET_KEY": settings.SECRET_KEY,
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
        "db_path": str(settings.DATABASES["default"]["NAME"]),
        "hostname": socket.gethostname(),
        "env_sample": {k: os.environ.get(k, "") for k in ("PATH", "USERNAME")},
    })
