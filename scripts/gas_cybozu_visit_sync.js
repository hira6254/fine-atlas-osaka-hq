/**
 * 👑 社長専用：テレアポ獲得案件 → サイボウズ営業日報（訪問報告）1時間おき自動回収＆原文そのまま転記エンジン
 *
 * 【機能概要】
 * 1. サイボウズOffice「報告書」の7大営業日報スレッド（関西：戸井 麻衣 日報 / 関東：有福 浩一_日報 /
 *    関西：富田 湧介_日報 / 【FS】全国テレアポ 報告 / 関西：藤井 皓一朗 日報 / 関西：宮川 玲子 日報 / 関西：山上 海優 日報）
 *    をバックグラウンドで自動巡回し、テレアポ獲得案件（🏆獲得アポ一覧_詳細台帳）の店舗名と自動突合します。
 * 2. 営業さんが普段通りサイボウズに書いた訪問報告（【トピックス】◆店舗名、◇商談内容、①〜⑩累計報告など）を
 *    要約・改変せず「原文そのまま」抽出し、シート『📋テレアポ獲得_営業訪問結果台帳』および
 *    架電デスク画面上の『👑 訪問商談・結果管理（社長ボード）』タブへ全自動反映します。
 * 3. 初回1回だけ `setupHourlyCybozuVisitReportTrigger()` を実行すれば、1時間おき自動トリガーが重複ゼロで設置されます。
 */

var VISIT_REPORT_LEDGER_SHEET_ = '📋テレアポ獲得_営業訪問結果台帳';
var VISIT_REPORT_TRIGGER_HANDLER_ = 'syncCybozuVisitReportsToLedgerInGas';

var CYBOZU_VISIT_THREADS_ = [
  { rRID: '6645', label: '関西：戸井 麻衣 日報', region: '関西（大阪・梅田・難波）', defaultRep: '戸井 麻衣' },
  { rRID: '69', label: '関東：有福 浩一_日報', region: '関東（東京・新宿・本社）', defaultRep: '有福 浩一・西川 ひなの' },
  { rRID: '243259', label: '関西：富田 湧介_日報', region: '関西（大阪・アトラス同行）', defaultRep: '富田 湧介' },
  { rRID: '124797', label: '【FS】全国テレアポ 報告', region: '全国（関西・関東・本社）', defaultRep: '各拠点営業担当' },
  { rRID: '144', label: '関西：藤井 皓一朗 日報', region: '関西（神戸・大阪）', defaultRep: '藤井 皓一朗' },
  { rRID: '6653', label: '関西：宮川 玲子 日報', region: '関西（大阪・京都）', defaultRep: '宮川 玲子' },
  { rRID: '83377', label: '関西：山上 海優 日報', region: '関西（京都・大阪）', defaultRep: '山上 海優' }
];

/**
 * 1クリックで「1時間おきサイボウズ訪問報告自動回収トリガー」を重複ゼロで設定＆初回即時同期を実行する関数
 */
function setupHourlyCybozuVisitReportTrigger() {
  var triggers = ScriptApp.getProjectTriggers() || [];
  var deleted = 0;
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction && triggers[i].getHandlerFunction() === VISIT_REPORT_TRIGGER_HANDLER_) {
      ScriptApp.deleteTrigger(triggers[i]);
      deleted++;
    }
  }
  ScriptApp.newTrigger(VISIT_REPORT_TRIGGER_HANDLER_)
    .timeBased()
    .everyHours(1)
    .create();

  var syncRes = syncCybozuVisitReportsToLedgerInGas();
  return {
    ok: true,
    triggerInstalled: true,
    deletedOldTriggers: deleted,
    syncResult: syncRes
  };
}

/**
 * 店舗名照合用の正規化ヘルパー
 */
function normalizeShopForVisitMatch_(text) {
  var s = String(text || '')
    .replace(/[\uFF01-\uFF5E]/g, function(ch) { return String.fromCharCode(ch.charCodeAt(0) - 0xFEE0); })
    .toLowerCase();
  s = s.replace(/https?:\/\/\S+/g, '');
  s = s.replace(/\(テレアポ獲得案件\)|（テレアポ獲得案件）|\(飛び込み\)|（飛び込み）|\(la\s*tourelle\)/gi, '');
  s = s.replace(/[\s　・｜|／/\(\)（）【】\[\]「」『』\-ー〜~_、。,.・:：]/g, '');
  return s;
}

