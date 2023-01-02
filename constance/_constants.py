import locale
import os

__all__ = (
    'DEFAULT_ENCODING',
    'PAYLOAD_FIELDS_ATTR',
    'CONSTRUCT_TYPE_COERCION_ATTR',
)

DEFAULT_ENCODING = os.getenv('CONSTANCE_ENCODING') or locale.getpreferredencoding()
PAYLOAD_FIELDS_ATTR = '__constance_fields__'
CONSTRUCT_TYPE_COERCION_ATTR = '__constance_type_coercion__'
