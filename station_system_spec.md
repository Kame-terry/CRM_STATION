# 🚀 CRM 系統開發需求規格書 (System Spec)

## 1. 系統概述
本系統為一套專為中小型企業或課程主辦方設計的 **客戶關係管理 (CRM) 系統**。核心目標是整合客戶資料、活動參與紀錄、課程購買統計，並具備自動化的電子郵件行銷與開啟率追蹤功能。

## 2. 技術棧 (Tech Stack)
*   **後端 (Backend)**: FastAPI (Python 3.12), SQLAlchemy (非同步非阻塞), PostgreSQL (Docker 容器化)。
*   **前端 (Frontend)**: Bootstrap 5 (UI 框架), Chart.js (數據視覺化), Vanilla JavaScript (SPA 單頁應用邏輯)。
*   **套件管理**: `uv` (高效 Python 套件管理)。
*   **整合服務**: Gmail API (OAuth2 授權發信)。
*   **排程系統**: APScheduler (處理預約發信任務)。

## 3. 核心功能模組

### A. 數據總覽 (Dashboard)
*   **KPI 卡片**: 顯示「總客戶數」、「總活動數」、「總購買次數」、「累計營收額 (NT$)」。
*   **轉換漏斗 (Conversion Funnel)**: 統計「報名人數」與「成交轉化人數」的比例，並自動計算「整體轉換率」。
*   **客戶分佈圖**: 使用甜甜圈圖顯示前五大客戶所屬公司或產業佔比。
*   **活動排行榜**: 條列各活動的報名人數、成交人數與個別轉換率。

### B. 客戶管理 (Customer Management)
*   **基礎 CRUD**: 支援新增、讀取、搜尋、刪除客戶。
*   **隱私保護**: 前端顯示 Email 時自動進行遮罩處理 (例如：`tes***@gmail.com`)。
*   **詳細資料**: 可查看客戶購買過的課程、參加過的活動以及聯絡紀錄 (Interactions)。

### C. 活動管理 (Event Management)
*   **活動追蹤**: 建立新活動（名稱、時間、地點）。
*   **出席統計**: 除了報名人數，需追蹤「實際出席人數」並自動計算「出席率」。

### D. 郵件行銷 (Email Marketing)
*   **收件人選擇**: 支援從客戶名單中「手動複選」或「搜尋新增」收件人。
*   **範本管理**: 可自訂郵件主旨與內容，支援變數替換（如 `{name}`），並可「另存為新範本」。
*   **排程發送**: 支援「立即發送」或「預約特定時間發送」。
*   **開信追蹤**: 系統自動植入 1x1 追蹤像素，即時統計每場活動的「已開啟人數」與「開啟率」。

## 4. 資料模型 (Data Model)
*   `Customer`: 客戶資料表。
*   `Course`: 課程資料表。
*   `Event`: 活動資料表。
*   `EventRegistration`: 客戶與活動的關聯表（含 `attended` 出席狀態）。
*   `Campaign`: 郵件行銷活動表（含 `status` 狀態與排程時間）。
*   `CampaignRecipient`: 發信對象追蹤表（含 `sent_at` 與 `opened_at`）。
*   `EmailTemplate`: 郵件範本儲存表。

## 5. 安全與部署 (Security & DevOps)
*   **認證安全**: 嚴格禁止將 `.env`, `credentials.json`, `token.json` 推送到 Git。
*   **環境變數**: 支援從環境變數載入 Google OAuth2 的 ID、Secret 以及 Token JSON 字串（相容 Zeabur 部署）。
*   **WSL2 整合**: 支援 WSL2 與 Windows Docker 的網路穿透連線。
