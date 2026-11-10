#!/usr/bin/env python3
# まなび4択問題データベース：ビルド＋点検
#   python3 tools/build.py            … src/ を読んで点検し、dist/ に書き出す
#   python3 tools/build.py --check    … 点検だけ（書き出さない）
#   python3 tools/build.py --yomi     … 読みがなの機械照合もする（pykakasi が必要。目で確かめる用）
#
# 原稿の書き方（src/<教科コード>/<学年>.txt）
#   % 教科名 学年                      ← ファイルの1行目
#   @ 番号 | 領域 | 単元名              ← 単元のはじまり（番号は2けた・学年の中で重ならない）
#   問題文                              ← ここから6行で1問。問題と問題の間は空行
#   正解
#   まちがい1
#   まちがい2
#   まちがい3
#   解説
#
# 文字の記法
#   {漢字|かんじ}   読みつきの漢字。漢字モードは「その学年までに習う漢字だけなら漢字、そうでなければ読み」
#   {!漢字|かんじ}  人名・地名など。漢字モードでは学年に関係なく漢字で出す
#   [漢字]          問題の対象になっている字（漢字の読み問題など）。どちらのモードでもそのまま出す
#   _               分かち書きの切れ目。かなモード（と1・2年の漢字モード）で空白になる
#   はだかの漢字（上の記法の外にある漢字）はエラー
import json, re, sys, pathlib, csv
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC, DIST = ROOT / 'src', ROOT / 'dist'
VERSION = 1
SUBJECTS = [  # コード, 教科名, 学年
    ('ko', '国語', range(1, 7)), ('sa', '算数', range(1, 7)),
    ('la', 'せいかつA', range(1, 3)), ('lb', 'せいかつB', range(1, 3)),
    ('ri', '理科', range(3, 7)), ('sh', '社会', range(3, 7)), ('ei', '英語', range(3, 7)),
]
KG = {}
for g, ks in json.load(open(ROOT / 'tools' / 'kyoiku_kanji.json', encoding='utf-8')).items():
    for k in ks: KG[k] = int(g)

KANJI = r'一-鿿㐀-䶿々〆'
RE_KANJI = re.compile(f'[{KANJI}]')
RE_TOKEN = re.compile(r'\{(!?)([^|{}]+)\|([^|{}]+)\}|\[([^\[\]]+)\]|(_)')
RE_KANA = re.compile(r'^[ぁ-ゖァ-ヺー・0-9A-Za-z.〜、 ]+$')
errs, warns = [], []

def learned(base, grade):
    prev = None
    for c in base:
        if c == '々':
            if prev is None: return False
            continue
        if RE_KANJI.match(c):
            if KG.get(c, 99) > grade: return False
            prev = c
    return True

def render(src, grade, mode, where=''):
    """mode: 'kanji' / 'kana'"""
    out, pos = [], 0
    for m in RE_TOKEN.finditer(src):
        plain = src[pos:m.start()]
        if RE_KANJI.search(plain): errs.append(f'{where}: はだかの漢字「{plain}」')
        out.append(plain); pos = m.end()
        force, base, yomi, lit, sp = m.groups()
        if sp:
            out.append(' ' if (mode == 'kana' or grade <= 2) else '')
        elif lit is not None:
            out.append(lit)
        else:
            if not RE_KANA.match(yomi): errs.append(f'{where}: 読みがかなでない {{{base}|{yomi}}}')
            if not RE_KANJI.search(base): errs.append(f'{where}: 漢字のないルビ {{{base}|{yomi}}}')
            if mode == 'kana': out.append(yomi)
            else: out.append(base if (force or learned(base, grade)) else yomi)
    plain = src[pos:]
    if RE_KANJI.search(plain): errs.append(f'{where}: はだかの漢字「{plain}」')
    if re.search(r'[{}\[\]|]', plain) or any(re.search(r'[{}|]', o) for o in out if False):
        errs.append(f'{where}: 記法のくずれ「{plain}」')
    out.append(plain)
    s = ''.join(out)
    s = re.sub(r' +', ' ', s).strip()
    s = re.sub(r' ([、。？！）」])', r'\1', s)
    s = re.sub(r'([（「]) ', r'\1', s)
    return s

