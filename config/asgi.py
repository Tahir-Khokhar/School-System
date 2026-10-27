"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# Set the default before anything else imports Django settings.
# An explicit DJANGO_SETTINGS_MODULE in the environment always wins.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Initialise Django before importing anything that touches models/apps.
# get_asgi_application() calls django.setup() internally, so this must
# come *after* DJANGO_SETTINGS_MODULE is set.
application = get_asgi_application()

# If you later add Channels, replace the line above with something like:
#
#     from channels.routing import ProtocolTypeRouter, URLRouter
#     from config.routing import websocket_urlpatterns
#
#     django_asgi_app = get_asgi_application()
#     application = ProtocolTypeRouter({
#         "http": django_asgi_app,
#         "websocket": URLRouter(websocket_urlpatterns),
#     })
