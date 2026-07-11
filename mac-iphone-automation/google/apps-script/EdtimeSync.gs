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

/** GET ?action=edtime-schedule | cursor-edtime-export */
function doGetEdtime(e) {
  const action = (e.parameter.action || '').toLowerCase();
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
