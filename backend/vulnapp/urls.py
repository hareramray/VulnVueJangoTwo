from django.urls import path

from . import views

urlpatterns = [
    # 1. Authentication
    path("register", views.register),
    path("login", views.login_view),
    path("logout", views.logout_view),            # 3. Session
    path("whoami", views.whoami),
    path("forgot-password", views.forgot_password),
    path("reset-password", views.reset_password),

    # 2. Access control (IDOR)
    path("orders/<int:order_id>", views.get_order),
    path("orders/<int:order_id>/delete", views.delete_order),

    # 4. SQL injection
    path("search", views.search_orders),

    # 5. XSS
    path("comments", views.comments),
    path("greet", views.greet),

    # 6. CSRF
    path("change-email", views.change_email),

    # 7. File upload / path traversal
    path("upload", views.upload),
    path("download", views.download),

    # 8. SSRF
    path("import-url", views.import_url),

    # 9. Business logic
    path("checkout", views.checkout),

    # 10. API data exposure
    path("users", views.list_users),

    # 11. Config / info disclosure
    path("debug", views.debug_info),
]
