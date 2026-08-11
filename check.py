import os
import smtplib
from email.mime.text import MIMEText
import requests

# ---- تنظیمات ----
CO_CD = "A420"
SITE_NO = "0089"          # CGV سنتام‌سیتی
MOV_NO = "30001323"       # فیلم اودیسه
TARGET_DATE = "20260829"  # 29 اگوست
TARGET_TIME = "1055"      # ساعت 10:55

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


def send_email(subject: str, body: str):
    # چاپ اطلاعات دیباگ (بدون افشای پسورد کامل)
    print(f"[DEBUG] GMAIL_ADDRESS = {GMAIL_ADDRESS!r}")
    print(f"[DEBUG] NOTIFY_TO     = {NOTIFY_TO!r}")
    print(f"[DEBUG] APP_PASSWORD length = {len(GMAIL_APP_PASSWORD)} chars")

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = NOTIFY_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.set_debuglevel(1)  # چاپ کامل مکالمه‌ی SMTP در لاگ
            login_resp = server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            print(f"[DEBUG] login response: {login_resp}")

            refused = server.sendmail(GMAIL_ADDRESS, [NOTIFY_TO], msg.as_string())
            if refused:
                print(f"[WARN] این آدرس‌ها توسط سرور رد شدند: {refused}")
            else:
                print("[OK] sendmail بدون هیچ آدرس ردشده تکمیل شد")
    except smtplib.SMTPAuthenticationError as e:
        print(f"[ERROR] خطای احراز هویت (پسورد/ایمیل اشتباه است): {e}")
        raise
    except smtplib.SMTPRecipientsRefused as e:
        print(f"[ERROR] گیرنده رد شد: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] خطای غیرمنتظره در ارسال ایمیل: {type(e).__name__}: {e}")
        raise

    print(f"[OK] ایمیل با موضوع '{subject}' به {NOTIFY_TO} ارسال شد")


def check():
    resp = requests.get(API_URL, params=PARAMS, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    sessions = payload.get("data") or []
    for s in sessions:
        if s.get("scnsrtTm") == TARGET_TIME:
            seats = s.get("frSeatCnt")
            print(f"سانس {TARGET_TIME} پیدا شد - صندلی خالی: {seats}")
            return True, seats
    print(f"هنوز سانس {TARGET_TIME} برای تاریخ {TARGET_DATE} باز نشده")
    return False, None


if __name__ == "__main__":
    # --- تست ارسال ایمیل (این خط رو بعد از اطمینان از کارکرد حذف کن) ---
    try:
        send_email("تست ✅", "اگه اینو گرفتی یعنی ایمیل درست تنظیم شده")
    except Exception:
        print("[FATAL] ارسال ایمیل تست شکست خورد - اجرا متوقف می‌شود")
        raise SystemExit(1)

    try:
        found, seats = check()
    except Exception as e:
        print(f"خطا در چک کردن: {e}")
        raise SystemExit(0)

    if found:
        send_email(
            subject="🎬 بلیط اودیسه ساعت 10:55 (سنتام‌سیتی) باز شد!",
            body=(
                f"سانس ساعت 10:55 تاریخ 29 اگوست الان توی سیستم CGV دیده می‌شه.\n"
                f"صندلی خالی فعلی: {seats}\n\n"
                f"سریع برو رزرو کن: https://cgv.co.kr/cnm/movieBook/movie"
            ),
        )
        print("ایمیل فرستاده شد ✅")
