from enum import IntEnum


class InventoryStatus(IntEnum):
    PURCHASING = 0
    TRANSPORTING = 1
    INSPECTING = 2
    NORMAL = 3
    OUT_OF_STOCK = 4
    OFF_SHELF = 5

    def __str__(self) -> str:
        mapping = {
            InventoryStatus.PURCHASING: "采购中",
            InventoryStatus.TRANSPORTING: "运输中",
            InventoryStatus.INSPECTING: "验收中",
            InventoryStatus.NORMAL: "正常",
            InventoryStatus.OUT_OF_STOCK: "缺货",
            InventoryStatus.OFF_SHELF: "下架",
        }
        return mapping.get(self, "未知")

    @classmethod
    def from_string(cls, s: str) -> 'InventoryStatus':
        mapping = {
            "采购中": cls.PURCHASING,
            "运输中": cls.TRANSPORTING,
            "验收中": cls.INSPECTING,
            "正常": cls.NORMAL,
            "缺货": cls.OUT_OF_STOCK,
            "下架": cls.OFF_SHELF,
        }
        return mapping.get(s, cls.NORMAL)
