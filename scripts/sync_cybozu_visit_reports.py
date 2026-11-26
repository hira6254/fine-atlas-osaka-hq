#!/usr/bin/env python3
"""
サイボウズOffice（関西：戸井 麻衣 日報 / 関東：有福 浩一_日報 / 関西：富田 湧介_日報 / 【FS】全国テレアポ 報告 ほか）
＆ Googleスプレッドシート（🏆獲得アポ一覧_詳細台帳 / 東京テレアポ商談管理表）から
テレアポ獲得案件と営業訪問報告（原文そのまま転記）を自動突合・統合するエンジンスクリプト。

セキュリティ・運用原則:
- 認証情報は環境変数（CYBOZU_USER / CYBOZU_PASSWORD）または安全キャッシュから読み込み、
  出力ファイル（JSON / JS / シート）にはパスワード・認証キー・トークンを一切含めない。
- 営業さんの日報原文（【トピックス】◆店舗名、商談内容、累計報告など）を要約・改変せずそのまま全文転記する。
"""

from __future__ import annotations

import html
import http.cookiejar
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

JST = timezone(timedelta(hours=9))

REPORT_SPREADSHEET_ID = "1V4YaTIpTn5dE_s1R3NvYQlmFoa3gXHX30jDK9bVwQJg"
MAIN_SPREADSHEET_ID = "19jOHEvbzqFQdtt5DAYUjyM-1ODihEIkK3XVVtLHbJR4"
TOKYO_SPREADSHEET_ID = "1MQNzadEvFJ4f7xhxBLE_JxJOp8QAxl_mlpSlmn4dpkI"
VISIT_SHEET_TITLE = "📋テレアポ獲得_営業訪問結果台帳"

CYBOZU_BASE_URL = "https://fine-staff.cybozu.com"
CYBOZU_REPORT_THREADS = [
    {"rRID": "6645", "label": "関西：戸井 麻衣 日報", "region": "関西（大阪・梅田・難波）", "defaultRep": "戸井 麻衣"},
    {"rRID": "69", "label": "関東：有福 浩一_日報", "region": "関東（東京・新宿・本社）", "defaultRep": "有福 浩一・西川 ひなの"},
    {"rRID": "243259", "label": "関西：富田 湧介_日報", "region": "関西（大阪・アトラス同行）", "defaultRep": "富田 湧介"},
    {"rRID": "124797", "label": "【FS】全国テレアポ 報告", "region": "全国（関西・関東・本社）", "defaultRep": "各拠点営業担当"},
    {"rRID": "144", "label": "関西：藤井 皓一朗 日報", "region": "関西（神戸・大阪）", "defaultRep": "藤井 皓一朗"},
    {"rRID": "6653", "label": "関西：宮川 玲子 日報", "region": "関西（大阪・京都）", "defaultRep": "宮川 玲子"},
    {"rRID": "83377", "label": "関西：山上 海優 日報", "region": "関西（京都・大阪）", "defaultRep": "山上 海優"},
]


def norm_for_match(text: str) -> str:
    s = unicodedata.normalize("NFKC", str(text or "")).lower()
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"\(テレアポ獲得案件\)|（テレアポ獲得案件）|\(飛び込み\)|（飛び込み）|\(la\s*tourelle\)", "", s)
    s = re.sub(r"[\s　・｜|／/\(\)（）【】\[\]「」『』\-ー〜~_、。,.・:：]", "", s)
    return s


def core_shop_token(norm_str: str) -> str:
    x = norm_str
    strip_words = [
        "株式会社", "有限会社", "合同会社", "首都圏第二支社",
        "新宿本店", "新宿総本店", "新宿東口店", "新宿東南口店", "新宿西口ハルク店",
        "新宿南口店", "新宿駅南口店", "なんば道頓堀店", "なんばパークス店",
        "なんば御堂筋店", "梅田店", "キタ店", "阪急三番街店", "ルクア大阪店",
        "ルクアサウス店", "ホワイティうめだ店", "大丸心斎橋店", "大丸心斎橋", "本館10f",
        "京阪モール京橋店", "kitte大阪店", "リンクス梅田店", "アポロビル店",
        "アルデ新大阪店", "天王寺ミオ店", "天王寺店", "あべのハルカスダイニング",
        "梅田ハービスプラザ店", "渋谷サクラステージ店", "新大阪店", "飯田橋", "新宿店",
        "四ツ谷", "神楽坂", "難波店", "食べ飲み放題個室居酒屋", "食べ放題飲み放題個室居酒屋",
        "食べ飲み放題", "肉と魚がうまい酒場", "1ポンドのステーキハンバーグ",
        "焼き鳥居酒屋", "おでん&焼き鳥食べ放題", "板前がいる町の酒場", "大衆酒場",
        "ハンバーグ&ステーキ専門店", "中国料理", "中国老舗", "リストランテ",
    ]
    for w in strip_words:
        x = x.replace(w, "")
    return x


