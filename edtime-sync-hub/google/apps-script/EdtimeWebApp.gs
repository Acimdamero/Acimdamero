/**
 * Edtime Sync Hub — Google Apps Script Web App (STANDALONE)
 * Deploy di Spreadsheet "Automation Queue" — tab edtime + Queue
 * TIDAK termasuk WhatsApp / WAHA / Mac backup (repo terpisah: mac-iphone-automation)
 */

const SHEET_NAME = 'Queue';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Edtime Sync')
    .addItem('Setup edtime tabs', 'menuSetupEdtime')
    .addItem('Sample edtime-fetch', 'addSampleEdtimeCommand')
    .addToUi();
}

function menuSetupEdtime() {
  const r = setupEdtimeTabs_();
  SpreadsheetApp.getUi().alert('Edtime tabs: ' + JSON.stringify(r));
}

function appendCommand(device, command, args, status) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error('Tab Queue tidak ditemukan');
  const id = Utilities.getUuid().slice(0, 8);
  sheet.appendRow([id, device, command, status || 'pending', args || '']);
}

function addSampleEdtimeCommand() {
  appendCommand('iphone', 'edtime-fetch', 'week=current', 'pending');
}

function doPost(e) {
  const data = JSON.parse(e.postData.contents);

  const edtimeResult = processEdtimePost(data);
  if (edtimeResult) return edtimeResult;

  if (data.action === 'status' || (data.device && !data.command && !data.action)) {
    return handleStatus(data);
  }

  if (data.device && data.command) {
    appendCommand(data.device, data.command, data.args || '', 'pending');
  }
  return jsonOk_({ ok: true });
}

function doGet(e) {
  const edtimeExport = doGetEdtime(e);
  if (edtimeExport) return edtimeExport;

  const device = (e.parameter.device || 'iphone').toLowerCase();
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  if (!sheet) {
    return jsonOk_({ pending: [], error: 'Queue tab missing' });
  }
  const rows = sheet.getDataRange().getValues();
  const pending = [];

  for (let i = 1; i < rows.length; i++) {
    const [id, dev, command, status, args] = rows[i];
    if (String(dev).toLowerCase() === device && String(status).toLowerCase() === 'pending') {
      pending.push({ row: i + 1, id, device: dev, command, args });
    }
  }
  return jsonOk_({ pending: pending });
}

function markDone(row) {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(SHEET_NAME);
  sheet.getRange(Number(row), 4).setValue('done');
}

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
    data.extra || data.disk || '',
  ]);
  return jsonOk_({ ok: true });
}

// === Edtime handlers (EdtimeSync.gs inline) ===

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

function processEdtimePost(data) {
  const action = String(data.action || '').toLowerCase();
  if (!action.startsWith('edtime')) return null;
  switch (action) {
    case 'edtime_schedule': return handleEdtimeSchedule(data);
    case 'edtime_raw': return handleEdtimeRaw(data);
    case 'edtime_screenshot': return handleEdtimeScreenshot(data);
    case 'edtime_session': return handleEdtimeSession(data);
    case 'edtime_cursor_export': return handleEdtimeCursorExport(data);
    default:
      return jsonOk_({ ok: false, error: 'unknown edtime action' });
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
      id, row.date || '', row.start_time || '', row.end_time || '',
      row.shift_code || '', row.break_minutes || '', row.location || '',
      row.status || 'planned', row.source || row.raw_source || data.source || 'iphone',
      new Date().toISOString(), row.notes || '',
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
    new Date().toISOString(), data.device || 'iphone',
    data.payload_type || 'unknown', JSON.stringify(data.payload || data),
  ]);
  return jsonOk_({ ok: true });
}

function handleEdtimeScreenshot(data) {
  const sheet = ensureEdtimeSheet(EDTIME_TABS.screenshots, [
    'timestamp', 'device', 'screen_type', 'filename', 'drive_path', 'notes',
  ]);
  sheet.appendRow([
    new Date().toISOString(), data.device || 'iphone',
    data.screen_type || 'schichtplan', data.filename || '',
    data.drive_path || '', data.notes || '',
  ]);
  return jsonOk_({ ok: true });
}

function handleEdtimeSession(data) {
  const sheet = ensureEdtimeSheet(EDTIME_TABS.session, [
    'timestamp', 'device', 'status', 'extra',
  ]);
  sheet.appendRow([
    data.at || new Date().toISOString(), data.device || 'iphone',
    data.status || 'unknown', data.extra || '',
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
    schedule.length, JSON.stringify(payload).slice(0, 50000),
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
    const hours = computeHours_(r[2], r[3], r[5]);
    sheet.appendRow([
      r[1], r[2], r[3], r[4], r[5], hours, r[6], r[7], r[8],
      'Schicht ' + r[4] + ' ' + r[2] + '-' + r[3],
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
    return Math.max(0, Math.round((diff / 3600000 - (parseFloat(breakMin) || 0) / 60) * 100) / 100);
  } catch (err) { return 0; }
}

function parseTime_(t) {
  const parts = String(t).split(':');
  const d = new Date();
  d.setHours(parseInt(parts[0], 10), parseInt(parts[1] || 0, 10), 0, 0);
  return d.getTime();
}

function doGetEdtime(e) {
  const action = (e.parameter.action || '').toLowerCase();
  if (action === 'setup-edtime') return jsonOk_(setupEdtimeTabs_());
  if (!action.startsWith('edtime') && action !== 'cursor-edtime-export') return null;

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sched = ss.getSheetByName(EDTIME_TABS.schedule);
  const schedule = [];
  if (sched && sched.getLastRow() > 1) {
    const rows = sched.getDataRange().getValues();
    for (let i = 1; i < rows.length; i++) {
      schedule.push({
        id: rows[i][0], date: rows[i][1], start_time: rows[i][2], end_time: rows[i][3],
        shift_code: rows[i][4], break_minutes: rows[i][5], location: rows[i][6],
        status: rows[i][7], source: rows[i][8], synced_at: rows[i][9], notes: rows[i][10],
        hours_worked: computeHours_(rows[i][2], rows[i][3], rows[i][5]),
      });
    }
  }
  return jsonOk_({
    schema: 'edtime-sync-hub/cursor-export/v1',
    exported_at: new Date().toISOString(),
    schedule: schedule,
    meta: { source: 'google_sheet', tab: EDTIME_TABS.schedule },
  });
}

function jsonOk_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

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
    if (!sheet) { sheet = ss.insertSheet(t.name); created.push(t.name); }
    if (sheet.getLastRow() === 0) sheet.appendRow(t.headers);
  });
  return { ok: true, created: created, message: 'edtime tabs ready' };
}