def parse():
    qs, units = [], []
    for code, subj, grades in SUBJECTS:
        for g in grades:
            p = SRC / code / f'{g}.txt'
            if not p.exists():
                warns.append(f'原稿がない: {p.relative_to(ROOT)}'); continue
            lines = p.read_text(encoding='utf-8').split('\n')
            if lines[0].strip() != f'% {subj} {g}': errs.append(f'{p.name}: 1行目が「% {subj} {g}」でない')
            unit, block, seen_u = None, [], set()
            def flush(ln):
                nonlocal block
                if not block: return
                if unit is None: errs.append(f'{code}{g} {ln}行: 単元の前に問題がある')
                elif len(block) != 6: errs.append(f'{code}{g} {ln}行あたり: 6行でない（{len(block)}行）「{block[0][:20]}」')
                else:
                    unit['n'] += 1
                    qid = f"{code}{g}-{unit['no']}-{unit['n']:02d}"
                    qs.append(dict(id=qid, subject=subj, grade=g, unit=unit, raw=block))
                block = []
            for ln, line in enumerate(lines[1:], 2):
                line = line.strip()
                if line.startswith('@'):
                    flush(ln)
                    parts = [x.strip() for x in line[1:].split('|')]
                    # 単元名にはルビの | があるので、先頭2つだけで分ける
                    parts = [x.strip() for x in line[1:].split('|', 2)]
                    if len(parts) != 3 or not re.fullmatch(r'\d\d', parts[0]):
                        errs.append(f'{code}{g} {ln}行: 単元の行がおかしい'); continue
                    if parts[0] in seen_u: errs.append(f'{code}{g} {ln}行: 単元番号が重複 {parts[0]}')
                    seen_u.add(parts[0])
                    w = f'{code}{g}-{parts[0]} 単元名'
                    unit = dict(id=f'{code}{g}-{parts[0]}', no=parts[0], subject=subj, grade=g, area=parts[1],
                                name=render(parts[2], 6, 'kanji', w).replace(' ', ''),
                                nameKana=render(parts[2], g, 'kana', w), n=0)
                    units.append(unit)
                elif line.startswith('#'): continue
                elif line == '': flush(ln)
                else: block.append(line)
            flush(len(lines))
    return qs, units

def num(s):
    """数として読めれば Fraction、だめなら None"""
    t = s.replace(',', '').replace(' ', '').strip()
    t = re.sub(r'(cm²|m²|km²|cm³|m³|mm|cm|km|m|kg|mg|g|t|dL|mL|kL|L|a|ha|°|度|こ|個|人|円|本|まい|枚|倍|分|秒|時間|日|さい|才|ひき|匹|だい|台|さつ|冊|わ|羽|％|%|点|回|つ|ばん|番|番目|ばんめ|組|通り|とおり)$', '', t)
    m = re.fullmatch(r'(\d+)と(\d+)/(\d+)', t)
    if m and int(m[3]): return Fraction(int(m[1])) + Fraction(int(m[2]), int(m[3]))
    m = re.fullmatch(r'(\d+)/(\d+)', t)
    if m and int(m[2]): return Fraction(int(m[1]), int(m[2]))
    if re.fullmatch(r'\d+(\.\d+)?', t): return Fraction(t)
    return None

RE_NUMTOK = re.compile(r'\d+と\d+/\d+|\d+/\d+|\d+(?:\.\d+)?|[＋−×÷+\-（）()]')
def try_eval(q):
    """「12×3＝？」の形なら値を返す"""
    t = q.replace(' ', '')
    m = re.fullmatch(r'(.+?)[＝=]？?', t)
    if not m: return None
    toks = RE_NUMTOK.findall(m[1])
    if ''.join(toks) != m[1] or not any(x in '＋−×÷+-' for x in toks): return None
    py = []
    for x in toks:
        mm = re.fullmatch(r'(\d+)と(\d+)/(\d+)', x)
        if mm: py.append(f'(F({mm[1]})+F({mm[2]},{mm[3]}))')
        elif '/' in x: py.append('F(%s,%s)' % tuple(x.split('/')))
        elif x[0].isdigit(): py.append(f'F("{x}")')
        else: py.append({'＋': '+', '−': '-', '×': '*', '÷': '/', '（': '(', '）': ')'}.get(x, x))
    try: return eval(''.join(py), {'F': Fraction, '__builtins__': {}})
    except Exception: return 'ERR'