def is_same_shop(shop_a: str, title_b: str) -> bool:
    na = norm_for_match(shop_a)
    nb = norm_for_match(title_b)
    if not na or not nb:
        return False

    # Distinguish multi-branch chains (e.g. 大起水産回転寿司 京阪モール京橋店 vs 大丸心斎橋店)
    if "大起水産" in na and "大起水産" in nb:
        if "京橋" in na and "心斎橋" in nb:
            return False
        if "心斎橋" in na and "京橋" in nb:
            return False

    if na in nb or nb in na:
        if min(len(na), len(nb)) >= 3:
            return True

    ca = core_shop_token(na)
    cb = core_shop_token(nb)
    if len(ca) >= 3 and len(cb) >= 3 and (ca in cb or cb in ca):
        return True

    # Known typos in daily reports
    typo_aliases = {
        "pronto": ["praonto", "プロント"],
        "ニューツルマツ": ["ニューマルマツ"],
        "ベアフットカリー": ["ベアフックカリー"],
        "青いナポリ": ["aoinapoli", "青いナポリインザパーク"],
        "ココスジャパン": ["ゼンショーホールディングス", "ココスジャパン"],
        "カフェエクラ": ["cafeecla"],
        "cosmologia": ["コスモロジア"],
        "latlas": ["ラトラス"],
        "ラトゥーエル": ["latourelle"],
    }
    for k, alias_list in typo_aliases.items():
        if k in na or k in ca:
            for al in alias_list:
                if al in nb or al in cb:
                    return True
        if k in nb or k in cb:
            for al in alias_list:
                if al in na or al in ca:
                    return True

    return False


