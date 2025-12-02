class CaseInsensitiveMixin:
    """
    Миксин для StrEnum с помощью которого можно конструировать ENUM из строк в независимости от их регистра.
    """
    @classmethod
    def _missing_(cls, value: str) -> str | None:
        # noinspection PyUnresolvedReferences
        return cls.__members__.get(value.upper(), None)
