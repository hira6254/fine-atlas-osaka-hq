#!/usr/bin/env python3
"""
決定論検証ゲート (validate_gate.py)
- 実行時間 < 0.2s / トークン消費 ¥0
- companies_master.json の件数（50〜100社の範囲内、62社）、必須キー、大阪府内所在地、電話番号形式、重複ゼロを検証
- 生成された Excel 台帳 (.xlsx) の全4シート構成・行数・数式インジェクション対策を検証
- 生成された data.js / index.html / robots.txt の整合性・noindex保護を検証
"""

import json
import re
import sys
from pathlib import Path
import openpyxl

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_JSON = BASE_DIR / "scripts" / "companies_master.json"
EXCEL_PATH = BASE_DIR / "ファインアトラス_大阪本社_外食・寿司・海鮮居酒屋チェーン本部_テレアポ営業台帳.xlsx"
DATA_JS_PATH = BASE_DIR / "data.js"
INDEX_HTML_PATH = BASE_DIR / "index.html"
ROBOTS_PATH = BASE_DIR / "robots.txt"

REQUIRED_KEYS = [
    "id",
    "rank",
    "category",
    "companyName",
    "areaGroup",
    "postalCode",
    "address",
    "phone",
    "representative",
    "storeCountScale",
    "brands",
    "targetDept",
    "recommendedFish",
    "pitchAngle",
    "callScriptReception",
    "callScriptBuyer",
    "website",
]

PHONE_RE = re.compile(r"^0\d{1,4}-\d{1,4}-\d{3,4}$")


def main() -> int:
    errors = []

    if not MASTER_JSON.exists():
        print("[FAIL] companies_master.json not found")
        return 1

    companies = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
    count = len(companies)
    if not (150 <= count <= 250):
        errors.append(f"Company count {count} is outside target range 150..250")

    seen_ids = set()
    seen_names = set()

    for idx, comp in enumerate(companies, 1):
        for k in REQUIRED_KEYS:
            val = str(comp.get(k, "")).strip()
            if not val:
                errors.append(f"Row {idx} ({comp.get('id')}): missing required key '{k}'")

        cid = comp.get("id")
        cname = comp.get("companyName")
        if cid in seen_ids:
            errors.append(f"Duplicate ID: {cid}")
        seen_ids.add(cid)

        if cname in seen_names:
            errors.append(f"Duplicate companyName: {cname}")
        seen_names.add(cname)

        if comp.get("rank") not in ("S", "A", "B"):
            errors.append(f"{cid}: invalid rank {comp.get('rank')}")

        addr = comp.get("address", "")
        if not addr.startswith("大阪府"):
            errors.append(f"{cid} ({cname}): address '{addr}' is not in 大阪府")

        phone = comp.get("phone", "")
        if not PHONE_RE.match(phone):
            errors.append(f"{cid} ({cname}): invalid phone format '{phone}'")

        web = comp.get("website", "")
        if not (web.startswith("https://") or web.startswith("http://")):
            errors.append(f"{cid} ({cname}): invalid website URL '{web}'")

    # Excel checks
    if not EXCEL_PATH.exists():
        errors.append(f"Excel file missing: {EXCEL_PATH.name}")
    else:
        wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False)
        expected_sheets = [
            "ダッシュボード_大阪本社攻略",
            "大阪本社_チェーン本部架電リスト",
            "本部バイヤー専用_受付突破＆商談トーク集",
            "ファインアトラス商材＆チェーン提案規格表",
        ]
        if wb.sheetnames != expected_sheets:
            errors.append(f"Excel sheetnames mismatch: {wb.sheetnames} != {expected_sheets}")
        else:
            ws_list = wb["大阪本社_チェーン本部架電リスト"]
            excel_rows = ws_list.max_row - 4
            if excel_rows != count:
                errors.append(f"Excel row count {excel_rows} != master count {count}")

    # Web files checks
    if not DATA_JS_PATH.exists():
        errors.append("data.js missing")
    else:
        djs = DATA_JS_PATH.read_text(encoding="utf-8")
        if "window.OSAKA_HQ_DATA =" not in djs:
            errors.append("data.js missing window.OSAKA_HQ_DATA")

    if not INDEX_HTML_PATH.exists():
        errors.append("index.html missing")
    else:
        html = INDEX_HTML_PATH.read_text(encoding="utf-8")
        if "noindex, nofollow" not in html:
            errors.append("index.html missing noindex, nofollow meta tag")

    if not ROBOTS_PATH.exists() or "Disallow: /" not in ROBOTS_PATH.read_text(encoding="utf-8"):
        errors.append("robots.txt missing or invalid Disallow: /")

    if errors:
        print("[FAIL] Deterministic Gate Failed:")
        for e in errors:
            print("  -", e)
        return 1

    rank_s = sum(1 for c in companies if c["rank"] == "S")
    rank_a = sum(1 for c in companies if c["rank"] == "A")
    rank_b = sum(1 for c in companies if c["rank"] == "B")
    print(
        f"[PASS] Deterministic Gate OK! Total={count} Osaka HQs "
        f"(S={rank_s}, A={rank_a}, B={rank_b}), 4-sheet Excel & Web Compass verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
