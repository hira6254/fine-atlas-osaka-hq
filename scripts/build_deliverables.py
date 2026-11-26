#!/usr/bin/env python3
"""
株式会社ファインアトラス（ファインスタッフ × 対馬水産）
『大阪本社 外食・寿司・海鮮居酒屋・和食チェーン本部 テレアポ営業コンパス＆Excel台帳』
生成スクリプト (build_deliverables.py)

出力成果物:
1. ファインアトラス_大阪本社_外食・寿司・海鮮居酒屋チェーン本部_テレアポ営業台帳.xlsx
2. data.js (Webコンパス用データ・トークスクリプト定義)
3. index.html / styles.css / app.js / robots.txt / README.md
"""

import json
from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_JSON = BASE_DIR / "scripts" / "companies_master.json"
EXCEL_FILENAME = "ファインアトラス_大阪本社_外食・寿司・海鮮居酒屋チェーン本部_テレアポ営業台帳.xlsx"
EXCEL_PATH = BASE_DIR / EXCEL_FILENAME
DATA_JS_PATH = BASE_DIR / "data.js"


def sanitize_excel_cell(val: str) -> str:
    """数式インジェクション防止: 先頭が =, +, -, @ の場合はアポストロフィを付与"""
    if not isinstance(val, str):
        return val
    if val and val[0] in ("=", "+", "-", "@"):
        return "'" + val
    return val


HQ_SCRIPTS = [
    {
        "id": "hq-reception",
        "step": "STEP 1",
        "title": "【受付突破】本部代表電話 → 商品部・仕入バイヤーへの取次ぎトーク",
        "target": "受付・総務・代表電話応対者",
        "point": "「売り込み感」を消し、「同じ大阪（吹田・千里）拠点の対馬水産グループ」「各店舗の仕込み削減・季節フェア用の下処理済み水産加工品のサンプル案内」として商品部・購買部へ繋いでもらう。",
        "script": (
            "「お世話になります。私、同じ大阪の吹田・千里エリアと長崎・対馬を拠点に、"
            "外食チェーン様向けの下処理済み水産加工品を製造・卸しております、"
            "株式会社ファインアトラス（対馬水産グループ）の〇〇と申します。\n\n"
            "御社が展開されている『〇〇（主力ブランド名）』様の季節フェアやグランドメニュー向けに、"
            "店舗での仕込み・魚捌きが一切不要な【無添加炊き上げ煮穴子】や【炙りのどぐろ・赤甘鯛フィレ】の"
            "サンプルと規格書をお届けしたくお電話いたしました。\n\n"
            "水産食材の仕入れやメニュー開発をご担当されている【商品部・購買部のバイヤーご担当者様】は"
            "いらっしゃいますでしょうか？」"
        ),
    },
    {
        "id": "hq-buyer-pitch",
        "step": "STEP 2",
        "title": "【バイヤー接続】商品部・購買担当者への30秒コア提案トーク",
        "target": "商品部・購買バイヤー・メニュー開発責任者・統括料理長",
        "point": "チェーン本部が最も悩んでいる「①店舗ごとの職人・人手不足」「②原価率と歩留まりのブレ（廃棄ロス）」「③新メニュー・季節フェアの目玉不足」の3点を100%解決する提案。",
        "script": (
            "「お忙しいところ恐れ入ります。吹田・千里と長崎・対馬を拠点に水産加工卸をしております、"
            "株式会社ファインアトラスの〇〇と申します。\n\n"
            "現在、大阪に本社を置かれる寿司・和食・居酒屋チェーンの本部様に、"
            "【セントラルキッチンや店舗での仕込みが一切いらない職人下処理済みの5大商材】をご案内しております。\n"
            "特に、解凍するだけでふっくら提供できる『無添加炊き上げ煮穴子』、そのまま一本揚げにできる『活〆真穴子フィレ』、"
            "松笠焼き用の『鱗付き赤甘鯛フィレ』『炙りのどぐろ』『皮むき剣先イカ柵』が、"
            "歩留まり100%・廃棄ロスゼロで原価率を26〜30%にピタッと安定させられるとご好評をいただいております。\n\n"
            "同じ大阪ですので、来週にでも本社へ実物サンプルと規格書をお持ちして、"
            "5分ほどご試食・情報交換をさせていただけませんでしょうか？」"
        ),
    },
    {
        "id": "hq-trial-close",
        "step": "STEP 3",
        "title": "【スモールスタート打診】1〜2店舗テスト導入 ＆ 公式お試しセット案内",
        "target": "全店一括導入には慎重なバイヤー・統括料理長",
        "point": "いきなり全数十店舗の切り替えを求めず、「旗艦店1〜2店舗での季節フェア試作」や「公式お試しセット（税込10,000円・送料無料）」または「本社サンプル持参」でハードルを極限まで下げる。",
        "script": (
            "「もちろん、いきなり全店舗での定番切り替えということでなくて全く構いません。\n\n"
            "まずは梅田や難波などの旗艦店様1〜2店舗での『季節のおすすめフェア』や、"
            "テストキッチンでのご試作用として、弊社の主力5種（煮穴子・真穴子フィレ・甘鯛・のどぐろ・剣先イカ）を"
            "詰め合わせた【公式お試しセット（税込10,000円・送料無料）】や試食用サンプルで、"
            "身の厚みやオペレーションの楽さを実感していただいております。\n\n"
            "まずは一度、商品規格書とサンプルを御社本部宛てにお送り（またはご持参）してもよろしいでしょうか？」"
        ),
    },
]