def fetch_cybozu_threads_live(cy_user: str, cy_pass: str) -> Dict[str, Dict[str, str]]:
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [("User-Agent", "Mozilla/5.0")]

    r1 = opener.open(f"{CYBOZU_BASE_URL}/login", timeout=20)
    html1 = r1.read().decode("utf-8", "ignore")
    m = (
        re.search(r"REQUEST_TOKEN\s*=\s*['\"]([^'\"]+)['\"]", html1)
        or re.search(r"name=['\"]__REQUEST_TOKEN__['\"][^>]*value=['\"]([^'\"]+)['\"]", html1)
    )
    tok = m.group(1) if m else ""

    req2 = urllib.request.Request(
        f"{CYBOZU_BASE_URL}/api/auth/login.json?_lc=ja",
        data=json.dumps({
            "username": cy_user,
            "password": cy_pass,
            "keepUsername": True,
            "redirect": "/o/ag.cgi",
            "__REQUEST_TOKEN__": tok,
        }).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    opener.open(req2, timeout=20)

    threads: Dict[str, Dict[str, str]] = {}
    for th in CYBOZU_REPORT_THREADS:
        rid = th["rRID"]
        lbl = th["label"]
        url = f"{CYBOZU_BASE_URL}/o/ag.cgi?page=ReportView&rRID={rid}"
        r = opener.open(url, timeout=25)
        h = r.read().decode("utf-8", "ignore")
        if 'name="_account"' in h or 'name="_password"' in h:
            data_form = urllib.parse.urlencode({
                "_system": "1",
                "_account": cy_user,
                "_password": cy_pass,
            }).encode("utf-8")
            r = opener.open(url, data=data_form, timeout=25)
            h = r.read().decode("utf-8", "ignore")

        c = re.sub(r"<script[\s\S]*?</script>", " ", h, flags=re.I)
        c = re.sub(r"<style[\s\S]*?</style>", " ", c, flags=re.I)
        c = re.sub(r"<(?:br|hr)\b[^>]*>", "\n", c, flags=re.I)
        c = re.sub(r"</(?:p|div|tr|li|table|h[1-6])>", "\n", c, flags=re.I)
        c = html.unescape(re.sub(r"<[^>]+>", " ", c))
        lines = [re.sub(r"[ \t\u3000\xa0]+", " ", ln).strip() for ln in c.splitlines()]
        lines = [ln for ln in lines if ln]
        txt = "\n".join(lines)
        idx = txt.find("コメント一覧")
        threads[rid] = {
            "label": lbl,
            "region": th["region"],
            "defaultRep": th["defaultRep"],
            "text": txt[idx:] if idx >= 0 else txt,
        }
    return threads


def parse_visit_blocks_from_threads(threads: Dict[str, Dict[str, str]]) -> List[Dict[str, Any]]:
    visit_blocks: List[Dict[str, Any]] = []

    for rid, tinfo in threads.items():
        lbl = tinfo["label"]
        txt = tinfo["text"]
        hdrs = list(
            re.finditer(
                r"(?:^|\n)(\d{1,6})\s*:\s*([^\n]{1,60}?)\s+(20\d{2}/\d{1,2}/\d{1,2}\s*\([^\)]+\)\s*\d{1,2}:\d{2})",
                txt,
            )
        )
        for idx_h, hm in enumerate(hdrs):
            c_no = hm.group(1)
            author = hm.group(2).strip()
            posted_at = hm.group(3).strip()
            st = hm.end()
            ed = hdrs[idx_h + 1].start() if idx_h + 1 < len(hdrs) else len(txt)
            body = txt[st:ed].strip()
            body = re.sub(
                r"(?:いいね！|確認しました|「(?:いいね！|確認しました)」を取り消す|返信する|固定リンク|削除する|\d+\s*名|名)\s*$",
                "",
                body,
                flags=re.M,
            ).strip()

            # 1) Toi style ◆ShopName...
            if "◆" in body:
                parts = re.split(r"(?=\n◆|^◆)", body)
                for p in parts:
                    p = p.strip()
                    if not p.startswith("◆"):
                        continue
                    for stop_w in ["【ストックリスト】", "【投入実績】", "【明日の行動予定】", "≪アポイント進捗≫"]:
                        if stop_w in p:
                            p = p[: p.index(stop_w)].strip()
                    first_line = p.splitlines()[0].lstrip("◆").strip()
                    if first_line in ("大阪", "京都", "神戸"):
                        continue
                    is_teleapo = ("テレアポ" in first_line) or ("テレアポ" in p)
                    visit_blocks.append({
                        "threadRid": rid,
                        "threadLabel": lbl,
                        "commentNo": int(c_no),
                        "source": f"サイボウズ『{lbl}』#{c_no}",
                        "author": author,
                        "postedAt": posted_at,
                        "title": first_line,
                        "rawText": p,
                        "isTeleapoTagged": is_teleapo,
                        "isJumpIn": "飛び込み" in p and not is_teleapo,
                    })

            # 2) Arifuku style in 【FS】全国テレアポ 報告 or 関東：有福 浩一_日報 (商談: ... / ●TOPIX ...)
            if "◇商談内容" in body or "商談:" in body or "商談：" in body:
                m_sh = re.search(r"商談[：:]\s*([^\n]+)", body)
                if m_sh:
                    visit_blocks.append({
                        "threadRid": rid,
                        "threadLabel": lbl,
                        "commentNo": int(c_no),
                        "source": f"サイボウズ『{lbl}』#{c_no}",
                        "author": author,
                        "postedAt": posted_at,
                        "title": m_sh.group(1).strip(),
                        "rawText": body,
                        "isTeleapoTagged": True,
                        "isJumpIn": False,
                    })

            if "●TOPIX" in body and "テレアポ" in body:
                t_idx = body.find("●TOPIX")
                topix_part = body[t_idx:]
                for stop_w in ["CD池下", "〇CD幾度", "≪アポイント進捗≫", "≪沖縄契約書進捗≫"]:
                    if stop_w in topix_part:
                        topix_part = topix_part[: topix_part.index(stop_w)].strip()
                t_lines = [ln for ln in topix_part.splitlines() if ln.strip() and ln.strip() != "●TOPIX"]
                if t_lines:
                    visit_blocks.append({
                        "threadRid": rid,
                        "threadLabel": lbl,
                        "commentNo": int(c_no),
                        "source": f"サイボウズ『{lbl}』#{c_no}",
                        "author": author,
                        "postedAt": posted_at,
                        "title": t_lines[0],
                        "rawText": "\n".join(t_lines),
                        "isTeleapoTagged": True,
                        "isJumpIn": False,
                    })

            # 3) Nishikawa / Arifuku numbered teleapo report items (①〜⑩)
            if rid == "69" and ("テレアポ" in body or "アポイント" in body or "累計" in body):
                # Split before cumulative summary table if detailed sections exist
                main_section = body
                for m_num in re.finditer(r"(?:^|\n)([①-⑩])\s*(?:(\d{1,2}/\d{1,2})\s+)?([^\n]+)", main_section):
                    rest = main_section[m_num.end() :]
                    m_next = re.search(r"\n(?:[①-⑩]|累計|10月累計|11月テレアポ|商談：)", rest)
                    chunk = (m_num.group(0).strip() + ("\n" + rest[: m_next.start()].strip() if m_next else "\n" + rest.strip())).strip()
                    title_line = m_num.group(3).strip()
                    visit_blocks.append({
                        "threadRid": rid,
                        "threadLabel": lbl,
                        "commentNo": int(c_no),
                        "source": f"サイボウズ『{lbl}』#{c_no}",
                        "author": author,
                        "postedAt": posted_at,
                        "title": title_line,
                        "rawText": chunk,
                        "isTeleapoTagged": True,
                        "isJumpIn": False,
                    })

                # Also extract follow-up reply comments like >558 Cosmologia
                if ">>" in body and "⇒" in body:
                    m_q = re.search(r">>\s*[①-⑩]?\s*([^\n]+)", body)
                    if m_q:
                        visit_blocks.append({
                            "threadRid": rid,
                            "threadLabel": lbl,
                            "commentNo": int(c_no),
                            "source": f"サイボウズ『{lbl}』#{c_no}",
                            "author": author,
                            "postedAt": posted_at,
                            "title": m_q.group(1).strip(),
                            "rawText": body,
                            "isTeleapoTagged": True,
                            "isJumpIn": False,
                        })

            # 4) Tomita style in 関西：富田 湧介_日報
            if rid == "243259" and author.startswith("富田"):
                lines = body.splitlines()
                skip_headers = {
                    "朝会議後、ファインアトラス用のトークスクリプトを作成、",
                    "ファインスタッフ営業用資料と名刺を用意して梅田へ。",
                    "1日を通してカレンダーお渡しやテレアポの資料お渡し",
                    "午後は梅田営業所に移動して戸井さんのファインスタッフ営業同行。",
                }
                for li, ln in enumerate(lines):
                    if re.match(r"^\d{1,2}:\d{2}\s*", ln) or ln.startswith("【") or ln.startswith("次回出勤") or ln in skip_headers:
                        continue
                    if (
                        2 <= len(ln) <= 36
                        and not ln.endswith("。")
                        and not ln.endswith("、")
                        and not ln.startswith("・")
                        and not ln.startswith("※")
                    ):
                        sub_lines = [ln]
                        for lj in range(li + 1, min(len(lines), li + 12)):
                            nxt = lines[lj]
                            if (
                                2 <= len(nxt) <= 36
                                and not nxt.endswith("。")
                                and not nxt.endswith("、")
                                and not nxt.startswith("・")
                            ) or nxt.startswith("次回出勤"):
                                break
                            sub_lines.append(nxt)
                        if len(sub_lines) >= 2:
                            joined = "\n".join(sub_lines)
                            visit_blocks.append({
                                "threadRid": rid,
                                "threadLabel": lbl,
                                "commentNo": int(c_no),
                                "source": f"サイボウズ『{lbl}』#{c_no}",
                                "author": author,
                                "postedAt": posted_at,
                                "title": ln,
                                "rawText": joined,
                                "isTeleapoTagged": "テレアポ" in joined,
                                "isJumpIn": "飛び込み" in ln,
                            })

            # 5) Takahashi / Teleapo detailed acquisition & schedule notes in 【FS】全国テレアポ 報告 (rRID=124797)
            if rid == "124797" and ("【テレアポ" in body or "獲得：" in body):
                lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
                # Extract shop name candidate from lines
                shop_cand = ""
                for ln in lines[:6]:
                    if any(w in ln for w in ["【テレアポ", "〇", "獲得：", "担当：", "商談方法：", "席数：", "客単価：", "～アポ", "～商談"]):
                        if "獲得：" in ln and not ln.startswith("獲得："):
                            shop_cand = re.sub(r"[\s　]*[：:]?獲得[：:].*$", "", ln).strip()
                            break
                        continue
                    if not re.match(r"^\d{1,2}[月/]\d{1,2}", ln):
                        shop_cand = ln
                        break
                if not shop_cand:
                    for ln in reversed(lines[-8:]):
                        if any(w in ln for w in ["住所", "TEL", "HP", "食べログ", "http", "↓", "・"]):
                            continue
                        if 2 <= len(ln) <= 35:
                            shop_cand = ln
                            break
                if shop_cand:
                    visit_blocks.append({
                        "threadRid": rid,
                        "threadLabel": lbl,
                        "commentNo": int(c_no),
                        "source": f"サイボウズ『{lbl}』#{c_no}（アポ詳細投稿）",
                        "author": author,
                        "postedAt": posted_at,
                        "title": shop_cand,
                        "rawText": body,
                        "isTeleapoTagged": True,
                        "isJumpIn": False,
                        "isApoHandoverNote": True,
                    })

    return visit_blocks


def classify_visit_status(reports: List[Dict[str, Any]], apo_dt_str: str, shop_name: str = "") -> Tuple[str, str]:
    """
    Returns (visitStatusBadge, sentimentRank)
    """
    sales_reports = [r for r in reports if not r.get("isApoHandoverNote")]
    handover_reports = [r for r in reports if r.get("isApoHandoverNote")]
    combined = "\n".join(r.get("rawText", "") for r in sales_reports)
    handover_text = "\n".join(r.get("rawText", "") for r in handover_reports)

    if not sales_reports:
        m_dt = re.search(r"(20\d{2})[/\-](\d{1,2})[/\-](\d{1,2})", str(apo_dt_str or ""))
        if m_dt:
            ymd = f"{int(m_dt.group(1)):04d}/{int(m_dt.group(2)):02d}/{int(m_dt.group(3)):02d}"
            if ymd >= "2026/11/26":
                return ("🗓️ 訪問予定（アポ確定・訪問前）", "訪問前")
        if "11月26日" in handover_text or "11月27日" in handover_text or "11月30日" in handover_text or "12月" in handover_text:
            return ("🗓️ 訪問予定（アポ確定・訪問前）", "訪問前")
        if "会社案内をいただきたい" in handover_text or "メール" in handover_text:
            return ("📧 事前資料送付・商談調整中", "事前送付済")
        return ("⏳ 訪問結果確認中（日程調整・報告待ち）", "確認中")

    if any(w in combined for w in ["契約済", "契約書の雛形送付済", "契約書雛形メールにて送付", "個別契約書を更新", "提案人員調整中"]):
        return ("🎉 契約・スタッフ提案進行中", "A（高確度）")

    if any(w in combined for w in ["両方に興味をもっていただく", "うなぎに対しての反応が大きかった", "本部にしっかりとプッシュ", "金曜日に本社に行く用事があるとの事で、弊社の資料やお話をしていただける", "少し興味を持って頂いた感じで、アルバイト採用担当と協議し連絡いただける", "来春の育成就労の外食枠ミャンマー人に期待を寄せている", "お昼のサービスとキッチンは必要との事"]):
        return ("🤝 責任者商談済（前向き・本部/社内検討）", "A〜B（有望）")

    if any(w in combined for w in ["不在のため", "不在の為", "いらっしゃらず", "おられず", "資料配布のみ", "会社案内のみ配布", "名刺交換も出来ず資料配布で終了", "インフルエンザになりお休み"]):
        if not any(w in combined for w in ["着席し商談", "と商談", "対応していただける"]):
            return ("📄 訪問済・資料/名刺お渡し（不在・次回再訪）", "C（再訪・後追い）")

    return ("💬 責任者面談・ヒアリング済（関係構築中）", "B〜C（関係構築）")


def build_integrated_visit_dataset(
    apos_rows: List[List[str]],
    tokyo_rows: List[List[str]],
    visit_blocks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    now_jst = datetime.now(JST).strftime("%Y/%m/%d %H:%M")

    # Sort visit_blocks so longer / more detailed reports come first when deduplicating
    records: List[Dict[str, Any]] = []
    seen_shops_norm = set()

    # 1. Process all rows from 🏆獲得アポ一覧_詳細台帳
    for idx, r in enumerate(apos_rows, 1):
        while len(r) < 14:
            r.append("")
        apo_no = str(r[0] or idx).strip()
        apo_dt = str(r[1] or "").strip()
        area = str(r[2] or "").strip()
        teleapo_staff = str(r[3] or "").strip()
        eval_rank = str(r[4] or "").strip()
        shop_name = str(r[5] or "").strip()
        spec = str(r[6] or "").strip()
        contact_name = str(r[7] or "").strip()
        tel = str(r[8] or "").strip()
        addr = str(r[9] or "").strip()
        url = str(r[10] or "").strip()
        list_cat = str(r[11] or "").strip()
        teleapo_memo = str(r[12] or "").strip()
        cy_status = str(r[13] or "").strip()

        if not shop_name:
            continue
        seen_shops_norm.add(norm_for_match(shop_name))

        # Infer sales rep
        m_rep = re.search(r"営業担当[：:]\s*([^）\)]+)", apo_dt)
        if m_rep:
            sales_rep = m_rep.group(1).strip()
        elif "東京" in area or "新宿" in list_cat or tel.startswith("03") or "本社・人事" in area:
            sales_rep = "有福 浩一・西川 ひなの"
        else:
            sales_rep = "戸井 麻衣・富田 湧介"

        # Find matching Cybozu visit reports
        matched_reports: List[Dict[str, Any]] = []
        seen_rep_keys = set()

        for vb in visit_blocks:
            if is_same_shop(shop_name, vb["title"]):
                # Avoid matching short 1-line cumulative summary if we already have the detailed report from the same author
                raw_t = vb["rawText"].strip()
                dedup_key = f"{vb['author']}_{norm_for_match(raw_t)[:45]}"
                if dedup_key in seen_rep_keys:
                    continue
                seen_rep_keys.add(dedup_key)
                matched_reports.append({
                    "source": vb["source"],
                    "author": vb["author"],
                    "postedAt": vb["postedAt"],
                    "title": vb["title"],
                    "rawText": raw_t,
                    "isApoHandoverNote": bool(vb.get("isApoHandoverNote")),
                })

        # Also check Tokyo tracking sheet
        for tr in tokyo_rows:
            while len(tr) < 16:
                tr.append("")
            if is_same_shop(shop_name, tr[3]) and tr[7].strip():
                raw_t = f"【感触：{tr[6] or '-'}｜訪問担当：{tr[4] or '有福・西川'}｜先方：{tr[5] or contact_name}】\n{tr[7].strip()}"
                dedup_key = f"tokyo_sheet_{norm_for_match(tr[7])[:45]}"
                if dedup_key not in seen_rep_keys:
                    seen_rep_keys.add(dedup_key)
                    matched_reports.append({
                        "source": "関東テレアポ商談管理表（有福・西川）",
                        "author": tr[4] or "有福 浩一・西川 ひなの",
                        "postedAt": tr[1] or "",
                        "title": tr[3],
                        "rawText": raw_t,
                    })

        # Keep longer/detailed reports if a short cumulative 1-liner duplicates the same store
        if len(matched_reports) > 1:
            detailed = [mr for mr in matched_reports if len(mr["rawText"]) >= 55 or "⇒" in mr["rawText"]]
            if detailed:
                matched_reports = detailed

        visit_status, sentiment = classify_visit_status(matched_reports, apo_dt, shop_name)

        # Clean teleapo hearing summary for display
        clean_teleapo_memo = re.sub(r"🎙️\[文字起こし全文:[\s\S]*$", "", teleapo_memo).strip()

        records.append({
            "id": f"APO-{idx:03d}",
            "apoNo": apo_no,
            "apoDateTime": apo_dt,
            "area": area,
            "regionGroup": "関東（東京・新宿・首都圏本社）" if ("東京" in area or "新宿" in area or "本社" in area or tel.startswith("03")) else "関西（大阪・梅田・難波・京橋）",
            "teleapoStaff": teleapo_staff,
            "salesRep": sales_rep,
            "evalRank": eval_rank,
            "shopName": shop_name,
            "spec": spec,
            "contactName": contact_name,
            "tel": tel,
            "addr": addr,
            "url": url,
            "listCategory": list_cat,
            "teleapoMemo": clean_teleapo_memo,
            "cybozuScheduleStatus": cy_status,
            "visitStatus": visit_status,
            "sentiment": sentiment,
            "hasVisitReport": len(matched_reports) > 0,
            "visitReportsCount": len(matched_reports),
            "visitReports": matched_reports,
            "verbatimCombined": "\n\n━━━━━━━━━━━━━━━\n".join(
                f"📌 【{mr['source']}｜報告者：{mr['author']}｜{mr['postedAt']}】\n{mr['rawText']}"
                for mr in matched_reports
            ) if matched_reports else "",
        })

    # 2. Also add Tokyo/Kansai Cybozu-reported teleapo visits that were in the Oct/Early-Nov batch (e.g. 株式会社アラスカ, Parador de KAGURA, 中国老舗 天津飯店 新宿本店, 珈琲貴族エジンバラ, ラ・トゥーエル, ラ・ボケリア 四ツ谷, 井筒まい泉株式会社)
    extra_teleapo_shops = [
        {"shopName": "株式会社アラスカ", "apoDateTime": "2026/10/09 14:00", "area": "東京(千代田区)", "teleapoStaff": "高橋", "salesRep": "有福 浩一・西川 ひなの", "evalRank": "A"},
        {"shopName": "Parador de KAGURA", "apoDateTime": "2026/11/02 15:00", "area": "東京(神楽坂)", "teleapoStaff": "高橋", "salesRep": "有福 浩一・西川 ひなの", "evalRank": "C"},
        {"shopName": "中国老舗 天津飯店 新宿本店", "apoDateTime": "2026/11/02 16:00", "area": "東京(新宿)", "teleapoStaff": "高橋", "salesRep": "有福 浩一・西川 ひなの", "evalRank": "C"},
        {"shopName": "珈琲貴族エジンバラ", "apoDateTime": "2026/11/04 15:00", "area": "東京(新宿)", "teleapoStaff": "高橋", "salesRep": "有福 浩一・西川 ひなの", "evalRank": "C"},
        {"shopName": "ラ・トゥーエル (La Tourelle)", "apoDateTime": "2026/11/05 15:00", "area": "東京(神楽坂)", "teleapoStaff": "高橋", "salesRep": "有福 浩一・西川 ひなの", "evalRank": "B"},
        {"shopName": "ラ・ボケリア 四ツ谷", "apoDateTime": "2026/11/06 15:00", "area": "東京(四ツ谷)", "teleapoStaff": "高橋", "salesRep": "有福 浩一・西川 ひなの", "evalRank": "C"},
    ]

    for ex_idx, ex in enumerate(extra_teleapo_shops, len(records) + 1):
        sname = ex["shopName"]
        if norm_for_match(sname) in seen_shops_norm:
            continue
        seen_shops_norm.add(norm_for_match(sname))

        matched_reports = []
        seen_rep_keys = set()
        for vb in visit_blocks:
            if is_same_shop(sname, vb["title"]):
                raw_t = vb["rawText"].strip()
                dedup_key = f"{vb['author']}_{norm_for_match(raw_t)[:45]}"
                if dedup_key not in seen_rep_keys:
                    seen_rep_keys.add(dedup_key)
                    matched_reports.append({
                        "source": vb["source"],
                        "author": vb["author"],
                        "postedAt": vb["postedAt"],
                        "title": vb["title"],
                        "rawText": raw_t,
                    })

        contact_name = "担当者様"
        spec = ""
        tel = ""
        addr = ""
        url = ""
        for tr in tokyo_rows:
            while len(tr) < 16:
                tr.append("")
            if is_same_shop(sname, tr[3]):
                contact_name = tr[5] or contact_name
                spec = tr[11] or spec
                tel = tr[12] or tel
                addr = tr[13] or addr
                url = tr[14] or url
                if tr[7].strip():
                    raw_t = f"【感触：{tr[6] or '-'}｜訪問担当：{tr[4] or '有福・西川'}｜先方：{tr[5] or contact_name}】\n{tr[7].strip()}"
                    dedup_key = f"tokyo_sheet_{norm_for_match(tr[7])[:45]}"
                    if dedup_key not in seen_rep_keys:
                        seen_rep_keys.add(dedup_key)
                        matched_reports.append({
                            "source": "関東テレアポ商談管理表（有福・西川）",
                            "author": tr[4] or "有福 浩一・西川 ひなの",
                            "postedAt": tr[1] or "",
                            "title": tr[3],
                            "rawText": raw_t,
                        })

        if len(matched_reports) > 1:
            detailed = [mr for mr in matched_reports if len(mr["rawText"]) >= 45]
            if detailed:
                matched_reports = detailed

        visit_status, sentiment = classify_visit_status(matched_reports, ex["apoDateTime"], sname)

        records.append({
            "id": f"APO-{ex_idx:03d}",
            "apoNo": f"T-{ex_idx}",
            "apoDateTime": ex["apoDateTime"],
            "area": ex["area"],
            "regionGroup": "関東（東京・新宿・首都圏本社）",
            "teleapoStaff": ex["teleapoStaff"],
            "salesRep": ex["salesRep"],
            "evalRank": ex["evalRank"],
            "shopName": sname,
            "spec": spec,
            "contactName": contact_name,
            "tel": tel,
            "addr": addr,
            "url": url,
            "listCategory": "新宿・東京テレアポ獲得",
            "teleapoMemo": "テレアポ獲得・営業訪問案件",
            "cybozuScheduleStatus": "✅訪問報告済",
            "visitStatus": visit_status,
            "sentiment": sentiment,
            "hasVisitReport": len(matched_reports) > 0,
            "visitReportsCount": len(matched_reports),
            "visitReports": matched_reports,
            "verbatimCombined": "\n\n━━━━━━━━━━━━━━━\n".join(
                f"📌 【{mr['source']}｜報告者：{mr['author']}｜{mr['postedAt']}】\n{mr['rawText']}"
                for mr in matched_reports
            ) if matched_reports else "",
        })

    # 3. Also collect "アポ同行時の周辺飛び込み訪問報告" (e.g. 百楽, PIER30GRILL, GRILL&BAR DINING燦) as bonus field insights
    jump_in_shops = ["中国料理 百楽 天王寺店", "PIER30GRILL ハンバーグ＆ステーキ専門店", "GRILL＆BAR DINING燦"]
    for j_idx, j_name in enumerate(jump_in_shops, 1):
        matched_reports = []
        seen_rep_keys = set()
        for vb in visit_blocks:
            if is_same_shop(j_name, vb["title"]):
                raw_t = vb["rawText"].strip()
                dedup_key = f"{vb['author']}_{norm_for_match(raw_t)[:45]}"
                if dedup_key not in seen_rep_keys:
                    seen_rep_keys.add(dedup_key)
                    matched_reports.append({
                        "source": vb["source"],
                        "author": vb["author"],
                        "postedAt": vb["postedAt"],
                        "title": vb["title"],
                        "rawText": raw_t,
                    })
        if matched_reports:
            records.append({
                "id": f"JMP-{j_idx:02d}",
                "apoNo": f"飛込-{j_idx}",
                "apoDateTime": "2026/11/25（テレアポ訪問時の近隣飛び込み）",
                "area": "大阪(梅田・天王寺)",
                "regionGroup": "関西（大阪・梅田・難波・京橋）",
                "teleapoStaff": "戸井・富田(現地開拓)",
                "salesRep": "戸井 麻衣・富田 湧介",
                "evalRank": "開拓",
                "shopName": j_name,
                "spec": "テレアポアポ訪問時の同フロア高単価店・飛び込み開拓",
                "contactName": "店長・店舗責任者様",
                "tel": "",
                "addr": "天王寺ミオ / ルクアサウス",
                "url": "",
                "listCategory": "アポ同行・近隣飛び込み開拓",
                "teleapoMemo": "テレアポ訪問先（世界の山ちゃん・大阪竹葉亭）の同フロアで客単価が合う店舗へ飛び込みでパンフレット・名刺配布",
                "cybozuScheduleStatus": "✅現地飛び込み訪問済",
                "visitStatus": "📄 訪問済・資料/名刺お渡し（不在・次回再訪）",
                "sentiment": "C（再訪・後追い）",
                "hasVisitReport": True,
                "visitReportsCount": len(matched_reports),
                "visitReports": matched_reports,
                "verbatimCombined": "\n\n━━━━━━━━━━━━━━━\n".join(
                    f"📌 【{mr['source']}｜報告者：{mr['author']}｜{mr['postedAt']}】\n{mr['rawText']}"
                    for mr in matched_reports
                ),
            })

    # Sort records: items with visit reports first (most recent visit date descending), then upcoming appointments
    def sort_key(item: Dict[str, Any]) -> Tuple[int, str]:
        m_dt = re.search(r"(20\d{2})[/\-](\d{1,2})[/\-](\d{1,2})", item.get("apoDateTime", ""))
        ymd = f"{int(m_dt.group(1)):04d}/{int(m_dt.group(2)):02d}/{int(m_dt.group(3)):02d}" if m_dt else "0000/00/00"
        has_rep = 1 if item.get("hasVisitReport") else 0
        return (has_rep, ymd)

    records.sort(key=sort_key, reverse=True)

    # Calculate KPI summary
    total_count = len(records)
    reported_count = sum(1 for r in records if r["hasVisitReport"])
    upcoming_count = sum(1 for r in records if "訪問予定" in r["visitStatus"])
    contract_or_hot_count = sum(1 for r in records if "契約" in r["visitStatus"] or "前向き" in r["visitStatus"])
    kansai_count = sum(1 for r in records if "関西" in r["regionGroup"])
    kanto_count = sum(1 for r in records if "関東" in r["regionGroup"])

    return {
        "syncedAt": now_jst,
        "cybozuThreadsMonitored": [
            {"rRID": th["rRID"], "label": th["label"], "region": th["region"], "defaultRep": th["defaultRep"]}
            for th in CYBOZU_REPORT_THREADS
        ],
        "summary": {
            "totalCount": total_count,
            "reportedCount": reported_count,
            "upcomingCount": upcoming_count,
            "contractOrHotCount": contract_or_hot_count,
            "kansaiCount": kansai_count,
            "kantoCount": kanto_count,
        },
        "records": records,
    }


def main() -> None:
    # Load cached or live data
    apos_path = Path("/tmp/all_56_apos.json")
    tokyo_path = Path("/tmp/tokyo_sheet_cache.json")
    threads_path = Path("/tmp/cybozu_threads_cache.json")

    if apos_path.exists():
        apos_rows = json.loads(apos_path.read_text(encoding="utf-8"))[1:]
    else:
        out = subprocess.check_output(
            ["gsheets", "readonly", "read", REPORT_SPREADSHEET_ID, "🏆獲得アポ一覧_詳細台帳!A1:N100", "--json"],
            text=True,
        )
        apos_rows = json.loads(out)[1:]

    if tokyo_path.exists():
        tokyo_rows = json.loads(tokyo_path.read_text(encoding="utf-8"))[1:]
    else:
        out = subprocess.check_output(
            ["gsheets", "readonly", "read", TOKYO_SPREADSHEET_ID, "A1:P50", "--json"],
            text=True,
        )
        tokyo_rows = json.loads(out)[1:]

    cy_user = os.environ.get("CYBOZU_USER", "").strip()
    cy_pass = os.environ.get("CYBOZU_PASSWORD", "").strip()
    if cy_user and cy_pass:
        threads = fetch_cybozu_threads_live(cy_user, cy_pass)
    elif threads_path.exists():
        threads = json.loads(threads_path.read_text(encoding="utf-8"))
    else:
        raise RuntimeError("Cybozu threads cache or credentials required")

    visit_blocks = parse_visit_blocks_from_threads(threads)
    dataset = build_integrated_visit_dataset(apos_rows, tokyo_rows, visit_blocks)

    out_json = Path("/tmp/cybozu_visit_dataset.json")
    out_json.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(dataset["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
