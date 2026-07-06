/**
 * WhatsApp Business API — Webhook inbound messages
 * Pasang di Apps Script project yang sama dengan QueueSync.gs
 *
 * Meta Developer Console → WhatsApp → Configuration:
 *   Callback URL: YOUR_WEB_APP_URL?hub=whatsapp
 *   Verify Token: HUB_VERIFY_TOKEN (set di Script Properties)
 */

const WA_VERIFY_TOKEN = PropertiesService.getScriptProperties().getProperty('HUB_VERIFY_TOKEN') || 'automation-hub-verify';
const INBOX_SHEET = 'Inbox';

function verifyWhatsAppWebhook(e) {
  const mode = e.parameter['hub.mode'];
  const token = e.parameter['hub.verify_token'];
  const challenge = e.parameter['hub.challenge'];
  if (mode === 'subscribe' && token === WA_VERIFY_TOKEN) {
    return ContentService.createTextOutput(challenge);
  }
  return ContentService.createTextOutput('Forbidden');
}

function handleWhatsAppInbound(body) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(INBOX_SHEET);
  if (!sheet) sheet = ss.insertSheet(INBOX_SHEET);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(['timestamp', 'from', 'message', 'type', 'status']);
  }

  const entries = body.entry || [];
  entries.forEach(function (entry) {
    const changes = entry.changes || [];
    changes.forEach(function (change) {
      const value = change.value || {};
      const messages = value.messages || [];
      messages.forEach(function (msg) {
        const from = msg.from || '';
        const text = (msg.text && msg.text.body) || msg.type || '';
        sheet.appendRow([new Date().toISOString(), from, text, msg.type || 'text', 'new']);
      });
    });
  });
}

/** Call from merged doGet — WhatsApp verification */
function doGetWhatsApp(e) {
  if (e.parameter.hub === 'whatsapp') {
    return verifyWhatsAppWebhook(e);
  }
  return null;
}

/** Call from merged doPost — WhatsApp inbound */
function processWhatsAppPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    if (body.object === 'whatsapp_business_account') {
      handleWhatsAppInbound(body);
      return ContentService.createTextOutput('OK').setMimeType(ContentService.MimeType.TEXT);
    }
  } catch (err) {
    // not whatsapp payload
  }
  return null;
}