HQ_OBJECTIONS = [
    {
        "id": "obj-1",
        "title": "①「うちは既に大手商社・中央市場の仲卸と口座が決まっているから」",
        "answer": (
            "「左様でございますよね。多店舗展開されておられますので、メインの生鮮ルートはしっかり固めていらっしゃると思います。\n"
            "弊社は既存の仲卸様をリプレイスするのではなく、『店舗で炊くと手間とブレが出る無添加煮穴子』や"
            "『鱗を残して開いた赤甘鯛フィレ』『炙りのどぐろ』など、大手商社様では扱いにくい"
            "【職人の一次加工済み・ニッチ高付加価値商材】だけをスポットや季節フェア用にご活用いただいております。\n"
            "今後のメニュー改定の引き出しとして、規格書とサンプルだけでも置かせていただけませんか？」"
        ),
    },
    {
        "id": "obj-2",
        "title": "②「新規口座の開設ハードルが高い（帳合・物流指定がある）」",
        "answer": (
            "「ありがとうございます。まずはテストキッチンでのご試食や、1〜2店舗様でのスポット検証からで全く問題ございません。\n"
            "クール便での各店舗直送（お魚カスタム定期便）にも、本部様・センター様への一括納品にも柔軟に対応しております。\n"
            "まずはバイヤー様に『モノの良さ』と『歩留まり100%の使い勝手』を見ていただきたいので、"
            "一度サンプルをご試食だけでもお願いできませんでしょうか？」"
        ),
    },
    {
        "id": "obj-3",
        "title": "③「今はメニュー改定の時期じゃない（春夏／秋冬メニューは決定済み）」",
        "answer": (
            "「承知いたしました！ちなみに次回のグランドメニュー改定や、季節フェア（春夏の穴子・甘鯛フェア、"
            "秋冬ののどぐろ・海鮮鍋フェアなど）のご検討時期は何月頃になりますでしょうか？\n"
            "そのご検討タイミングに合わせて、今のうちに最新の商品規格書とサンプルだけお手元にお届けしておければ幸いです。」"
        ),
    },
    {
        "id": "obj-4",
        "title": "④「まずは資料（メール・FAX・郵送）だけ送っておいて」",
        "answer": (
            "「ありがとうございます！ぜひお送りさせていただきます。\n"
            "バイヤー様に一番刺さる規格をご案内したいのですが、現在御社で一番出数が多いのは"
            "『お寿司・鉢物用の煮穴子』『天ぷら・フライ用の開いた真穴子』『お造り・焼き物用の甘鯛・のどぐろ・剣先イカ』の"
            "どちらになりますでしょうか？\n"
            "（※回答を聞いて部署名・ご担当者様名・メールアドレスまたは郵送先を確認）\n"
            "本日中に規格書をお送りし、来週また着荷確認のお電話をさせていただきます！」"
        ),
    },
    {
        "id": "obj-5",
        "title": "⑤「バイヤー（担当者）が不在・外出中・店舗巡回中」",
        "answer": (
            "「承知いたしました。お忙しいところ恐れ入ります。\n"
            "ちなみに水産担当のバイヤー様のお名前はどなた様になりますでしょうか？\n"
            "また、比較的本社にいらっしゃる曜日や時間帯（午前中・夕方など）があれば教えていただけますと幸いです。\n"
            "そのお時間にあらためてお電話させていただきます！」"
        ),
    },
    {
        "id": "obj-6",
        "title": "⑥「電話での新規営業はお断りしている（Webフォームから送って）」",
        "answer": (
            "「失礼いたしました。それでは公式ホームページのお問い合わせフォーム（または代表アドレス）から、"
            "商品部のバイヤー様宛てに『職人下処理済み・水産加工品5種（無添加煮穴子・のどぐろ・甘鯛・剣先イカ）』の"
            "ご提案資料をお送りさせていただきます。\n"
            "宛先として部署名は【商品部（または購買部）ご担当者様】宛てでよろしいでしょうか？ありがとうございます、失礼いたします。」"
        ),
    },
]

