import enum

class Role(str, enum.Enum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    FINANCE = "finance"
    ADMIN = "admin"

class RequestStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Decision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"