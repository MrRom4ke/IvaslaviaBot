from enum import Enum


class DrawingType(str, Enum):
    free = "free"
    paid = "paid"


class DrawingStatus(str, Enum):
    upcoming = "upcoming"
    active = "active"
    ready_to_draw = "ready_to_draw"
    completed = "completed"


class ApplicationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    payment_pending = "payment_pending"
    payment_bill_loaded = "payment_bill_loaded"
    payment_confirmed = "payment_confirmed"
    payment_rejected = "payment_rejected"
    completed = "completed"


class EvidenceType(str, Enum):
    profile = "profile"
    payment = "payment"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"
