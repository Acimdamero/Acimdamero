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

/** Web App endpoint — Mac/iPhone POST, WhatsApp inbound, status */
function doPost(e) {
  const waResult = processWhatsAppPost(e);
  if (waResult) return waResult;

  const data = JSON.parse(e.postData.contents);
  if (data.action === 'status' || (data.device && !data.command)) {
    return handleStatus(data);
  }
  if (data.action === 'wa_sent') {
    return logWaSent(data);
  }
  appendCommand(data.device, data.command, data.args || '', 'pending');
  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

/** iPhone Shortcuts polling — GET pending commands OR WhatsApp verify */
function doGet(e) {
  const waVerify = doGetWhatsApp(e);
  if (waVerify) return waVerify;

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

/** Log device status from iPhone/Mac POST */
function handleStatus(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('Devices');
  if (!sheet) sheet = ss.insertSheet('Devices');
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['timestamp', 'device', 'battery', 'wifi', 'hostname', 'extra']);
  }
  sheet.appendRow([
    new Date().toISOString(),
    data.device || 'unknown',
    data.battery || '',
    data.wifi || data.network || '',
    data.name || data.hostname || '',
    data.extra || data.disk || ''
  ]);
  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}

function logWaSent(data) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName('Outbox');
  if (!sheet) sheet = ss.insertSheet('Outbox');
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['timestamp', 'to', 'message', 'status']);
  }
  sheet.appendRow([new Date().toISOString(), data.to || '', data.message || '', 'sent']);
  return ContentService.createTextOutput(JSON.stringify({ ok: true }))
    .setMimeType(ContentService.MimeType.JSON);
}
