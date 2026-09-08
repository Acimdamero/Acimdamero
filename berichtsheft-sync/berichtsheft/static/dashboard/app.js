(() => {
  const TITLES = {
    overview: "Overview",
    live: "Live feed",
    katalog: "Katalog / Abteilung",
    shifts: "Jadwal / Shifts",
    school: "Sekolah / Templates",
    blok: "BLok dry-run",
    bots: "Bots",
  };

  const tokenInput = document.getElementById("dash-token");
  const statusPill = document.getElementById("status-pill");
  const panelTitle = document.getElementById("panel-title");

  tokenInput.value = localStorage.getItem("bh_dash_token") || "";
  tokenInput.addEventListener("change", () => {
    localStorage.setItem("bh_dash_token", tokenInput.value.trim());
  });

  function headers(json = false) {
    const h = {};
    if (json) h["Content-Type"] = "application/json";
    const t = tokenInput.value.trim();
    if (t) h["X-Dashboard-Token"] = t;
    return h;
  }

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      ...opts,
      headers: { ...headers(Boolean(opts.body)), ...(opts.headers || {}) },
    });
    const text = await res.text();
    let data;
    try {
      data = text ? JSON.parse(text) : {};
    } catch {
      data = { raw: text };
    }
    if (!res.ok) {
      const msg = data.detail || data.error || res.statusText || "error";
      throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
    }
    return data;
  }

  function showPanel(name) {
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    document.querySelectorAll("#nav button").forEach((b) => b.classList.remove("active"));
    document.getElementById(`panel-${name}`).classList.add("active");
    document.querySelector(`#nav button[data-panel="${name}"]`).classList.add("active");
    panelTitle.textContent = TITLES[name] || name;
    loadPanel(name);
  }

  document.querySelectorAll("#nav button").forEach((btn) => {
    btn.addEventListener("click", () => showPanel(btn.dataset.panel));
  });
  document.getElementById("btn-refresh").addEventListener("click", () => {
    const active = document.querySelector("#nav button.active");
    loadPanel(active ? active.dataset.panel : "overview");
  });

  async function loadPanel(name) {
    try {
      if (name === "overview") await loadHealth();
      if (name === "live") await loadLive();
      if (name === "katalog") await loadCatalog();
      if (name === "shifts") await loadShiftsTable();
      if (name === "school") await loadSchool();
      if (name === "blok") await loadBlok();
      if (name === "bots") await loadBots();
    } catch (e) {
      statusPill.textContent = e.message;
      statusPill.className = "pill warn";
    }
  }

  function esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function loadHealth() {
    const h = await api("/dashboard/api/health");
    statusPill.textContent = h.ok ? "API OK" : "degraded";
    statusPill.className = h.ok ? "pill ok" : "pill warn";
    document.getElementById("auth-note").textContent = h.auth_note || "";

    const cells = [
      ["API", true, true],
      ["Gemini key", h.gemini_key_present, h.gemini_enabled],
      ["Vision", h.vision_enabled, h.vision_enabled],
      ["Cursor", h.cursor_available, h.cursor_available],
      ["Telegram token", h.telegram_token_present, h.telegram_token_present],
      ["TG chat saved", h.telegram_chat_id_saved, h.telegram_chat_id_saved],
      ["WA allowlist", h.whatsapp_allowlist_set, h.whatsapp_allowlist_set],
      ["WA chat saved", h.whatsapp_chat_id_saved, h.whatsapp_chat_id_saved],
      ["WAHA", Boolean(h.waha && h.waha.ok), Boolean(h.waha && h.waha.ok)],
      ["Token required", h.dashboard_token_required, true],
    ];

    const grid = document.getElementById("health-grid");
    grid.innerHTML = cells
      .map(([label, present, ok]) => {
        const cls = ok ? "ok" : "bad";
        const val = present ? "yes" : "no";
        return `<div class="stat"><div class="label">${esc(label)}</div><div class="value ${cls}">${val}</div></div>`;
      })
      .join("");

    if (h.waha && !h.waha.ok && h.waha.error) {
      grid.insertAdjacentHTML(
        "beforeend",
        `<div class="stat"><div class="label">WAHA detail</div><div class="value" style="font-size:0.8rem;font-weight:400;color:var(--muted)">${esc(h.waha.error)}</div></div>`
      );
    }
  }

  async function loadLive() {
    const data = await api("/dashboard/api/live?limit=30");
    const logs = document.getElementById("live-logs");
    logs.innerHTML = (data.work_logs || [])
      .map(
        (r) => `<div class="feed-item"><div class="meta">${esc(r.date)} · ${esc(r.source)} · ${esc(r.created_at)}</div>${esc(r.content)}</div>`
      )
      .join("") || '<div class="feed-item meta">Belum ada work log</div>';

    document.getElementById("live-drafts").innerHTML =
      (data.drafts || [])
        .map(
          (r) =>
            `<div class="feed-item"><div class="meta">${esc(r.date)} · ${esc(r.status)} · ${esc(r.ort)}</div>${esc((r.taetigkeiten || "").slice(0, 280))}</div>`
        )
        .join("") || '<div class="feed-item meta">Belum ada draft</div>';

    document.getElementById("live-atts").innerHTML =
      (data.attachments || [])
        .map((r) => {
          const img = r.media_url
            ? `<img src="${esc(r.media_url)}" alt="attachment ${esc(r.id)}" loading="lazy" />`
            : `<span class="meta">file missing</span>`;
          return `<div class="feed-item"><div class="meta">#${esc(r.id)} · ${esc(r.date)} · ${esc(r.vision_mode || r.kind)}</div>${esc(r.caption || r.path)}${img}</div>`;
        })
        .join("") || '<div class="feed-item meta">Belum ada lampiran</div>';
  }

  async function loadCatalog() {
    const data = await api("/dashboard/api/catalog");
    document.getElementById("katalog-editor").value = JSON.stringify(data.katalog, null, 2);
    setMsg("katalog-msg", `Loaded ${data.path}`, true);
  }

  document.getElementById("btn-cat-reload").addEventListener("click", () => loadCatalog().catch(showErr));
  document.getElementById("btn-cat-save").addEventListener("click", async () => {
    try {
      const katalog = JSON.parse(document.getElementById("katalog-editor").value);
      const res = await api("/dashboard/api/catalog", {
        method: "PUT",
        body: JSON.stringify({ katalog, sync_db: true, export_legacy: true, write_md: false }),
      });
      setMsg(
        "katalog-msg",
        `Saved ${res.path}` + (res.sync ? `\nSync: ${JSON.stringify(res.sync)}` : ""),
        true
      );
    } catch (e) {
      setMsg("katalog-msg", e.message, false);
    }
  });

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");
      const which = tab.dataset.shiftTab;
      document.getElementById("shifts-table-wrap").classList.toggle("hidden", which !== "table");
      document.getElementById("shifts-json-wrap").classList.toggle("hidden", which !== "json");
      if (which === "json") loadShiftsJson().catch(showErr);
      else loadShiftsTable().catch(showErr);
    });
  });

  async function loadShiftsTable() {
    const data = await api("/dashboard/api/shifts?limit=120");
    const tbody = document.querySelector("#shifts-table tbody");
    tbody.innerHTML = (data.shifts || [])
      .map((s) => {
        const tags = (s.tags || []).join(", ");
        return `<tr>
          <td>${esc(s.date)}</td>
          <td>${esc(s.day_type)}</td>
          <td>${esc(s.start_time || "")}</td>
          <td>${esc(s.end_time || "")}</td>
          <td>${esc(tags)}</td>
          <td><button type="button" class="danger" data-del="${esc(s.date)}">Del</button></td>
        </tr>`;
      })
      .join("");
    tbody.querySelectorAll("button[data-del]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!confirm(`Hapus shift ${btn.dataset.del}?`)) return;
        try {
          await api(`/dashboard/api/shifts/${btn.dataset.del}`, { method: "DELETE" });
          await loadShiftsTable();
        } catch (e) {
          setMsg("shift-msg", e.message, false);
        }
      });
    });
  }

  document.getElementById("btn-shift-reload").addEventListener("click", () =>
    loadShiftsTable().catch(showErr)
  );
  document.getElementById("btn-shift-save").addEventListener("click", async () => {
    try {
      const tags = document
        .getElementById("sh-tags")
        .value.split(",")
        .map((x) => x.trim())
        .filter(Boolean);
      const body = {
        date: document.getElementById("sh-date").value,
        day_type: document.getElementById("sh-type").value,
        start: document.getElementById("sh-start").value || null,
        end: document.getElementById("sh-end").value || null,
        tags,
        segments: tags.length
          ? [
              {
                start: document.getElementById("sh-start").value || null,
                end: document.getElementById("sh-end").value || null,
                code: tags[0],
              },
            ]
          : [],
      };
      if (!body.date) throw new Error("Date wajib");
      const res = await api("/dashboard/api/shifts", {
        method: "PUT",
        body: JSON.stringify(body),
      });
      setMsg("shift-msg", `Upserted ${res.date}`, true);
      await loadShiftsTable();
    } catch (e) {
      setMsg("shift-msg", e.message, false);
    }
  });

  async function loadShiftsJson() {
    const data = await api("/dashboard/api/shifts/json");
    document.getElementById("shifts-json-editor").value = JSON.stringify(data.data, null, 2);
    setMsg("sj-msg", `Loaded ${data.path}`, true);
  }
  document.getElementById("btn-sj-reload").addEventListener("click", () =>
    loadShiftsJson().catch(showErr)
  );
  document.getElementById("btn-sj-save").addEventListener("click", async () => {
    try {
      const parsed = JSON.parse(document.getElementById("shifts-json-editor").value);
      const res = await api("/dashboard/api/shifts/json", {
        method: "PUT",
        body: JSON.stringify({ data: parsed, import_to_db: true }),
      });
      setMsg("sj-msg", `Saved ${res.path}\nImported: ${res.imported}`, true);
    } catch (e) {
      setMsg("sj-msg", e.message, false);
    }
  });

  async function loadSchool() {
    const data = await api("/dashboard/api/school");
    const el = document.getElementById("school-content");
    const abts = data.abteilungen || [];
    if (!abts.length) {
      el.innerHTML = `<p class="hint">${esc(data.hint)}</p><p class="hint">Tidak ada Abteilung Schule di katalog.</p>`;
      return;
    }
    el.innerHTML =
      `<p class="hint">${esc(data.hint)}</p>` +
      abts
        .map((a) => {
          const codes = (a.codes || [])
            .map((c) => {
              const templates = (c.templates_de || []).map((t) => `<li>${esc(t)}</li>`).join("");
              const defaults = (c.default_activities_de || [])
                .map((t) => `<li>${esc(t)}</li>`)
                .join("");
              return `<div class="card" style="margin-top:0.75rem">
                <strong>${esc(c.code)} — ${esc(c.name_de || "")}</strong>
                <div class="meta">Lernfeld: ${esc(c.lernfeld || "-")}</div>
                <p class="hint">Default</p><ul class="cmd-list">${defaults || "<li>—</li>"}</ul>
                <p class="hint">Templates DE</p><ul class="cmd-list">${templates || "<li>—</li>"}</ul>
              </div>`;
            })
            .join("");
          return `<h2 style="margin-top:0">${esc(a.blok_name || "Schule")}</h2>
            <p class="hint">${esc(a.description_de || "")}</p>${codes}`;
        })
        .join("");
  }

  async function loadBlok() {
    const data = await api("/dashboard/api/blok");
    document.getElementById("blok-meta").innerHTML = `
      Mode: <strong>${esc(data.mode)}</strong> ·
      Keychain: ${data.keychain_available ? "yes" : "no"} ·
      <a href="${esc(data.blok_url)}" target="_blank" rel="noopener" style="color:var(--accent)">online-ausbildungsnachweis.de</a><br/>
      Docs: ${(data.docs || []).map((d) => `<code>${esc(d)}</code>`).join(" ")}<br/>
      ${esc(data.note)}`;

    const list = document.getElementById("blok-files");
    list.innerHTML = (data.files || [])
      .map(
        (f) =>
          `<button type="button" data-url="${esc(f.preview_url)}" data-kind="${esc(f.kind)}">${esc(f.name)}</button>`
      )
      .join("") || '<span class="hint">Belum ada file di output/blok_dry_run/</span>';

    const iframe = document.getElementById("blok-iframe");
    const pre = document.getElementById("blok-json");
    list.querySelectorAll("button[data-url]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (btn.dataset.kind === "html") {
          iframe.classList.remove("hidden");
          pre.classList.add("hidden");
          iframe.src = btn.dataset.url;
        } else {
          iframe.classList.add("hidden");
          pre.classList.remove("hidden");
          const res = await fetch(btn.dataset.url, { headers: headers() });
          pre.textContent = await res.text();
        }
      });
    });

    const firstHtml = (data.files || []).find((f) => f.kind === "html");
    if (firstHtml) {
      iframe.classList.remove("hidden");
      iframe.src = firstHtml.preview_url;
    }
  }

  async function loadBots() {
    const data = await api("/dashboard/api/bots");
    const tg = data.telegram || {};
    const wa = data.whatsapp || {};
    document.getElementById("bot-telegram").innerHTML = `
      <h2 style="margin:0 0 0.5rem">Telegram</h2>
      <div class="meta">Token: ${tg.token_present ? "present" : "missing"} · Chat ID file: ${tg.chat_id_saved ? esc(tg.chat_id) : "—"}</div>
      <p class="hint">${esc(tg.open_hint)}</p>
      <p class="hint">Docs: <code>${esc(tg.docs)}</code></p>
      <p class="hint">Menu buttons</p>
      <ul class="cmd-list">${(tg.menu_buttons || []).map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
      <p class="hint">Commands</p>
      <ul class="cmd-list">${(tg.commands || []).map((c) => `<li>/${esc(c.command)} — ${esc(c.description)}</li>`).join("")}</ul>`;

    const waha = wa.waha || {};
    document.getElementById("bot-whatsapp").innerHTML = `
      <h2 style="margin:0 0 0.5rem">WhatsApp (WAHA)</h2>
      <div class="meta">Allowlist: ${wa.allowlist_set ? "set" : "empty"} · Chat ID: ${wa.chat_id_saved ? esc(wa.chat_id) : "—"}</div>
      <div class="meta">WAHA: ${waha.ok ? "reachable" : esc(waha.error || "unreachable")}</div>
      <p class="hint">${esc(wa.open_hint)}</p>
      <p class="hint">Docs: <code>${esc(wa.docs)}</code></p>`;
  }

  function setMsg(id, text, ok) {
    const el = document.getElementById(id);
    el.textContent = text;
    el.className = "msg " + (ok ? "ok" : "err");
  }

  function showErr(e) {
    statusPill.textContent = e.message || String(e);
    statusPill.className = "pill warn";
  }

  showPanel("overview");
  setInterval(() => {
    const active = document.querySelector("#nav button.active");
    if (active && (active.dataset.panel === "live" || active.dataset.panel === "overview")) {
      loadPanel(active.dataset.panel).catch(() => {});
    }
  }, 15000);
})();