PRODUCTS_CATALOG = [
    {
        "code": "FA-01",
        "name": "無添加 炊き上げ煮穴子",
        "targetChain": "回転寿司・グルメ寿司・和食会席・仕出し折詰・そば屋のセイロ飯",
        "prepState": "活〆穴子を化学調味料・保存料無添加でふっくら炊き上げ・真空急速冷凍",
        "chainMerit": "店舗での炊き上げ工程ゼロ・煮崩れロスゼロ。誰が解凍・炙りしても老舗寿司店のふっくら食感を全店舗で100%均一再現。",
        "menuExample": "名物一本穴子握り、煮穴子炙り、穴子セイロ御膳、特上仕出し折詰（原価率目安：26〜30%）",
    },
    {
        "code": "FA-02",
        "name": "活〆 真穴子フィレ（開き・骨切り・下処理済）",
        "targetChain": "天ぷら・天丼チェーン・そばうどんチェーン・串かつ・大衆海鮮居酒屋",
        "prepState": "対馬海峡等の活〆真穴子を開き・ヌメリ取り・下処理済みフィレ加工",
        "chainMerit": "アルバイトスタッフでも解凍して衣（またはパン粉）をつけるだけで、丼からはみ出す『名物・一本穴子天／大穴子フライ／大穴子串』が即完成。",
        "menuExample": "大穴子一本天丼、穴子天ざるそば、名物大穴子串かつ、穴子フィッシュ＆チップス（原価率目安：25〜28%）",
    },
    {
        "code": "FA-03",
        "name": "鱗付き 赤甘鯛フィレ（松笠焼き・うろこ焼き用）",
        "targetChain": "日本料理・懐石・高級鮨コース・海鮮鉄板焼・割烹居酒屋",
        "prepState": "高級魚・赤甘鯛を鱗を残したまま三枚おろし・骨抜き下処理済み",
        "chainMerit": "一番手間がかかる甘鯛の下処理が不要。フライパンや鉄板・オーブンで皮目に油をかけるだけで、パリッパリの高級料理『甘鯛の松笠焼き（うろこ焼き）』が全店で提供可能。",
        "menuExample": "赤甘鯛の松笠焼き（うろこ焼き）、甘鯛の鉄板ポワレ、季節会席の焼物八寸（原価率目安：28〜32%）",
    },
    {
        "code": "FA-04",
        "name": "炙りのどぐろ（刺身・炙り寿司・焼き物用）",
        "targetChain": "グルメ回転寿司・鮨酒場・炉端焼き・北前海鮮居酒屋・和食御膳",
        "prepState": "脂乗りの良いのどぐろ（アカムツ）を下処理・皮目炙り加工済み",
        "chainMerit": "「のどぐろ」の圧倒的ブランド力で客単価と注文率が跳ね上がるキラー商材。店舗でのウロコ取り・内臓処理不要で、スライス・炙るだけで即提供。",
        "menuExample": "炙りのどぐろ握り、のどぐろ炙り刺し、のどぐろ塩焼き・土鍋ご飯（原価率目安：28〜32%）",
    },
    {
        "code": "FA-05",
        "name": "皮むき 剣先イカ柵（お造り・寿司・天ぷら兼用）",
        "targetChain": "海鮮居酒屋・すし酒場・立ち呑み・炉端・天ぷら・お好み鉄板焼",
        "prepState": "高鮮度の剣先イカを皮むき・柵取り加工し急速冷凍",
        "chainMerit": "狭小キッチンの居酒屋でもイカのワタ・皮の生ゴミが一切出ず、歩留まり100%。包丁で引くだけで透明感と甘みのあるイカ刺し・握り・天ぷらに即対応。",
        "menuExample": "剣先イカのお造り、イカ糸造り、剣先イカ握り、特撰イカ天ぷら・鉄板焼き（原価率目安：25〜29%）",
    },
    {
        "code": "FA-06",
        "name": "【本部バイヤー試食用】公式お試しセット（主力5種詰合せ）",
        "targetChain": "全チェーン本部の商品開発部・テストキッチン・旗艦店料理長",
        "prepState": "上記主力5商材（煮穴子・真穴子・赤甘鯛・のどぐろ・剣先イカ）を1箱に凝縮",
        "chainMerit": "新規口座開設の前に、まずは税込10,000円（送料無料）またはサンプル持参でテストキッチンにて全5品の品質・歩留まり・オペレーションを一括検証可能。",
        "menuExample": "公式EC（https://zmqxpe-6h.myshopify.com/products/trialset）または大阪本社へ直接サンプル持参",
    },
]


