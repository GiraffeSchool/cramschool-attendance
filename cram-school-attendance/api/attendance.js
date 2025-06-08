import { google } from 'googleapis';

const sheetInfos = [
  { sheetId: '1SOTkqaIN3g4Spk0Cri4F1mEzdiD1xvLzR5x5KLmhrmY', label: '國中' },
  { sheetId: '1c7zuwUaz-gzY0hbDDO2coixOcQLGhbZbdUXZ9X63Wfo', label: '兒美' },
  { sheetId: '14k7fkfiPdhrSnYPXLJ7--8s_Qk3wehI0AZDpgFw83AM', label: '先修' }
];

export default async function handler(req, res) {
  const { sid } = req.query;
  if (!sid) return res.status(400).send('Missing sid');

  const credentials = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON);
  const scopes = ['https://www.googleapis.com/auth/spreadsheets'];
  const auth = new google.auth.GoogleAuth({ credentials, scopes });
  const sheets = google.sheets({ version: 'v4', auth });

  // 時區與今天日期
  const now = new Date();
  const taipeiNow = new Date(now.toLocaleString('en-US', { timeZone: 'Asia/Taipei' }));
  const today = taipeiNow.toISOString().slice(0, 10);
  const time = taipeiNow.toTimeString().slice(0, 5);

  let found = false;
  for (const info of sheetInfos) {
    // 列出這個年級所有班級分頁
    const getMeta = await sheets.spreadsheets.get({ spreadsheetId: info.sheetId });
    const worksheets = getMeta.data.sheets.map(s => s.properties.title);

    for (const sheetName of worksheets) {
      // 取得分頁內容
      const getRes = await sheets.spreadsheets.values.get({
        spreadsheetId: info.sheetId,
        range: `${sheetName}!A1:Z`,
      });
      const values = getRes.data.values;
      if (!values || !values.length) continue;

      const header = values[0];
      const idCol = header.indexOf('student_id') >= 0 ? header.indexOf('student_id') : header.indexOf('唯一ID');
      if (idCol === -1) continue;

      const rowIdx = values.findIndex((row, i) => i > 0 && row[idCol] === sid);
      if (rowIdx === -1) continue;

      // 找/建日期欄
      let dateCol = header.indexOf(today);
      if (dateCol === -1) {
        dateCol = header.length;
        header.push(today);
        await sheets.spreadsheets.values.update({
          spreadsheetId: info.sheetId,
          range: `${sheetName}!A1`,
          valueInputOption: 'RAW',
          requestBody: { values: [header] },
        });
      }

      // 寫入已簽到
      values[rowIdx][dateCol] = `已簽到 ${time}`;
      await sheets.spreadsheets.values.update({
        spreadsheetId: info.sheetId,
        range: `${sheetName}!A${rowIdx + 1}`,
        valueInputOption: 'RAW',
        requestBody: { values: [values[rowIdx]] },
      });

      found = true;
      return res.status(200).send(`<h2>簽到完成！</h2><p>${sid} 已簽到 ${time}（${info.label} ${sheetName}）</p>`);
    }
  }

  if (!found) return res.status(404).send('查無此學生');
}