def norm(s): return re.sub(r'[\s、。．！!？?「」『』（）()・〜~ー\-]|(?<!\d)\.|\.(?!\d)', '', s).lower()
def kata2hira(s): return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in s)

def check_and_build(qs, units):
    out, seenq = [], {}
    for q in qs:
        g, raw, qid = q['grade'], q['raw'], q['id']
        kj = [render(x, g, 'kanji', qid) for x in raw]
        kn = [render(x, g, 'kana', qid) for x in raw]
        # かなモードに漢字が残っていないか（[ ] の中は対象の字なのでよい）
        for x in raw:
            stripped = RE_TOKEN.sub(lambda m: '' if m.group(4) else (m.group(3) or ''), x)
            if RE_KANJI.search(stripped): pass  # はだかの漢字として報告ずみ
        tag = f'{qid} {kj[0][:26]}'
        for name, v in (('漢字', kj), ('かな', kn)):
            c = v[1:5]
            if len(set(c)) != 4: errs.append(f'{tag}: {name}モードで選択肢が重複 {c}')
            elif len({norm(x) for x in c}) != 4: errs.append(f'{tag}: {name}モードで選択肢がほぼ同じ {c}')
            elif len({kata2hira(norm(x)) for x in c}) != 4: warns.append(f'{tag}: {name}モードでかな/カナちがいだけの選択肢 {c}')
        c = kj[1:5]
        nums = [num(x) for x in c]
        if all(n is not None for n in nums) and len(set(nums)) != 4: errs.append(f'{tag}: 同じ値の選択肢 {c}')
        if q['subject'] == '算数':
            v = try_eval(kj[0])
            if v == 'ERR': warns.append(f'{tag}: 式を計算できなかった')
            elif v is not None:
                m = re.fullmatch(r'(\d+)あまり(\d+)', c[0].replace(' ', ''))
                if m:
                    mm = re.fullmatch(r'(\d+)÷(\d+)[＝=]？?', kj[0].replace(' ', ''))
                    if not mm or divmod(int(mm[1]), int(mm[2])) != (int(m[1]), int(m[2])): errs.append(f'{tag}: 計算が合わない（正解 {c[0]}）')
                elif nums[0] is None: warns.append(f'{tag}: 正解を数として読めない {c[0]}')
                elif nums[0] != v: errs.append(f'{tag}: 計算が合わない（式の値 {v}・正解 {c[0]}）')
        L = [len(x) for x in c]
        if L[0] >= 10 and L[0] > 1.7 * max(L[1:]): warns.append(f'{tag}: 正解だけ長い {c}')
        if L[0] * 1.7 < min(L[1:]) and min(L[1:]) >= 10: warns.append(f'{tag}: 正解だけ短い {c}')
        nq = norm(kj[0])
        if len(norm(c[0])) >= 3 and norm(c[0]) in nq and q['subject'] != '英語' and not all(norm(x) in nq for x in c[1:]):
            warns.append(f'{tag}: 正解が問題文に入っている「{c[0]}」')
        k = (q['subject'], re.sub(r'\s', '', kj[0]))
        if k in seenq: errs.append(f'{tag}: 同じ問題文が {seenq[k]} にある')
        seenq[k] = qid
        if not kj[5]: errs.append(f'{tag}: 解説がない')
        if len(kj[5]) > 70: warns.append(f'{tag}: 解説が長い（{len(kj[5])}字）')
        u = q['unit']
        out.append(dict(id=qid, subject=q['subject'], grade=g, unitId=u['id'], unit=u['name'], area=u['area'],
                        q=kj[0], choices=kj[1:5], exp=kj[5], kana=dict(q=kn[0], choices=kn[1:5], exp=kn[5])))
    for u in units:
        if not 5 <= u['n'] <= 10: warns.append(f"{u['id']} {u['name']}: 問題数が {u['n']} 問（5〜10問にする）")
    return out

