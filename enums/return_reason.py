

from enum import IntEnum


class ReturnReason(IntEnum):
    
    
    QUALITY = 0        
    DAMAGED = 1        
    WRONG_ITEM = 2        
    NOT_AS_DESC = 3         
    NO_NEED = 4        
    OTHER = 5        

    def __str__(self) -> str:
        
        mapping = {
            ReturnReason.QUALITY: "质量问题",
            ReturnReason.DAMAGED: "商品破损",
            ReturnReason.WRONG_ITEM: "发错商品",
            ReturnReason.NOT_AS_DESC: "与描述不符",
            ReturnReason.NO_NEED: "不想要了",
            ReturnReason.OTHER: "其他原因",
        }
        return mapping.get(self, "未知")

    @classmethod
    def from_string(cls, s: str) -> 'ReturnReason':
        
        mapping = {
            "质量问题": cls.QUALITY,
            "商品破损": cls.DAMAGED,
            "发错商品": cls.WRONG_ITEM,
            "与描述不符": cls.NOT_AS_DESC,
            "不想要了": cls.NO_NEED,
            "其他原因": cls.OTHER,
        }
        return mapping.get(s, cls.OTHER)

    @classmethod
    def get_all_reasons(cls) -> list:
        
        return [
            "质量问题",
            "商品破损",
            "发错商品",
            "与描述不符",
            "不想要了",
            "其他原因",
        ]
