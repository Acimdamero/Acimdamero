/**
 * Google Apps Script — pasang di Spreadsheet "Automation Queue"
 * Extensions > Apps Script > paste script ini > Deploy > Test
 *
 * Sheet "Queue" kolom:
 * A: id | B: device (mac|iphone) | C: command | D: status | E: args
 */

const SHEET_NAME = 'Queue';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Automation Hub')
    .addItem('Tambah perintah contoh Mac', 'addSampleMacCommand')
    .addItem('Tambah perintah contoh iPhone', 'addSampleIphoneCommand')
    .addToUi();
}

function addSampleMacCommand() {
  appendCommand('mac', 'status', '', 'pending');
}

function addSampleIphoneCommand() {
  appendCommand('iphone', 'notify', 'Automation Hub aktif', 'pending');
}

function appendCommand(device, command, args, status) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const id = Utilities.getUuid().slice(0, 8);
  sheet.appendRow([id, device, command, status || 'pending', args || '']);
}

/** Web App endpoint — Mac/iPhone bisa POST perintah baru */
function doPost(e) {
  const data = JSON.parse(e.postData.contents);
  appendCommand(data.device, data.command, data.args || '', 'pending');
  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

/** iPhone Shortcuts polling — GET pending commands for device */
function doGet(e) {
  const device = (e.parameter.device || 'iphone').toLowerCase();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  const rows = sheet.getDataRange().getValues();
  const pending = [];

  for (let i = 1; i < rows.length; i++) {
    const [id, dev, command, status, args] = rows[i];
    if (String(dev).toLowerCase() === device && String(status).toLowerCase() === 'pending') {
      pending.push({ row: i + 1, id, device: dev, command, args });
    }
  }

  return ContentService.createTextOutput(JSON.stringify({ pending }))
    .setMimeType(ContentService.MimeType.JSON);
}

/** Mark command done — call from Shortcuts after execution */
function markDone(row) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  sheet.getRange(Number(row), 4).setValue('done');
}
