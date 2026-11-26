#!/usr/bin/env python3
"""
既存の62社と2体のサブエージェントが収集・裏取りした新規企業リストを重複排除・整形し、
150社以上（約166社）の companies_master.json に統合・拡張するスクリプト。
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_JSON = BASE_DIR / "scripts" / "companies_master.json"
SEG56_JSON = Path("/home/antigravity/.gemini/jetski/brain/2c83613c8719faa12c99edd8eb76dde3/scratch/verified_67_osaka_companies_seg5_seg6.json")

BATCH_1_COMPANIES = [
  {
    "companyName": "株式会社オーゼットカンパニー",
    "postalCode": "〒553-0003",
    "address": "大阪府大阪市福島区福島5-1-26 MF西梅田ビル3D",
    "phone": "06-6225-8290",
    "representative": "岡本 匡洋",
    "storeCountScale": "26店舗（福島・梅田・天満・大阪・東京）",
    "brands": "酒菜や いしもん 本店、いしもん 対屋、あねの元カレ、お料理 五勝手、うたげどころ うぉっしゅ、魚屋 十忠八九",
    "website": "https://oz-company.com/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社竹茂（徳田酒店グループ本部）",
    "postalCode": "〒534-0025",
    "address": "大阪府大阪市都島区片町2-2-40 京橋大発ビル412号室",
    "phone": "06-6355-0956",
    "representative": "徳田 信子",
    "storeCountScale": "16店舗（京橋・大阪駅前第1〜第4ビル・ルクア大阪・西梅田・有楽町・丸の内）",
    "brands": "徳田酒店、大衆呑処 徳田酒店（鮮魚刺身・海鮮アテ・地酒大衆酒場）",
    "website": "https://tokuda-group.co.jp/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社フジオカンパニー（丸万寿司グループ本部）",
    "postalCode": "〒530-0041",
    "address": "大阪府大阪市北区天神橋4-7-6 3階",
    "phone": "06-6358-5800",
    "representative": "藤尾 正治",
    "storeCountScale": "10店舗（梅田・曽根崎・東通り・堂山・天満・OAP・神戸ミント）",
    "brands": "丸万寿司、牡蠣とワイン立喰い すしまる、天満すし、大阪すし たこ竹",
    "website": "https://fujiocompany.com/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社UOTERU（魚輝水産グループ本部）",
    "postalCode": "〒544-0005",
    "address": "大阪府大阪市生野区中川2-15-18",
    "phone": "06-6754-8886",
    "representative": "古志 晃清",
    "storeCountScale": "約15店舗（東大阪・八尾・大東・富田林・生野・大阪市東部・奈良）",
    "brands": "海鮮れすとらん 魚輝水産、マグロ卸のフィッシュマーケット 魚輝水産、魚輝すし、大衆串カツ酒場 なかむら",
    "website": "https://uoteru.co.jp/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社小鯛雀鮨鮨萬（すし萬本部）",
    "postalCode": "〒550-0004",
    "address": "大阪府大阪市西区靱本町2-3-7 鮨萬本社ビル",
    "phone": "06-6448-6435",
    "representative": "小倉 康宏",
    "storeCountScale": "約15店舗（リーガロイヤル・阪急うめだ・阪神・大丸心斎橋・高島屋・阿倍野近鉄・芦屋・東京）",
    "brands": "小鯛雀鮨 すし萬、波沙鮓（なみさす）、おすしカフェ あるにあらむ",
    "website": "https://www.sushiman.co.jp/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "有限会社なかの満（なかの家・回転寿し仁本部）",
    "postalCode": "〒534-0024",
    "address": "大阪府大阪市都島区東野田町2-4-20",
    "phone": "06-6948-6004",
    "representative": "中野 満男",
    "storeCountScale": "3店舗（京橋・あべのハルカスダイニング大型店）",
    "brands": "旬魚旬菜 なかの家 あべのハルカスダイニング店、回転寿し 仁 京橋店、回転寿し 仁 あべのハルカス店",
    "website": "https://nakanoya-group.com/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社こうむら（海鮮屋台おくまん本部）",
    "postalCode": "〒530-0015",
    "address": "大阪府大阪市北区中崎西1-4-22 梅田東ビル415",
    "phone": "06-4802-0787",
    "representative": "香村 達信",
    "storeCountScale": "約35店舗（大阪・兵庫・東京・千葉・福岡）",
    "brands": "海鮮屋台 おくまん、大衆酒場 おくまん",
    "website": "https://koumura-okuman.net/",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社WILL（鮨仙酢・すし金・魚頂天酒場本部）",
    "postalCode": "〒531-0072",
    "address": "大阪府大阪市北区豊崎2-1-9 G&Rビル402",
    "phone": "06-6136-4073",
    "representative": "代表取締役",
    "storeCountScale": "約20店舗（北新地・梅田・天満・高槻・京都・三宮・名古屋）",
    "brands": "鮨 仙酢、北新地 鮨 千功堂、寿司のだりぴん、天満酒場 すし金、梅田酒場 すし金、魚頂天酒場 まつり、魚屋 めのじ、大阪 かに蔵",
    "website": "https://compalyze.co.jp/company/4120001183828",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社服部春駒（春駒本部）",
    "postalCode": "〒530-0021",
    "address": "大阪府大阪市北区浮田1-1-20",
    "phone": "06-6351-9103",
    "representative": "服部 武利",
    "storeCountScale": "2店舗（天満・天神橋筋五丁目 本店・支店）",
    "brands": "春駒 本店、春駒 支店（天満名物・大衆江戸前寿司）",
    "website": "https://www.careermap.jp/corporations/94877",
    "categoryHint": "① 寿司・海鮮居酒屋・炉端チェーン本部"
  },
  {
    "companyName": "株式会社オペレーションファクトリー",
    "postalCode": "〒550-0014",
    "address": "大阪府大阪市西区北堀江1-12-10 山田ビル2F",
    "phone": "06-6535-9006",
    "representative": "笠島 明裕",
    "storeCountScale": "約50店舗（梅田・難波・堀江・関西・首都圏）",
    "brands": "梅田 牡蠣と海鮮 ワーフ（Wharf）、魚イタリアン＆オイスター、堀江ブルー、ちょうつがひ、ファクトリーカフェ",
    "website": "https://www.opefac.com/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社きちりホールディングス",
    "postalCode": "〒541-0052",
    "address": "大阪府大阪市中央区安土町2-3-13 大阪国際ビルディング8階",
    "phone": "06-6262-3456",
    "representative": "平川 昌紀",
    "storeCountScale": "約130店舗（関西・首都圏）",
    "brands": "KICHIRI（きちり）、たんとと和くら（炭火焼干物・牛たん・和食）、いしがまやハンバーグ",
    "website": "https://www.kichiri.co.jp/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社エターナルホスピタリティグループ（旧：鳥貴族HD）",
    "postalCode": "〒541-0047",
    "address": "大阪府大阪市中央区淡路町4-2-13 アーバンネット御堂筋ビル20階",
    "phone": "06-6206-0808",
    "representative": "大倉 忠司",
    "storeCountScale": "国内約650店舗（鳥貴族・やきとり大吉 等）",
    "brands": "鳥貴族、やきとり大吉、TORIKI BURGER",
    "website": "https://eternal-hospitality.co.jp/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社バルニバービ 大阪本部",
    "postalCode": "〒550-0015",
    "address": "大阪府大阪市西区南堀江1-14-26 中澤唐木ビル6F",
    "phone": "06-4390-6544",
    "representative": "佐藤 裕久",
    "storeCountScale": "約100店舗（大阪・関西・首都圏・淡路島）",
    "brands": "GARB（ガーブ）、中之島ソーシャルイートアウェイク、ガーブウィークス、海鮮・和食・イタリアンダイニング各店",
    "website": "https://www.balnibarbi.com/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社松屋（松屋グループ・ニューツルマツ本部）",
    "postalCode": "〒583-0036",
    "address": "大阪府藤井寺市恵美坂1-13-29",
    "phone": "072-952-0298",
    "representative": "松山 知弘",
    "storeCountScale": "約30店舗（天王寺・難波・梅田・心斎橋・大阪・関西圏）",
    "brands": "大衆酒場 ニューツルマツ（海鮮・魚介天ぷら・寿司・大衆酒場）、和匠肉料理 松屋、黒毛和牛焼肉 松屋",
    "website": "https://www.matsuya-gr.com/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社Push Up（大衆酒場さんま本部）",
    "postalCode": "〒531-0071",
    "address": "大阪府大阪市北区中津1-2-21",
    "phone": "06-4300-6671",
    "representative": "重坂 浩貴",
    "storeCountScale": "6店舗（天満本店・裏天満店・天満駅前店・京橋店・大阪駅前第1ビル店・梅田東通り店）",
    "brands": "大衆酒場 さんま（海鮮・寿司・天ぷら・大衆居酒屋）",
    "website": "https://taisyusakaba-sanma.com/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社G'Style",
    "postalCode": "〒530-0033",
    "address": "大阪府大阪市北区池田町6-7",
    "phone": "06-6314-6477",
    "representative": "金子 健治",
    "storeCountScale": "5店舗（天満・天神橋エリア）",
    "brands": "天満ビストロワイン酒場 Gobuプラス、天満駅前西洋酒場 Gobuトレス、Bar&Deli ROSSELLO、餃子イェスタデイ",
    "website": "http://gstyle.shop/",
    "categoryHint": "② 総合居酒屋・大衆酒場・ダイニング本部"
  },
  {
    "companyName": "株式会社美々卯",
    "postalCode": "〒541-0046",
    "address": "大阪府大阪市中央区平野町4-6-18",
    "phone": "06-6226-7401",
    "representative": "薩摩 和男",
    "storeCountScale": "15店舗（本町・心斎橋・梅田・新大阪・堺・京都・阪神間）",
    "brands": "美々卯（名物うどんすき・日本料理・天ぷら・季節懐石）",
    "website": "https://mimiu.co.jp/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社フーズクリエーション",
    "postalCode": "〒540-0036",
    "address": "大阪府大阪市中央区船越町1-6-6 ODC天満橋ビル2F",
    "phone": "06-6940-3787",
    "representative": "岡本 英征",
    "storeCountScale": "15店舗（大阪・関西商業施設・温浴施設レストラン）",
    "brands": "旬魚旬菜ダイニング、和食・海鮮レストラン、大黒麺食堂、商業施設レストラン運営",
    "website": "https://www.foods-creation.com/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社ハートダイニング（H2Oリテイリンググループ）",
    "postalCode": "〒532-0022",
    "address": "大阪府大阪市淀川区野中南2-8-10 H2O十三ビル本館6階",
    "phone": "06-7633-0722",
    "representative": "竹本 賢市",
    "storeCountScale": "約30店舗（阪急うめだ本店・阪神梅田本店・千里阪急・川西阪急等の百貨店内レストラン）",
    "brands": "美味旬菜（阪急うめだ本店和食）、阪神髭定（海鮮・魚介レストラン）、百貨店内和食・ダイニング各店",
    "website": "https://www.heart-dining.co.jp/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社1&D（ワン・ダイニング）",
    "postalCode": "〒550-0013",
    "address": "大阪府大阪市西区新町1-27-9",
    "phone": "06-6541-4284",
    "representative": "髙橋 淳",
    "storeCountScale": "約100店舗（大阪・関西圏中心）",
    "brands": "きんのぶた（和食しゃぶしゃぶ）、旬菜しゃぶ重、ワンカルビ、あぶりや",
    "website": "https://1andd.co.jp/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社ダンシンダイナー",
    "postalCode": "〒532-0011",
    "address": "大阪府大阪市淀川区西中島7-10-3 エルブ新大阪2F",
    "phone": "06-6100-2720",
    "representative": "田華 久登",
    "storeCountScale": "約35店舗（梅田・北浜・なんば・千里EXPOCITY・関西・首都圏）",
    "brands": "但馬屋、但馬屋 蔓萬、すきやきしゃぶしゃぶ 神戸牛石田、焼肉の牛太 本陣",
    "website": "https://d-diner.net/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社エースケータリング",
    "postalCode": "〒574-0013",
    "address": "大阪府大東市中垣内5-6-10",
    "phone": "072-875-9330",
    "representative": "宮本 聡",
    "storeCountScale": "関西一円の法人パーティ・イベントケータリング・飲食店運営",
    "brands": "エースケータリング（法人懇親会・寿司・海鮮オードブル・イベント飲食プロデュース）",
    "website": "https://ace-catering.co.jp/",
    "categoryHint": "⑤ 仕出し割烹・デパ地下和惣菜・弁当給食・ケータリング本社"
  },
  {
    "companyName": "株式会社大成閣",
    "postalCode": "〒542-0083",
    "address": "大阪府大阪市中央区東心斎橋1-18-12",
    "phone": "06-6271-5238",
    "representative": "梅木 貴喜",
    "storeCountScale": "心斎橋大型6フロア本店（最大500名宴会・海鮮中華懐石・婚礼宴会）",
    "brands": "中国料理 大成閣（大型宴会・海鮮中華コース・仕出し）",
    "website": "https://taiseikaku.jp/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社塩梅（あんばい）",
    "postalCode": "〒567-0834",
    "address": "大阪府茨木市学園南町7-5",
    "phone": "072-657-1122",
    "representative": "今井 清秀",
    "storeCountScale": "関西圏約300事業所（企業社員食堂・病院・福祉施設・学校給食受託）",
    "brands": "総合給食・フードサービス 塩梅（あんばい）",
    "website": "https://anbai.co.jp/",
    "categoryHint": "⑤ 仕出し割烹・デパ地下和惣菜・弁当給食・ケータリング本社"
  },
  {
    "companyName": "株式会社三栄フーズ",
    "postalCode": "〒561-0891",
    "address": "大阪府豊中市走井3-3-18",
    "phone": "06-6853-3336",
    "representative": "竹田 晴彦",
    "storeCountScale": "北摂・豊中本社工場（ホテル・和食店・居酒屋チェーン向け業務用調理加工・OEM製造卸）",
    "brands": "三栄フーズ（甘鯛柚子幽庵漬・和食惣菜・ホテル居酒屋向け調理加工品）",
    "website": "https://san-ei-foods.com/",
    "categoryHint": "⑤ 仕出し割烹・デパ地下和惣菜・弁当給食・ケータリング本社"
  },
  {
    "companyName": "株式会社NIS（SRSグループ）",
    "postalCode": "〒544-0001",
    "address": "大阪府大阪市生野区新今里3-3-6",
    "phone": "06-6755-4949",
    "representative": "岡田 連平",
    "storeCountScale": "直営およびFC約200店舗（上本町YUFURA・東大阪・関西・全国）",
    "brands": "ビフテキ牛ノ福・厨房さと、からあげ専門店 鶏笑",
    "website": "https://nis-torisho.com/",
    "categoryHint": "③ 和食・割烹・しゃぶしゃぶ・仕出し本部"
  },
  {
    "companyName": "株式会社今井（道頓堀今井）",
    "postalCode": "〒542-0071",
    "address": "大阪府大阪市中央区道頓堀1-7-22",
    "phone": "06-6211-0319",
    "representative": "今井 徹",
    "storeCountScale": "直営・百貨店イートイン・ギフト店計7拠点（道頓堀本店・リーガロイヤル・新大阪・泉北 等）",
    "brands": "道頓堀 今井（うどん寄せ鍋・穴子うどん・季節うどん懐石）",
    "website": "https://www.d-imai.com/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社与太呂",
    "postalCode": "〒530-0005",
    "address": "大阪府大阪市北区中之島3-3-23 中之島ダイビル3F",
    "phone": "06-6147-2313",
    "representative": "高畠 啓",
    "storeCountScale": "5店舗（中之島ダイビル本店・ハービスPLAZA梅田店・大丸心斎橋・神戸 等）",
    "brands": "天ぷら・鯛めし 与太呂（よたろ）",
    "website": "https://yotaro.co.jp/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社アゲル（天ぷらとワイン大塩本部）",
    "postalCode": "〒530-0012",
    "address": "大阪府大阪市北区芝田2-3-16 東洋ビル別館302",
    "phone": "06-6467-8233",
    "representative": "大塩 智史",
    "storeCountScale": "8店舗（天満市場・梅田・大阪駅前第3ビル・天五横丁・日比谷・丸の内・有楽町・中野）",
    "brands": "天ぷらとワイン 大塩",
    "website": "https://tempura-oshio.com/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社一門会（串かつだるま本部）",
    "postalCode": "〒556-0002",
    "address": "大阪府大阪市浪速区恵美須東1-6-8",
    "phone": "06-6645-7056",
    "representative": "上山 勝也",
    "storeCountScale": "17店舗（新世界・難波・道頓堀・梅田ルクア・KITTE大阪・新大阪・伊丹空港・京都）",
    "brands": "大阪新世界元祖 串かつだるま、創作串揚げ だるま きわ味",
    "website": "https://www.kushikatu-daruma.com/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "Fモトアキラ株式会社（串かつ凡・串揚げキッチンだん本部）",
    "postalCode": "〒530-0003",
    "address": "大阪府大阪市北区堂島1-3-16 堂島メリーセンタービルB1F",
    "phone": "06-6344-0400",
    "representative": "若狭 洋介",
    "storeCountScale": "8店舗（北新地・梅田・難波・石橋・京都御所南・銀座・パリ）",
    "brands": "串かつ凡、串揚げキッチン だん、天婦羅 ぼん次",
    "website": "http://kitchen-dan.jp/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社六覺燈",
    "postalCode": "〒542-0073",
    "address": "大阪府大阪市中央区日本橋1-21-16 たこそうビル2F",
    "phone": "06-6633-1302",
    "representative": "水野 幾郎",
    "storeCountScale": "3店舗（黒門市場本店・銀座店・麻布十番店）",
    "brands": "串かつ・ワイン 六覺燈（ろっかくてい）",
    "website": "https://www.rokukakutei.co.jp/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社イデア（鶴橋風月本部）",
    "postalCode": "〒543-0014",
    "address": "大阪府大阪市天王寺区玉造元町3-9 八光玉造ビル8階",
    "phone": "06-4304-0213",
    "representative": "五影 隆則",
    "storeCountScale": "約75店舗（大阪・関西中心・全国・海外）",
    "brands": "鶴橋風月、鶴橋風月LIGHT（海鮮お好み焼・いか・えび・牡蠣フェア・鉄板焼）",
    "website": "https://fugetsu.jp/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "白ハト食品工業株式会社",
    "postalCode": "〒570-0083",
    "address": "大阪府守口市京阪本通1-4-10",
    "phone": "06-6997-0151",
    "representative": "永尾 俊一",
    "storeCountScale": "約100店舗（道頓堀・梅田・新大阪・全国の百貨店・駅ナカ・商業施設）",
    "brands": "たこ家道頓堀くくる、道頓堀コナモンミュージアム、らぽっぽファーム",
    "website": "https://www.shirohato.com/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社ゆかり",
    "postalCode": "〒530-0057",
    "address": "大阪府大阪市北区曾根崎2-14-13",
    "phone": "06-6311-0214",
    "representative": "山下 真明",
    "storeCountScale": "9店舗（曽根崎本店・富国ビル・ホワイティうめだ・KITTE大阪・なんばウォーク・天王寺ミオ・横浜・東京）",
    "brands": "お好み焼 ゆかり（海鮮お好み焼・鉄板焼・冷凍お好み焼製造卸）",
    "website": "https://www.yukarichan.co.jp/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "株式会社蛸之徹",
    "postalCode": "〒531-0071",
    "address": "大阪府大阪市北区中津4-6-9",
    "phone": "06-6314-0847",
    "representative": "松岡 真希",
    "storeCountScale": "2店舗（梅田角田店・マルビル/梅田エリア）",
    "brands": "蛸之徹（たこ焼・海鮮鉄板焼・お好み焼）",
    "website": "http://takonotetsu.com/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  },
  {
    "companyName": "大真実業株式会社",
    "postalCode": "〒531-0071",
    "address": "大阪府大阪市北区中津3-3-35",
    "phone": "06-6375-8787",
    "representative": "大里 仁志",
    "storeCountScale": "約25店舗（梅田・新大阪・江坂・難波・大阪・阪神間）",
    "brands": "中華料理 龍鳳、九州らーめん亀王、チャイニーズダイニング",
    "website": "https://daishin-jitugyou.jp/",
    "categoryHint": "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部"
  }
]


def detect_area_group(address: str) -> str:
    if any(k in address for k in ["吹田市", "豊中市", "茨木市", "池田市", "箕面市", "高槻市", "摂津市"]):
        return "北摂（吹田・豊中・茨木・池田）"
    if any(k in address for k in ["北区", "福島区"]):
        return "キタ（梅田・福島・天満・中津）"
    if any(k in address for k in ["中央区", "西区"]):
        return "中央区（本町・心斎橋・難波・道頓堀）"
    if any(k in address for k in ["淀川区", "東淀川区", "西淀川区", "都島区", "旭区", "鶴見区", "城東区", "東成区", "生野区", "守口市", "門真市", "寝屋川市", "枚方市", "大東市"]):
        return "新大阪・淀川・京橋・東部"
    if any(k in address for k in ["天王寺区", "阿倍野区", "浪速区", "住之江区", "住吉区", "東住吉区", "港区", "大正区", "西成区"]):
        return "天王寺・阿倍野・なんば南部・湾岸"
    return "堺・南大阪・東大阪"


def build_enriched_record(raw: dict) -> dict:
    cat = raw["categoryHint"]
    cname = raw["companyName"]
    brands = raw["brands"]
    area = detect_area_group(raw["address"])
    is_hokusetsu = area == "北摂（吹田・豊中・茨木・池田）"
    geo_prefix = "同じ北摂エリア（吹田・千里）と長崎・対馬を拠点に" if is_hokusetsu else "大阪（吹田・千里）と長崎・対馬を拠点に"

    if cat == "① 寿司・海鮮居酒屋・炉端チェーン本部":
        rank = "S"
        target_dept = "商品部・仕入バイヤー（寿司・鮮魚担当）"
        rec_fish = "無添加炊き上げ煮穴子 / 炙りのどぐろ / 皮むき剣先イカ柵"
        pitch = f"『{brands.split('、')[0]}』を展開する大阪本社！店舗での魚捌きや炊き上げ手間ゼロで即提供できる無添加煮穴子・炙りのどぐろ・剣先イカ柵が直球で刺さる。"
        reception = (
            f"お世話になります。{geo_prefix}寿司・海鮮チェーン様向けの下処理済み水産品を卸しております、株式会社ファインアトラスの〇〇と申します。"
            f"『{brands.split('、')[0]}』各店様の魚介仕入れ・季節メニューを担当されている【商品部・仕入バイヤー様】はいらっしゃいますでしょうか？"
        )
        buyer = (
            f"突然のお電話失礼いたします。ファインアトラスの〇〇と申します。御社の『{brands.split('、')[0]}』様向けに、"
            f"店舗での仕込み手間ゼロでそのまま握りやお造りに出せる【無添加炊き上げ煮穴子】【炙りのどぐろ】【皮むき剣先イカ柵】をご提案しております。"
            f"歩留まり100%で廃棄ロスが出ない規格ですので、ぜひ本社へサンプルをお持ちさせていただけませんか？"
        )
    elif cat == "② 総合居酒屋・大衆酒場・ダイニング本部":
        rank = "A"
        target_dept = "商品開発部・購買バイヤー"
        rec_fish = "皮むき剣先イカ柵 / 活〆真穴子フィレ / 炙りのどぐろ"
        pitch = f"『{brands.split('、')[0]}』を多店舗展開する大阪本部！アルバイト中心のキッチンでも封を開けるだけで海鮮目玉メニューが作れる下処理済み商材が最適。"
        reception = (
            f"お世話になります。{geo_prefix}居酒屋・ダイニングチェーン様向けに下処理済み水産加工品を卸しております、株式会社ファインアトラスの〇〇と申します。"
            f"『{brands.split('、')[0]}』様のメニュー開発・食材仕入れをご担当されている【購買・商品開発のバイヤー様】にお繋ぎいただけますでしょうか？"
        )
        buyer = (
            f"お忙しいところ恐れ入ります。ファインアトラスの〇〇と申します。御社の『{brands.split('、')[0]}』様の季節フェアや海鮮メニュー向けに、"
            f"キッチンでのウロコ取りや皮むきが一切不要な【皮むき剣先イカ柵】【活〆真穴子フィレ】【炙りのどぐろ】をご案内しております。"
            f"まず1〜2店舗でのテスト導入やサンプル試食から対応可能ですので、一度サンプルをお届けさせていただけないでしょうか？"
        )
    elif cat == "③ 和食・割烹・しゃぶしゃぶ・仕出し本部":
        rank = "A"
        target_dept = "購買部・総料理長（和食メニュー開発担当）"
        rec_fish = "鱗付き赤甘鯛フィレ / 無添加炊き上げ煮穴子 / 炙りのどぐろ"
        pitch = f"『{brands.split('、')[0]}』の会席・御膳の格を上げつつ、板前・調理師の仕込み時間を劇的に短縮する『鱗付き赤甘鯛フィレ（松笠焼き用）』『無添加煮穴子』が合致。"
        reception = (
            f"お世話になります。{geo_prefix}和食・日本料理チェーン様向けに特選水産加工品を卸しております、株式会社ファインアトラスの〇〇と申します。"
            f"季節御膳や会席メニューの水産食材仕入れをご担当されている【購買部・総料理長様】はいらっしゃいますでしょうか？"
        )
        buyer = (
            f"突然のお電話失礼いたします。ファインアトラスの〇〇と申します。御社の『{brands.split('、')[0]}』様の季節御膳・会席の一品向けに、"
            f"そのまま松笠焼きにできる【鱗付き赤甘鯛フィレ】や【無添加炊き上げ煮穴子】【炙りのどぐろ】をご提案しております。"
            f"全店舗で均一な割烹品質をロスゼロで再現できますので、一度ご試食用サンプルをお持ちさせていただけませんか？"
        )
    elif cat == "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部":
        rank = "B"
        target_dept = "商品部・メニュー開発バイヤー"
        rec_fish = "活〆真穴子フィレ / 皮むき剣先イカ柵 / 無添加炊き上げ煮穴子"
        pitch = f"『{brands.split('、')[0]}』の名物天ぷら・串揚げ・海鮮鉄板メニュー向けに、開き・骨切り・皮むき済みの『活〆真穴子フィレ』『剣先イカ柵』が即戦力。"
        reception = (
            f"お世話になります。{geo_prefix}専門料理チェーン様向けに下処理済み穴子・イカ等の水産品を卸しております、株式会社ファインアトラスの〇〇と申します。"
            f"『{brands.split('、')[0]}』様の季節メニューや水産食材仕入れをご担当されている【商品部のバイヤー様】にお繋ぎいただけますでしょうか？"
        )
        buyer = (
            f"お忙しいところ恐れ入ります。ファインアトラスの〇〇と申します。御社の『{brands.split('、')[0]}』様向けに、"
            f"店舗での下処理ゼロでそのまま一本揚げや鉄板焼きに出せる【活〆真穴子フィレ】と【皮むき剣先イカ柵】をご提案しております。"
            f"歩留まり100%で原価管理が非常にしやすい規格ですので、本社へサンプルをお持ちさせていただけないでしょうか？"
        )
    elif cat == "⑤ 仕出し割烹・デパ地下和惣菜・弁当給食・ケータリング本社":
        # 寿司・デパ地下和惣菜・高級仕出しはSまたはA
        is_high_match = any(k in (cname + brands) for k in ["水了軒", "阪急デリカ", "なだ万", "湯木", "吉兆", "千惣", "咲菜", "惣兵衛", "よしや", "魚吉", "神宗", "光洋", "ダイエー", "ライフ", "万代", "関西フード", "サンプラザ", "佐竹"])
        rank = "S" if is_high_match else "A"
        target_dept = "商品部・購買部（水産・デリカ惣菜バイヤー）"
        rec_fish = "無添加炊き上げ煮穴子 / 鱗付き赤甘鯛フィレ / 活〆真穴子フィレ"
        pitch = f"大量の折詰弁当・デパ地下惣菜・ケータリング製造において、冷めてもふっくら柔らかく歩留まり100%の『無添加炊き上げ煮穴子』『赤甘鯛フィレ』『真穴子天』が製造ラインの省力化に直結。"
        reception = (
            f"お世話になります。{geo_prefix}デパ地下惣菜・仕出し・フードサービス本部様向けに業務用の一級水産加工品を卸しております、株式会社ファインアトラスの〇〇と申します。"
            f"お弁当・お惣菜や季節企画の水産原料をご担当されている【商品部・購買バイヤー様】はいらっしゃいますでしょうか？"
        )
        buyer = (
            f"突然のお電話失礼いたします。対馬水産グループのファインアトラス〇〇と申します。御社の『{brands.split('、')[0]}』様向けに、"
            f"解凍・盛り付けだけで均一ポーションが出せる【無添加炊き上げ煮穴子】や、天ぷら・焼き物用の【活〆真穴子フィレ】【鱗付き赤甘鯛フィレ】をご案内しております。"
            f"セントラルキッチンや店舗での下処理工数をゼロにできる規格ですので、商品規格書とサンプルをお届けさせていただけませんか？"
        )
    else:
        # ⑥ ホテル・旅館・温浴施設・冠婚葬祭（宴会・法要）運営本社
        is_high_match = any(k in (cname + brands) for k in ["水春", "ビーバー", "延羽", "延田", "おゆば", "ツルカメ", "なにわの湯", "スパワールド", "不死王閣", "南天苑", "み奈美亭", "不動口館", "滝の湯", "ベルコ", "公益社", "セルビス", "大阪祭典", "玉泉院"])
        rank = "A" if is_high_match else "B"
        target_dept = "購買部・総料理長（日本料理・宴会・温浴和食統括）"
        rec_fish = "鱗付き赤甘鯛フィレ / 炙りのどぐろ / 無添加炊き上げ煮穴子"
        pitch = f"婚礼・法要宴会や温浴施設内の和食レストラン（『{brands.split('、')[0]}』）で、数百名規模の宴会や週末ピーク時にも職人不要で割烹品質を出せる『鱗付き赤甘鯛フィレ』『炙りのどぐろ』『無添加煮穴子』が活躍。"
        reception = (
            f"お世話になります。{geo_prefix}ホテル・温浴施設・会館様の日本料理・宴会部門向けに特選水産加工品を卸しております、株式会社ファインアトラスの〇〇と申します。"
            f"和食レストランやご宴会・法要料理の魚介仕入れを担当されている【購買部のご担当者様、または和食総料理長様】にお繋ぎいただけますでしょうか？"
        )
        buyer = (
            f"お忙しいところ恐れ入ります。ファインアトラスの〇〇と申します。御社の『{brands.split('、')[0]}』様のご宴会・法要会席や和食ダイニング向けに、"
            f"鱗付きのまま松笠焼きにできる【赤甘鯛フィレ】や【炙りのどぐろ】【無添加炊き上げ煮穴子】をご提案しております。"
            f"調理場の仕込み負担を大幅に減らしながら客単価・満足度を高められる商材ですので、ぜひ一度サンプルをご試食いただけないでしょうか？"
        )

    return {
        "id": "",  # assigned after sort
        "rank": rank,
        "category": cat,
        "companyName": cname,
        "areaGroup": area,
        "postalCode": raw["postalCode"],
        "address": raw["address"],
        "phone": raw["phone"],
        "representative": raw["representative"],
        "storeCountScale": raw["storeCountScale"],
        "brands": brands,
        "targetDept": target_dept,
        "recommendedFish": rec_fish,
        "pitchAngle": pitch,
        "callScriptReception": reception,
        "callScriptBuyer": buyer,
        "website": raw["website"],
    }


def main() -> None:
    existing = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
    seg56 = json.loads(SEG56_JSON.read_text(encoding="utf-8"))

    # Normalize existing categories if any were moved
    seen_names = {c["companyName"] for c in existing}
    seen_phones = {c["phone"] for c in existing}

    new_records = []
    for raw in BATCH_1_COMPANIES + seg56:
        cname = raw["companyName"].strip()
        phone = raw["phone"].strip()
        if cname in seen_names or phone in seen_phones:
            continue
        seen_names.add(cname)
        seen_phones.add(phone)
        new_records.append(build_enriched_record(raw))

    all_companies = existing + new_records

    # Sort by Category order (①..⑥) then Rank (S -> A -> B)
    cat_order = {
        "① 寿司・海鮮居酒屋・炉端チェーン本部": 1,
        "② 総合居酒屋・大衆酒場・ダイニング本部": 2,
        "③ 和食・割烹・しゃぶしゃぶ・仕出し本部": 3,
        "④ 蕎麦・うどん・天ぷら・専門料理チェーン本部": 4,
        "⑤ 仕出し割烹・デパ地下和惣菜・弁当給食・ケータリング本社": 5,
        "⑥ ホテル・旅館・温浴施設・冠婚葬祭（宴会・法要）運営本社": 6,
    }
    rank_order = {"S": 1, "A": 2, "B": 3}

    all_companies.sort(key=lambda x: (rank_order.get(x["rank"], 9), cat_order.get(x["category"], 9), x["companyName"]))

    for idx, comp in enumerate(all_companies, 1):
        comp["id"] = f"OHQ-{idx:03d}"

    MASTER_JSON.write_text(json.dumps(all_companies, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Merged master dataset: {len(existing)} -> {len(all_companies)} companies (+{len(new_records)} added)")


if __name__ == "__main__":
    main()
