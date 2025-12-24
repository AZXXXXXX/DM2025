from enum import IntEnum


class CustomerType(IntEnum):
    ONLINE_RETAIL = 0
    OFFLINE_RETAIL = 1
    UNKNOWN = 2

    def __str__(self) -> str:
        mapping = {
            CustomerType.ONLINE_RETAIL: "线上预定",
            CustomerType.OFFLINE_RETAIL: "线下零售",
        }
        return mapping.get(self, "未知")

    @classmethod
    def from_string(cls, s: str) -> 'CustomerType':
        mapping = {
            "线上预定": cls.ONLINE_RETAIL,
            "线下零售": cls.OFFLINE_RETAIL,
        }
        return mapping.get(s, cls.UNKNOWN)
