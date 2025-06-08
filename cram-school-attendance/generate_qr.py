import gspread
from google.oauth2.service_account import Credentials
import qrcode
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
CREDS = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
gc = gspread.authorize(CREDS)

sheet_infos = {
    '國中': '1SOTkqaIN3g4Spk0Cri4F1mEzdiD1xvLzR5x5KLmhrmY',

}

output_dir = 'file'
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

for grade_name, sheet_id in sheet_infos.items():
    sh = gc.open_by_key(sheet_id)
    for worksheet in sh.worksheets():
        class_name = worksheet.title
        # 以班級為單位建立子資料夾
        class_dir = os.path.join(output_dir, class_name)
        if not os.path.isdir(class_dir):
            os.makedirs(class_dir)
        students = worksheet.get_all_records()
        for student in students:
            sid = student.get('student_id') or student.get('唯一ID')
            name = student.get('學生姓名')
            eng_name = student.get('Name')
            if not sid or not name:
                continue
            qr_url = f"https://your-domain.com/attendance?sid={sid}"
            img = qrcode.make(qr_url)
            # 學生的檔名：中文名_英文名_唯一ID.png
            filename = f"{name}_{eng_name}_{sid}.png"
            img.save(os.path.join(class_dir, filename))

print("QR code 已依班級分資料夾存放於 file/ 下！")
