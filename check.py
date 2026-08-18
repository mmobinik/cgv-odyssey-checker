import os
import smtplib
from email.mime.text import MIMEText
import requests
# ---- تنظیمات ----
CO_CD = "A420"
SITE_NO = "0089"          # CGV سنتام‌سیتی
MOV_NO = "30001323"       # فیلم اودیسه
TARGET_DATE = "20260824"  # 29 اگوست
API_URL = "https://cgv.co.kr/api/v1/booking/searchSchByMov"
PARAMS = {
    "coCd": CO_CD,
    "siteNo": SITE_NO,
    "scnYmd": TARGET_DATE,
    "movNo": MOV_NO,
    "rtctlScopCd": "08",
}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": "https://cgv.co.kr/cnm/movieBook/movie",
    "Accept": "application/json",
}
GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
NOTIFY_TO = os.environ["NOTIFY_TO"]
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


def send_email(subject: str, body: str):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_TO
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            refused = server.sendmail(GMAIL_ADDRESS, [NOTIFY_TO], msg.as_string())
            if refused:
                print(f"[WARN] برخی گیرنده‌ها توسط سرور رد شدند (تعداد: {len(refused)})")
            else:
                print(f"[OK] ایمیل با موضوع '{subject}' ارسال شد")
    except Exception as e:
        print(f"[ERROR] خطا در ارسال ایمیل: {type(e).__name__}: {e}")
        raise


def send_telegram(text: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[WARN] TELEGRAM_BOT_TOKEN یا TELEGRAM_CHAT_ID تنظیم نشده — از ارسال تلگرام صرف‌نظر شد")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "HTML",
            },
            timeout=15,
        )
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            print("[OK] پیام تلگرام ارسال شد")
        else:
            print(f"[WARN] تلگرام پاسخ ناموفق داد: {result}")
    except Exception as e:
        print(f"[ERROR] خطا در ارسال تلگرام: {type(e).__name__}: {e}")


def check():
    resp = requests.get(API_URL, params=PARAMS, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    sessions = payload.get("data") or []
    if sessions:
        print(f"تعداد {len(sessions)} سانس برای تاریخ {TARGET_DATE} پیدا شد:")
        for s in sessions:
            time = s.get("scnsrtTm")
            seats = s.get("frSeatCnt")
            print(f"  - ساعت {time} - صندلی خالی: {seats}")
        return True, sessions
    print(f"هنوز هیچ سانسی برای تاریخ {TARGET_DATE} باز نشده")
    return False, None


if __name__ == "__main__":
    try:
        found, sessions = check()
    except Exception as e:
        print(f"خطا در چک کردن: {e}")
        raise SystemExit(0)
    if found:
        lines = [
            f"ساعت {s.get('scnsrtTm')} - صندلی خالی: {s.get('frSeatCnt')}"
            for s in sessions
        ]
        subject = "🎬 بلیط اودیسه تاریخ 29 اگوست (سنتام‌سیتی) باز شد!"
        body = (
            "سانس‌(های) زیر برای تاریخ 29 اگوست الان توی سیستم CGV دیده می‌شن:\n\n"
            + "\n".join(lines)
            + "\n\nسریع برو رزرو کن: https://cgv.co.kr/cnm/movieBook/movie"
        )
        send_email(subject=subject, body=body)
        send_telegram(f"<b>{subject}</b>\n\n{body}")
        print("نوتیف‌ها فرستاده شدن ✅")
