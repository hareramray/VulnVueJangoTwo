"""Seed demo data. Run:  python manage.py shell -c "import seed; seed.run()"
or simply:  python seed.py   (it bootstraps Django for you)."""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vulnproject.settings")
django.setup()

from django.contrib.auth.models import User  # noqa: E402
from vulnapp.models import Comment, Coupon, Order, Profile  # noqa: E402


def run():
    Comment.objects.all().delete()
    Order.objects.all().delete()
    Coupon.objects.all().delete()
    Profile.objects.all().delete()
    User.objects.filter(username__in=["alice", "bob", "admin"]).delete()

    alice = User.objects.create_user("alice", password="123456", email="alice@example.com")
    bob = User.objects.create_user("bob", password="password", email="bob@example.com")
    admin = User.objects.create_superuser("admin", password="admin", email="admin@example.com")

    Profile.objects.create(user=alice, full_name="Alice Able",
                           ssn="111-11-1111", internal_notes="VIP, do not refund")
    Profile.objects.create(user=bob, full_name="Bob Baker",
                           ssn="222-22-2222", internal_notes="chargeback risk")
    Profile.objects.create(user=admin, full_name="Site Admin", is_admin=True,
                           ssn="999-99-9999", internal_notes="root")

    Order.objects.create(owner=alice, item="Blue Widget", price_cents=1999, quantity=2, status="paid")
    Order.objects.create(owner=bob, item="Red Gadget", price_cents=4999, quantity=1, status="paid")

    Coupon.objects.create(code="SAVE50", percent_off=50)

    Comment.objects.create(author="alice", body="Love this product!")

    print("Seeded users: alice/123456, bob/password, admin/admin")


if __name__ == "__main__":
    run()
