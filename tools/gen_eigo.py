#!/usr/bin/env python3
# 英語の単語問題をつくる（src/ei/<学年>-gen.txt に書き出す）
#   python3 tools/gen_eigo.py
# ・下の単語表（英語|日本語|読み方）から、1語につき2問つくる
#     ①「日本語」を英語で言うと？  ②「英語」の意味は？
# ・まちがいの選択肢は、同じなかま（色・動物…）の ほかの単語から選ぶ
#   → 同じなかまの中に、同じ意味の単語（big と large など）を入れないこと
# ・乱数の種は固定。単語を足すときは、なかまの最後に足す（前の問題IDが変わらない）
import random, pathlib, re
ROOT = pathlib.Path(__file__).resolve().parent.parent

# (学年, 単元番号, 単元名, [単語…])
WORDS = [
(3, '21', '{色|いろ}', '''
red|{赤|あか}|レッド
blue|{青|あお}|ブルー
yellow|{黄色|きいろ}|イエロー
green|みどり|グリーン
black|{黒|くろ}|ブラック
white|{白|しろ}|ホワイト
pink|ピンク|ピンク
orange|オレンジ{色|いろ}|オレンジ
purple|むらさき|パープル
brown|{茶色|ちゃいろ}|ブラウン
'''),
(3, '22', 'くだもの', '''
apple|りんご|アップル
banana|バナナ|バナナ
grapes|ぶどう|グレープス
strawberry|いちご|ストロベリー
melon|メロン|メロン
peach|もも|ピーチ
lemon|レモン|レモン
cherry|さくらんぼ|チェリー
pineapple|パイナップル|パイナップル
watermelon|すいか|ウォーターメロン
'''),
(3, '23', 'やさい', '''
tomato|トマト|トメイトウ
carrot|にんじん|キャロット
onion|たまねぎ|アニオン
potato|じゃがいも|ポテイトウ
cucumber|きゅうり|キューカンバー
cabbage|キャベツ|キャベジ
corn|とうもろこし|コーン
pumpkin|かぼちゃ|パンプキン
green pepper|ピーマン|グリーンペッパー
mushroom|きのこ|マッシュルーム
'''),
(3, '24', '{動物|どうぶつ}', '''
dog|{犬|いぬ}|ドッグ
cat|ねこ|キャット
bird|{鳥|とり}|バード
rabbit|うさぎ|ラビット
elephant|ぞう|エレファント
monkey|さる|マンキー
lion|ライオン|ライオン
tiger|とら|タイガー
bear|くま|ベア
horse|{馬|うま}|ホース
pig|ぶた|ピッグ
cow|{牛|うし}|カウ
panda|パンダ|パンダ
mouse|ねずみ|マウス
fish|{魚|さかな}|フィッシュ
frog|カエル|フロッグ
'''),
(3, '25', '{数|かず}（1〜20）', '''
one|1|ワン
two|2|トゥー
three|3|スリー
four|4|フォー
five|5|ファイブ
six|6|シックス
seven|7|セブン
eight|8|エイト
nine|9|ナイン
ten|10|テン
eleven|11|イレブン
twelve|12|トゥエルブ
thirteen|13|サーティーン
fourteen|14|フォーティーン
fifteen|15|フィフティーン
sixteen|16|シックスティーン
seventeen|17|セブンティーン
eighteen|18|エイティーン
nineteen|19|ナインティーン
twenty|20|トゥエンティ
'''),
(3, '26', '{気|き}もち・ようす', '''
happy|うれしい|ハッピー
sad|かなしい|サッド
hungry|おなかが_すいた|ハングリー
sleepy|ねむい|スリーピー
tired|つかれた|タイアド
angry|おこって_いる|アングリー
fine|{元気|げんき}|ファイン
thirsty|のどが_かわいた|サースティ
'''),
(3, '27', '{形|かたち}', '''
circle|{円|えん}（まる）|サークル
triangle|{三角形|さんかくけい}|トライアングル
square|{正方形|せいほうけい}|スクエア
star|{星|ほし}の_{形|かたち}|スター
heart|ハートの_{形|かたち}|ハート
diamond|ひし{形|がた}|ダイヤモンド
rectangle|{長方形|ちょうほうけい}|レクタングル
'''),
(3, '28', '{体|からだ}', '''
head|{頭|あたま}|ヘッド
eye|{目|め}|アイ
ear|{耳|みみ}|イア
nose|{鼻|はな}|ノウズ
mouth|{口|くち}|マウス
hand|{手|て}|ハンド
leg|{足|あし}|レッグ
shoulder|かた|ショウルダー
knee|ひざ|ニー
'''),
(4, '21', '{天気|てんき}', '''
sunny|{晴|は}れ|サニー
rainy|{雨|あめ}|レイニー
cloudy|くもり|クラウディ
snowy|{雪|ゆき}|スノウィ
windy|{風|かぜ}が_{強|つよ}い|ウィンディ
hot|{暑|あつ}い|ホット
cold|{寒|さむ}い|コウルド
'''),
(4, '22', '{曜日|ようび}', '''
Sunday|{日曜日|にちようび}|サンデイ
Monday|{月曜日|げつようび}|マンデイ
Tuesday|{火曜日|かようび}|チューズデイ
Wednesday|{水曜日|すいようび}|ウェンズデイ
Thursday|{木曜日|もくようび}|サーズデイ
Friday|{金曜日|きんようび}|フライデイ
Saturday|{土曜日|どようび}|サタデイ
'''),
(4, '23', '{文|ぶん}ぼう{具|ぐ}', '''
pencil|えんぴつ|ペンスル
eraser|{消|け}しゴム|イレイサー
ruler|じょうぎ|ルーラー
notebook|ノート|ノウトブック
scissors|はさみ|シザーズ
glue|のり|グルー
pen|ペン|ペン
crayon|クレヨン|クレイオン
stapler|ホッチキス|ステイプラー
pencil case|ふでばこ|ペンスルケイス
'''),
(4, '24', '{食|た}べ{物|もの}・{飲|の}み{物|もの}', '''
rice|ごはん|ライス
bread|パン|ブレッド
milk|{牛|ぎゅう}にゅう|ミルク
egg|たまご|エッグ
pizza|ピザ|ピッツァ
cake|ケーキ|ケイク
salad|サラダ|サラッド
soup|スープ|スープ
hamburger|ハンバーガー|ハンバーガー
spaghetti|スパゲッティ|スパゲティ
ice cream|アイスクリーム|アイスクリーム
juice|ジュース|ジュース
sandwich|サンドイッチ|サンドウィッチ
curry and rice|カレーライス|カリーアンドライス
steak|ステーキ|ステイク
water|{水|みず}|ウォーター
tea|お{茶|ちゃ}|ティー
'''),
(4, '25', 'スポーツ・{遊|あそ}び', '''
soccer|サッカー|サッカー
baseball|{野球|やきゅう}|ベイスボール
tennis|テニス|テニス
basketball|バスケットボール|バスケットボール
swimming|{水泳|すいえい}|スウィミング
volleyball|バレーボール|バリボール
dodgeball|ドッジボール|ドッジボール
table tennis|たっきゅう|テイブルテニス
badminton|バドミントン|バドミントン
tag|おにごっこ|タッグ
jump rope|なわとび|ジャンプロウプ
'''),
(4, '26', '{学校|がっこう}の {場所|ばしょ}', '''
classroom|{教室|きょうしつ}|クラスルーム
library|{図書室|としょしつ}|ライブラリー
gym|{体育館|たいいくかん}|ジム
music room|{音楽室|おんがくしつ}|ミュージックルーム
science room|{理科室|りかしつ}|サイエンスルーム
playground|{運動場|うんどうじょう}|プレイグラウンド
teachers' office|しょく{員室|いんしつ}|ティーチャーズオフィス
nurse's office|ほけん{室|しつ}|ナースィズオフィス
restroom|トイレ|レストルーム
computer room|コンピューター{室|しつ}|コンピュータールーム
principal's office|{校長室|こうちょうしつ}|プリンスィパルズオフィス
'''),
(4, '27', '{数|かず}（21〜100）', '''
twenty-one|21|トゥエンティワン
thirty|30|サーティ
forty|40|フォーティ
fifty|50|フィフティ
sixty|60|シックスティ
seventy|70|セブンティ
eighty|80|エイティ
ninety|90|ナインティ
one hundred|100|ワンハンドレッド
thirty-five|35|サーティファイブ
forty-two|42|フォーティトゥー
fifty-eight|58|フィフティエイト
sixty-three|63|シックスティスリー
seventy-six|76|セブンティシックス
ninety-nine|99|ナインティナイン
eighty-four|84|エイティフォー
'''),
(4, '28', '1{日|にち}の {生活|せいかつ}', '''
get up|{起|お}きる|ゲットアップ
wash my face|{顔|かお}を_あらう|ウォッシュマイフェイス
eat breakfast|{朝|あさ}ごはんを_{食|た}べる|イートブレックファスト
go to school|{学校|がっこう}へ_{行|い}く|ゴウトゥースクール
go home|{家|いえ}に_{帰|かえ}る|ゴウホウム
do my homework|{宿題|しゅくだい}を_する|ドゥーマイホウムワーク
take a bath|おふろに_{入|はい}る|テイクアバス
go to bed|ねる|ゴウトゥーベッド
brush my teeth|{歯|は}を_みがく|ブラッシュマイティース
watch TV|テレビを_{見|み}る|ウォッチティーヴィー
'''),
(5, '21', '{月|つき}', '''
January|1{月|がつ}|ジャニュアリー
February|2{月|がつ}|フェブラリー
March|3{月|がつ}|マーチ
April|4{月|がつ}|エイプリル
May|5{月|がつ}|メイ
June|6{月|がつ}|ジューン
July|7{月|がつ}|ジュライ
August|8{月|がつ}|オーガスト
September|9{月|がつ}|セプテンバー
October|10{月|がつ}|オクトウバー
November|11{月|がつ}|ノウベンバー
December|12{月|がつ}|ディセンバー
'''),
(5, '22', '{教科|きょうか}', '''
Japanese|{国語|こくご}|ジャパニーズ
math|{算数|さんすう}|マス
science|{理科|りか}|サイエンス
social studies|{社会|しゃかい}|ソウシャルスタディーズ
English|{英語|えいご}|イングリッシュ
music|{音楽|おんがく}|ミュージック
P.E.|{体育|たいいく}|ピーイー
arts and crafts|{図工|ずこう}|アーツアンドクラフツ
home economics|{家庭科|かていか}|ホウムエコノミクス
calligraphy|{書写|しょしゃ}|カリグラフィー
moral education|{道徳|どうとく}|モラルエデュケイション
'''),
(5, '23', '{職業|しょくぎょう}', '''
teacher|{先生|せんせい}|ティーチャー
doctor|{医者|いしゃ}|ドクター
nurse|かんご{師|し}|ナース
chef|{料理人|りょうりにん}|シェフ
farmer|{農家|のうか}|ファーマー
police officer|けいさつ{官|かん}|ポリースオフィサー
firefighter|{消防士|しょうぼうし}|ファイアファイター
pilot|パイロット|パイロット
singer|{歌手|かしゅ}|シンガー
baker|パン{屋|や}さん|ベイカー
vet|じゅう{医|い}|ヴェット
bus driver|バスの_{運転手|うんてんしゅ}|バスドライバー
soccer player|サッカー{選手|せんしゅ}|サッカープレイヤー
florist|{花屋|はなや}さん|フローリスト
dentist|{歯医者|はいしゃ}|デンティスト
artist|{画家|がか}|アーティスト
scientist|{科学者|かがくしゃ}|サイエンティスト
astronaut|うちゅうひこう{士|し}|アストロノート
'''),
(5, '24', '{動作|どうさ}', '''
run|{走|はし}る|ラン
walk|{歩|ある}く|ウォーク
swim|{泳|およ}ぐ|スウィム
jump|ジャンプする|ジャンプ
sing|{歌|うた}う|シング
dance|おどる|ダンス
cook|{料理|りょうり}する|クック
read|{読|よ}む|リード
write|{字|じ}を_{書|か}く|ライト
draw|{絵|え}を_かく|ドロー
play the piano|ピアノを_ひく|プレイザピアノ
ride a unicycle|{一輪車|いちりんしゃ}に_{乗|の}る|ライドアユニサイクル
ski|スキーを_する|スキー
skate|スケートを_する|スケイト
speak|{話|はな}す|スピーク
fly|{空|そら}を_とぶ|フライ
eat|{食|た}べる|イート
drink|{飲|の}む|ドリンク
study|{勉強|べんきょう}する|スタディ
sleep|ねむる|スリープ
buy|{買|か}う|バイ
make|{作|つく}る|メイク
clean|そうじする|クリーン
wash|あらう|ウォッシュ
'''),
(5, '25', '{町|まち}の {建物|たてもの}', '''
station|{駅|えき}|ステイション
hospital|{病院|びょういん}|ホスピタル
park|{公園|こうえん}|パーク
post office|ゆうびん{局|きょく}|ポウストオフィス
police station|けいさつしょ|ポリースステイション
fire station|{消防|しょうぼう}しょ|ファイアステイション
supermarket|スーパーマーケット|スーパーマーケット
convenience store|コンビニ|コンビーニエンスストア
bookstore|{本屋|ほんや}|ブックストア
restaurant|レストラン|レストラント
flower shop|{花屋|はなや}|フラワーショップ
school|{学校|がっこう}|スクール
zoo|{動物園|どうぶつえん}|ズー
aquarium|{水族館|すいぞくかん}|アクエリアム
museum|はく{物館|ぶつかん}|ミュージアム
temple|{寺|てら}|テンプル
shrine|{神社|じんじゃ}|シュライン
bank|{銀行|ぎんこう}|バンク
department store|デパート|デパートメントストア
amusement park|{遊園地|ゆうえんち}|アミューズメントパーク
stadium|スタジアム|ステイディアム
'''),
(5, '26', 'ようすを {表|あらわ}す {言葉|ことば}', '''
big|{大|おお}きい|ビッグ
small|{小|ちい}さい|スモール
long|{長|なが}い|ロング
short|{短|みじか}い|ショート
new|{新|あたら}しい|ニュー
old|{古|ふる}い|オウルド
sweet|あまい|スウィート
sour|すっぱい|サワー
bitter|{苦|にが}い|ビター
salty|しょっぱい|ソールティ
spicy|からい|スパイシー
soft|やわらかい|ソフト
hard|かたい|ハード
delicious|おいしい|デリシャス
beautiful|{美|うつく}しい|ビューティフル
cute|かわいい|キュート
cool|かっこいい|クール
kind|{親切|しんせつ}な|カインド
strong|{強|つよ}い|ストロング
brave|ゆうかんな|ブレイブ
funny|おもしろい|ファニー
famous|{有名|ゆうめい}な|フェイマス
fast|{速|はや}い|ファスト
tall|せが_{高|たか}い|トール
'''),
(5, '27', '{家族|かぞく}・{人|ひと}', '''
father|お{父|とう}さん|ファーザー
mother|お{母|かあ}さん|マザー
brother|{兄|あに}・{弟|おとうと}|ブラザー
sister|{姉|あね}・{妹|いもうと}|シスター
grandfather|おじいさん|グランドファーザー
grandmother|おばあさん|グランドマザー
uncle|おじさん|アンクル
aunt|おばさん|アント
cousin|いとこ|カズン
friend|{友|とも}だち|フレンド
baby|{赤|あか}ちゃん|ベイビー
boy|{男|おとこ}の{子|こ}|ボーイ
girl|{女|おんな}の{子|こ}|ガール
'''),
(5, '28', '{国|くに}', '''
Japan|{日本|にほん}|ジャパン
America|アメリカ|アメリカ
China|{中国|ちゅうごく}|チャイナ
Korea|{韓国|かんこく}|コリア
Australia|オーストラリア|オーストレイリア
Canada|カナダ|キャナダ
France|フランス|フランス
Italy|イタリア|イタリー
Germany|ドイツ|ジャーマニー
Brazil|ブラジル|ブラズィル
India|インド|インディア
Egypt|エジプト|イージプト
the U.K.|イギリス|ザ ユーケイ
Spain|スペイン|スペイン
Russia|ロシア|ラシア
Thailand|タイ|タイランド
Kenya|ケニア|ケニア
Peru|ペルー|ペルー
'''),
(5, '29', '{季節|きせつ}・{行事|ぎょうじ}', '''
spring|{春|はる}|スプリング
summer|{夏|なつ}|サマー
fall|{秋|あき}|フォール
winter|{冬|ふゆ}|ウィンター
New Year's Day|{元日|がんじつ}|ニューイヤーズデイ
Children's Day|こどもの{日|ひ}|チルドレンズデイ
Star Festival|{七夕|たなばた}|スターフェスティバル
Christmas|クリスマス|クリスマス
Halloween|ハロウィン|ハロウィーン
birthday|たんじょう{日|び}|バースデイ
summer vacation|{夏休|なつやす}み|サマーヴァケイション
festival|{祭|まつ}り|フェスティバル
'''),
(6, '21', '{過去|かこ}を {表|あらわ}す {言葉|ことば}', '''
went|{行|い}った|ウェント
ate|{食|た}べた|エイト
saw|{見|み}た|ソー
enjoyed|{楽|たの}しんだ|エンジョイド
made|{作|つく}った|メイド
bought|{買|か}った|ボート
visited|おとずれた|ヴィズィテッド
studied|{勉強|べんきょう}した|スタディード
cooked|{料理|りょうり}した|クックト
cleaned|そうじした|クリーンド
sang|{歌|うた}った|サング
played soccer|サッカーを_した|プレイドサッカー
read a book|{本|ほん}を_{読|よ}んだ|レッドアブック
took a bath|おふろに_{入|はい}った|トゥックアバス
got up|{起|お}きた|ゴットアップ
ran|{走|はし}った|ラン
drank|{飲|の}んだ|ドランク
'''),
(6, '22', '{学校|がっこう}{行事|ぎょうじ}・{部活動|ぶかつどう}', '''
sports day|{運動会|うんどうかい}|スポーツデイ
school trip|{修学旅行|しゅうがくりょこう}|スクールトリップ
entrance ceremony|{入学式|にゅうがくしき}|エントランスセレモニー
graduation ceremony|{卒業式|そつぎょうしき}|グラジュエイションセレモニー
field trip|{遠足|えんそく}|フィールドトリップ
music festival|{音楽会|おんがくかい}|ミュージックフェスティバル
swimming meet|{水泳大会|すいえいたいかい}|スウィミングミート
drama festival|{学芸会|がくげいかい}|ドラーマフェスティバル
brass band|すい{奏楽部|そうがくぶ}|ブラスバンド
art club|{美術部|びじゅつぶ}|アートクラブ
science club|{科学部|かがくぶ}|サイエンスクラブ
chorus|{合唱部|がっしょうぶ}|コーラス
track and field team|{陸上部|りくじょうぶ}|トラックアンドフィールドティーム
volunteer day|ボランティアの{日|ひ}|ヴォランティアデイ
'''),
(6, '23', '{自然|しぜん}・{生|い}き{物|もの}', '''
sea|{海|うみ}|スィー
mountain|{山|やま}|マウンテン
river|{川|かわ}|リバー
lake|{湖|みずうみ}|レイク
forest|{森|もり}|フォレスト
island|{島|しま}|アイランド
desert|さばく|デザート
sky|{空|そら}|スカイ
sun|{太陽|たいよう}|サン
moon|{月|つき}|ムーン
whale|クジラ|ウェイル
dolphin|イルカ|ドルフィン
sea turtle|ウミガメ|スィータートル
penguin|ペンギン|ペングウィン
eagle|ワシ|イーグル
snake|ヘビ|スネイク
giraffe|キリン|ジラフ
zebra|シマウマ|ズィーブラ
gorilla|ゴリラ|ゴリラ
koala|コアラ|コウアーラ
kangaroo|カンガルー|キャンガルー
polar bear|ホッキョクグマ|ポウラーベア
owl|フクロウ|アウル
butterfly|チョウ|バタフライ
ant|アリ|アント
bee|ハチ|ビー
spider|クモ|スパイダー
wolf|オオカミ|ウルフ
'''),
(6, '24', '{時|とき}・ひん{度|ど}', '''
always|いつも|オールウェイズ
usually|たいてい|ユージュアリー
sometimes|ときどき|サムタイムズ
never|けっして_〜ない|ネバー
today|{今日|きょう}|トゥデイ
tomorrow|{明日|あした}|トゥモロウ
yesterday|{昨日|きのう}|イエスタデイ
morning|{朝|あさ}|モーニング
afternoon|{午後|ごご}|アフタヌーン
evening|{夕方|ゆうがた}|イーブニング
night|{夜|よる}|ナイト
week|{週|しゅう}|ウィーク
month|{月|つき}（1か{月|げつ}）|マンス
year|{年|とし}（1{年|ねん}）|イヤー
'''),
(6, '25', '{身|み}の{回|まわ}りの {物|もの}・{乗|の}り{物|もの}', '''
bag|かばん|バッグ
cap|ぼうし|キャップ
shoes|くつ|シューズ
watch|うで{時計|どけい}|ウォッチ
umbrella|かさ|アンブレラ
book|{本|ほん}|ブック
desk|つくえ|デスク
chair|いす|チェア
bed|ベッド|ベッド
window|まど|ウィンドウ
door|ドア|ドア
box|{箱|はこ}|ボックス
key|かぎ|キー
glasses|めがね|グラスィズ
camera|カメラ|キャメラ
computer|コンピューター|コンピューター
bicycle|{自転車|じてんしゃ}|バイスィクル
car|{車|くるま}|カー
bus|バス|バス
train|{電車|でんしゃ}|トレイン
airplane|{飛行機|ひこうき}|エアプレイン
ship|{船|ふね}|シップ
racket|ラケット|ラケット
guitar|ギター|ギター
recorder|リコーダー|リコーダー
towel|タオル|タウエル
'''),
(6, '26', '{料理|りょうり}・{食材|しょくざい}', '''
beef|{牛肉|ぎゅうにく}|ビーフ
pork|ぶた{肉|にく}|ポーク
chicken|とり{肉|にく}|チキン
vegetable|{野菜|やさい}|ヴェジタブル
fruit|くだもの|フルート
sugar|{砂糖|さとう}|シュガー
salt|{塩|しお}|ソールト
noodles|めん|ヌードルズ
rice ball|おにぎり|ライスボール
fried chicken|からあげ|フライドチキン
omelet|オムレツ|オムレット
grilled fish|{焼|や}き{魚|ざかな}|グリルドフィッシュ
miso soup|みそしる|ミソスープ
green tea|{緑茶|りょくちゃ}|グリーンティー
pudding|プリン|プディング
chocolate|チョコレート|チョコレット
donut|ドーナツ|ドウナット
french fries|フライドポテト|フレンチフライズ
sausage|ソーセージ|ソースィジ
yogurt|ヨーグルト|ヨウガート
'''),
(6, '27', 'たずねる {言葉|ことば}', '''
what|{何|なに}|ワット
who|だれ|フー
where|どこ|ウェア
when|いつ|ウェン
why|なぜ|ワイ
how|どのように|ハウ
which|どちら|ウィッチ
whose|だれの|フーズ
how many|いくつ（{数|かず}）|ハウメニー
how much|いくら（ねだん）|ハウマッチ
'''),
(6, '28', '{人|ひと}を {表|あらわ}す {言葉|ことば}', '''
I|わたしは|アイ
you|あなたは|ユー
he|かれは|ヒー
she|かのじょは|シー
we|わたしたちは|ウィー
they|かれらは|ゼイ
my|わたしの|マイ
your|あなたの|ユア
his|かれの|ヒズ
her|かのじょの|ハー
'''),
]

