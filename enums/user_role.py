

from enum import IntEnum


class UserRole(IntEnum):
    
    
    ADMIN = 0       
    MANAGER = 1        
    OPERATOR = 2       
    VIEWER = 3        
    CUSTOMER = 4      

    def __str__(self) -> str:
        
        mapping = {
            UserRole.ADMIN: "管理员",
            UserRole.MANAGER: "管理人员",
            UserRole.OPERATOR: "操作员",
            UserRole.VIEWER: "只读用户",
            UserRole.CUSTOMER: "客户",
        }
        return mapping.get(self, "未知")

    @classmethod
    def from_string(cls, s: str) -> 'UserRole':
        
        mapping = {
            "管理员": cls.ADMIN,
            "管理人员": cls.MANAGER,
            "操作员": cls.OPERATOR,
            "只读用户": cls.VIEWER,
            "客户": cls.CUSTOMER,
        }
        return mapping.get(s, cls.VIEWER)
