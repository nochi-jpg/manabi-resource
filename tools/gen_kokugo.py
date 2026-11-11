#!/usr/bin/env python3
# 国語の漢字問題をつくる（src/ko/<学年>-gen.txt に書き出す）
#   python3 tools/gen_kokugo.py        （pykakasi が必要： pip install pykakasi）
# ・tables/20-kanji-words.txt の「言葉=読み」から、1語につき2問
#     ① 読み：「景色」の読み方は？   まちがい＝その漢字の ほかの読み方を組み合わせたもの（けいしょく など）
#     ② 書き：「けしき」を漢字で書くと？ まちがい＝同じ音の漢字・形のにた漢字に入れかえたもの（実在する言葉は使わない）
# ・画数の問題（2年〜）：tools/kanji_info.json の画数から
# ・乱数の種は固定。言葉を足すときは その学年の最後に足す
import json, re, random, pathlib, itertools, difflib, sys
import pykakasi
ROOT = pathlib.Path(__file__).resolve().parent.parent
INFO = json.load(open(ROOT / 'tools' / 'kanji_info.json', encoding='utf-8'))
KKS = pykakasi.kakasi()
isk = lambda c: c in INFO
def stems(k):
    """漢字 k の読み（音読み＋訓読みの語幹）"""
    out = list(INFO[k]['on'])
    for r in INFO[k]['kun']:
        s = r.replace('-', '').split('.')[0]
        if s and s not in out: out.append(s)
    return out
def real_word(w):
    """辞書にある言葉か（pykakasi が1語として読めるか）"""
    r = KKS.convert(w)
    return len(r) == 1 and r[0]['hira'] != w and not any(isk(c) for c in r[0]['hira'])
def sim(a, b): return difflib.SequenceMatcher(None, a, b).ratio()
HIRA = re.compile(r'^[ぁ-ゖー]+$')
ALLKUN = {r.replace('-', '').replace('.', '') for v in INFO.values() for r in v['kun'] if '.' in r}

def load():
    words, g = {}, None
    for line in (ROOT / 'tables' / '20-kanji-words.txt').read_text(encoding='utf-8').split('\n'):
        line = line.strip()
        if not line or line.startswith('#'): continue
        if line.startswith('=='): g = int(line[2:]); words[g] = []; continue
        for item in line.split():
            w, y = item.split('=')
            words[g].append((w, y))
    return words

def mutate(y):
    """長音・つまる音の書きまちがい"""
    out = []
    for i, c in enumerate(y):
        if c == 'う' and i > 0: out.append(y[:i] + y[i + 1:])
        if c == 'っ': out += [y[:i] + 'つ' + y[i + 1:], y[:i] + y[i + 1:]]
        if c in 'ょゅ' and (i + 1 == len(y) or y[i + 1] != 'う'): out.append(y[:i + 1] + 'う' + y[i + 1:])
        if c in 'こそとほもよろごぞどぼ' and (i + 1 == len(y) or y[i + 1] != 'う') and i + 1 < len(y): out.append(y[:i + 1] + 'う' + y[i + 1:])
    return [x for x in out if x != y and len(x) >= 1]

def yomi_wrongs(w, y, grade, all_words, rng):
    ks = [c for c in w if isk(c)]
    tail = re.sub(r'^[^ぁ-ゖ]*', '', w) if len(ks) == 1 else ''          # 送りがな
    cand = []
    if len(ks) >= 2:
        opts = [stems(c) if isk(c) else [c] for c in w]
        for combo in itertools.islice(itertools.product(*opts), 400):
            c = ''.join(combo)
            if c != y and HIRA.match(c) and c not in cand: cand.append(c)
        kk = ''.join(i['hira'] for i in KKS.convert(w))
        cand = [c for c in cand if c != kk]
        cand.sort(key=lambda c: -sim(c, y))
        cand = cand[:6]
        m = [x for x in mutate(y) if x not in cand]
        if len(cand) < 3 or (m and rng.random() < 0.5): cand = cand[:2] + m[:2] + cand[2:]
    elif tail and w.index(ks[0]) == 0:
        # 同じ終わり方をする ほかの言葉の読み（やすむ → よむ・のむ・すむ…）。学年に関係なく、訓読みの表から選ぶ
        mine = {r.replace('-', '').replace('.', '') for r in INFO[ks[0]]['kun']}
        for n in (len(tail), 1):
            for r in sorted(ALLKUN):
                if r.endswith(tail[-n:]) and r not in mine and r != y and r not in cand: cand.append(r)
            if len(cand) >= 6: break
        cand.sort(key=lambda c: (abs(len(c) - len(y)), rng.random()))
        cand = cand[:7]
    if len(cand) < 3:
        # ほかの言葉の読み（同じ形の言葉・同じくらいの長さ）
        shape = lambda ow: (sum(isk(c) for c in ow) == 1, isk(ow[-1]))
        mine = set(itertools.chain.from_iterable(stems(k) for k in ks))
        others = [oy for ow, oy in all_words if oy != y and oy not in mine and oy not in cand and shape(ow) == shape(w)]
        others.sort(key=lambda c: (abs(len(c) - len(y)), -sim(c, y), rng.random()))
        cand += others[:6]
    pool = cand[:6]
    return rng.sample(pool, 3) if len(pool) >= 3 else None

