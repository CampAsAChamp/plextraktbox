"""plextraktbox: all-in-one Plex + Letterboxd + Trakt sync tool."""

from plextraktbox import ssl_compat as _ssl_compat  # noqa: F401 — TLS setup before HTTPS clients load
from plextraktbox.version_info import __version__

__all__ = ["__version__"]
