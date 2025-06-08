from flask import Flask, request, render_template_string
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz

app = Flask(__name__)

# Google Sheets 認證
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
gc = gspread.authorize(CREDS)

# 國中sheet_id
SHEET_ID = '1SOTkqaIN3g4Spk0Cri4F1mEzdiD1xvLzR5x5KLmhrmY'

@app.route("/attendance")
def attendance():
    sid = request.args.get('sid')
    if not sid:
        return "無效的 QR code（缺少 SID）"

    # 固定使用第一個分頁（或班級名）
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet("國二菁英")  # 這裡如果要自動找班級可以再調整
    data = worksheet.get_all_records()
    row_idx = None
    for idx, student in enumerate(data, start=2):  # 第一行是header
        if str(student.get('student_id')) == sid:
            row_idx = idx
            break

    if row_idx is None:
        return "查無此學生"

    # 取得台北時區現在日期、時間
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    # 找日期欄位
    header = worksheet.row_values(1)
    col_idx = None
    for idx, val in enumerate(header, start=1):
        if val == today_str:
            col_idx = idx
            break

    if col_idx is None:
        worksheet.update_cell(1, len(header) + 1, today_str)
        col_idx = len(header) + 1

    sign_str = f"已簽到 {time_str}"
    worksheet.update_cell(row_idx, col_idx, sign_str)

    return render_template_string(
        "<h2>簽到完成！</h2><p>{{name}} 已簽到 {{time}}</p>",
        name=student.get('學生姓名', '') or student.get('Name', ''), time=time_str
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
