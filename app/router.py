from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, insert, desc, text
from sqlalchemy.orm import selectinload
from typing import List, Optional
import base64
import os
import json
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from google_auth_oauthlib.flow import Flow

from .database import get_db
from .models import (
    Customer, Interaction, Course, Event, customer_courses, 
    EventRegistration, Campaign, CampaignStatus, CampaignRecipient, EmailTemplate
)
from .email_utils import send_email, TOKEN_FILE
from .config import settings
from .schemas import (
    CustomerCreate, CustomerResponse, DashboardStats,
    EventResponse, EventCreate, EventListResponse, CampaignCreateRequest, TemplateCreate,
    TestEmailRequest, CustomerDetailResponse
)

router = APIRouter(prefix="/customers", tags=["customers"])

# --- Google OAuth 設定 ---
SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
REDIRECT_URI = "http://localhost:8080/customers/marketing/callback"

def get_google_flow():
    if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "project_id": "crm-pro",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [REDIRECT_URI]
            }
        }
        return Flow.from_client_config(client_config, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    return None

# --- 1. 認證相關路由 ---

@router.get("/marketing/auth")
async def google_auth():
    flow = get_google_flow()
    if not flow: return JSONResponse(status_code=400, content={"message": "請先在 .env 設定 GOOGLE_CLIENT_ID"})
    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')
    return RedirectResponse(auth_url)

@router.get("/marketing/callback")
async def auth_callback(code: str):
    flow = get_google_flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(TOKEN_FILE, "w") as token:
        token.write(creds.to_json())
    return RedirectResponse(url="/")

@router.get("/marketing/status")
def get_auth_status():
    return {"is_authenticated": os.path.exists(TOKEN_FILE)}

# --- 2. 數據統計 API ---

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    cust_res = await db.execute(select(Customer).options(selectinload(Customer.courses), selectinload(Customer.registrations)))
    customers = cust_res.scalars().all()
    all_events = (await db.execute(select(Event))).scalars().all()

    total_revenue = sum(sum(course.price for course in c.courses) for c in customers)
    total_purchases = sum(len(c.courses) for c in customers)
    attendee_ids = {c.id for c in customers if c.registrations}
    purchaser_ids = {c.id for c in customers if c.courses}
    converted = len(attendee_ids.intersection(purchaser_ids))

    comp_map = {}
    for c in customers:
        name = c.company or "其他"
        comp_map[name] = comp_map.get(name, 0) + 1
    segments = [{"company": k, "count": v} for k, v in sorted(comp_map.items(), key=lambda x: x[1], reverse=True)[:5]]

    top_events = []
    for ev in all_events:
        regs = [c for c in customers if any(r.event_id == ev.id for r in c.registrations)]
        conv = [c for c in regs if c.courses]
        top_events.append({"name": ev.name, "registrations": len(regs), "converted": len(conv), "rate": round(len(conv)/len(regs)*100, 2) if regs else 0})

    return {
        "total_customers": len(customers), "total_events": len(all_events), "total_purchases": total_purchases,
        "total_revenue": total_revenue, "unique_event_attendees": len(attendee_ids),
        "converted_purchasers": converted, "conversion_rate": round(converted/len(attendee_ids)*100, 2) if attendee_ids else 0,
        "customer_segments": segments, "top_converting_events": sorted(top_events, key=lambda x: x['rate'], reverse=True)
    }

# --- 3. 客戶與活動管理 API ---

@router.get("/", response_model=List[CustomerResponse])
async def read_customers(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Customer).order_by(Customer.created_at.desc()))
    return res.scalars().all()

@router.post("/", response_model=CustomerResponse)
async def create_customer(customer: CustomerCreate, db: AsyncSession = Depends(get_db)):
    db_c = Customer(**customer.model_dump())
    db.add(db_c); await db.commit(); await db.refresh(db_c)
    return db_c

@router.delete("/{customer_id}")
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Customer).where(Customer.id == customer_id))
    c = res.scalars().first()
    if c: await db.delete(c); await db.commit()
    return {"status": "ok"}