function extractCoreShopToken_(normStr) {
  var x = String(normStr || '');
  var words = [
    '株式会社', '有限会社', '合同会社', '首都圏第二支社',
    '新宿本店', '新宿総本店', '新宿東口店', '新宿東南口店', '新宿西口ハルク店',
    '新宿南口店', '新宿駅南口店', 'なんば道頓堀店', 'なんばパークス店',
    'なんば御堂筋店', '梅田店', 'キタ店', '阪急三番街店', 'ルクア大阪店',
    'ルクアサウス店', 'ホワイティうめだ店', '大丸心斎橋店', '大丸心斎橋', '本館10f',
    '京阪モール京橋店', 'kitte大阪店', 'リンクス梅田店', 'アポロビル店',
    'アルデ新大阪店', '天王寺ミオ店', '天王寺店', 'あべのハルカスダイニング',
    '梅田ハービスプラザ店', '渋谷サクラステージ店', '新大阪店', '飯田橋', '新宿店',
    '四ツ谷', '神楽坂', '難波店', '食べ飲み放題個室居酒屋', '食べ放題飲み放題個室居酒屋',
    '食べ飲み放題', '肉と魚がうまい酒場', '1ポンドのステーキハンバーグ',
    '焼き鳥居酒屋', 'おでん&焼き鳥食べ放題', '板前がいる町の酒場', '大衆酒場',
    'ハンバーグ&ステーキ専門店', '中国料理', '中国老舗', 'リストランテ'
  ];
  for (var i = 0; i < words.length; i++) {
    x = x.split(words[i]).join('');
  }
  return x;
}

function isSameShopForVisitMatch_(shopA, titleB) {
  var na = normalizeShopForVisitMatch_(shopA);
  var nb = normalizeShopForVisitMatch_(titleB);
  if (!na || !nb) return false;

  if (na.indexOf('大起水産') !== -1 && nb.indexOf('大起水産') !== -1) {
    if (na.indexOf('京橋') !== -1 && nb.indexOf('心斎橋') !== -1) return false;
    if (na.indexOf('心斎橋') !== -1 && nb.indexOf('京橋') !== -1) return false;
  }

  if ((na.indexOf(nb) !== -1 || nb.indexOf(na) !== -1) && Math.min(na.length, nb.length) >= 3) {
    return true;
  }

  var ca = extractCoreShopToken_(na);
  var cb = extractCoreShopToken_(nb);
  if (ca.length >= 3 && cb.length >= 3 && (ca.indexOf(cb) !== -1 || cb.indexOf(ca) !== -1)) {
    return true;
  }

  var aliases = [
    ['pronto', 'praonto'],
    ['ニューツルマツ', 'ニューマルマツ'],
    ['ベアフットカリー', 'ベアフックカリー'],
    ['青いナポリ', '青いナポリインザパーク'],
    ['ココスジャパン', 'ゼンショーホールディングス'],
    ['カフェエクラ', 'cafeecla'],
    ['cosmologia', 'コスモロジア']
  ];
  for (var k = 0; k < aliases.length; k++) {
    var a1 = aliases[k][0], a2 = aliases[k][1];
    if ((na.indexOf(a1) !== -1 && nb.indexOf(a2) !== -1) || (na.indexOf(a2) !== -1 && nb.indexOf(a1) !== -1)) {
      return true;
    }
  }
  return false;
}

/**
 * サイボウズOffice「報告書」から営業訪問報告を自動抽出し、シート『📋テレアポ獲得_営業訪問結果台帳』を更新する
 */
