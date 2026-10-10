"""
[VULN-11-CONFIG] Wide-open CORS middleware.

It reflects whatever Origin the caller sends and allows credentials, so ANY
website a victim visits can make authenticated calls to this API using the
victim's session cookie. Combined with the disabled CSRF middleware this makes
cross-site attacks trivial.

Fix: use a vetted library (django-cors-headers) with an explicit allow-list,
and never return Access-Control-Allow-Origin: <reflected> together with
Access-Control-Allow-Credentials: true.
"""


class WideOpenCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            from django.http import HttpResponse
            response = HttpResponse()
        else:
            response = self.get_response(request)

        origin = request.headers.get("Origin", "*")
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
        # When credentials are allowed, browsers reject a literal "*" for the
        # allowed headers, so we reflect exactly what the preflight asked for
        # (still wide open -- this remains [VULN-11-CONFIG]).
        requested = request.headers.get("Access-Control-Request-Headers", "Content-Type")
        response["Access-Control-Allow-Headers"] = requested
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response["Access-Control-Max-Age"] = "600"
        return response
