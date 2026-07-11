
// === WhatsApp stubs (edtime-only; hapus jika paste WhatsAppInbound.gs terpisah) ===
function processWhatsAppPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.object === 'whatsapp_business_account') {
      return ContentService.createTextOutput('OK').setMimeType(ContentService.MimeType.TEXT);
    }
  } catch (err) {}
  return null;
}
function doGetWhatsApp(e) {
  if (e.parameter.hub === 'whatsapp') {
    return ContentService.createTextOutput('Forbidden');
  }
  return null;
}
/**
 * Google Apps Script — pasang di Spreadsheet "Automation Queue"
 * Extensions > Apps Script > paste script ini > Deploy > Test
 *
 * Sheet "Queue" kolom:
 * A: id | B: device (mac|iphone) | C: command | D: status | E: args
 *
 * Pasang juga file EdtimeSync.gs dan WhatsAppInbound.gs di project yang sama.
 */

const SHEET_NAME = 'Queue';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Automation Hub')
    .addItem('Tambah perintah contoh Mac', 'addSampleMacCommand')
    .addItem('Tambah perintah contoh iPhone', 'addSampleIphoneCommand')
    .addItem('Tambah edtime-fetch contoh', 'addSampleEdtimeCommand')
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

/** Web App endpoint — Mac/iPhone POST, WhatsApp inbound, status, edtime */
function doPost(e) {
  const waResult = processWhatsAppPost(e);
  if (waResult) return waResult;

  const data = JSON.parse(e.postData.contents);

  const edtimeResult = processEdtimePost(data);
  if (edtimeResult) return edtimeResult;

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

/** iPhone Shortcuts polling — GET pending OR WhatsApp verify OR edtime export */
function doGet(e) {
  const edtimeExport = doGetEdtime(e);
  if (edtimeExport) return edtimeExport;

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

/**
 * EdtimeSync.gs — handler data edtime untuk Automation Hub
 * Pasang di project Apps Script yang sama dengan QueueSync.gs
 * File ini di-include otomatis jika paste di bawah QueueSync.gs
 */

const EDTIME_TABS = {
  schedule: 'EdtimeSchedule',
  raw: 'EdtimeRaw',
  screenshots: 'EdtimeScreenshots',
  cursor: 'CursorExport',
  session: 'EdtimeSession',
};

function ensureEdtimeSheet(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) sheet.appendRow(headers);
  return sheet;
}

/** Route edtime actions from doPost */
function processEdtimePost(data) {
  const action = String(data.action || '').toLowerCase();
  if (!action.startsWith('edtime')) return null;

  switch (action) {
    case 'edtime_schedule':
      return handleEdtimeSchedule(data);
    case 'edtime_raw':
      return handleEdtimeRaw(data);
    case 'edtime_screenshot':
      return handleEdtimeScreenshot(data);
    case 'edtime_session':
      return handleEdtimeSession(data);
    case 'edtime_cursor_export':
      return handleEdtimeCursorExport(data);
    default:
      return ContentService.createTextOutput(JSON.stringify({ ok: false, error: 'unknown edtime action' }))
        .setMimeType(ContentService.MimeType.JSON);
  }
}

function handleEdtimeSchedule(data) {
  const sheet = ensureEdtimeSheet(EDTIME_TABS.schedule, [
    'id', 'date', 'start_time', 'end_time', 'shift_code', 'break_minutes',
    'location', 'status', 'raw_source', 'synced_at', 'notes',
  ]);
  const rows = data.schedule || data.rows || (data.row ? [data.row] : []);
  const ids = [];
  rows.forEach(function (row) {
    const id = Utilities.getUuid().slice(0, 8);
    sheet.appendRow([
      id,
      row.date || '',
      row.start_time || '',
      row.end_time || '',
      row.shift_code || '',
      row.break_minutes || '',
      row.location || '',
      row.status || 'planned',
      row.source || row.raw_source || data.source || 'iphone',
      new Date().toISOString(),
      row.notes || '',
    ]);
    ids.push(id);
  });
  refreshCursorExportTab_();
  return jsonOk_({ ok: true, inserted: ids.length, ids: ids });
}

function handleEdtimeRaw(data) {
  const sheet = ensureEdtimeSheet(EDTIME_TABS.raw, [
    'timestamp', 'device', 'payload_type', 'payload_json',
  ]);
  sheet.appendRow([
    new Date().toISOString(),
    data.device || 'iphone',
    data.payload_type || 'unknown',
    JSON.stringify(data.payload || data),
  ]);
  return jsonOk_({ ok: true });
}

function handleEdtimeScreenshot(data) {
  const sheet = ensureEdtimeSheet(EDTIME_TABS.screenshots, [
    'timestamp', 'device', 'screen_type', 'filename', 'drive_path', 'notes',
  ]);
  sheet.appendRow([
    new Date().toISOString(),
    data.device || 'iphone',
    data.screen_type || 'schichtplan',
    data.filename || '',
    data.drive_path || '',
    data.notes || '',
  ]);
  return jsonOk_({ ok: true });
}

function handleEdtimeSession(data) {
  const sheet = ensureEdtimeSheet(EDTIME_TABS.session, [
    'timestamp', 'device', 'status', 'extra',
  ]);
  sheet.appendRow([
    data.at || new Date().toISOString(),
    data.device || 'iphone',
    data.status || 'unknown',
    data.extra || '',
  ]);
  return jsonOk_({ ok: true });
}

function handleEdtimeCursorExport(data) {
  const payload = data.payload || data;
  const sheet = ensureEdtimeSheet(EDTIME_TABS.cursor, [
    'exported_at', 'record_count', 'json_summary',
  ]);
  const schedule = payload.schedule || [];
  sheet.appendRow([
    payload.exported_at || new Date().toISOString(),
    schedule.length,
    JSON.stringify(payload).slice(0, 50000),
  ]);
  refreshCursorExportTab_(payload);
  return jsonOk_({ ok: true, records: schedule.length });
}

function refreshCursorExportTab_(payloadOpt) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sched = ss.getSheetByName(EDTIME_TABS.schedule);
  if (!sched || sched.getLastRow() < 2) return;

  let sheet = ss.getSheetByName('CursorExportRows');
  if (!sheet) sheet = ss.insertSheet('CursorExportRows');
  sheet.clear();
  sheet.appendRow([
    'date', 'start_time', 'end_time', 'shift_code', 'break_minutes',
    'hours_worked', 'location', 'status', 'source', 'berichtsheft_template',
  ]);

  const rows = sched.getDataRange().getValues();
  for (let i = 1; i < rows.length; i++) {
    const r = rows[i];
    const date = r[1], st = r[2], et = r[3], code = r[4], br = r[5];
    const hours = computeHours_(st, et, br);
    sheet.appendRow([
      date, st, et, code, br, hours, r[6], r[7], r[8],
      'Schicht ' + code + ' ' + st + '-' + et,
    ]);
  }
}

