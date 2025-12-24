from enum import IntEnum


class OrderStatus(IntEnum):
    NEW = 0
    PENDING_PAYMENT = 1
    PENDING_SHIP = 2
    PACKING = 3
    PENDING_RECEIVE = 4
    COMPLETED = 5
    PAUSED = 6
    CANCELLED = 7
    RETURN_APPLYING = 8
    RETURNING = 9
    UNKNOWN = 10
    RETURN_REJECTED = 11

    def __str__(self) -> str:
        mapping = {
            OrderStatus.NEW: "新建",
            OrderStatus.PENDING_PAYMENT: "待付款",
            OrderStatus.PENDING_SHIP: "待发货",
            OrderStatus.PACKING: "打包中",
            OrderStatus.PENDING_RECEIVE: "待收货",
            OrderStatus.COMPLETED: "完成",
            OrderStatus.PAUSED: "暂停",
            OrderStatus.CANCELLED: "取消",
            OrderStatus.RETURN_APPLYING: "退货申请中",
            OrderStatus.RETURNING: "退货中",
            OrderStatus.RETURN_REJECTED: "退货驳回",
        }
        return mapping.get(self, "未知")

    @classmethod
    def from_string(cls, s: str) -> 'OrderStatus':
        mapping = {
            "新建": cls.NEW,
            "待付款": cls.PENDING_PAYMENT,
            "待发货": cls.PENDING_SHIP,
            "打包中": cls.PACKING,
            "待收货": cls.PENDING_RECEIVE,
            "完成": cls.COMPLETED,
            "暂停": cls.PAUSED,
            "取消": cls.CANCELLED,
            "退货申请中": cls.RETURN_APPLYING,
            "退货中": cls.RETURNING,
            "退货驳回": cls.RETURN_REJECTED,
        }
        return mapping.get(s, cls.UNKNOWN)

    @classmethod
    def get_pending_statuses(cls) -> list:
        return [
            cls.NEW,
            cls.PENDING_PAYMENT,
            cls.PENDING_SHIP,
            cls.PACKING,
            cls.PENDING_RECEIVE,
        ]

    @classmethod
    def get_return_statuses(cls) -> list:
        return [
            cls.RETURN_APPLYING,
            cls.RETURNING,
        ]
