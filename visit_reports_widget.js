/**
 * 株式会社ファインスタッフ × 株式会社ファインアトラス（対馬水産）
 * 👑 社長専用「テレアポ獲得案件 → 営業訪問報告（サイボウズ日報原文転記）＆商談進捗ボード」共通コンポーネント
 * (visit_reports_widget.js)
 *
 * 特徴:
 * - 営業担当者（戸井 麻衣・有福 浩一・西川 ひなの・富田 湧介・藤井 皓一朗・宮川 玲子 ほか）が
 *   普段通りサイボウズOffice「報告書（日報・全国テレアポ報告）」に書いた訪問結果を1時間おきに自動回収し、
 *   一切要約・改変せず「原文そのまま」転記して一覧化。
 * - 既存の架電リストやブラウザ保存データ（localStorage）を一切壊さず、社長の指示メモ・進捗変更は
 *   専用キー（fine_president_visit_board_memo_v1）で自動保護。
 */
(function () {
  "use strict";

  var STORAGE_KEY_PRES_OVERRIDE = "fine_president_visit_board_memo_v1";
  var REMOTE_JSON_URL = "https://hira6254.github.io/fine-atlas-osaka-hq/visit_reports_data.json";
  var REPORT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1V4YaTIpTn5dE_s1R3NvYQlmFoa3gXHX30jDK9bVwQJg/edit";

  var VISIT_STATUS_LIST = [
    "🎉 契約・スタッフ提案進行中",
    "🤝 責任者商談済（前向き・本部/社内検討）",
    "💬 責任者面談・ヒアリング済（関係構築中）",
    "📄 訪問済・資料/名刺お渡し（不在・次回再訪）",
    "🗓️ 訪問予定（アポ確定・訪問前）",
    "📧 事前資料送付・商談調整中",
    "⏳ 訪問結果確認中（日程調整・報告待ち）"
  ];

  var state = {
    dataset: window.FINE_TELEAPO_VISIT_REPORT_DATA || { syncedAt: "", summary: {}, records: [], cybozuThreadsMonitored: [] },
    regionFilter: "ALL",
    statusFilter: "ALL",
    repFilter: "ALL",
    onlyReported: false,
    searchQuery: "",
    overrides: loadOverrides()
  };

  function loadOverrides() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY_PRES_OVERRIDE);
      return raw ? JSON.parse(raw) : {};
    } catch (_e) {
      return {};
    }
  }

  function saveOverrides() {
    try {
      localStorage.setItem(STORAGE_KEY_PRES_OVERRIDE, JSON.stringify(state.overrides));
    } catch (_e) {}
  }

  function getRecordStatus(rec) {
    var ov = state.overrides[rec.id];
    if (ov && ov.status) return ov.status;
    return rec.visitStatus || "⏳ 訪問結果確認中（日程調整・報告待ち）";
  }

  function getRecordPresidentMemo(rec) {
    var ov = state.overrides[rec.id];
    return (ov && ov.memo) ? ov.memo : "";
  }

  function getRecordManualReport(rec) {
    var ov = state.overrides[rec.id];
    return (ov && ov.manualReport) ? ov.manualReport : "";
  }

  function updateRecordOverride(recId, patch) {
    var cur = state.overrides[recId] || {};
    state.overrides[recId] = Object.assign({}, cur, patch, { updatedAt: new Date().toISOString() });
    saveOverrides();
  }

  function injectStyles() {
    if (document.getElementById("fvb-injected-styles")) return;
    var st = document.createElement("style");
    st.id = "fvb-injected-styles";
    st.textContent = [
      ".fvb-wrap{font-family:'Zen Kaku Gothic New','Hiragino Kaku Gothic ProN','BIZ UDPGothic',Meiryo,sans-serif;color:#0f172a;margin:12px 0 32px;}",
      ".fvb-hero{background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 60%,#0f766e 100%);color:#ffffff;border-radius:16px;padding:22px 24px;margin-bottom:18px;box-shadow:0 10px 25px rgba(15,23,42,0.16);border:2px solid #38bdf8;}",
      ".fvb-hero-top{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:10px;}",
      ".fvb-badge-auto{display:inline-flex;align-items:center;gap:6px;background:rgba(16,185,129,0.22);border:1.5px solid #34d399;color:#ecfdf5;padding:5px 13px;border-radius:999px;font-weight:900;font-size:13px;}",
      ".fvb-hero h2{margin:4px 0 8px;font-size:clamp(1.25rem,2.2vw,1.65rem);font-weight:900;line-height:1.35;color:#ffffff;}",
      ".fvb-hero p{margin:0;font-size:14.5px;line-height:1.65;color:#e2e8f0;}",
      ".fvb-threads-bar{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px;padding-top:12px;border-top:1px solid rgba(255,255,255,0.18);align-items:center;}",
      ".fvb-thread-chip{background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.28);color:#f8fafc;padding:4px 10px;border-radius:8px;font-size:12.5px;font-weight:700;}",
      ".fvb-hero-actions{display:flex;flex-wrap:wrap;gap:8px;align-items:center;}",
      ".fvb-btn{display:inline-flex;align-items:center;gap:6px;padding:9px 15px;border-radius:10px;font-weight:900;font-size:13.5px;cursor:pointer;border:1.5px solid transparent;text-decoration:none;transition:all 0.15s ease;}",
      ".fvb-btn-sync{background:#10b981;color:#052e16;border-color:#6ee7b7;}",
      ".fvb-btn-sync:hover{background:#34d399;}",
      ".fvb-btn-sheet{background:#f59e0b;color:#451a03;border-color:#fde68a;}",
      ".fvb-btn-sheet:hover{background:#fbbf24;}",
      ".fvb-btn-csv{background:rgba(255,255,255,0.14);color:#ffffff;border-color:rgba(255,255,255,0.35);}",
      ".fvb-btn-csv:hover{background:rgba(255,255,255,0.24);}",
      ".fvb-kpi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:12px;margin-bottom:18px;}",
      ".fvb-kpi-card{background:#ffffff;border:2px solid #cbd5e1;border-radius:14px;padding:14px 16px;box-shadow:0 2px 8px rgba(15,23,42,0.05);cursor:pointer;transition:transform 0.12s ease,border-color 0.12s ease;}",
      ".fvb-kpi-card:hover{transform:translateY(-2px);border-color:#2563eb;}",
      ".fvb-kpi-card.is-hot{border-color:#f59e0b;background:#fffbeb;}",
      ".fvb-kpi-card.is-green{border-color:#10b981;background:#ecfdf5;}",
      ".fvb-kpi-card.is-blue{border-color:#3b82f6;background:#eff6ff;}",
      ".fvb-kpi-label{font-size:12.5px;font-weight:800;color:#475569;margin-bottom:4px;}",
      ".fvb-kpi-val{font-size:26px;font-weight:900;color:#0f172a;line-height:1.2;}",
      ".fvb-kpi-sub{font-size:11.5px;font-weight:700;color:#64748b;margin-top:4px;}",
      ".fvb-filter-box{background:#ffffff;border:2px solid #cbd5e1;border-radius:14px;padding:16px;margin-bottom:18px;box-shadow:0 2px 8px rgba(15,23,42,0.04);}",
      ".fvb-filter-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-bottom:12px;}",
      ".fvb-field label{display:block;font-size:12.5px;font-weight:900;color:#1e3a8a;margin-bottom:5px;}",
      ".fvb-input,.fvb-select{width:100%;padding:9px 12px;border-radius:10px;border:1.5px solid #94a3b8;font-size:14px;font-weight:700;background:#f8fafc;color:#0f172a;box-sizing:border-box;}",
      ".fvb-input:focus,.fvb-select:focus{outline:none;border-color:#2563eb;background:#ffffff;box-shadow:0 0 0 3px rgba(37,99,235,0.15);}",
      ".fvb-pills-bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;padding-top:8px;border-top:1px dashed #cbd5e1;}",
      ".fvb-pill{padding:7px 14px;border-radius:999px;border:1.5px solid #94a3b8;background:#f8fafc;color:#334155;font-weight:800;font-size:13px;cursor:pointer;}",
      ".fvb-pill.is-active{background:#1e3a8a;color:#ffffff;border-color:#1e3a8a;}",
      ".fvb-cards-list{display:flex;flex-direction:column;gap:16px;}",
      ".fvb-card{background:#ffffff;border:2px solid #cbd5e1;border-radius:16px;padding:18px 20px;box-shadow:0 4px 12px rgba(15,23,42,0.05);transition:border-color 0.15s ease;}",
      ".fvb-card.has-report{border-left:8px solid #0d9488;}",
      ".fvb-card.is-contract{border-left:8px solid #d97706;background:#fffdf5;}",
      ".fvb-card.is-upcoming{border-left:8px solid #3b82f6;}",
      ".fvb-card-head{display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #e2e8f0;}",
      ".fvb-head-left{display:flex;flex-direction:column;gap:5px;}",
      ".fvb-badges{display:flex;flex-wrap:wrap;gap:6px;align-items:center;}",
      ".fvb-tag{display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;font-weight:900;}",
      ".fvb-tag-no{background:#0f172a;color:#ffffff;}",
      ".fvb-tag-region-kansai{background:#dbeafe;color:#1e40af;border:1px solid #93c5fd;}",
      ".fvb-tag-region-kanto{background:#fce7f3;color:#9d174d;border:1px solid #f9a8d4;}",
      ".fvb-tag-rank{background:#fef3c7;color:#92400e;border:1px solid #fcd34d;}",
      ".fvb-tag-status-hot{background:#dcfce7;color:#166534;border:1.5px solid #4ade80;font-size:13px;}",
      ".fvb-tag-status-talk{background:#ccfbf1;color:#115e59;border:1.5px solid #2dd4bf;font-size:13px;}",
      ".fvb-tag-status-doc{background:#f1f5f9;color:#334155;border:1.5px solid #94a3b8;font-size:13px;}",
      ".fvb-tag-status-plan{background:#eff6ff;color:#1d4ed8;border:1.5px solid #60a5fa;font-size:13px;}",
      ".fvb-shop-title{margin:2px 0 0;font-size:clamp(1.15rem,1.8vw,1.4rem);font-weight:900;color:#0f172a;display:flex;align-items:center;flex-wrap:wrap;gap:10px;}",
      ".fvb-meta-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 16px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:10px 14px;margin-bottom:14px;font-size:13.5px;}",
      ".fvb-meta-item b{color:#334155;}",
      ".fvb-two-col{display:grid;grid-template-columns:1.35fr 1fr;gap:14px;}",
      "@media (max-width:860px){.fvb-two-col{grid-template-columns:1fr;}}",
      ".fvb-report-box{background:#f0fdf4;border:2px solid #10b981;border-radius:12px;padding:14px 16px;}",
      ".fvb-report-box.is-empty{background:#f8fafc;border:2px dashed #94a3b8;}",
      ".fvb-box-title{font-size:13.5px;font-weight:900;color:#065f46;margin:0 0 8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;}",
      ".fvb-report-box.is-empty .fvb-box-title{color:#475569;}",
      ".fvb-verbatim-text{white-space:pre-wrap;font-size:14.5px;line-height:1.72;color:#0f172a;font-weight:600;background:#ffffff;border:1px solid #a7f3d0;border-radius:8px;padding:12px 14px;margin:0;font-family:inherit;}",
      ".fvb-teleapo-box{background:#eff6ff;border:1.5px solid #93c5fd;border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;justify-content:space-between;gap:10px;}",
      ".fvb-teleapo-title{font-size:13px;font-weight:900;color:#1e3a8a;margin:0 0 6px;}",
      ".fvb-teleapo-text{white-space:pre-wrap;font-size:13px;line-height:1.6;color:#1e293b;margin:0;}",
      ".fvb-pres-controls{margin-top:10px;padding-top:10px;border-top:1px dashed #93c5fd;display:flex;flex-direction:column;gap:8px;}",
      ".fvb-pres-row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;}",
      ".fvb-textarea{width:100%;padding:8px 10px;border-radius:8px;border:1.5px solid #94a3b8;font-size:13.5px;font-family:inherit;box-sizing:border-box;}"
    ].join("\n");
    document.head.appendChild(st);
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function statusTagClass(st) {
    if (st.indexOf("契約") !== -1 || st.indexOf("前向き") !== -1) return "fvb-tag fvb-tag-status-hot";
    if (st.indexOf("面談") !== -1) return "fvb-tag fvb-tag-status-talk";
    if (st.indexOf("訪問予定") !== -1 || st.indexOf("事前資料") !== -1) return "fvb-tag fvb-tag-status-plan";
    return "fvb-tag fvb-tag-status-doc";
  }

  function getFilteredRecords() {
    var recs = (state.dataset && state.dataset.records) || [];
    var q = (state.searchQuery || "").trim().toLowerCase();

    return recs.filter(function (r) {
      var st = getRecordStatus(r);
      var manualRep = getRecordManualReport(r);
      var hasRep = Boolean(r.hasVisitReport || manualRep);

      if (state.onlyReported && !hasRep) return false;
      if (state.regionFilter !== "ALL" && (r.regionGroup || "").indexOf(state.regionFilter) === -1) return false;
      if (state.statusFilter !== "ALL" && st !== state.statusFilter) return false;
      if (state.repFilter !== "ALL" && (r.salesRep || "").indexOf(state.repFilter) === -1 && (r.verbatimCombined || "").indexOf(state.repFilter) === -1) {
        return false;
      }

      if (q) {
        var hay = [
          r.apoNo,
          r.shopName,
          r.area,
          r.salesRep,
          r.teleapoStaff,
          r.contactName,
          r.tel,
          r.addr,
          r.verbatimCombined,
          r.teleapoMemo,
          getRecordPresidentMemo(r),
          manualRep
        ].join(" ").toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });
  }

  function exportVisitCsv() {
    var recs = getFilteredRecords();
    var headers = [
      "No", "アポ・訪問日時", "地域", "エリア", "テレアポ獲得担当", "訪問営業担当",
      "評価ランク", "企業・店舗名", "先方担当者", "電話番号", "住所",
      "訪問進捗ステータス", "営業訪問報告（サイボウズ日報原文）", "社長・幹部メモ", "テレアポ獲得時メモ"
    ];
    var lines = [headers.join(",")];
    recs.forEach(function (r) {
      var verb = r.verbatimCombined || "";
      var man = getRecordManualReport(r);
      if (man) verb = (verb ? verb + "\n\n" : "") + "【手動追記報告】\n" + man;
      var row = [
        r.apoNo,
        r.apoDateTime,
        r.regionGroup,
        r.area,
        r.teleapoStaff,
        r.salesRep,
        r.evalRank,
        r.shopName,
        r.contactName,
        r.tel,
        r.addr,
        getRecordStatus(r),
        verb,
        getRecordPresidentMemo(r),
        r.teleapoMemo
      ].map(function (v) {
        return '"' + String(v == null ? "" : v).replace(/"/g, '""') + '"';
      });
      lines.push(row.join(","));
    });
    var blob = new Blob(["\uFEFF" + lines.join("\r\n")], { type: "text/csv;charset=utf-8;" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "ファイングループ_テレアポ獲得_営業訪問結果台帳_" + new Date().toISOString().slice(0, 10) + ".csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function fetchLatestRemoteDataset(btnEl) {
    if (btnEl) {
      btnEl.disabled = true;
      btnEl.textContent = "⏳ 最新の日報データを同期中...";
    }
    fetch(REMOTE_JSON_URL + "?t=" + Date.now(), { cache: "no-store" })
      .then(function (res) {
        if (!res.ok) throw new Error("HTTP " + res.status);
        return res.json();
      })
      .then(function (json) {
        if (json && Array.isArray(json.records)) {
          state.dataset = json;
          window.FINE_TELEAPO_VISIT_REPORT_DATA = json;
          renderAllContainers();
        }
        if (btnEl) {
          btnEl.disabled = false;
          btnEl.textContent = "✅ 最新同期完了 (" + (json.syncedAt || "今") + ")";
          setTimeout(function () {
            btnEl.textContent = "🔄 最新のサイボウズ日報を再取得";
          }, 3000);
        }
      })
      .catch(function () {
        if (btnEl) {
          btnEl.disabled = false;
          btnEl.textContent = "✅ 最新データ反映済 (" + (state.dataset.syncedAt || "") + ")";
        }
      });
  }

  function renderBoardInto(container) {
    if (!container) return;
    injectStyles();

    var ds = state.dataset || { syncedAt: "-", summary: {}, records: [], cybozuThreadsMonitored: [] };
    var allRecs = ds.records || [];
    var filtered = getFilteredRecords();

    var totalCount = allRecs.length;
    var reportedCount = 0;
    var hotCount = 0;
    var upcomingCount = 0;
    var kansaiCount = 0;
    var kantoCount = 0;

    allRecs.forEach(function (r) {
      var st = getRecordStatus(r);
      var hasRep = Boolean(r.hasVisitReport || getRecordManualReport(r));
      if (hasRep) reportedCount++;
      if (st.indexOf("契約") !== -1 || st.indexOf("前向き") !== -1) hotCount++;
      if (st.indexOf("訪問予定") !== -1 || st.indexOf("事前資料") !== -1) upcomingCount++;
      if ((r.regionGroup || "").indexOf("関西") !== -1) kansaiCount++;
      if ((r.regionGroup || "").indexOf("関東") !== -1) kantoCount++;
    });

    var threadsHtml = (ds.cybozuThreadsMonitored || []).map(function (t) {
      return '<span class="fvb-thread-chip">📡 ' + escapeHtml(t.label) + '（' + escapeHtml(t.defaultRep) + '）</span>';
    }).join("");

    var statusOptsHtml = ['<option value="ALL">すべての訪問ステータス（全' + totalCount + '件）</option>']
      .concat(VISIT_STATUS_LIST.map(function (s) {
        return '<option value="' + escapeHtml(s) + '"' + (state.statusFilter === s ? " selected" : "") + '>' + escapeHtml(s) + '</option>';
      })).join("");

    var cardsHtml = filtered.map(function (r) {
      var st = getRecordStatus(r);
      var presMemo = getRecordPresidentMemo(r);
      var manualRep = getRecordManualReport(r);
      var combinedVerb = r.verbatimCombined || "";
      if (manualRep) {
        combinedVerb = (combinedVerb ? combinedVerb + "\n\n━━━━━━━━━━━━━━━\n" : "")
          + "📌 【Web画面からの追記報告】\n" + manualRep;
      }
      var hasRep = Boolean(combinedVerb);

      var cardCls = "fvb-card";
      if (st.indexOf("契約") !== -1 || st.indexOf("前向き") !== -1) cardCls += " is-contract";
      else if (hasRep) cardCls += " has-report";
      else if (st.indexOf("訪問予定") !== -1) cardCls += " is-upcoming";

      var isKansai = (r.regionGroup || "").indexOf("関西") !== -1;

      var perCardStatusOpts = VISIT_STATUS_LIST.map(function (s) {
        return '<option value="' + escapeHtml(s) + '"' + (st === s ? " selected" : "") + '>' + escapeHtml(s) + '</option>';
      }).join("");

      return [
        '<article class="' + cardCls + '" data-rec-id="' + escapeHtml(r.id) + '">',
        '  <div class="fvb-card-head">',
        '    <div class="fvb-head-left">',
        '      <div class="fvb-badges">',
        '        <span class="fvb-tag fvb-tag-no">アポNo.' + escapeHtml(r.apoNo) + '</span>',
        '        <span class="fvb-tag ' + (isKansai ? "fvb-tag-region-kansai" : "fvb-tag-region-kanto") + '">' + escapeHtml(r.area || r.regionGroup) + '</span>',
        '        <span class="fvb-tag fvb-tag-rank">評価: ' + escapeHtml(r.evalRank || "-") + '</span>',
        '        <span class="' + statusTagClass(st) + '">' + escapeHtml(st) + '</span>',
        '      </div>',
        '      <h3 class="fvb-shop-title">',
        '        <span>🏪 ' + escapeHtml(r.shopName) + '</span>',
        (r.tel ? '<a href="tel:' + escapeHtml(r.tel) + '" style="font-size:14px;color:#2563eb;text-decoration:none;background:#eff6ff;padding:3px 10px;border-radius:8px;border:1px solid #93c5fd;">📞 ' + escapeHtml(r.tel) + '</a>' : ''),
        (r.url ? '<a href="' + escapeHtml(r.url) + '" target="_blank" rel="noopener noreferrer" style="font-size:12.5px;color:#0f766e;text-decoration:none;background:#f0fdfa;padding:3px 9px;border-radius:8px;border:1px solid #5eead4;">🌐 店舗・企業HP</a>' : ''),
        '      </h3>',
        '    </div>',
        '    <div style="text-align:right;font-size:13px;font-weight:800;color:#334155;">',
        '      <div>📅 アポ・訪問日時：<strong style="color:#dc2626;font-size:14.5px;">' + escapeHtml(r.apoDateTime || "-") + '</strong></div>',
        '      <div style="margin-top:3px;">🏃 訪問営業：<strong style="color:#1e3a8a;">' + escapeHtml(r.salesRep || "-") + '</strong> ／ 📞 獲得：<strong>' + escapeHtml(r.teleapoStaff || "-") + '</strong></div>',
        '    </div>',
        '  </div>',
        '  <div class="fvb-meta-grid">',
        '    <div class="fvb-meta-item"><b>👤 先方ご担当者：</b>' + escapeHtml(r.contactName || "店長・採用ご担当者様") + '</div>',
        '    <div class="fvb-meta-item"><b>🍻 業態・規模：</b>' + escapeHtml(r.spec || r.listCategory || "-") + '</div>',
        '    <div class="fvb-meta-item" style="grid-column:1 / -1;"><b>📍 所在地：</b>' + escapeHtml(r.addr || "-") + '</div>',
        '  </div>',
        '  <div class="fvb-two-col">',
        '    <div class="fvb-report-box' + (hasRep ? "" : " is-empty") + '">',
        '      <div class="fvb-box-title">',
        '        <span>' + (hasRep ? "📋 営業訪問報告（サイボウズ日報より原文そのまま自動転記）" : "⏳ サイボウズ訪問報告（訪問前・または日報書き込み待ち）") + '</span>',
        '        <span style="font-size:11.5px;font-weight:700;">' + (hasRep ? ("自動検出 " + r.visitReportsCount + "件") : "サイボウズ自動巡回対象") + '</span>',
        '      </div>',
        (hasRep
          ? '<pre class="fvb-verbatim-text">' + escapeHtml(combinedVerb) + '</pre>'
          : '<div style="font-size:13.5px;color:#475569;line-height:1.6;padding:8px 4px;">まだサイボウズ日報（戸井日報・有福日報・富田日報・全国テレアポ報告）にこの店舗の訪問後コメントが投稿されていません。<br>営業さんがサイボウズに店名入りで日報を書くと自動でここに原文転記されます（下の欄から手動で追記することも可能です）。</div>'),
        '    </div>',
        '    <div class="fvb-teleapo-box">',
        '      <div>',
        '        <div class="fvb-teleapo-title">📞 テレアポ獲得時のヒアリング・引継ぎ内容</div>',
        '        <p class="fvb-teleapo-text">' + escapeHtml(r.teleapoMemo || "（特記事項なし）") + '</p>',
        '      </div>',
        '      <div class="fvb-pres-controls">',
        '        <div class="fvb-pres-row">',
        '          <label style="font-size:12px;font-weight:900;color:#1e3a8a;">👑 進捗ステータス変更：</label>',
        '          <select class="fvb-select js-fvb-status-sel" data-id="' + escapeHtml(r.id) + '" style="flex:1;padding:5px 8px;font-size:12.5px;">',
        perCardStatusOpts,
        '          </select>',
        '        </div>',
        '        <div>',
        '          <textarea class="fvb-textarea js-fvb-pres-memo" data-id="' + escapeHtml(r.id) + '" rows="2" placeholder="✍️ 社長コメント・次回フォロー指示メモ（入力すると自動保存されます）">' + escapeHtml(presMemo) + '</textarea>',
        '        </div>',
        '      </div>',
        '    </div>',
        '  </div>',
        '</article>'
      ].join("\n");
    }).join("\n");

    container.innerHTML = [
      '<div class="fvb-wrap">',
      '  <div class="fvb-hero">',
      '    <div class="fvb-hero-top">',
      '      <div>',
      '        <span class="fvb-badge-auto">🤖 営業さんの追加負担ゼロ｜サイボウズOffice「報告書」1時間おき全自動回収＆原文そのまま転記</span>',
      '        <h2>👑 社長専用：テレアポ獲得案件「営業訪問後の商談結果＆進捗管理ボード」</h2>',
      '        <p>',
      '          テレアポで獲得したアポ案件に対し、営業さんが訪問して<strong>「誰とどんな話をしたのか」「人材・お魚（ファインアトラス）の感触はどうだったか」</strong>を、サイボウズOfficeの日報から自動抽出して<strong>原文そのまま</strong>集約しています。<br>',
      '          営業さんは普段通りサイボウズの日報に書くだけで、自動的にこのボードとGoogleスプレッドシート（<code>📋テレアポ獲得_営業訪問結果台帳</code>）が最新化されます。',
      '        </p>',
      '      </div>',
      '      <div class="fvb-hero-actions">',
      '        <button type="button" class="fvb-btn fvb-btn-sync js-fvb-sync-btn">🔄 最新のサイボウズ日報を再取得</button>',
      '        <a href="' + REPORT_SHEET_URL + '" target="_blank" rel="noopener noreferrer" class="fvb-btn fvb-btn-sheet">📊 Googleスプレッドシート台帳を開く</a>',
      '        <button type="button" class="fvb-btn fvb-btn-csv js-fvb-csv-btn">📥 訪問結果一覧をCSV出力</button>',
      '      </div>',
      '    </div>',
      '    <div class="fvb-threads-bar">',
      '      <span style="font-size:12.5px;font-weight:900;color:#93c5fd;">自動巡回中のサイボウズ報告書（最終同期: ' + escapeHtml(ds.syncedAt || "-") + '）：</span>',
      threadsHtml,
      '    </div>',
      '  </div>',
      '  <div class="fvb-kpi-grid">',
      '    <div class="fvb-kpi-card js-fvb-kpi-filter" data-kfilter="ALL">',
      '      <div class="fvb-kpi-label">📋 テレアポ獲得・訪問追跡 総数</div>',
      '      <div class="fvb-kpi-val">' + totalCount + ' <small style="font-size:14px;">件</small></div>',
      '      <div class="fvb-kpi-sub">関西 ' + kansaiCount + '件 ／ 関東 ' + kantoCount + '件（クリックで全件）</div>',
      '    </div>',
      '    <div class="fvb-kpi-card is-green js-fvb-kpi-filter" data-kfilter="REPORTED">',
      '      <div class="fvb-kpi-label">✅ 営業訪問済・サイボウズ報告回収済</div>',
      '      <div class="fvb-kpi-val" style="color:#047857;">' + reportedCount + ' <small style="font-size:14px;">件</small></div>',
      '      <div class="fvb-kpi-sub">日報原文そのまま転記済（クリックで絞り込み）</div>',
      '    </div>',
      '    <div class="fvb-kpi-card is-hot js-fvb-kpi-filter" data-kfilter="HOT">',
      '      <div class="fvb-kpi-label">🔥 契約進行中・前向き商談（A/B高確度）</div>',
      '      <div class="fvb-kpi-val" style="color:#b45309;">' + hotCount + ' <small style="font-size:14px;">件</small></div>',
      '      <div class="fvb-kpi-sub">竹葉亭(水産+人材)・すし萬・ココス・ひらまつ等</div>',
      '    </div>',
      '    <div class="fvb-kpi-card is-blue js-fvb-kpi-filter" data-kfilter="UPCOMING">',
      '      <div class="fvb-kpi-label">🗓️ これから訪問予定（アポ確定済）</div>',
      '      <div class="fvb-kpi-val" style="color:#1d4ed8;">' + upcomingCount + ' <small style="font-size:14px;">件</small></div>',
      '      <div class="fvb-kpi-sub">11/26〜12/3 訪問予定（訪問後に自動転記）</div>',
      '    </div>',
      '  </div>',
      '  <div class="fvb-filter-box">',
      '    <div class="fvb-filter-row">',
      '      <div class="fvb-field">',
      '        <label>🔍 店舗・企業名・営業担当・会話キーワードで検索</label>',
      '        <input type="search" class="fvb-input js-fvb-search" value="' + escapeHtml(state.searchQuery) + '" placeholder="例：竹葉亭、すし萬、大起水産、ココス、穴子、タイミー、本社..." />',
      '      </div>',
      '      <div class="fvb-field">',
      '        <label>🗾 地域エリア（関西 ／ 関東）</label>',
      '        <select class="fvb-select js-fvb-region">',
      '          <option value="ALL"' + (state.regionFilter === "ALL" ? " selected" : "") + '>全国すべて（関西＋関東）</option>',
      '          <option value="関西"' + (state.regionFilter === "関西" ? " selected" : "") + '>🏠 関西（大阪・梅田・難波・天王寺・京橋）</option>',
      '          <option value="関東"' + (state.regionFilter === "関東" ? " selected" : "") + '>🗼 関東（東京・新宿・神楽坂・首都圏本社）</option>',
      '        </select>',
      '      </div>',
      '      <div class="fvb-field">',
      '        <label>🏃 訪問営業担当（サイボウズ日報）</label>',
      '        <select class="fvb-select js-fvb-rep">',
      '          <option value="ALL"' + (state.repFilter === "ALL" ? " selected" : "") + '>すべての営業担当者</option>',
      '          <option value="戸井"' + (state.repFilter === "戸井" ? " selected" : "") + '>関西：戸井 麻衣 日報</option>',
      '          <option value="富田"' + (state.repFilter === "富田" ? " selected" : "") + '>関西：富田 湧介 日報（アトラス＋同行）</option>',
      '          <option value="有福"' + (state.repFilter === "有福" ? " selected" : "") + '>関東：有福 浩一_日報</option>',
      '          <option value="西川"' + (state.repFilter === "西川" ? " selected" : "") + '>関東：西川 ひなの（有福日報）</option>',
      '          <option value="宮川"' + (state.repFilter === "宮川" ? " selected" : "") + '>関西：宮川 玲子・山上 海優</option>',
      '        </select>',
      '      </div>',
      '      <div class="fvb-field">',
      '        <label>📊 訪問後の商談ステータス</label>',
      '        <select class="fvb-select js-fvb-status">',
      statusOptsHtml,
      '        </select>',
      '      </div>',
      '    </div>',
      '    <div class="fvb-pills-bar">',
      '      <div style="display:flex;flex-wrap:wrap;gap:8px;">',
      '        <button type="button" class="fvb-pill js-fvb-toggle-reported' + (state.onlyReported ? " is-active" : "") + '">📋 訪問報告（原文）がある案件のみ表示</button>',
      '        <button type="button" class="fvb-pill js-fvb-reset">🔄 絞り込みリセット</button>',
      '      </div>',
      '      <div style="font-size:14px;font-weight:900;color:#1e3a8a;">表示中: ' + filtered.length + ' 件 ／ 全 ' + totalCount + ' 件</div>',
      '    </div>',
      '  </div>',
      '  <div class="fvb-cards-list">',
      (cardsHtml || '<div style="padding:36px;text-align:center;background:#ffffff;border-radius:14px;border:2px dashed #94a3b8;font-weight:800;color:#475569;">条件に一致する訪問報告がありません。「🔄 絞り込みリセット」を押してください。</div>'),
      '  </div>',
      '</div>'
    ].join("\n");

    // Wire events
    var syncBtn = container.querySelector(".js-fvb-sync-btn");
    if (syncBtn) {
      syncBtn.addEventListener("click", function () {
        fetchLatestRemoteDataset(syncBtn);
      });
    }
    var csvBtn = container.querySelector(".js-fvb-csv-btn");
    if (csvBtn) {
      csvBtn.addEventListener("click", exportVisitCsv);
    }
    var searchInp = container.querySelector(".js-fvb-search");
    if (searchInp) {
      searchInp.addEventListener("input", function (e) {
        state.searchQuery = e.target.value;
        var pos = e.target.selectionStart;
        renderBoardInto(container);
        var newInp = container.querySelector(".js-fvb-search");
        if (newInp) {
          newInp.focus();
          try { newInp.setSelectionRange(pos, pos); } catch (_e) {}
        }
      });
    }
    var regSel = container.querySelector(".js-fvb-region");
    if (regSel) {
      regSel.addEventListener("change", function (e) {
        state.regionFilter = e.target.value;
        renderBoardInto(container);
      });
    }
    var repSel = container.querySelector(".js-fvb-rep");
    if (repSel) {
      repSel.addEventListener("change", function (e) {
        state.repFilter = e.target.value;
        renderBoardInto(container);
      });
    }
    var stSel = container.querySelector(".js-fvb-status");
    if (stSel) {
      stSel.addEventListener("change", function (e) {
        state.statusFilter = e.target.value;
        renderBoardInto(container);
      });
    }
    var repToggle = container.querySelector(".js-fvb-toggle-reported");
    if (repToggle) {
      repToggle.addEventListener("click", function () {
        state.onlyReported = !state.onlyReported;
        renderBoardInto(container);
      });
    }
    var resetBtn = container.querySelector(".js-fvb-reset");
    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        state.regionFilter = "ALL";
        state.statusFilter = "ALL";
        state.repFilter = "ALL";
        state.onlyReported = false;
        state.searchQuery = "";
        renderBoardInto(container);
      });
    }
    container.querySelectorAll(".js-fvb-kpi-filter").forEach(function (card) {
      card.addEventListener("click", function () {
        var kf = card.getAttribute("data-kfilter");
        state.regionFilter = "ALL";
        state.repFilter = "ALL";
        state.searchQuery = "";
        if (kf === "ALL") {
          state.onlyReported = false;
          state.statusFilter = "ALL";
        } else if (kf === "REPORTED") {
          state.onlyReported = true;
          state.statusFilter = "ALL";
        } else if (kf === "HOT") {
          state.onlyReported = false;
          state.statusFilter = "🤝 責任者商談済（前向き・本部/社内検討）";
        } else if (kf === "UPCOMING") {
          state.onlyReported = false;
          state.statusFilter = "🗓️ 訪問予定（アポ確定・訪問前）";
        }
        renderBoardInto(container);
      });
    });

    container.querySelectorAll(".js-fvb-status-sel").forEach(function (sel) {
      sel.addEventListener("change", function (e) {
        var id = e.target.getAttribute("data-id");
        updateRecordOverride(id, { status: e.target.value });
        renderBoardInto(container);
      });
    });

    container.querySelectorAll(".js-fvb-pres-memo").forEach(function (ta) {
      ta.addEventListener("change", function (e) {
        var id = e.target.getAttribute("data-id");
        updateRecordOverride(id, { memo: e.target.value });
      });
    });
  }

  function renderAllContainers() {
    document.querySelectorAll(".js-fine-visit-board-container").forEach(function (el) {
      renderBoardInto(el);
    });
  }

  window.FineVisitBoard = {
    render: renderAllContainers,
    renderInto: renderBoardInto,
    refreshRemote: fetchLatestRemoteDataset
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderAllContainers);
  } else {
    renderAllContainers();
  }
})();
