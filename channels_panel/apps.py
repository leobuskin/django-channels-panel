from django.apps import AppConfig, apps
from django.conf import settings

from channels.asgi import channel_layers
from channels import DEFAULT_CHANNEL_LAYER

from .utils import layer_factory, debug_decorator, in_debug, is_no_debug
from . import routes


class ChannelsDebugConfig(AppConfig):

    name = "channels_panel"
    verbose_name = "Channels Debug Toolbar Panel"

    def ready(self):
        if not apps.is_installed('debug_toolbar'):
            return

        # patch routes: adding debug routes to default layer
        for route in routes.debug_channel_routes:
            channel_layers[DEFAULT_CHANNEL_LAYER].router.add_route(route)

        # patch layers: substitution by debug layer with events monitoring
        for alias in getattr(settings, "CHANNEL_LAYERS", {}).keys():
            new_backend = layer_factory(channel_layers[alias],  alias)
            channel_layers.set(alias, new_backend)

        # patch routes: wrap routes debug decorator
        for alias in getattr(settings, "CHANNEL_LAYERS", {}).keys():
            _match = channel_layers[alias].router.root.match

            def new_match(message):
                if in_debug(message.channel.name):
                    m = _match(message)
                    if m and not is_no_debug(m[0]):
                        return debug_decorator(m[0], alias), m[1]
                return _match(message)
            channel_layers[alias].router.root.match = new_match