def build_excel(companies: list) -> None:
    wb = openpyxl.Workbook()

    # カラーパレット（視認性の高い濃紺×ゴールド×ティール）
    navy_header_fill = PatternFill("solid", fgColor="0F2C59")
    sub_header_fill = PatternFill("solid", fgColor="1E40AF")
    gold_accent_fill = PatternFill("solid", fgColor="FEF3C7")
    s_rank_fill = PatternFill("solid", fgColor="FFF1F2")
    a_rank_fill = PatternFill("solid", fgColor="EFF6FF")
    b_rank_fill = PatternFill("solid", fgColor="F8FAFC")
    zebra_fill = PatternFill("solid", fgColor="F1F5F9")

    white_bold_font = Font(name="Yu Gothic", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Yu Gothic", size=16, bold=True, color="0F2C59")
    section_font = Font(name="Yu Gothic", size=13, bold=True, color="0F2C59")
    regular_font = Font(name="Yu Gothic", size=10.5, bold=False, color="1E293B")
    bold_font = Font(name="Yu Gothic", size=10.5, bold=True, color="0F172A")
    phone_font = Font(name="Yu Gothic", size=11, bold=True, color="B91C1C")
    link_font = Font(name="Yu Gothic", size=10, underline="single", color="1D4ED8")

    thin_side = Side(style="thin", color="CBD5E1")
    med_navy = Side(style="medium", color="0F2C59")
    border_all = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)
    border_box = Border(left=thin_side, right=thin_side, top=thin_side, bottom=med_navy)

    # =========================================================================
    # Sheet 1: ダッシュボード_大阪本社攻略
    # =========================================================================
    ws_dash = wb.active
    ws_dash.title = "ダッシュボード_大阪本社攻略"
    ws_dash.views.sheetView[0].showGridLines = True

    ws_dash["A1"] = "🐟 株式会社ファインアトラス｜大阪本社 外食・寿司・海鮮居酒屋・和食チェーン本部 テレアポ営業ダッシュボード"
    ws_dash["A1"].font = title_font
    ws_dash["A2"] = "対象：大阪府内に本社・本部を置く多店舗展開チェーン（仕入部・商品開発部・購買バイヤーへの一括アプローチ専用台帳）"
    ws_dash["A2"].font = Font(name="Yu Gothic", size=11, bold=True, color="475569")

    total_count = len(companies)
    last_row = total_count + 4  # Sheet2 data rows: 5 to total_count+4

    # KPIサマリーテーブル
    ws_dash["A4"] = "📊 1. 優先ランク別・架電ターゲット集計（自動計算）"
    ws_dash["A4"].font = section_font

    kpi_headers = ["優先ランク", "戦略セグメント定義", "登録本社数", "構成比", "本部アプローチの最優先ポイント"]
    for col_idx, h in enumerate(kpi_headers, 1):
        cell = ws_dash.cell(row=5, column=col_idx, value=h)
        cell.fill = navy_header_fill
        cell.font = white_bold_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = border_all

    rank_rows = [
        ("S", "最優先Sランク：寿司・海鮮居酒屋・炉端チェーン本部＋デパ地下和惣菜・鮮魚寿司本部", "寿司ネタ・お造り・炉端・デパ地下折詰の主役（無添加煮穴子・炙りのどぐろ・赤甘鯛・剣先イカ）を直球提案"),
        ("A", "重点Aランク：総合居酒屋・和食割烹・仕出しケータリング・大型温浴施設＆冠婚葬祭本部", "季節フェア・会席鉢物・温浴和食・法要婚礼会席の省力化商材としてサンプル試食＆テスト導入から打診"),
        ("B", "拡大Bランク：蕎麦・うどん・天ぷら・専門料理（ふぐ・かに・鉄板・串かつ）＋シティホテル本部", "名物『一本穴子天丼』『大穴子串』『海鮮鉄板焼き』『ホテル日本料理・宴会メニュー』として提案"),
    ]
    for idx, (rk, desc, pt) in enumerate(rank_rows, start=6):
        c1 = ws_dash.cell(row=idx, column=1, value=rk)
        c2 = ws_dash.cell(row=idx, column=2, value=desc)
        c3 = ws_dash.cell(row=idx, column=3, value=f'=COUNTIF(大阪本社_チェーン本部架電リスト!B5:B{last_row}, "{rk}")')
        c4 = ws_dash.cell(row=idx, column=4, value=f"=C{idx}/C9")
        c4.number_format = "0.0%"
        c5 = ws_dash.cell(row=idx, column=5, value=pt)
        for c in (c1, c2, c3, c4, c5):
            c.font = bold_font if c in (c1, c3) else regular_font
            c.border = border_all
            c.alignment = Alignment(horizontal="center" if c in (c1, c3, c4) else "left", vertical="center", wrap_text=True)

    # 合計行
    ws_dash.cell(row=9, column=1, value="合計").font = bold_font
    ws_dash.cell(row=9, column=2, value="大阪府内本社 マルチ店舗展開チェーン本部 総数").font = bold_font
    ws_dash.cell(row=9, column=3, value=f"=COUNTA(大阪本社_チェーン本部架電リスト!A5:A{last_row})").font = bold_font
    ws_dash.cell(row=9, column=4, value="=SUM(D6:D8)").font = bold_font
    ws_dash.cell(row=9, column=4).number_format = "0.0%"
    ws_dash.cell(row=9, column=5, value="全社：実在電話番号・本社所在地・代表者・展開ブランド・受付突破＆バイヤートーク完備").font = bold_font
    for col_i in range(1, 6):
        cell = ws_dash.cell(row=9, column=col_i)
        cell.fill = gold_accent_fill
        cell.border = border_box
        cell.alignment = Alignment(horizontal="center" if col_i in (1, 3, 4) else "left", vertical="center")

    # エリア別集計と進捗ステータス集計を並べて配置
    ws_dash["A11"] = "🗺️ 2. 大阪府内 本社エリア別集計"
    ws_dash["A11"].font = section_font

    area_headers = ["本社エリア区分", "登録社数", "構成比", "訪問・サンプル持参の地の利"]
    for col_idx, h in enumerate(area_headers, 1):
        cell = ws_dash.cell(row=12, column=col_idx, value=h)
        cell.fill = sub_header_fill
        cell.font = white_bold_font
        cell.border = border_all
        cell.alignment = Alignment(horizontal="center", vertical="center")

    areas = [
        ("北摂（吹田・豊中・茨木・池田）", "★ファインアトラス（千里・江坂）のお膝元！当日サンプル持参・即訪問が可能な最重点エリア"),
        ("キタ（梅田・福島・天満・中津）", "御堂筋線・新御堂筋で15〜20分！急成長の鮨酒場・大型居酒屋本部が密集する最重要エリア"),
        ("中央区（本町・心斎橋・難波・道頓堀）", "御堂筋沿線（安土町・平野町・道頓堀）に上場和食チェーン・老舗本部が集結"),
        ("新大阪・淀川・京橋・東部", "江坂のすぐ隣（東三国・西中島・田川北・十八条）に海鮮居酒屋・がんこ等の本社が集中"),
        ("天王寺・阿倍野・なんば南部・湾岸", "スタンドふじ・吾作どん・マルシェ・グルメ杵屋・千房など実力派チェーン本社が集結"),
        ("堺・南大阪・東大阪", "大起水産・くら寿司・たちばな・きらく・玄品など大型チェーン本社が立地"),
    ]
    for idx, (ar, note) in enumerate(areas, start=13):
        c1 = ws_dash.cell(row=idx, column=1, value=ar)
        c2 = ws_dash.cell(row=idx, column=2, value=f'=COUNTIF(大阪本社_チェーン本部架電リスト!E5:E{last_row}, "{ar}")')
        c3 = ws_dash.cell(row=idx, column=3, value=f"=B{idx}/$C$9")
        c3.number_format = "0.0%"
        c4 = ws_dash.cell(row=idx, column=4, value=note)
        ws_dash.merge_cells(start_row=idx, start_column=4, end_row=idx, end_column=5)
        for col_i in range(1, 6):
            c = ws_dash.cell(row=idx, column=col_i)
            c.font = bold_font if col_i in (1, 2) else regular_font
            c.border = border_all
            c.alignment = Alignment(horizontal="center" if col_i in (2, 3) else "left", vertical="center", wrap_text=True)

    # 架電進捗ステータス集計
    ws_dash["A21"] = "📞 3. 架電・商談進捗ステータス集計（リストのN列を変更すると自動更新）"
    ws_dash["A21"].font = section_font

    status_headers = ["架電進捗ステータス", "件数", "進捗率", "次のアクション指針"]
    for col_idx, h in enumerate(status_headers, 1):
        cell = ws_dash.cell(row=22, column=col_idx, value=h)
        cell.fill = navy_header_fill
        cell.font = white_bold_font
        cell.border = border_all
        cell.alignment = Alignment(horizontal="center", vertical="center")

    statuses = [
        ("未架電", "まずはSランク（寿司・海鮮本部）＆北摂・淀川・キタエリアから架電開始"),
        ("受付・資料送付済", "規格書・サンプル案内送付後、3営業日以内にバイヤーへ着荷確認コール"),
        ("バイヤー不在・再架電", "バイヤーの氏名と在席曜日・時間帯をメモし、指定日時にピンポイント再架電"),
        ("サンプル・お試し送付", "試食日程に合わせて感想ヒアリング＆1〜2店舗での季節フェア試作を打診"),
        ("商談・試食アポ獲得", "本社またはテストキッチンへ主力5商材サンプルを持参し歩留まり・原価試算を提示"),
        ("テスト導入・成約", "旗艦店でのテスト導入から全店舗グランドメニュー・季節フェアへの拡大フォロー"),
        ("見送り・時期改め", "次回メニュー改定時期（春夏／秋冬）を控え、改定2ヶ月前に再アプローチ"),
    ]
    for idx, (st, act) in enumerate(statuses, start=23):
        c1 = ws_dash.cell(row=idx, column=1, value=st)
        c2 = ws_dash.cell(row=idx, column=2, value=f'=COUNTIF(大阪本社_チェーン本部架電リスト!N5:N{last_row}, "{st}")')
        c3 = ws_dash.cell(row=idx, column=3, value=f"=B{idx}/$C$9")
        c3.number_format = "0.0%"
        c4 = ws_dash.cell(row=idx, column=4, value=act)
        ws_dash.merge_cells(start_row=idx, start_column=4, end_row=idx, end_column=5)
        for col_i in range(1, 6):
            c = ws_dash.cell(row=idx, column=col_i)
            c.font = bold_font if col_i in (1, 2) else regular_font
            c.border = border_all
            c.alignment = Alignment(horizontal="center" if col_i in (2, 3) else "left", vertical="center")

    ws_dash.column_dimensions["A"].width = 30
    ws_dash.column_dimensions["B"].width = 48
    ws_dash.column_dimensions["C"].width = 16
    ws_dash.column_dimensions["D"].width = 16
    ws_dash.column_dimensions["E"].width = 58
    for r in range(5, 31):
        ws_dash.row_dimensions[r].height = 25

    # =========================================================================
    # Sheet 2: 大阪本社_チェーン本部架電リスト
    # =========================================================================
    ws_list = wb.create_sheet(title="大阪本社_チェーン本部架電リスト")
    ws_list.views.sheetView[0].showGridLines = True
    ws_list.freeze_panes = "E5"

    ws_list["A1"] = f"📞 ファインアトラス｜大阪本社 外食・寿司・海鮮・仕出し惣菜・ホテル温浴本部 テレアポ架電リスト（全{total_count}社・実在検証済）"
    ws_list["A1"].font = title_font
    ws_list["A2"] = (
        "※個店ではなく「複数店舗を展開する大阪本社（商品部・仕入バイヤー・メニュー開発担当）」へのアプローチ専用リストです。"
        "1社成約で5〜100店舗への一括・継続導入が見込めます。"
    )
    ws_list["A2"].font = Font(name="Yu Gothic", size=10.5, bold=True, color="B91C1C")

    headers = [
        "管理ID",
        "優先ランク",
        "業態カテゴリ",
        "運営会社名（大阪本社）",
        "本社エリア区分",
        "本社電話番号",
        "郵便番号",
        "本社所在地（大阪府内）",
        "代表者・窓口",
        "展開店舗規模",
        "主な展開ブランド（屋号）",
        "狙うべき本部部署・ターゲット",
        "推奨アプローチ魚種（主力5商材）",
        "架電進捗ステータス",
        "バイヤー氏名・次回架電日メモ",
        "本部攻略の切り口（なぜ刺さるか）",
        "【STEP1】受付突破トーク（代表電話→バイヤー取次ぎ）",
        "【STEP2】バイヤー接続トーク（サンプル持参・試食打診）",
        "公式Webサイト",
    ]

    for col_idx, h in enumerate(headers, 1):
        cell = ws_list.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_header_fill
        cell.font = white_bold_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border_all
    ws_list.row_dimensions[4].height = 32

    for idx, comp in enumerate(companies, start=5):
        rk = comp["rank"]
        row_fill = s_rank_fill if rk == "S" else (a_rank_fill if rk == "A" else b_rank_fill)

        vals = [
            sanitize_excel_cell(comp["id"]),
            sanitize_excel_cell(comp["rank"]),
            sanitize_excel_cell(comp["category"]),
            sanitize_excel_cell(comp["companyName"]),
            sanitize_excel_cell(comp["areaGroup"]),
            sanitize_excel_cell(comp["phone"]),
            sanitize_excel_cell(comp["postalCode"]),
            sanitize_excel_cell(comp["address"]),
            sanitize_excel_cell(comp["representative"]),
            sanitize_excel_cell(comp["storeCountScale"]),
            sanitize_excel_cell(comp["brands"]),
            sanitize_excel_cell(comp["targetDept"]),
            sanitize_excel_cell(comp["recommendedFish"]),
            "未架電",
            "",
            sanitize_excel_cell(comp["pitchAngle"]),
            sanitize_excel_cell(comp["callScriptReception"]),
            sanitize_excel_cell(comp["callScriptBuyer"]),
            sanitize_excel_cell(comp["website"]),
        ]

        for col_idx, val in enumerate(vals, 1):
            cell = ws_list.cell(row=idx, column=col_idx, value=val)
            cell.fill = row_fill
            cell.border = border_all
            if col_idx in (1, 2, 14):
                cell.font = bold_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 4:
                cell.font = bold_font
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            elif col_idx == 6:
                cell.font = phone_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == 19:
                cell.font = link_font
                cell.hyperlink = comp["website"]
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.font = regular_font
                cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

        ws_list.row_dimensions[idx].height = 54

    # プルダウン入力規則（N列：架電進捗ステータス）
    dv = DataValidation(
        type="list",
        formula1='"未架電,受付・資料送付済,バイヤー不在・再架電,サンプル・お試し送付,商談・試食アポ獲得,テスト導入・成約,見送り・時期改め"',
        allow_blank=True,
    )
    ws_list.add_data_validation(dv)
    dv.add(f"N5:N{last_row}")

    ws_list.auto_filter.ref = f"A4:S{last_row}"

    col_widths = {
        1: 11,
        2: 11,
        3: 28,
        4: 34,
        5: 26,
        6: 16,
        7: 11,
        8: 38,
        9: 18,
        10: 26,
        11: 38,
        12: 28,
        13: 34,
        14: 20,
        15: 28,
        16: 46,
        17: 55,
        18: 58,
        19: 32,
    }
    for col_i, w in col_widths.items():
        ws_list.column_dimensions[get_column_letter(col_i)].width = w

    # =========================================================================
    # Sheet 3: 本部バイヤー専用_受付突破＆商談トーク集
    # =========================================================================
    ws_talk = wb.create_sheet(title="本部バイヤー専用_受付突破＆商談トーク集")
    ws_talk.views.sheetView[0].showGridLines = True

    ws_talk["A1"] = "🎤 大阪チェーン本部（商品部・仕入バイヤー）専用 受付突破＆商談トーク・切り返し大全"
    ws_talk["A1"].font = title_font
    ws_talk["A2"] = "※個店（店長・大将）への架電と異なり、本社架電では「①受付から商品部バイヤーへの取次ぎ」と「②全店舗の仕込み削減・歩留まり100%・サンプル持参」がカギになります。"
    ws_talk["A2"].font = Font(name="Yu Gothic", size=10.5, bold=True, color="475569")

    talk_headers = ["ステップ", "フェーズ・場面", "対象相手", "攻略の急所（ポイント）", "そのまま使える実践トークスクリプト"]
    for col_idx, h in enumerate(talk_headers, 1):
        cell = ws_talk.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_header_fill
        cell.font = white_bold_font
        cell.border = border_all
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_talk.row_dimensions[4].height = 28

    for idx, sc in enumerate(HQ_SCRIPTS, start=5):
        vals = [sc["step"], sc["title"], sc["target"], sc["point"], sc["script"]]
        for col_idx, v in enumerate(vals, 1):
            c = ws_talk.cell(row=idx, column=col_idx, value=sanitize_excel_cell(v))
            c.font = bold_font if col_idx in (1, 2) else regular_font
            c.fill = gold_accent_fill if col_idx == 1 else b_rank_fill
            c.border = border_all
            c.alignment = Alignment(horizontal="center" if col_idx == 1 else "left", vertical="center", wrap_text=True)
        ws_talk.row_dimensions[idx].height = 95

    ws_talk["A10"] = "🛡️ 本社・バイヤー架電でよくある断り文句への切り返し（反論処理 6選）"
    ws_talk["A10"].font = section_font

    obj_headers = ["No.", "よくある断り文句（受付・バイヤー）", "切り返しのゴール", "そのまま使える切り返しトーク"]
    for col_idx, h in enumerate(obj_headers, 1):
        cell = ws_talk.cell(row=11, column=col_idx, value=h)
        cell.fill = sub_header_fill
        cell.font = white_bold_font
        cell.border = border_all
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_talk.merge_cells("D11:E11")
    ws_talk.row_dimensions[11].height = 28

    for idx, ob in enumerate(HQ_OBJECTIONS, start=12):
        c1 = ws_talk.cell(row=idx, column=1, value=f"切り返し {idx - 11}")
        c2 = ws_talk.cell(row=idx, column=2, value=sanitize_excel_cell(ob["title"]))
        c3 = ws_talk.cell(row=idx, column=3, value="既存卸と競合しない『一次加工済みニッチ高付加価値枠』『規格書＆サンプル試食』へ着地")
        c4 = ws_talk.cell(row=idx, column=4, value=sanitize_excel_cell(ob["answer"]))
        ws_talk.merge_cells(start_row=idx, start_column=4, end_row=idx, end_column=5)
        for col_i in range(1, 6):
            c = ws_talk.cell(row=idx, column=col_i)
            c.font = bold_font if col_i in (1, 2) else regular_font
            c.fill = zebra_fill if idx % 2 == 0 else PatternFill("solid", fgColor="FFFFFF")
            c.border = border_all
            c.alignment = Alignment(horizontal="center" if col_i == 1 else "left", vertical="center", wrap_text=True)
        ws_talk.row_dimensions[idx].height = 82

    ws_talk.column_dimensions["A"].width = 14
    ws_talk.column_dimensions["B"].width = 38
    ws_talk.column_dimensions["C"].width = 30
    ws_talk.column_dimensions["D"].width = 40
    ws_talk.column_dimensions["E"].width = 68

    # =========================================================================
    # Sheet 4: ファインアトラス商材＆チェーン提案規格表
    # =========================================================================
    ws_prod = wb.create_sheet(title="ファインアトラス商材＆チェーン提案規格表")
    ws_prod.views.sheetView[0].showGridLines = True

    ws_prod["A1"] = "🐟 ファインアトラス 主力5商材＋お試しセット｜多店舗チェーン本部向けメリット＆原価率提案表"
    ws_prod["A1"].font = title_font
    ws_prod["A2"] = "公式サイト：https://fineatlas.co.jp/ ｜ 公式お試しセット（税込10,000円）：https://zmqxpe-6h.myshopify.com/products/trialset"
    ws_prod["A2"].font = Font(name="Yu Gothic", size=10.5, bold=True, color="1D4ED8")

    prod_headers = ["商材コード", "商材名", "ターゲットチェーン業態", "加工・下処理状態", "チェーン本部への導入メリット（職人不要・ロスゼロ）", "看板メニュー＆原価率シミュレーション"]
    for col_idx, h in enumerate(prod_headers, 1):
        cell = ws_prod.cell(row=4, column=col_idx, value=h)
        cell.fill = navy_header_fill
        cell.font = white_bold_font
        cell.border = border_all
        cell.alignment = Alignment(horizontal="center", vertical="center")
    ws_prod.row_dimensions[4].height = 28

    for idx, pr in enumerate(PRODUCTS_CATALOG, start=5):
        vals = [pr["code"], pr["name"], pr["targetChain"], pr["prepState"], pr["chainMerit"], pr["menuExample"]]
        for col_idx, v in enumerate(vals, 1):
            c = ws_prod.cell(row=idx, column=col_idx, value=sanitize_excel_cell(v))
            c.font = bold_font if col_idx in (1, 2) else regular_font
            c.fill = gold_accent_fill if pr["code"] == "FA-06" else (s_rank_fill if idx % 2 == 1 else PatternFill("solid", fgColor="FFFFFF"))
            c.border = border_all
            c.alignment = Alignment(horizontal="center" if col_idx == 1 else "left", vertical="center", wrap_text=True)
        ws_prod.row_dimensions[idx].height = 60

    ws_prod.column_dimensions["A"].width = 14
    ws_prod.column_dimensions["B"].width = 34
    ws_prod.column_dimensions["C"].width = 36
    ws_prod.column_dimensions["D"].width = 38
    ws_prod.column_dimensions["E"].width = 50
    ws_prod.column_dimensions["F"].width = 46

    wb.save(EXCEL_PATH)
    print(f"[OK] Saved Excel ledger: {EXCEL_PATH}")


def build_data_js(companies: list) -> None:
    payload = {
        "generatedAt": "2026-11-26",
        "totalCompanies": len(companies),
        "excelFileName": EXCEL_FILENAME,
        "fineAtlasLinks": {
            "corporateUrl": "https://fineatlas.co.jp/",
            "trialSetUrl": "https://zmqxpe-6h.myshopify.com/products/trialset",
        },
        "hqScripts": HQ_SCRIPTS,
        "hqObjections": HQ_OBJECTIONS,
        "productsCatalog": PRODUCTS_CATALOG,
        "companies": companies,
    }
    js_content = "// Auto-generated by scripts/build_deliverables.py\n"
    js_content += "window.OSAKA_HQ_DATA = " + json.dumps(payload, ensure_ascii=False, indent=2) + ";\n"
    DATA_JS_PATH.write_text(js_content, encoding="utf-8")
    print(f"[OK] Saved data.js: {DATA_JS_PATH}")


def main() -> None:
    companies = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
    build_excel(companies)
    build_data_js(companies)


if __name__ == "__main__":
    main()
