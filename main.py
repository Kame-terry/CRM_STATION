import uvicorn
import os
import time

# 在啟動前強制設定伺服器時區為台北
os.environ['TZ'] = 'Asia/Taipei'
if hasattr(time, 'tzset'):
    time.tzset()

if __name__ == "__main__":
    # 讀取 Zeabur 自動分配的 PORT，若無則預設 8080
    port = int(os.getenv("PORT", 8080))
    # 啟動 app 資料夾下的 main.py 裡的 app
    uvicorn.run("app.main:app", host="0.0.0.0", port=port)