@router.get("/events/", response_model=List[EventListResponse])
async def read_events(db: AsyncSession = Depends(get_db)):
    events = (await db.execute(select(Event).order_by(Event.date.desc()))).scalars().all()
    output = []
    for e in events:
        reg_res = await db.execute(select(EventRegistration).where(EventRegistration.event_id == e.id))
        regs = reg_res.scalars().all()
        total = len(regs)
        checked = sum(1 for r in regs if r.attended)
        output.append({"id": e.id, "name": e.name, "date": e.date, "location": e.location, "attendee_count": total, "checkin_count": checked, "attendance_rate": round(checked/total*100, 2) if total > 0 else 0})
    return output

@router.post("/events/", response_model=EventResponse)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_db)):
    db_e = Event(**event.model_dump())
    db.add(db_e); await db.commit(); await db.refresh(db_e)
    return db_e

# --- 4. 郵件行銷 API ---

@router.post("/marketing/campaigns")
async def create_campaign(request: CampaignCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
        final_time = request.scheduled_at
        
        if not final_time:
            # 如果沒傳時間，設定 10 秒後發送
            # 在台北時區設定下的 datetime.now() 會是正確的
            final_time = datetime.now() + timedelta(seconds=10)
        else:
            # 確保傳進來的時間是被視為本地時間 (台北)
            # 如果帶有時區資訊，轉換它；如果沒有，它已經是台北時間字串轉過來的
            if final_time.tzinfo is not None:
                # 這裡假設您的伺服器已經設為 Asia/Taipei，我們統一轉為 naive datetime
                final_time = final_time.replace(tzinfo=None)
        
        campaign = Campaign(
            name=request.name, subject=request.subject, body=request.body, 
            scheduled_at=final_time,
            status=CampaignStatus.SCHEDULED
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        
        if request.customer_ids:
            recipients = [{"campaign_id": campaign.id, "customer_id": cid} for cid in request.customer_ids]
            await db.execute(insert(CampaignRecipient), recipients)
            await db.commit()
        
        return {"id": campaign.id, "message": "Success"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/marketing/campaigns")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    campaigns = res.scalars().all()
    output = []
    for c in campaigns:
        total_res = await db.execute(select(func.count(CampaignRecipient.customer_id)).where(CampaignRecipient.campaign_id == c.id))
        total = total_res.scalar() or 0
        opened_res = await db.execute(select(func.count(CampaignRecipient.opened_at)).where(CampaignRecipient.campaign_id == c.id))
        opened = opened_res.scalar() or 0
        output.append({
            "id": c.id, "name": c.name, "status": c.status.value, 
            "total_recipients": total, "opened_count": opened, 
            "open_rate": round(opened/total*100, 2) if total > 0 else 0, 
            "scheduled_at": c.scheduled_at
        })
    return output

@router.get("/marketing/templates")
async def get_templates(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(EmailTemplate).order_by(EmailTemplate.created_at.desc()))
    return res.scalars().all()

@router.post("/marketing/templates")
async def create_template(request: TemplateCreate, db: AsyncSession = Depends(get_db)):
    tpl = EmailTemplate(**request.model_dump())
    db.add(tpl); await db.commit()
    return tpl

@router.post("/marketing/test")
async def send_test_email(request: TestEmailRequest):
    success, msg = send_email(request.email, request.subject, request.body.replace("{name}", "測試員"), is_html=True)
    if success:
        return {"message": "測試信寄送成功！"}
    else:
        raise HTTPException(status_code=500, detail=f"寄送失敗：{msg}")

@router.get("/tracking/open/{campaign_id}/{customer_id}")
async def track_open(campaign_id: int, customer_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CampaignRecipient).where(CampaignRecipient.campaign_id == campaign_id, CampaignRecipient.customer_id == customer_id))
    rec = res.scalars().first()
    if rec and not rec.opened_at:
        rec.opened_at = datetime.now(timezone.utc)
        await db.commit()
    return Response(content=base64.b64decode("R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"), media_type="image/gif")

@router.get("/{customer_id}", response_model=CustomerDetailResponse)
async def read_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Customer).options(selectinload(Customer.interactions), selectinload(Customer.courses), selectinload(Customer.registrations)).where(Customer.id == customer_id))
    return res.scalars().first()