def main():
    files = {}
    for grade, no, name, body in WORDS:
        rng = random.Random(f'{grade}-{no}')
        ws = [tuple(re.split(r'\|(?![^{}]*\})', l)) for l in body.strip().split('\n')]
        assert all(len(w) == 3 for w in ws), (grade, no)
        assert len({w[0] for w in ws}) == len(ws) and len({w[1] for w in ws}) == len(ws), (grade, no)
        out = files.setdefault(grade, [f'% 英語 {grade}', '# tools/gen_eigo.py がつくったファイル。手で直さない（直すときは gen_eigo.py の単語表を直す）', ''])
        out += [f'@ {no} | 単語 | {name}', '']
        for i, (en, ja, yomi) in enumerate(ws):
            others = [w for j, w in enumerate(ws) if j != i]
            # 長さの近い単語を えらぶ（正解だけ長い・短い を さける）
            near = lambda k: sorted(others, key=lambda w: (abs(len(w[k]) - len(ws[i][k])), rng.random()))[:6]
            a = rng.sample(near(0), 3)
            out += [f'「{ja}」を_{{英語|えいご}}で_{{言|い}}うと？', en, *[w[0] for w in a], f'「{ja}」は_{en}（{yomi}）。', '']
            b = rng.sample(near(1), 3)
            out += [f'「{en}」の_{{意味|いみ}}は？', ja, *[w[1] for w in b], f'{en}（{yomi}）は「{ja}」。', '']
    for g, out in files.items():
        (ROOT / 'src' / 'ei' / f'{g}-gen.txt').write_text('\n'.join(out), encoding='utf-8')
        print(f'{g}年: {sum(1 for l in out if l.startswith("「") and l.endswith("？"))} 問')

if __name__ == '__main__':
    main()
