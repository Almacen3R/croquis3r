from ipaddress import ip_address
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import DisallowedHost
from django.middleware.security import SecurityMiddleware


class LanAwareSecurityMiddleware(SecurityMiddleware):
    """COOP sigue activo en HTTPS y loopback; HTTP LAN no puede aplicarlo."""

    def process_response(self, request, response):
        response = super().process_response(request, response)
        if not settings.LAN_HTTP_MODE or request.is_secure():
            return response
        try:
            host = urlsplit('//' + request.get_host()).hostname or ''
        except (DisallowedHost, ValueError):
            return response
        if host == 'localhost' or host.endswith('.localhost'):
            return response
        try:
            if ip_address(host).is_loopback:
                return response
        except ValueError:
            pass
        # El navegador ya ignora COOP en estos orígenes HTTP. No tocar HTTPS,
        # CSRF, autenticación, X-Frame-Options ni las otras cabeceras de Django.
        response.headers.pop('Cross-Origin-Opener-Policy', None)
        return response
