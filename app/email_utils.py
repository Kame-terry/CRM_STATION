import os.path
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from .config import settings

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

def get_gmail_service():
    creds = None
    # 1. 嘗試環境變數
    token_env = os.getenv("GMAIL_TOKEN_JSON")
    if token_env:
        try:
            creds = Credentials.from_authorized_user_info(json.loads(token_env), SCOPES)
            print("💡 從環境變數載入 Gmail Token 成功")
        except Exception as e: print(f"⚠️ 環境變數 Token 載入失敗: {e}")

    # 2. 嘗試本地檔案
    if not creds and os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
            print("💡 從 token.json 載入成功")
        except Exception as e: print(f"⚠️ token.json 載入失敗: {e}")
    
    # 3. 處理過期刷新
    if creds and creds.expired and creds.refresh_token:
        try:
            print("🔄 正在刷新 Gmail 存取權限...")
            creds.refresh(Request())
        except Exception as e:
            print(f"❌ 刷新權限失敗: {e}")
            creds = None

    if not creds:
        print("❌ 完全找不到有效的 Gmail 授權資訊")
        return None

    try:
        return build("gmail", "v1", credentials=creds)
    except Exception as e:
        print(f"❌ 建立 Gmail Service 失敗: {e}")
        return None

def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    service = get_gmail_service()
    if not service:
        return False, "找不到授權資訊 (Token)"

    try:
        message = MIMEMultipart()
        message["to"] = to_email
        message["from"] = "me" # Gmail API 固定使用 me
        message["subject"] = subject
        
        # 內文處理
        part = MIMEText(body, 'html' if is_html else 'plain')
        message.attach(part)
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        sent_msg = service.users().messages().send(userId="me", body={'raw': raw}).execute()
        print(f"✅ 郵件已成功寄出至 {to_email} (ID: {sent_msg['id']})")
        return True, "Success"
    except HttpError as error:
        err_msg = f"Gmail API 錯誤: {error.reason}"
        print(f"❌ {err_msg}")
        return False, err_msg
    except Exception as e:
        err_msg = f"發生未知錯誤: {str(e)}"
        print(f"❌ {err_msg}")
        return False, err_msg