function computeHours_(start, end, breakMin) {
  if (!start || !end) return 0;
  try {
    const s = parseTime_(start);
    const e = parseTime_(end);
    let diff = e - s;
    if (diff < 0) diff += 24 * 3600000;
    const br = parseFloat(breakMin) || 0;
    return Math.max(0, Math.round((diff / 3600000 - br / 60) * 100) / 100);
  } catch (err) {
    return 0;
  }
}

function parseTime_(t) {
  const parts = String(t).split(':');
  const d = new Date();
  d.setHours(parseInt(parts[0], 10), parseInt(parts[1] || 0, 10), 0, 0);
  return d.getTime();
}

/** GET ?action=edtime-schedule | cursor-edtime-export | setup-edtime */
function doGetEdtime(e) {
  const action = (e.parameter.action || '').toLowerCase();

  if (action === 'setup-edtime') {
    return jsonOk_(setupEdtimeTabs_());
  }

  if (!action.startsWith('edtime') && action !== 'cursor-edtime-export') return null;

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sched = ss.getSheetByName(EDTIME_TABS.schedule);
  const schedule = [];

  if (sched && sched.getLastRow() > 1) {
    const rows = sched.getDataRange().getValues();
    for (let i = 1; i < rows.length; i++) {
      schedule.push({
        id: rows[i][0],
        date: rows[i][1],
        start_time: rows[i][2],
        end_time: rows[i][3],
        shift_code: rows[i][4],
        break_minutes: rows[i][5],
        location: rows[i][6],
        status: rows[i][7],
        source: rows[i][8],
        synced_at: rows[i][9],
        notes: rows[i][10],
        hours_worked: computeHours_(rows[i][2], rows[i][3], rows[i][5]),
      });
    }
  }

  const out = {
    schema: 'automation-hub/edtime-cursor-export/v1',
    exported_at: new Date().toISOString(),
    schedule: schedule,
    meta: { source: 'google_sheet', tab: EDTIME_TABS.schedule },
  };

  return ContentService.createTextOutput(JSON.stringify(out))
    .setMimeType(ContentService.MimeType.JSON);
}

function jsonOk_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function addSampleEdtimeCommand() {
  appendCommand('iphone', 'edtime-fetch', 'week=current', 'pending');
}

/** Auto-create all edtime Sheet tabs — call GET ?action=setup-edtime */
function setupEdtimeTabs_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const tabs = [
    { name: EDTIME_TABS.schedule, headers: [
      'id', 'date', 'start_time', 'end_time', 'shift_code', 'break_minutes',
      'location', 'status', 'raw_source', 'synced_at', 'notes',
    ]},
    { name: EDTIME_TABS.raw, headers: ['timestamp', 'device', 'payload_type', 'payload_json'] },
    { name: EDTIME_TABS.screenshots, headers: [
      'timestamp', 'device', 'screen_type', 'filename', 'drive_path', 'notes',
    ]},
    { name: EDTIME_TABS.cursor, headers: ['exported_at', 'record_count', 'json_summary'] },
    { name: EDTIME_TABS.session, headers: ['timestamp', 'device', 'status', 'extra'] },
    { name: 'CursorExportRows', headers: [
      'date', 'start_time', 'end_time', 'shift_code', 'break_minutes',
      'hours_worked', 'location', 'status', 'source', 'berichtsheft_template',
    ]},
  ];
  const created = [];
  tabs.forEach(function (t) {
    let sheet = ss.getSheetByName(t.name);
    if (!sheet) {
      sheet = ss.insertSheet(t.name);
      created.push(t.name);
    }
    if (sheet.getLastRow() === 0) sheet.appendRow(t.headers);
  });
  return { ok: true, created: created, message: 'edtime tabs ready' };
}
