from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from .database import AsyncSessionLocal
from .models import Campaign, CampaignStatus, CampaignRecipient
from .email_utils import send_email
import asyncio
import os

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")

async def process_scheduled_campaigns():
    """背景任務：使用本地時間檢查排程"""
    async with AsyncSessionLocal() as db:
        now = datetime.now() # 使用本地時間
        print(f"🕒 [Scheduler 心跳] 目前時間: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 找出狀態為「已排程」且「時間已到」的活動
        query = select(Campaign).where(Campaign.status == CampaignStatus.SCHEDULED).where(Campaign.scheduled_at <= now)
        result = await db.execute(query)
        campaigns = result.scalars().all()

        if not campaigns:
            return

        print(f"🚀 [Scheduler] 偵測到 {len(campaigns)} 個待發送任務！")

        for campaign in campaigns:
            print(f"📩 正在發送信件: {campaign.name}")
            campaign.status = CampaignStatus.SENDING
            await db.commit()

            rec_query = select(CampaignRecipient).options(selectinload(CampaignRecipient.customer)).where(CampaignRecipient.campaign_id == campaign.id)
            rec_result = await db.execute(rec_query)
            recipients = rec_result.scalars().all()

            sent_ok = 0
            for rec in recipients:
                try:
                    html_body = campaign.body.replace("{name}", rec.customer.name).replace("\n", "<br>")
                    pixel_url = f"{BASE_URL}/customers/tracking/open/{campaign.id}/{rec.customer.id}"
                    full_content = f"<html><body>{html_body}<img src='{pixel_url}' width='1' height='1' style='display:none;'></body></html>"

                    success, msg = send_email(rec.customer.email, campaign.subject, full_content, is_html=True)
                    if success:
                        rec.sent_at = datetime.now()
                        sent_ok += 1
                    else:
                        rec.error = msg
                except Exception as e:
                    rec.error = str(e)
                await asyncio.sleep(0.5)

            campaign.status = CampaignStatus.COMPLETED
            await db.commit()
            print(f"✅ 活動 '{campaign.name}' 已發送完成，共寄出 {sent_ok} 封。")

# 設定排程器：增加 misfire_grace_time 容錯
scheduler = AsyncIOScheduler()
scheduler.add_job(
    process_scheduled_campaigns, 
    'interval',
    minutes=1, 
    misfire_grace_time=60, # 允許 60 秒內的延遲執行
    coalesce=True,         # 如果多次執行重疊，只執行一次
    max_instances=1        # 同一時間只允許一個任務在跑
)