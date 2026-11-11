#!/usr/bin/env python3
# 表から問題をつくる（tables/*.txt → src/<教科>/<学年>-tab.txt）
#   python3 tools/gen_table.py
#
# 表の書き方（tables/NN-なまえ.txt。ファイル名の順・ファイルの中の順につくる）
#   == 教科 学年 | 単元番号 | 領域 | 単元名     ← 新しい単元。「== 教科 学年 | +03」なら 手書きの単元03に足す
#   Q: 問題文 -> 答えの列                        ← <0> <1> … に その行の列が入る
#        ; wrong=2,3,4   まちがいを その行の 2,3,4 列目から とる（なければ ほかの行の答えから自動で選ぶ）
#        ; group=2       自動で選ぶとき、2列目が同じ行を 先に選ぶ（同じ地方の県 など）
#        ; only=3        3列目が空でない行だけ 問題にする
#        ; sort=num      自動で選ぶとき、数の近いものを選ぶ（年号など）
#   E: 解説
#   （Q: と E: の組は いくつ書いてもよい。1行から その数だけ問題ができる）
#   --
#   列1 | 列2 | 列3 …                            ← 1行が1つのデータ。区切りは「 | 」（前後に空白）
#
# 自動で選ぶ まちがいの決まり
#   ・正解と同じ文字のものは 選ばない
#   ・「同じ問題文で、それが正解になる行」があるものは 選ばない（答えが2つある問題を つくらない）
#   ・長さの近いものを 先に選ぶ
# 乱数の種は固定（表の見出し＋問題の番号）。行を足すときは 表の最後に足す。
import random, re, pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
CODES = {'国語': 'ko', '算数': 'sa', 'せいかつA': 'la', 'せいかつB': 'lb', '理科': 'ri', '社会': 'sh', '英語': 'ei'}

def fill(tpl, row): return re.sub(r'<(\d+)>', lambda m: row[int(m[1])] if int(m[1]) < len(row) else '', tpl)
def plain(s): return re.sub(r'\{!?([^|{}]+)\|[^{}]+\}', r'\1', s).replace('_', '').replace('[', '').replace(']', '')

def main():
    out, total, bad = {}, 0, 0
    for path in sorted((ROOT / 'tables').glob('*.txt')):
        text = path.read_text(encoding='utf-8')
        for chunk in re.split(r'^== ', text, flags=re.M)[1:]:
            head, _, rest = chunk.partition('\n')
            spec, _, body = rest.partition('\n--\n')
            hp = [x.strip() for x in head.split('|', 3)]
            subj, grade = hp[0].split()
            key = (subj, int(grade))
            o = out.setdefault(key, [f'% {subj} {grade}', '# tools/gen_table.py が tables/ からつくったファイル。手で直さない', ''])
            o += [f'@+ {hp[1][1:]}' if hp[1].startswith('+') else f'@ {hp[1]} | {hp[2]} | {hp[3]}', '']
            qs = []
            for line in spec.split('\n'):
                line = line.strip()
                if line.startswith('Q:'):
                    parts = [x.strip() for x in line[2:].split(' ; ')]
                    tpl, ans = parts[0].rsplit('->', 1)
                    opt = dict(p.split('=') for p in parts[1:])
                    qs.append(dict(tpl=tpl.strip(), ans=int(ans), wrong=[int(x) for x in opt['wrong'].split(',')] if 'wrong' in opt else None,
                                   group=int(opt['group']) if 'group' in opt else None, num=opt.get('sort') == 'num', only=int(opt['only']) if 'only' in opt else None, exp=''))
                elif line.startswith('E:'): qs[-1]['exp'] = line[2:].strip()
            rows = [[c.strip() for c in re.split(r'\s\|(?:\s+|$)', l.strip())] for l in body.split('\n') if l.strip() and not l.startswith('#')]
            for r in rows:
                for qi, q in enumerate(qs):
                    if q['only'] is not None and (len(r) <= q['only'] or not r[q['only']]): continue
                    rng = random.Random(f'{head}|{qi}|{r[0]}')
                    qt, correct = fill(q['tpl'], r), r[q['ans']]
                    if q['wrong']:
                        ws = [r[i] for i in q['wrong'] if i < len(r) and r[i]]
                    else:
                        use = [x for x in rows if q['only'] is None or (len(x) > q['only'] and x[q['only']])]
                        also = {x[q['ans']] for x in use if fill(q['tpl'], x) == qt}      # 同じ問題文で正解になるもの
                        cand = {}
                        for x in use:
                            a = x[q['ans']]
                            if a in also or plain(a) == plain(correct) or a in cand: continue
                            same = q['group'] is not None and len(x) > q['group'] and x[q['group']] == r[q['group']]
                            cand[a] = same
                        if q['num']:   # 数の近いものから選ぶ（年号など）
                            n = lambda a: int(re.sub(r'\D', '', plain(a)) or 0)
                            order = sorted(cand, key=lambda a: (abs(n(a) - n(correct)), rng.random())); pool = order[:5]
                        else:
                            order = sorted(cand, key=lambda a: (not cand[a], abs(len(plain(a)) - len(plain(correct))), rng.random()))
                            pool = order[:7]
                        ws = rng.sample(pool, 3) if len(pool) >= 3 else pool
                    if len(ws) < 3 or len(set(ws + [correct])) != 4:
                        print(f'NG {path.name}: まちがいが3つない「{plain(qt)}」{ws}'); bad += 1; continue
                    rng.shuffle(ws)
                    o += [qt, correct, *ws[:3], fill(q['exp'], r), '']
                    total += 1
    for (subj, g), o in out.items():
        (ROOT / 'src' / CODES[subj] / f'{g}-tab.txt').write_text('\n'.join(o), encoding='utf-8')
    print(f'表から {total} 問')
    if bad: sys.exit(1)

if __name__ == '__main__':
    main()
