from connexion.resolver import Resolver


class PrefixResolver(Resolver):
    def __init__(self, prefix=None):
        self._prefix = prefix
        super().__init__()

    def resolve_function_from_operation_id(self, operation_id):
        full_operation_id = self._prefix + operation_id
        return super().resolve_function_from_operation_id(full_operation_id)
