from bitbin import core
from bitbin import util

__all__ = ()

generic_types = util.generic_types
generic_types.register(list, core.Generic(list))
generic_types.register(set, core.Generic(set))
generic_types.register(frozenset, core.Generic(frozenset))
generic_types.register(tuple, core.Generic(tuple))
