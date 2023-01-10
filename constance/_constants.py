import locale
import os

__all__ = (
    'DEFAULT_ENCODING',
    'DATA_FIELDS_ATTR',
)

DEFAULT_ENCODING = os.getenv('CONSTANCE_ENCODING') or locale.getpreferredencoding()
DATA_FIELDS_ATTR = '__constance_fields__'
