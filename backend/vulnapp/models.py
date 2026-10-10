from django.db import models


class Profile(models.Model):
    """Extra per-user data. Linked 1:1 to Django's auth User by user_id."""
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    # [VULN-10-API] Sensitive fields that the UI hides but the API serializer
    #   below returns in full (SSN, internal notes, role flag).
    full_name = models.CharField(max_length=120, blank=True)
    ssn = models.CharField(max_length=20, blank=True, default="")
    internal_notes = models.TextField(blank=True, default="")
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile<{self.user.username}>"


class Order(models.Model):
    """Orders belong to a user. Used to demo broken access control (IDOR)."""
    owner = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="orders")
    item = models.CharField(max_length=200)
    # [VULN-09-LOGIC] Price is stored but the checkout endpoint trusts the
    #   client-supplied price instead of this one.
    price_cents = models.IntegerField(default=0)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=30, default="pending")
    created = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    """Product comments. Rendered unescaped on the frontend -> stored XSS."""
    author = models.CharField(max_length=120)
    # [VULN-05-XSS] Raw HTML stored verbatim and later injected with v-html.
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)


class PasswordResetToken(models.Model):
    """[VULN-01-AUTH] Reset tokens that never expire and can be reused."""
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    # Short, predictable token (see views) — no expiry, no single-use flag.
    token = models.CharField(max_length=64)
    used = models.BooleanField(default=False)  # written but never checked
    created = models.DateTimeField(auto_now_add=True)


class Coupon(models.Model):
    """[VULN-09-LOGIC] Coupon whose single-use limit is never enforced."""
    code = models.CharField(max_length=40, unique=True)
    percent_off = models.IntegerField(default=0)
    redeemed = models.BooleanField(default=False)  # never checked on redeem
