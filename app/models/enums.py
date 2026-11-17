import enum

class Role(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    FINANCE = "finance"
    ADMIN = "admin"