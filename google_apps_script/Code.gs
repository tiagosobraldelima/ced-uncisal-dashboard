const SPREADSHEET_ID = '';
const SHEET_NAME = '';

function doGet() {
  const spreadsheet = SPREADSHEET_ID
    ? SpreadsheetApp.openById(SPREADSHEET_ID)
    : SpreadsheetApp.getActiveSpreadsheet();
  const sheet = SHEET_NAME
    ? spreadsheet.getSheetByName(SHEET_NAME)
    : spreadsheet.getSheets()[0];

  if (!sheet) {
    return jsonOutput({ rows: [], error: 'Aba da planilha não encontrada.' });
  }

  const values = sheet.getDataRange().getDisplayValues();
  if (!values.length) {
    return jsonOutput({ rows: [], updatedAt: new Date().toISOString() });
  }

  const headers = uniqueHeaders(values[0]);
  const rows = values.slice(1)
    .filter(row => row.some(cell => String(cell || '').trim()))
    .map(row => {
      const record = {};
      headers.forEach((header, index) => {
        record[header] = row[index] || '';
      });
      return record;
    });

  return jsonOutput({
    rows,
    updatedAt: new Date().toISOString(),
    count: rows.length
  });
}

function uniqueHeaders(headers) {
  const seen = {};
  return headers.map(header => {
    const key = String(header || '').trim();
    seen[key] = (seen[key] || 0) + 1;
    if (key === 'Período' && seen[key] === 1) return 'Período Letivo';
    if (key === 'Período' && seen[key] === 2) return 'Período do Curso';
    return seen[key] > 1 ? `${key} ${seen[key]}` : key;
  });
}

function jsonOutput(payload) {
  return ContentService
    .createTextOutput(JSON.stringify(payload))
    .setMimeType(ContentService.MimeType.JSON);
}