function syncCybozuVisitReportsToLedgerInGas() {
  var props = PropertiesService.getScriptProperties();
  var cyUser = String(props.getProperty('CYBOZU_USER') || props.getProperty('CYBOZU_DIRECT_USER') || '').trim();
  var cyPass = String(props.getProperty('CYBOZU_PASSWORD') || props.getProperty('CYBOZU_DIRECT_PASS') || '').trim();
  if (!cyUser || !cyPass) {
    return {
      ok: false,
      error: 'スクリプトプロパティに CYBOZU_USER / CYBOZU_PASSWORD を設定してください。'
    };
  }

  var cookieMap = {};
  function collectCookies(res) {
    if (!res) return;
    var headers = res.getAllHeaders ? res.getAllHeaders() : {};
    var sc = headers['Set-Cookie'] || headers['set-cookie'];
    if (!sc) return;
    var arr = Array.isArray(sc) ? sc : [sc];
    for (var i = 0; i < arr.length; i++) {
      var kv = String(arr[i]).split(';')[0].split('=');
      if (kv.length >= 2) cookieMap[kv[0].trim()] = kv.slice(1).join('=').trim();
    }
  }
  function getCookieHeader() {
    return Object.keys(cookieMap).map(function(k) { return k + '=' + cookieMap[k]; }).join('; ');
  }

  /* 1. サイボウズログイン */
  var r1 = UrlFetchApp.fetch('https://fine-staff.cybozu.com/login', { followRedirects: false, muteHttpExceptions: true });
  collectCookies(r1);
  var loginHtml = r1.getContentText() || '';
  var tokMatch = loginHtml.match(/REQUEST_TOKEN\s*=\s*['"]([^'"]+)['"]/) || loginHtml.match(/name=['"]__REQUEST_TOKEN__['"][^>]*value=['"]([^'"]+)['"]/i);
  var reqToken = tokMatch ? tokMatch[1] : '';

  var r2 = UrlFetchApp.fetch('https://fine-staff.cybozu.com/api/auth/login.json?_lc=ja', {
    method: 'post',
    contentType: 'application/json',
    headers: { Cookie: getCookieHeader() },
    payload: JSON.stringify({
      username: cyUser,
      password: cyPass,
      keepUsername: true,
      redirect: '/o/ag.cgi',
      __REQUEST_TOKEN__: reqToken
    }),
    followRedirects: false,
    muteHttpExceptions: true
  });
  collectCookies(r2);

  /* 2. 各営業担当の報告書スレッドを取得して訪問ブロックを抽出 */
  var visitBlocks = [];
  for (var tIdx = 0; tIdx < CYBOZU_VISIT_THREADS_.length; tIdx++) {
    var th = CYBOZU_VISIT_THREADS_[tIdx];
    var url = 'https://fine-staff.cybozu.com/o/ag.cgi?page=ReportView&rRID=' + th.rRID;
    var res = UrlFetchApp.fetch(url, { headers: { Cookie: getCookieHeader() }, followRedirects: true, muteHttpExceptions: true });
    collectCookies(res);
    var html = res.getContentText('UTF-8') || '';
    if (/name=["']_account["']/i.test(html)) {
      res = UrlFetchApp.fetch(url, {
        method: 'post',
        headers: { Cookie: getCookieHeader() },
        payload: { _system: '1', _account: cyUser, _password: cyPass },
        followRedirects: true,
        muteHttpExceptions: true
      });
      collectCookies(res);
      html = res.getContentText('UTF-8') || '';
    }

    var cleaned = html
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<(?:br|hr)\b[^>]*>/gi, '\n')
      .replace(/<\/(?:p|div|tr|li|table|h[1-6])>/gi, '\n')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/gi, ' ')
      .replace(/&amp;/gi, '&')
      .replace(/&lt;/gi, '<')
      .replace(/&gt;/gi, '>');

    var lines = cleaned.split(/\r?\n/).map(function(l) { return l.replace(/[ \t\u3000\u00A0]+/g, ' ').trim(); }).filter(Boolean);
    var fullText = lines.join('\n');
    var cIdx = fullText.indexOf('コメント一覧');
    var targetText = cIdx >= 0 ? fullText.slice(cIdx) : fullText;

    var hdrRe = /(?:^|\n)(\d{1,6})\s*:\s*([^\n]{1,60}?)\s+(20\d{2}\/\d{1,2}\/\d{1,2}\s*\([^\)]+\)\s*\d{1,2}:\d{2})/g;
    var hdrs = [];
    var hm;
    while ((hm = hdrRe.exec(targetText)) !== null) {
      hdrs.push({
        cNo: hm[1],
        author: hm[2].trim(),
        postedAt: hm[3].trim(),
        start: hm.index,
        bodyStart: hm.index + hm[0].length
      });
    }

    for (var h = 0; h < hdrs.length; h++) {
      var curH = hdrs[h];
      /* 高橋・武市・中島・東山（テレアポ専任）や非営業担当の投稿は営業訪問報告に含めない */
      if (/(?:高橋|髙橋|武市|中島|東山)/.test(curH.author)) continue;
      if (!/(?:戸井|有福|藤井|富田|西川|宮川|山上)/.test(curH.author)) continue;

      var endPos = (h + 1 < hdrs.length) ? hdrs[h + 1].start : targetText.length;
      var body = targetText.slice(curH.bodyStart, endPos)
        .replace(/(?:いいね！|確認しました|「(?:いいね！|確認しました)」を取り消す|返信する|固定リンク|削除する|\d+\s*名|名)\s*$/gm, '')
        .trim();
      if (th.rRID === '124797' && /【テレアポ(?:獲得案件|\s*パンフレット配布案件)】/.test(body)) continue;

      /* パターンA: ◆店舗名（戸井日報ほか） */
      if (body.indexOf('◆') !== -1) {
        var parts = body.split(/(?=\n◆|^◆)/);
        for (var p = 0; p < parts.length; p++) {
          var seg = parts[p].trim();
          if (seg.indexOf('◆') !== 0) continue;
          ['【ストックリスト】', '【投入実績】', '【明日の行動予定】'].forEach(function(sw) {
            var sPos = seg.indexOf(sw);
            if (sPos !== -1) seg = seg.slice(0, sPos).trim();
          });
          var firstLn = seg.split('\n')[0].replace(/^◆+/, '').trim();
          if (firstLn === '大阪' || firstLn === '京都' || firstLn === '神戸') continue;
          visitBlocks.push({
            source: 'サイボウズ『' + th.label + '』#' + curH.cNo,
            author: curH.author,
            postedAt: curH.postedAt,
            title: firstLn,
            rawText: seg
          });
        }
      }

      /* パターンB: 商談:店舗名（有福日報・全国テレアポ報告） */
      if (body.indexOf('◇商談内容') !== -1 || body.indexOf('商談:') !== -1 || body.indexOf('商談：') !== -1) {
        var mSh = body.match(/商談[：:]\s*([^\n]+)/);
        if (mSh) {
          visitBlocks.push({
            source: 'サイボウズ『' + th.label + '』#' + curH.cNo,
            author: curH.author,
            postedAt: curH.postedAt,
            title: mSh[1].trim(),
            rawText: body
          });
        }
      }
    }
  }

  /* 3. 🏆獲得アポ一覧_詳細台帳 と突合して 📋テレアポ獲得_営業訪問結果台帳 を更新 */
  var repSs = typeof getReportSpreadsheet_ === 'function' ? getReportSpreadsheet_() : SpreadsheetApp.getActiveSpreadsheet();
  var apoSh = repSs.getSheetByName('🏆獲得アポ一覧_詳細台帳');
  if (!apoSh || apoSh.getLastRow() < 2) {
    return { ok: false, error: '🏆獲得アポ一覧_詳細台帳 が見つかりません' };
  }

  var apoVals = apoSh.getRange(2, 1, apoSh.getLastRow() - 1, 14).getDisplayValues();
  var nowStr = Utilities.formatDate(new Date(), 'Asia/Tokyo', 'yyyy/MM/dd HH:mm');
  var outRows = [[
    'No', 'アポ・訪問日時', '地域区分', 'エリア', 'テレアポ獲得担当', '訪問営業担当',
    '評価ランク', '企業・店舗名', '先方担当者名', '電話番号', '住所',
    '訪問進捗ステータス', '感触・見込み度', '📋 営業訪問報告（サイボウズ日報原文そのまま転記）',
    '📞 テレアポ獲得時のヒアリング内容', '報告取得元スレッド', '最終同期日時'
  ]];

  var matchedCount = 0;
  for (var r = 0; r < apoVals.length; r++) {
    var row = apoVals[r];
    var shopName = String(row[5] || '').trim();
    if (!shopName) continue;

    var matched = [];
    var seenKeys = {};
    for (var vbIdx = 0; vbIdx < visitBlocks.length; vbIdx++) {
      var vb = visitBlocks[vbIdx];
      if (isSameShopForVisitMatch_(shopName, vb.title)) {
        var dk = vb.author + '_' + normalizeShopForVisitMatch_(vb.rawText).slice(0, 40);
        if (!seenKeys[dk]) {
          seenKeys[dk] = true;
          matched.push(vb);
        }
      }
    }

    var combinedVerb = matched.map(function(m) {
      return '📌 【' + m.source + '｜報告者：' + m.author + '｜' + m.postedAt + '】\n' + m.rawText;
    }).join('\n\n━━━━━━━━━━━━━━━\n');

    if (matched.length > 0) matchedCount++;

    var statusLabel = matched.length > 0 ? '💬 営業訪問済（サイボウズ日報転記済）' : '🗓️ 訪問予定・報告待ち';
    if (/契約|雛形/.test(combinedVerb)) statusLabel = '🎉 契約・スタッフ提案進行中';
    else if (/興味|反応が大きかった|プッシュ|協議し連絡/.test(combinedVerb)) statusLabel = '🤝 責任者商談済（前向き・本部/社内検討）';
    else if (/不在|いらっしゃらず|おられず|資料配布のみ/.test(combinedVerb) && !/と商談|着席し商談/.test(combinedVerb)) {
      statusLabel = '📄 訪問済・資料/名刺お渡し（不在・次回再訪）';
    }

    var area = String(row[2] || '');
    var tel = String(row[8] || '');
    var isKanto = /東京|新宿|本社/.test(area) || tel.indexOf('03') === 0;
    var mRep = String(row[1] || '').match(/営業担当[：:]\s*([^）\)]+)/);
    var salesRep = mRep ? mRep[1].trim() : (isKanto ? '有福 浩一・西川 ひなの' : '戸井 麻衣・富田 湧介');

    outRows.push([
      String(row[0] || (r + 1)),
      String(row[1] || ''),
      isKanto ? '関東（東京・新宿・首都圏本社）' : '関西（大阪・梅田・難波・京橋）',
      area,
      String(row[3] || ''),
      salesRep,
      String(row[4] || ''),
      shopName,
      String(row[7] || ''),
      "'" + tel,
      String(row[9] || ''),
      statusLabel,
      matched.length > 0 ? '報告済' : '訪問前/確認中',
      combinedVerb || '（まだ訪問報告の書き込みはありません）',
      String(row[12] || '').replace(/🎙️\[文字起こし全文:[\s\S]*$/, '').trim(),
      matched.map(function(m) { return m.source; }).join(' / ') || '未報告',
      nowStr
    ]);
  }

  var targetSh = repSs.getSheetByName(VISIT_REPORT_LEDGER_SHEET_);
  if (!targetSh) {
    targetSh = repSs.insertSheet(VISIT_REPORT_LEDGER_SHEET_, 0);
  } else {
    targetSh.clearContents();
  }
  targetSh.getRange(1, 1, outRows.length, outRows[0].length).setValues(outRows);
  targetSh.getRange(1, 1, 1, outRows[0].length).setBackground('#1e3a8a').setFontColor('#ffffff').setFontWeight('bold');
  targetSh.setFrozenRows(1);
  SpreadsheetApp.flush();

  return {
    ok: true,
    syncedAt: nowStr,
    totalApos: outRows.length - 1,
    matchedReportsCount: matchedCount
  };
}

/**
 * Web画面（架電デスク等）から『📋テレアポ獲得_営業訪問結果台帳』の一覧データを0秒取得するAPI
 */
function getPresidentVisitReportBoardOnServer() {
  var repSs = typeof getReportSpreadsheet_ === 'function' ? getReportSpreadsheet_() : SpreadsheetApp.getActiveSpreadsheet();
  var sh = repSs.getSheetByName(VISIT_REPORT_LEDGER_SHEET_);
  if (!sh || sh.getLastRow() < 2) {
    return { ok: true, items: [], syncedAt: '' };
  }
  var vals = sh.getRange(2, 1, sh.getLastRow() - 1, 17).getDisplayValues();
  var items = [];
  for (var i = 0; i < vals.length; i++) {
    var r = vals[i];
    items.push({
      apoNo: r[0],
      apoDateTime: r[1],
      regionGroup: r[2],
      area: r[3],
      teleapoStaff: r[4],
      salesRep: r[5],
      evalRank: r[6],
      shopName: r[7],
      contactName: r[8],
      tel: r[9],
      addr: r[10],
      visitStatus: r[11],
      sentiment: r[12],
      verbatimCombined: r[13],
      teleapoMemo: r[14],
      sourceThreads: r[15],
      syncedAt: r[16]
    });
  }
  return {
    ok: true,
    syncedAt: items.length ? items[0].syncedAt : '',
    items: items
  };
}
