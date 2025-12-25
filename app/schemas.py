from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Customer ---
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

# --- Interaction ---
class InteractionCreate(BaseModel):
    customer_id: int
    type: str
    notes: Optional[str] = None

# --- Course & Event ---
class CourseResponse(BaseModel):
    id: int
    name: str
    price: float
    class Config: from_attributes = True

class EventResponse(BaseModel):
    id: int
    name: str
    date: datetime
    location: Optional[str] = None
    class Config: from_attributes = True

class EventListResponse(EventResponse):
    attendee_count: int
    checkin_count: int
    attendance_rate: float

class EventCreate(BaseModel):
    name: str
    date: datetime
    location: Optional[str] = None

# --- Marketing ---
class CampaignCreateRequest(BaseModel):
    name: str
    subject: str
    body: str
    customer_ids: List[int]
    scheduled_at: Optional[datetime] = None

class TemplateCreate(BaseModel):
    name: str
    subject: str
    body: str

class TestEmailRequest(BaseModel):
    email: str
    subject: str
    body: str

# --- Stats ---
class DashboardStats(BaseModel):
    total_customers: int
    total_events: int
    total_purchases: int
    total_revenue: float
    unique_event_attendees: int
    converted_purchasers: int
    conversion_rate: float
    customer_segments: List[dict]
    top_converting_events: List[dict]

# --- Full Customer ---
class CustomerDetailResponse(CustomerResponse):
    interactions: List[dict] = []
    courses: List[CourseResponse] = []
    registrations: List[dict] = []