def yomi_check(qs):
    import pykakasi
    kks = pykakasi.kakasi()
    seen = {}
    for q in qs:
        for x in q['raw'] + []:
            for m in RE_TOKEN.finditer(x):
                if m.group(2):
                    base, yomi = m.group(2), m.group(3)
                    seen.setdefault((base, yomi), q['id'])
    bad = []
    for (base, yomi), qid in sorted(seen.items()):
        auto = ''.join(i['hira'] for i in kks.convert(base))
        if auto != kata2hira(yomi): bad.append(f'{base}\t{yomi}\t(機械: {auto})\t{qid}')
    print(f'--- 読みの機械照合：{len(seen)} 組のうち {len(bad)} 組がちがう（まちがいとは限らない。目で確認）')
    for b in bad: print(b)

def main():
    qs, units = parse()
    out = check_and_build(qs, units)
    if '--yomi' in sys.argv: yomi_check(qs)
    table = {}
    for q in out: table[(q['subject'], q['grade'])] = table.get((q['subject'], q['grade']), 0) + 1
    if '-q' not in sys.argv:
        for w in warns: print('注意', w)
    for e in errs: print('NG', e)
    print(f'全 {len(out)} 問・{len(units)} 単元', ' '.join(f'{s}{g}:{n}' for (s, g), n in table.items()))
    print(f'NG {len(errs)} 件 / 注意 {len(warns)} 件')
    if errs: sys.exit(1)
    if '--check' in sys.argv: return
    DIST.mkdir(exist_ok=True)
    ulist = [dict(id=u['id'], subject=u['subject'], grade=u['grade'], area=u['area'], name=u['name'],
                  nameKana=u['nameKana'], count=u['n']) for u in units]
    db = dict(version=VERSION, count=len(out), units=ulist, questions=out)
    js = json.dumps(db, ensure_ascii=False, separators=(',', ':'))
    (DIST / 'questions.json').write_text(json.dumps(db, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (DIST / 'questions.min.json').write_text(js + '\n', encoding='utf-8')
    (DIST / 'questions.js').write_text('// まなび4択問題データベース（tools/build.py が作る。手で直さない）\nwindow.MANABI_QDB = ' + js + ';\n', encoding='utf-8')
    with open(DIST / 'questions.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['id', '教科', '学年', '領域', '単元', '問題', '正解', 'まちがい1', 'まちがい2', 'まちがい3', '解説',
                    '問題(かな)', '正解(かな)', 'まちがい1(かな)', 'まちがい2(かな)', 'まちがい3(かな)', '解説(かな)'])
        for q in out:
            w.writerow([q['id'], q['subject'], q['grade'], q['area'], q['unit'], q['q'], *q['choices'], q['exp'],
                        q['kana']['q'], *q['kana']['choices'], q['kana']['exp']])
    # 単元一覧
    md = ['# 単元一覧（自動生成）', '', f'全 {len(out)} 問・{len(units)} 単元', '']
    for code, subj, grades in SUBJECTS:
        md += [f'## {subj}', '']
        for g in grades:
            us = [u for u in ulist if u['subject'] == subj and u['grade'] == g]
            md += [f'### {g}年（{sum(u["count"] for u in us)}問）', '', '| ID | 領域 | 単元・ジャンル | 問題数 |', '|---|---|---|---|']
            md += [f"| {u['id']} | {u['area']} | {u['name']} | {u['count']} |" for u in us] + ['']
    (ROOT / 'docs').mkdir(exist_ok=True)
    (ROOT / 'docs' / 'UNITS.md').write_text('\n'.join(md), encoding='utf-8')
    print('dist/ に書き出しました')

if __name__ == '__main__':
    main()
