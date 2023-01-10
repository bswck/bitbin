import locale
import os

__all__ = (
    'DEFAULT_ENCODING',
    'FIELDS',
)

DEFAULT_ENCODING = os.getenv('CONSTANCE_ENCODING') or locale.getpreferredencoding()
FIELDS = '__constance_fields__'