def kaki_wrongs(w, y, grade, rng):
    ks = [(i, c) for i, c in enumerate(w) if isk(c)]
    pool_kanji = [k for k, v in INFO.items() if v['g'] <= grade]
    cand = []
    if len(ks) >= 2:
        for i, k in ks:
            homo = [x for x in pool_kanji if x != k and set(INFO[x]['on']) & set(INFO[k]['on'])]
            look = [x for x in pool_kanji if x != k and x not in homo and set(INFO[x]['rad']) & set(INFO[k]['rad'])]
            homo.sort(key=lambda x: (abs(INFO[x]['g'] - grade), rng.random())); look.sort(key=lambda x: (abs(INFO[x]['g'] - grade), rng.random()))
            for x in homo[:5] + look[:2]:
                c = w[:i] + x + w[i + 1:]
                if not real_word(c): cand.append((x in homo, c))
        rng.shuffle(cand)
        cand.sort(key=lambda t: not t[0])
        cand = [c for _, c in cand][:7]
        if len(cand) < 4:   # 同じ音・にた形の漢字が足りないとき：同じ学年の漢字に入れかえる
            same = [x for x in pool_kanji if INFO[x]['g'] == grade]; rng.shuffle(same)
            for x in same[:14]:
                i, k = rng.choice(ks)
                c = w[:i] + x + w[i + 1:]
                if x != k and c not in cand and not real_word(c): cand.append(c)
            cand = cand[:7]
    else:
        i, k = ks[0]
        stem = y[:len(y) - (len(w) - 1)] if len(w) > 1 and i == 0 else y
        ok = lambda x: x != k and stem not in stems(x) and not any(s == stem for s in INFO[x]['on'])
        look = [x for x in pool_kanji if ok(x) and set(INFO[x]['rad']) & set(INFO[k]['rad'])]
        rest = [x for x in pool_kanji if ok(x) and x not in look and INFO[x]['g'] == INFO[k]['g']]
        look.sort(key=lambda x: (abs(INFO[x]['g'] - grade), rng.random())); rng.shuffle(rest)
        for x in look[:5] + rest[:4]:
            c = w[:i] + x + w[i + 1:]
            if len(w) > 1 and real_word(c): continue
            cand.append(c)
        cand = cand[:7]
    seen = []
    for c in cand:
        if c != w and c not in seen: seen.append(c)
    return rng.sample(seen, 3) if len(seen) >= 3 else None

def main():
    words = load()
    total = 0
    seen_y = {}
    bad = False
    for g in sorted(words):
        ws = words[g]
        for w, y in ws:
            for c in w:
                if isk(c) and INFO[c]['g'] > g: print(f'注意 {g}年「{w}」の「{c}」は {INFO[c]["g"]}年の漢字')
                if not isk(c) and not HIRA.match(c): print(f'注意 {g}年「{w}」に 小学校で習わない字「{c}」')
            if y in seen_y: print(f'NG 同じ読みの言葉: {w} と {seen_y[y]}（{y}）'); bad = True
            seen_y[y] = w
        if bad: continue
        out = [f'% 国語 {g}', '# tools/gen_kokugo.py がつくったファイル。手で直さない（言葉は tables/20-kanji-words.txt）', '']
        A, B = [], []
        for w, y in ws:
            rng = random.Random(f'{g}{w}')
            a = yomi_wrongs(w, y, g, ws, rng)
            if a: A += [f'「[{w}]」の_{{読|よ}}み{{方|かた}}は？', y, *a, f'「[{w}]」は「{y}」と_{{読|よ}}みます。', '']
            else: print(f'注意 読みの まちがいが つくれない: {w}')
            b = kaki_wrongs(w, y, g, rng)
            if b: B += [f'「{y}」を_{{漢字|かんじ}}で_{{書|か}}くと？', f'[{w}]', *[f'[{x}]' for x in b], f'「{y}」は「[{w}]」と_{{書|か}}きます。', '']
            else: print(f'注意 書きの まちがいが つくれない: {w}')
        out += ['@ 01 | 漢字 | {漢字|かんじ}の {読|よ}み', ''] + A + ['@ 02 | 漢字 | {漢字|かんじ}の {書|か}き', ''] + B
        n = (len(A) + len(B)) // 7
        if g >= 2:
            rng = random.Random(f'kaku{g}')
            ks = [k for k, v in INFO.items() if v['g'] == g and v['s'] >= 3]
            out += ['@ 03 | 漢字 | {漢字|かんじ}の {画数|かくすう}', '']
            for k in rng.sample(ks, 30):
                s = INFO[k]['s']
                wr = [s - 1, s + 1, rng.choice([s - 2, s + 2]) if s > 3 else s + 2]
                rng.shuffle(wr)
                out += [f'「[{k}]」の_{{画数|かくすう}}は？', f'{s}{{画|かく}}', *[f'{x}{{画|かく}}' for x in wr], f'「[{k}]」は_{s}{{画|かく}}で_{{書|か}}きます。', '']
                n += 1
        (ROOT / 'src' / 'ko' / f'{g}-gen.txt').write_text('\n'.join(out), encoding='utf-8')
        print(f'{g}年: {n} 問'); total += n
    print('計', total)
    if bad: sys.exit(1)

if __name__ == '__main__':
    main()
