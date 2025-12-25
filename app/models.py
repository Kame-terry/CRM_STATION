from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table, Float, Boolean, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class CampaignStatus(enum.Enum):
    DRAFT = "草稿"
    SCHEDULED = "已排程"
    SENDING = "發送中"
    COMPLETED = "已完成"
    FAILED = "失敗"

# 多對多：客戶-課程
customer_courses = Table(
    "customer_courses",
    Base.metadata,
    Column("customer_id", Integer, ForeignKey("customers.id"), primary_key=True),
    Column("course_id", Integer, ForeignKey("courses.id"), primary_key=True),
)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    interactions = relationship("Interaction", back_populates="customer", cascade="all, delete-orphan")
    courses = relationship("Course", secondary=customer_courses, back_populates="students")
    registrations = relationship("EventRegistration", back_populates="customer", cascade="all, delete-orphan")

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    type = Column(String, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    customer = relationship("Customer", back_populates="interactions")

class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    students = relationship("Customer", secondary=customer_courses, back_populates="courses")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    location = Column(String, nullable=True)
    registrations = relationship("EventRegistration", back_populates="event", cascade="all, delete-orphan")

class EventRegistration(Base):
    __tablename__ = "event_registrations"
    customer_id = Column(Integer, ForeignKey("customers.id"), primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id"), primary_key=True)
    attended = Column(Boolean, default=False)
    registered_at = Column(DateTime(timezone=True), server_default=func.now())
    customer = relationship("Customer", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    recipients = relationship("CampaignRecipient", back_populates="campaign", cascade="all, delete-orphan")

class CampaignRecipient(Base):
    __tablename__ = "campaign_recipients"
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), primary_key=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(String, nullable=True)
    campaign = relationship("Campaign", back_populates="recipients")
    customer = relationship("Customer")

class EmailTemplate(Base):
    __tablename__ = "email_templates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
