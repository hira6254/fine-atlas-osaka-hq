/**
 * 株式会社ファインアトラス｜大阪本社 外食・寿司・海鮮居酒屋チェーン本部 テレアポ営業コンパス
 * フロントエンドロジック (app.js)
 */
(function () {
  "use strict";

  const STORAGE_KEY_STATUS = "fa_osaka_hq_status_v1";
  const STORAGE_KEY_MEMO = "fa_osaka_hq_memo_v1";
  const STORAGE_KEY_FONT = "fa_osaka_hq_font_v1";

  const STATUS_OPTIONS = [
    "未架電",
    "受付・資料送付済",
    "バイヤー不在・再架電",
    "サンプル・お試し送付",
    "商談・試食アポ獲得",
    "テスト導入・成約",
    "見送り・時期改め"
  ];

  const data = window.OSAKA_HQ_DATA || {
    companies: [],
    hqScripts: [],
    hqObjections: [],
    productsCatalog: []
  };

  let statusMap = loadJson(STORAGE_KEY_STATUS, {});
  let memoMap = loadJson(STORAGE_KEY_MEMO, {});

  function loadJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (_e) {
      return fallback;
    }
  }

  function saveJson(key, val) {
    try {
      localStorage.setItem(key, JSON.stringify(val));
    } catch (_e) {
      // ignore storage quota errors
    }
  }

  function showToast(msg) {
    const el = document.getElementById("toastNotice");
    if (!el) return;
    el.textContent = msg;
    el.hidden = false;
    clearTimeout(el._timer);
    el._timer = setTimeout(function () {
      el.hidden = true;
    }, 2200);
  }

  function copyToClipboard(text, label) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        showToast("📋 " + label + " をコピーしました");
      });
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      showToast("📋 " + label + " をコピーしました");
    }
  }

  function getCompanyStatus(id) {
    return statusMap[id] || "未架電";
  }

  function getCompanyMemo(id) {
    return memoMap[id] || "";
  }

  function updateKpiCounters() {
    const companies = data.companies;
    const total = companies.length;
    const rankS = companies.filter(function (c) { return c.rank === "S"; }).length;
    const rankA = companies.filter(function (c) { return c.rank === "A"; }).length;

    let calledCount = 0;
    let orderedCount = 0;
    companies.forEach(function (c) {
      const st = getCompanyStatus(c.id);
      if (st !== "未架電") calledCount++;
      if (st === "サンプル・お試し送付" || st === "商談・試食アポ獲得" || st === "テスト導入・成約") {
        orderedCount++;
      }
    });

    document.getElementById("kpiTotal").textContent = String(total);
    document.getElementById("kpiRankS").textContent = String(rankS);
    document.getElementById("kpiRankA").textContent = String(rankA);
    document.getElementById("kpiCalled").textContent = String(calledCount);
    document.getElementById("kpiOrdered").textContent = String(orderedCount);
  }

  function renderCompanyCards() {
    const container = document.getElementById("companyCardsContainer");
    const q = (document.getElementById("searchInput").value || "").trim().toLowerCase();
    const rankVal = document.getElementById("rankFilter").value;
    const catVal = document.getElementById("categoryFilter").value;
    const areaVal = document.getElementById("areaFilter").value;
    const fishVal = document.getElementById("fishFilter").value;
    const statusVal = document.getElementById("statusFilter").value;

    const filtered = data.companies.filter(function (c) {
      if (rankVal !== "ALL" && c.rank !== rankVal) return false;
      if (catVal !== "ALL" && c.category !== catVal) return false;
      if (areaVal !== "ALL" && c.areaGroup !== areaVal) return false;
      if (fishVal !== "ALL" && (c.recommendedFish || "").indexOf(fishVal) === -1) return false;

      const st = getCompanyStatus(c.id);
      if (statusVal !== "ALL" && st !== statusVal) return false;

      if (q) {
        const hay = [
          c.id,
          c.companyName,
          c.brands,
          c.address,
          c.areaGroup,
          c.recommendedFish,
          c.pitchAngle,
          c.targetDept,
          c.representative,
          getCompanyMemo(c.id)
        ].join(" ").toLowerCase();
        if (hay.indexOf(q) === -1) return false;
      }
      return true;
    });

    document.getElementById("filteredCount").textContent = String(filtered.length);
    document.getElementById("tabCountBadge").textContent = String(filtered.length);
    container.textContent = "";

    filtered.forEach(function (comp) {
      const card = document.createElement("article");
      card.className = "company-card rank-" + comp.rank;

      // Top part
      const topDiv = document.createElement("div");

      // Badges
      const badgesRow = document.createElement("div");
      badgesRow.className = "card-top-badges";

      const rankBadge = document.createElement("span");
      rankBadge.className = "rank-badge rank-" + comp.rank;
      rankBadge.textContent = comp.rank === "S"
        ? "🔥 Sランク（最優先・直球）"
        : (comp.rank === "A" ? "⭐ Aランク（重点本部）" : "🍤 Bランク（専門チェーン）");

      const areaBadge = document.createElement("span");
      areaBadge.className = "area-badge";
      areaBadge.textContent = comp.areaGroup;

      badgesRow.appendChild(rankBadge);
      badgesRow.appendChild(areaBadge);
      topDiv.appendChild(badgesRow);

      // Company Name
      const h3 = document.createElement("h3");
      h3.className = "company-name";
      h3.textContent = comp.companyName;
      topDiv.appendChild(h3);

      // Brands
      const brandsBox = document.createElement("div");
      brandsBox.className = "brands-box";
      brandsBox.textContent = "🏪 展開屋号：" + comp.brands;
      topDiv.appendChild(brandsBox);

      // Meta list
      const metaList = document.createElement("div");
      metaList.className = "meta-list";

      const items = [
        ["📍 本社所在地：", comp.postalCode + " " + comp.address],
        ["🏬 店舗規模：", comp.storeCountScale + "（代表：" + comp.representative + "）"],
        ["🎯 狙う部署：", comp.targetDept]
      ];
      items.forEach(function (pair) {
        const row = document.createElement("div");
        row.className = "meta-item";
        const st = document.createElement("strong");
        st.textContent = pair[0];
        const sp = document.createElement("span");
        sp.textContent = pair[1];
        row.appendChild(st);
        row.appendChild(sp);
        metaList.appendChild(row);
      });
      topDiv.appendChild(metaList);

      // Fish tags
      const fishTags = document.createElement("div");
      fishTags.className = "fish-tags";
      (comp.recommendedFish || "").split("/").forEach(function (f) {
        const tag = document.createElement("span");
        tag.className = "fish-tag";
        tag.textContent = "🐟 " + f.trim();
        fishTags.appendChild(tag);
      });
      topDiv.appendChild(fishTags);

      // Pitch box
      const pitchBox = document.createElement("div");
      pitchBox.className = "pitch-box";
      const pitchStrong = document.createElement("strong");
      pitchStrong.textContent = "💡 本部攻略の切り口：";
      const pitchText = document.createElement("span");
      pitchText.textContent = comp.pitchAngle;
      pitchBox.appendChild(pitchStrong);
      pitchBox.appendChild(pitchText);
      topDiv.appendChild(pitchBox);

      card.appendChild(topDiv);

      // Bottom Actions + Status
      const bottomDiv = document.createElement("div");

      const actionRow = document.createElement("div");
      actionRow.className = "card-action-row";

      const callLink = document.createElement("a");
      callLink.className = "btn-call";
      callLink.href = "tel:" + comp.phone;
      callLink.textContent = "📞 " + comp.phone;

      const cueBtn = document.createElement("button");
      cueBtn.type = "button";
      cueBtn.className = "btn-cue-modal";
      cueBtn.textContent = "🎤 受付＆バイヤートーク";
      cueBtn.addEventListener("click", function () {
        openScriptModal(comp);
      });

      actionRow.appendChild(callLink);
      actionRow.appendChild(cueBtn);
      bottomDiv.appendChild(actionRow);

      // Status & Memo
      const statusBox = document.createElement("div");
      statusBox.className = "status-memo-box";

      const statusRow = document.createElement("div");
      statusRow.className = "status-row";

      const statusSelect = document.createElement("select");
      statusSelect.className = "status-select";
      STATUS_OPTIONS.forEach(function (opt) {
        const o = document.createElement("option");
        o.value = opt;
        o.textContent = "進捗: " + opt;
        if (opt === getCompanyStatus(comp.id)) o.selected = true;
        statusSelect.appendChild(o);
      });
      statusSelect.addEventListener("change", function () {
        statusMap[comp.id] = statusSelect.value;
        saveJson(STORAGE_KEY_STATUS, statusMap);
        updateKpiCounters();
        showToast("✅ " + comp.companyName + " の進捗を保存しました");
      });

      const webLink = document.createElement("a");
      webLink.href = comp.website;
      webLink.target = "_blank";
      webLink.rel = "noopener noreferrer";
      webLink.className = "btn-secondary";
      webLink.style.textDecoration = "none";
      webLink.textContent = "🌐 公式HP";

      statusRow.appendChild(statusSelect);
      statusRow.appendChild(webLink);
      statusBox.appendChild(statusRow);

      const memoInput = document.createElement("input");
      memoInput.type = "text";
      memoInput.className = "memo-input";
      memoInput.placeholder = "📝 バイヤー氏名・在席曜日・次回架電メモ（自動保存）";
      memoInput.value = getCompanyMemo(comp.id);
      memoInput.addEventListener("change", function () {
        memoMap[comp.id] = memoInput.value;
        saveJson(STORAGE_KEY_MEMO, memoMap);
        showToast("📝 メモを自動保存しました");
      });
      statusBox.appendChild(memoInput);

      bottomDiv.appendChild(statusBox);
      card.appendChild(bottomDiv);

      container.appendChild(card);
    });
  }

  function renderScriptsAndProducts() {
    // Tab 2: HQ Scripts
    const scriptsContainer = document.getElementById("hqScriptsContainer");
    scriptsContainer.textContent = "";
    data.hqScripts.forEach(function (sc) {
      const box = document.createElement("div");
      box.className = "script-card";

      const badge = document.createElement("span");
      badge.className = "script-step-badge";
      badge.textContent = sc.step + "｜対象：" + sc.target;

      const h3 = document.createElement("h3");
      h3.textContent = sc.title;

      const pt = document.createElement("p");
      pt.textContent = "💡 急所：" + sc.point;

      const pre = document.createElement("div");
      pre.className = "script-body-pre";
      pre.textContent = sc.script;

      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "btn-copy-script";
      copyBtn.textContent = "📋 このトークをコピー";
      copyBtn.addEventListener("click", function () {
        copyToClipboard(sc.script, sc.title);
      });

      box.appendChild(badge);
      box.appendChild(h3);
      box.appendChild(pt);
      box.appendChild(pre);
      box.appendChild(copyBtn);
      scriptsContainer.appendChild(box);
    });

    // Tab 2: Objections
    const objContainer = document.getElementById("hqObjectionsContainer");
    objContainer.textContent = "";
    data.hqObjections.forEach(function (ob) {
      const card = document.createElement("div");
      card.className = "objection-card";

      const h3 = document.createElement("h3");
      h3.textContent = ob.title;

      const pre = document.createElement("div");
      pre.className = "script-body-pre";
      pre.textContent = ob.answer;

      const copyBtn = document.createElement("button");
      copyBtn.type = "button";
      copyBtn.className = "btn-copy-script";
      copyBtn.textContent = "📋 切り返しトークをコピー";
      copyBtn.addEventListener("click", function () {
        copyToClipboard(ob.answer, ob.title);
      });

      card.appendChild(h3);
      card.appendChild(pre);
      card.appendChild(copyBtn);
      objContainer.appendChild(card);
    });

    // Tab 3: Products
    const prodContainer = document.getElementById("productsCatalogContainer");
    prodContainer.textContent = "";
    data.productsCatalog.forEach(function (pr) {
      const card = document.createElement("div");
      card.className = "product-card";

      const badge = document.createElement("span");
      badge.className = "script-step-badge";
      badge.textContent = pr.code;

      const h3 = document.createElement("h3");
      h3.textContent = pr.name;

      const pTarget = document.createElement("p");
      pTarget.textContent = "🎯 推奨チェーン：" + pr.targetChain;

      const pPrep = document.createElement("p");
      pPrep.textContent = "🔪 下処理規格：" + pr.prepState;

      const pMerit = document.createElement("div");
      pMerit.className = "pitch-box";
      pMerit.textContent = "✅ 本部導入メリット：" + pr.chainMerit;

      const pMenu = document.createElement("p");
      pMenu.style.fontWeight = "700";
      pMenu.textContent = "🍽️ 提案メニュー例：" + pr.menuExample;

      card.appendChild(badge);
      card.appendChild(h3);
      card.appendChild(pTarget);
      card.appendChild(pPrep);
      card.appendChild(pMerit);
      card.appendChild(pMenu);
      prodContainer.appendChild(card);
    });
  }

  function openScriptModal(comp) {
    const modal = document.getElementById("scriptModal");
    document.getElementById("modalRankBadge").className = "rank-badge rank-" + comp.rank;
    document.getElementById("modalRankBadge").textContent = comp.rank + "ランク｜" + comp.areaGroup;
    document.getElementById("modalCompanyName").textContent = comp.companyName;
    document.getElementById("modalBrands").textContent = "展開ブランド：" + comp.brands + "（" + comp.storeCountScale + "）";

    const callLink = document.getElementById("modalCallLink");
    callLink.href = "tel:" + comp.phone;
    document.getElementById("modalPhoneText").textContent = comp.phone;
    document.getElementById("modalTargetDept").textContent = comp.targetDept;
    document.getElementById("modalRecFish").textContent = comp.recommendedFish;

    document.getElementById("modalScriptReception").textContent = comp.callScriptReception;
    document.getElementById("modalScriptBuyer").textContent = comp.callScriptBuyer;
    document.getElementById("modalPitchAngle").textContent = comp.pitchAngle;

    document.getElementById("btnCopyReception").onclick = function () {
      copyToClipboard(comp.callScriptReception, comp.companyName + " 受付突破トーク");
    };
    document.getElementById("btnCopyBuyer").onclick = function () {
      copyToClipboard(comp.callScriptBuyer, comp.companyName + " バイヤー接続トーク");
    };

    const objList = document.getElementById("modalObjectionsList");
    objList.textContent = "";
    data.hqObjections.forEach(function (ob) {
      const wrap = document.createElement("div");
      wrap.className = "objection-card";
      wrap.style.marginBottom = "0.75rem";
      const h4 = document.createElement("h3");
      h4.textContent = ob.title;
      const ans = document.createElement("div");
      ans.className = "script-body-pre";
      ans.textContent = ob.answer;
      wrap.appendChild(h4);
      wrap.appendChild(ans);
      objList.appendChild(wrap);
    });

    modal.hidden = false;
  }

  function exportCsv() {
    const headers = [
      "管理ID",
      "優先ランク",
      "業態カテゴリ",
      "運営会社名（大阪本社）",
      "本社エリア区分",
      "本社電話番号",
      "郵便番号",
      "本社所在地",
      "代表者",
      "展開店舗規模",
      "主な展開ブランド",
      "狙うべき本部部署",
      "推奨アプローチ魚種",
      "架電進捗ステータス",
      "バイヤー氏名・架電メモ",
      "公式Webサイト"
    ];

    const sanitizeCsvCell = function (val) {
      let s = String(val == null ? "" : val).replace(/\r?\n/g, " ");
      if (s && ["=", "+", "-", "@"].indexOf(s[0]) !== -1) {
        s = "'" + s;
      }
      return '"' + s.replace(/"/g, '""') + '"';
    };

    const rows = [headers.map(sanitizeCsvCell).join(",")];
    data.companies.forEach(function (c) {
      rows.push([
        c.id,
        c.rank,
        c.category,
        c.companyName,
        c.areaGroup,
        c.phone,
        c.postalCode,
        c.address,
        c.representative,
        c.storeCountScale,
        c.brands,
        c.targetDept,
        c.recommendedFish,
        getCompanyStatus(c.id),
        getCompanyMemo(c.id),
        c.website
      ].map(sanitizeCsvCell).join(","));
    });

    const bom = "\uFEFF";
    const blob = new Blob([bom + rows.join("\r\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ファインアトラス_大阪本社チェーン本部_架電進捗リスト.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("📤 架電メモ付きCSVをダウンロードしました");
  }

  function initEvents() {
    // Filter listeners
    ["searchInput", "rankFilter", "categoryFilter", "areaFilter", "fishFilter", "statusFilter"].forEach(function (id) {
      const el = document.getElementById(id);
      if (!el) return;
      el.addEventListener("input", renderCompanyCards);
      el.addEventListener("change", renderCompanyCards);
    });

    document.getElementById("btnResetFilters").addEventListener("click", function () {
      document.getElementById("searchInput").value = "";
      document.getElementById("rankFilter").value = "ALL";
      document.getElementById("categoryFilter").value = "ALL";
      document.getElementById("areaFilter").value = "ALL";
      document.getElementById("fishFilter").value = "ALL";
      document.getElementById("statusFilter").value = "ALL";
      renderCompanyCards();
    });

    document.getElementById("btnExportCsv").addEventListener("click", exportCsv);

    // Main tab switchers
    document.querySelectorAll(".tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".tab-btn").forEach(function (b) { b.classList.remove("active"); });
        document.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.remove("active"); });
        btn.classList.add("active");
        const target = document.getElementById(btn.getAttribute("data-tab"));
        if (target) target.classList.add("active");
      });
    });

    // Modal tab switchers
    document.querySelectorAll(".modal-tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".modal-tab-btn").forEach(function (b) { b.classList.remove("active"); });
        document.querySelectorAll(".modal-tab-content").forEach(function (c) { c.classList.remove("active"); });
        btn.classList.add("active");
        const target = document.getElementById(btn.getAttribute("data-mtab"));
        if (target) target.classList.add("active");
      });
    });

    document.getElementById("btnCloseModal").addEventListener("click", function () {
      document.getElementById("scriptModal").hidden = true;
    });

    document.getElementById("scriptModal").addEventListener("click", function (e) {
      if (e.target.id === "scriptModal") {
        document.getElementById("scriptModal").hidden = true;
      }
    });

    // Font switcher
    const savedFont = localStorage.getItem(STORAGE_KEY_FONT) || "large";
    setFontSize(savedFont);
    document.querySelectorAll(".btn-font").forEach(function (btn) {
      btn.addEventListener("click", function () {
        setFontSize(btn.getAttribute("data-size"));
      });
    });
  }

  function setFontSize(size) {
    document.body.className = "font-" + size;
    localStorage.setItem(STORAGE_KEY_FONT, size);
    document.querySelectorAll(".btn-font").forEach(function (btn) {
      btn.classList.toggle("active", btn.getAttribute("data-size") === size);
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    updateKpiCounters();
    renderCompanyCards();
    renderScriptsAndProducts();
    initEvents();
  });
})();
