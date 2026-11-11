#!/usr/bin/env python3
# 算数の計算問題をつくる（src/sa/<学年>-gen.txt に書き出す）
#   python3 tools/gen_sansu.py
# ・乱数の種は固定。何度つくっても同じ問題が同じ順番で出る（問題IDが変わらない）
# ・問題を足すときは、各タイプの「数」をふやす（後ろに足されるので、前のIDは変わらない）
# ・手書きの原稿（src/sa/<学年>.txt）と同じ問題文は つくらない
# ・まちがいの選択肢は「よくあるまちがい」（くり上がりわすれ・たす/ひくの とりちがえ など）から選ぶ
import random, re, pathlib
from fractions import Fraction as F
from decimal import Decimal
from math import gcd

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / 'src' / 'sa'

def plain(s): return re.sub(r'\{!?([^|{}]+)\|[^{}]+\}', r'\1', s).replace('_', '').replace(' ', '')
def dec(x):
    d = Decimal(x.numerator) / Decimal(x.denominator)
    s = format(d, 'f')
    return s.rstrip('0').rstrip('.') if '.' in s else s
def fr(x):
    """約分した分数（整数なら整数）"""
    x = F(x)
    return str(x.numerator) if x.denominator == 1 else f'{x.numerator}/{x.denominator}'

class Gen:
    def __init__(self, grade):
        self.g, self.rng = grade, random.Random(20261110 + grade)
        self.seen = set()
        hand = SRC / f'{grade}.txt'
        blocks = re.split(r'\n\s*\n', hand.read_text(encoding='utf-8'))
        for b in blocks:
            ls = [l for l in b.strip().split('\n') if l and not l.startswith(('%', '@', '#'))]
            if ls: self.seen.add(plain(ls[0]))
        self.out = [f'% 算数 {grade}', '# tools/gen_sansu.py がつくったファイル。手で直さない（直すときは gen_sansu.py を直す）', '']
        self.count = 0

    def unit(self, no): self.out += [f'@+ {no}', '']

    def add(self, q, correct, wrongs, exp):
        """wrongs: まちがいの候補（もっともらしい順）。3つ選ぶ"""
        if plain(q) in self.seen: return False
        def val(s):
            try: return F(s)
            except Exception: return s
        ws, vals = [], {val(correct)}
        for w in wrongs:
            if w is None or w == correct or w in ws or val(w) in vals: continue
            ws.append(w); vals.add(val(w))
        if len(ws) < 3: return False
        head, rest = ws[:2], ws[2:6]
        pick = head + [self.rng.choice(rest)] if rest else ws[:3]
        self.rng.shuffle(pick)
        self.seen.add(plain(q))
        self.out += [q, correct, *pick, exp, '']
        self.count += 1
        return True

    def many(self, n, make, tries=4000):
        """make() が (q, correct, wrongs, exp) か None を返す。n問できるまでくり返す"""
        done = 0
        for _ in range(tries):
            if done >= n: break
            r = make()
            if r and self.add(*r): done += 1
        if done < n: print(f'  注意: {self.g}年 {make.__name__} は {done}/{n} 問しかできなかった')

    def save(self):
        (SRC / f'{self.g}-gen.txt').write_text('\n'.join(self.out), encoding='utf-8')
        print(f'{self.g}年: {self.count} 問')

def ints(c, cands):
    """整数の正解 c に対する まちがい候補（0以上・正解とちがうもの）"""
    return [str(x) for x in cands if x is not None and x >= 0 and x != c]

# ---------- 1年 ----------
def grade1():
    G = Gen(1); R = G.rng
    G.unit('04')
    def add10():
        a = R.randint(1, 9); b = R.randint(1, 10 - a); c = a + b
        return f'{a}＋{b}＝？', str(c), ints(c, [c + 1, c - 1, abs(a - b), c + 2, c - 2, a * 10 + b]), f'{a}と_{b}を_あわせると_{c}。'
    G.many(26, add10)
    G.unit('05')
    def sub10():
        a = R.randint(2, 10); b = R.randint(1, a - 1); c = a - b
        return f'{a}−{b}＝？', str(c), ints(c, [c + 1, c - 1, a + b, c + 2, b, c - 2]), f'{a}から_{b}を_とると_{c}。'
    G.many(26, sub10)
    G.unit('06')
    def teen():
        k = R.randint(0, 3)
        if k == 0:
            b = R.randint(1, 9); a, c = 10, 10 + b; q = f'10＋{b}＝？'; e = f'10と_{b}で_{c}。'
        elif k == 1:
            b = R.randint(1, 9); a = 10 + b; c = 10; q = f'{a}−{b}＝？'; e = f'{a}は_10と_{b}。{b}を_とると_10。'
        elif k == 2:
            x = R.randint(1, 7); y = R.randint(1, 8 - x); a, b, c = 10 + x, y, 10 + x + y; q = f'{a}＋{b}＝？'; e = f'{a}は_10と_{x}。{x}＋{y}＝{x + y}だから_{c}。'
        else:
            x = R.randint(2, 9); y = R.randint(1, x - 1); a, b, c = 10 + x, y, 10 + x - y; q = f'{a}−{b}＝？'; e = f'{a}は_10と_{x}。{x}−{y}＝{x - y}だから_{c}。'
        return q, str(c), ints(c, [c + 1, c - 1, c - 10, c + 10, c + 2, c - 2]), e
    G.many(24, teen)
    G.unit('08')
    def carry():
        a = R.randint(2, 9); b = R.randint(11 - a, 9); c = a + b; big, small = max(a, b), min(a, b)
        return (f'{a}＋{b}＝？', str(c), ints(c, [c + 1, c - 1, c - 10, c + 2, c - 2, abs(a - b)]),
                f'{big}は_あと_{10 - big}で_10。{small}を_{10 - big}と_{small - (10 - big)}に_わけて、10と_{c - 10}で_{c}。')
    G.many(28, carry)
    G.unit('09')
    def borrow():
        a = R.randint(11, 18); b = R.randint(a - 9, 9); c = a - b
        return (f'{a}−{b}＝？', str(c), ints(c, [c + 1, c - 1, c + 10, c + 2, c - 2, a + b]),
                f'{a}を_10と_{a - 10}に_わける。10−{b}＝{10 - b}、{10 - b}と_{a - 10}で_{c}。')
    G.many(28, borrow)
    G.unit('10')
    def big():
        k = R.randint(0, 3)
        if k == 0:
            a = R.randint(1, 8) * 10; b = R.randint(1, 9 - a // 10) * 10; c = a + b; q = f'{a}＋{b}＝？'
            e = f'10が_{a // 10}つと_{b // 10}つで_{c // 10}つ。10が_{c // 10}つで_{c}。'; w = [c // 10, c + 10, c - 10, c + 1, abs(a - b) or 5]
        elif k == 1:
            a = R.randint(2, 9) * 10; b = R.randint(1, a // 10 - 1) * 10; c = a - b; q = f'{a}−{b}＝？'
            e = f'10が_{a // 10}つから_{b // 10}つ_とると_{c // 10}つ。10が_{c // 10}つで_{c}。'; w = [c // 10, c + 10, c - 10, a + b, c + 1]
        elif k == 2:
            t = R.randint(2, 9); x = R.randint(1, 7); y = R.randint(1, 9 - x - 1); a, b, c = t * 10 + x, y, t * 10 + x + y; q = f'{a}＋{b}＝？'
            e = f'{a}は_{t * 10}と_{x}。{x}＋{y}＝{x + y}だから_{c}。'; w = [c + 1, c - 1, c + 10, c - 10, a + b * 10]
        else:
            t = R.randint(2, 9); x = R.randint(2, 9); y = R.randint(1, x - 1); a, b, c = t * 10 + x, y, t * 10 + x - y; q = f'{a}−{b}＝？'
            e = f'{a}は_{t * 10}と_{x}。{x}−{y}＝{x - y}だから_{c}。'; w = [c + 1, c - 1, c + 10, c - 10, a + b]
        return q, str(c), ints(c, w), e
    G.many(24, big)
    G.save()

# ---------- 2年 ----------
def grade2():
    G = Gen(2); R = G.rng
    G.unit('02')
    def add2():
        a = R.randint(12, 79); b = R.randint(11, 99 - a) if a < 88 else 11; c = a + b
        nocarry = (a // 10 + b // 10) * 10 + (a % 10 + b % 10) % 10   # くり上がりわすれ
        return (f'{a}＋{b}＝？', str(c), ints(c, [nocarry, c + 10, c - 10, c + 1, c - 1, abs(a - b)]),
                f'{{一|いち}}のくらいは_{a % 10}＋{b % 10}＝{a % 10 + b % 10}。{{十|じゅう}}のくらいと_あわせて_{c}。')
    G.many(40, add2)
    G.unit('03')
    def sub2():
        a = R.randint(31, 99); b = R.randint(12, a - 11); c = a - b
        rev = abs(a // 10 - b // 10) * 10 + abs(a % 10 - b % 10)       # 大きい方から小さい方をひいてしまう
        return (f'{a}−{b}＝？', str(c), ints(c, [rev, c + 10, c - 10, c + 1, c - 1, a + b]),
                f'{{一|いち}}のくらいから_じゅんに_{{計算|けいさん}}します。{c}＋{b}＝{a}で_たしかめられます。')
    G.many(40, sub2)
    G.unit('05')
    def hund():
        k = R.randint(0, 2)
        if k == 0:
            a = R.randint(1, 8) * 100; b = R.randint(1, 9 - a // 100) * 100; c = a + b; q = f'{a}＋{b}＝？'
            e = f'100が_{a // 100}こと_{b // 100}こで_{c // 100}こ。'; w = [c // 10, c + 100, c - 100, c + 10, abs(a - b) or 50]
        elif k == 1:
            a = R.randint(2, 10) * 100; b = R.randint(1, a // 100 - 1) * 100; c = a - b; q = f'{a}−{b}＝？'
            e = f'100が_{a // 100}こから_{b // 100}こ_とると_{c // 100}こ。'; w = [c // 10, c + 100, c - 100, a + b, c + 10]
        else:
            a = R.randint(2, 9) * 100; b = R.randint(1, 9) * 10 + R.choice([0, 0, R.randint(1, 9)]); c = a + b; q = f'{a}＋{b}＝？'
            e = f'{a}と_{b}を_あわせて_{c}。'; w = [a + b * 10, c + 100, c + 10, c - 10, a // 10 + b]
        return q, str(c), ints(c, w), e
    G.many(18, hund)
    G.unit('08')
    def kuku_low():
        a = R.randint(2, 5); b = R.randint(1, 9); c = a * b
        return f'{a}×{b}＝？', str(c), ints(c, [a * (b + 1), a * (b - 1) if b > 1 else a + b, c + 1, c - 1, (a + 1) * b, a + b]), f'{a}のだんの_{{九九|くく}}。{a}×{b}＝{c}。'
    G.many(30, kuku_low)
    G.unit('09')
    def kuku_high():
        a = R.choice([6, 7, 8, 9, 6, 7, 8, 9, 1]); b = R.randint(1, 9); c = a * b
        return f'{a}×{b}＝？', str(c), ints(c, [a * (b + 1), a * (b - 1) if b > 1 else a + b, c + 1, c - 1, (a - 1) * b if a > 1 else c + 2, a + b]), f'{a}のだんの_{{九九|くく}}。{a}×{b}＝{c}。'
    G.many(38, kuku_high)
    G.save()

# ---------- 3年 ----------
def grade3():
    G = Gen(3); R = G.rng
    G.unit('01')
    def mul0():
        a = R.choice([2, 3, 4, 5, 6, 7, 8, 9, 11, 12]); k = R.randint(0, 3)
        if k == 0: q, c, e = f'{a}×0＝？', 0, 'どんな_{数|かず}に_0を_かけても_{答|こた}えは_0。'
        elif k == 1: q, c, e = f'0×{a}＝？', 0, '0に_どんな_{数|かず}を_かけても_{答|こた}えは_0。'
        elif k == 2: q, c, e = f'{a}×10＝？', a * 10, f'10{{倍|ばい}}すると、{{右|みぎ}}に_0が_1つ_つきます。'
        else: q, c, e = f'10×{a}＝？', a * 10, f'{a}×10と_{{同|おな}}じ。{{右|みぎ}}に_0が_1つ_つきます。'
        return q, str(c), ints(c, [a, a + 10, 1, a * 100, 10, a * 10 + a] if c else [a, 1, a * 10, 10, a + 1]), e
    G.many(12, mul0)
    G.unit('03')
    def div():
        d = R.randint(2, 9); q_ = R.randint(1, 9); n = d * q_
        return (f'{n}÷{d}＝？', str(q_), ints(q_, [q_ + 1, q_ - 1, d if d != q_ else q_ + 2, n - d, q_ + 2, n + d]),
                f'{d}のだんの_{{九九|くく}}で、{d}×{q_}＝{n}。')
    G.many(40, div)
    G.unit('04')
    def divrem():
        d = R.randint(2, 9); q_ = R.randint(1, 9); r = R.randint(1, d - 1); n = d * q_ + r
        r2 = r + 1 if r + 1 < d else r - 1
        w = [f'{q_}あまり{r2}' if r2 > 0 else None, f'{q_ + 1}あまり{r}', f'{q_ - 1}あまり{r + d}' if q_ > 1 else f'{q_ + 2}あまり{r}', f'{q_ + 1}あまり{r2}' if r2 > 0 else None, f'{r}あまり{q_}' if r != q_ else None]
        return f'{n}÷{d}＝？', f'{q_}あまり{r}', w, f'{d}×{q_}＝{d * q_}、{n}−{d * q_}＝{r}。'
    G.many(36, divrem)
    G.unit('05')
    def addsub3():
        if R.random() < 0.5:
            a = R.randint(11, 78) * 10; b = R.randint(11, 98 - a // 10) * 10; c = a + b   # 何百何十どうし（暗算できる大きさ）
            nc = sum(((a // p % 10 + b // p % 10) % 10) * p for p in (1, 10, 100))
            return f'{a}＋{b}＝？', str(c), ints(c, [nc, c + 10, c - 10, c + 100, c - 100, c + 1]), 'くらいを_そろえて、{一|いち}のくらいから_じゅんに_{計算|けいさん}します。'
        a = R.randint(30, 99) * 10; b = R.randint(11, a // 10 - 11) * 10; c = a - b
        rv = sum(abs(a // p % 10 - b // p % 10) * p for p in (1, 10, 100))
        return f'{a}−{b}＝？', str(c), ints(c, [rv, c + 10, c - 10, c + 100, c - 100, c + 1]), f'{c}＋{b}＝{a}で_たしかめられます。'
    G.many(34, addsub3)
    G.unit('08')
    def mul1():
        a = R.randint(12, 99); b = R.randint(2, 9); c = a * b
        parts = '、'.join(f'{(a // p % 10) * p}×{b}＝{(a // p % 10) * p * b}' for p in (1, 10, 100) if a // p % 10)
        nc = sum(((a // p % 10) * b % 10) * p for p in (1, 10, 100)) + (a // (100 if a > 99 else 10) % 10 * b // 10) * (1000 if a > 99 else 100)
        return f'{a}×{b}＝？', str(c), ints(c, [nc, c + b, c - b, c + 10, c - 10, c + 100]), f'{parts}。あわせて_{c}。'
    G.many(30, mul1)
    G.unit('10')
    def dec3():
        if R.random() < 0.5:
            a = F(R.randint(1, 49), 10); b = F(R.randint(1, 49), 10); c = a + b; q = f'{dec(a)}＋{dec(b)}＝？'
            e = f'0.1が_{a * 10}こと_{b * 10}こで_{c * 10}こ。'
        else:
            a = F(R.randint(11, 89), 10); b = F(R.randint(1, int(a * 10) - 1), 10); c = a - b; q = f'{dec(a)}−{dec(b)}＝？'
            e = f'0.1が_{a * 10}こから_{b * 10}こ_とると_{c * 10}こ。'
        w = [c * 10, c / 10, c + F(1, 10), c - F(1, 10), c + 1, abs(c - 1)]
        return q, dec(c), [dec(x) for x in w if x > 0 and x != c], e
    G.many(20, dec3)
    G.unit('12')
    def frac3():
        n = R.randint(4, 10)
        if R.random() < 0.5:
            a = R.randint(1, n - 2); b = R.randint(1, n - a); c = a + b; q = f'{a}/{n}＋{b}/{n}＝？'
            ans = '1' if c == n else f'{c}/{n}'; e = f'1/{n}が_{a}こと_{b}こで_{c}こ。{{分母|ぶんぼ}}は_そのまま。' + (f'{n}/{n}は_1。' if c == n else '')
            w = [f'{c}/{2 * n}', f'{c + 1}/{n}' if c + 1 != n else f'{c + 2}/{n}', f'{c - 1}/{n}', f'{abs(a - b) or 1}/{n}', f'{a * b}/{n}' if a * b not in (c, n) else None]
        else:
            a = R.randint(2, n); b = R.randint(1, a - 1); c = a - b; q = (f'1−{b}/{n}＝？' if a == n else f'{a}/{n}−{b}/{n}＝？')
            ans = f'{c}/{n}'; e = (f'1を_{n}/{n}と_{{考|かんが}}えます。' if a == n else '') + f'1/{n}が_{a}こから_{b}こ_とると_{c}こ。'
            w = [f'{c + 1}/{n}' if c + 1 != n else None, f'{c - 1}/{n}' if c > 1 else f'{c + 2}/{n}', f'{a + b}/{n}' if a + b != n else None, f'{c}/{2 * n}', f'{b}/{n}' if b != c else None]
        return q, ans, w, e
    G.many(20, frac3)
    G.unit('14')
    def mul2():
        a = R.randint(11, 30); b = R.choice([11, 12, 13, 14, 15, 20, 30, 40]); c = a * b
        return (f'{a}×{b}＝？', str(c), ints(c, [a * (b % 10) + a * (b // 10), c + a, c - a, c + 10, c - 10, c + 100]),
                f'{a}×{b % 10}＝{a * (b % 10)}、{a}×{b // 10 * 10}＝{a * (b // 10 * 10)}。あわせて_{c}。' if b % 10 else f'{a}×{b // 10}＝{a * (b // 10)}の_10{{倍|ばい}}。')
    G.many(22, mul2)
    G.save()

# ---------- 4年 ----------
def grade4():
    G = Gen(4); R = G.rng
    G.unit('03')
    def div4():
        k = R.randint(0, 2)
        if k == 0: d = R.randint(2, 9); q_ = R.randint(11, 99 // d) if 99 // d >= 11 else 11; n = d * q_
        elif k == 1: d = R.randint(2, 6); q_ = R.randint(101 // d + 1, 300 // d); n = d * q_
        else: d = R.randint(11, 25); q_ = R.randint(2, 9); n = d * q_
        return f'{n}÷{d}＝？', str(q_), ints(q_, [q_ + 1, q_ - 1, q_ + 10, q_ - 10 if q_ > 10 else q_ + 2, q_ * 10, q_ + 2]), f'{d}×{q_}＝{n}で_たしかめられます。'
    G.many(30, div4)
    def divrem4():
        d = R.randint(3, 8); q_ = R.randint(11, (99 - (d - 1)) // d); r = R.randint(1, d - 1); n = d * q_ + r   # 2けた÷1けた
        r2 = r + 1 if r + 1 < d else r - 1
        return (f'{n}÷{d}＝？', f'{q_}あまり{r}', [f'{q_}あまり{r2}' if r2 > 0 else None, f'{q_ + 1}あまり{r}', f'{q_ - 1}あまり{r + d}', f'{q_ - 10}あまり{r}' if q_ > 10 else None, f'{q_ + 10}あまり{r}'],
                f'{d}×{q_}＝{d * q_}、{n}−{d * q_}＝{r}。')
    G.many(16, divrem4)
    G.unit('05')
    def dec4():
        if R.random() < 0.5:
            a = F(R.randint(101, 599), 100); b = F(R.randint(11, 399), 100 if R.random() < 0.6 else 10); c = a + b; q = f'{dec(a)}＋{dec(b)}＝？'
        else:
            a = F(R.randint(201, 799), 100); b = F(R.randint(11, int(a * 10) - 1), 10) if R.random() < 0.4 else F(R.randint(11, int(a * 100) - 1), 100); c = a - b; q = f'{dec(a)}−{dec(b)}＝？'
        if c <= 0: return None
        w = [c + F(1, 10), c - F(1, 10), c * 10, c + F(1, 100), c + 1, c - F(1, 100)]
        return q, dec(c), [dec(x) for x in w if x > 0 and x != c], '{位|くらい}を_そろえて、{整数|せいすう}と_{同|おな}じ_ように_{計算|けいさん}します。'
    G.many(28, dec4)
    G.unit('06')
    def rnd():
        k = R.randint(0, 2); n = R.randint(1050, 98999)
        if n % 1000 == 0 or n % 100 == 0: return None
        if k == 0: p, nm = 100, '{百|ひゃく}の_{位|くらい}'; sub = '{十|じゅう}の_{位|くらい}'
        elif k == 1: p, nm = 1000, '{千|せん}の_{位|くらい}'; sub = '{百|ひゃく}の_{位|くらい}'
        else:
            if n < 10000: return None
            p, nm = 10000, '{一万|いちまん}の_{位|くらい}'; sub = '{千|せん}の_{位|くらい}'
        dgt = n // (p // 10) % 10
        c = (n + p // 2) // p * p; other = n // p * p if c != n // p * p else n // p * p + p
        w = [other, (n + p // 20) // (p // 10) * (p // 10), c + p, c - p if c > p else c + 2 * p, (n + p * 5) // (p * 10) * (p * 10)]
        return (f'{n}を_{{四捨五入|ししゃごにゅう}}して、{nm}までの_がい{{数|すう}}に_すると？', str(c), ints(c, w),
                f'{sub}の_{dgt}を_{"{切|き}り{上|あ}げ" if dgt >= 5 else "{切|き}り{捨|す}て"}て_{c}。')
    G.many(16, rnd)
    G.unit('07')
    def order():
        k = R.randint(0, 3)
        if k == 0: a, b, c_ = R.randint(2, 20), R.randint(2, 9), R.randint(2, 9); q = f'{a}＋{b}×{c_}＝？'; c = a + b * c_; w = [(a + b) * c_, a * b + c_, c + 1, c - 1]; e = f'かけ{{算|ざん}}を_{{先|さき}}に_{{計算|けいさん}}。{b}×{c_}＝{b * c_}、{a}＋{b * c_}＝{c}。'
        elif k == 1: a, b, c_ = R.randint(2, 10), R.randint(2, 10), R.randint(2, 9); q = f'（{a}＋{b}）×{c_}＝？'; c = (a + b) * c_; w = [a + b * c_, a * c_ + b, c + c_, c - c_]; e = f'（　）の_{{中|なか}}を_{{先|さき}}に_{{計算|けいさん}}。{a + b}×{c_}＝{c}。'
        elif k == 2:
            c_ = R.randint(2, 9); b = c_ * R.randint(2, 9); a = R.randint(b // c_ + 2, 60); q = f'{a}−{b}÷{c_}＝？'; c = a - b // c_
            w = [(a - b) // c_ if a > b and (a - b) % c_ == 0 else abs(a - b), a - b + c_, c + 1, c - 1, a + b // c_]; e = f'わり{{算|ざん}}を_{{先|さき}}に_{{計算|けいさん}}。{b}÷{c_}＝{b // c_}、{a}−{b // c_}＝{c}。'
        else:
            a, b, c_, d = R.randint(3, 9), R.randint(3, 9), R.randint(2, 5), R.randint(2, 5)
            if a * b <= c_ * d: return None
            q = f'{a}×{b}−{c_}×{d}＝？'; c = a * b - c_ * d; w = [(a * b - c_) * d, a * (b - c_) * d if b > c_ else c + 10, a * b + c_ * d, c + 1, c - 1]; e = f'かけ{{算|ざん}}を_{{先|さき}}に_{{計算|けいさん}}。{a * b}−{c_ * d}＝{c}。'
        return q, str(c), ints(c, w + [c + 2, c + 10]), e
    G.many(28, order)
    G.unit('09')
    def frac4():
        n = R.randint(3, 9)
        if R.random() < 0.5:
            a = R.randint(2, 2 * n - 1); b = R.randint(1, 2 * n); c = a + b; q = f'{a}/{n}＋{b}/{n}＝？'; e = f'{{分母|ぶんぼ}}は_そのまま、{{分子|ぶんし}}を_たします。{a}＋{b}＝{c}。'
            w = [F(c, 2 * n), F(c + 1, n), F(c - 1, n), F(abs(a - b) or 1, n), F(a * b, n)]
        else:
            a = R.randint(n + 1, 3 * n - 1); b = R.randint(1, a - 1); c = a - b; q = f'{a}/{n}−{b}/{n}＝？'; e = f'{{分母|ぶんぼ}}は_そのまま、{{分子|ぶんし}}を_ひきます。{a}−{b}＝{c}。'
            w = [F(c + 1, n), F(c - 1, n) if c > 1 else F(c + 2, n), F(a + b, n), F(c, 2 * n), F(b, n)]
        if c % n == 0 or a % n == 0 or b % n == 0: return None
        cv = F(c, n); ws = []
        for x in w:
            if x != cv and x > 0 and x not in ws: ws.append(x)
        # 4年は約分を習っていないので、分母をそのままにして表す
        def show(x):
            return f'{int(x * n)}/{n}' if (x * n).denominator == 1 and (x * n) % n != 0 else (f'{x.numerator}/{x.denominator}' if x.denominator != 1 else None)
        return q, f'{c}/{n}', [show(x) for x in ws], e
    G.many(22, frac4)
    G.unit('12')
    def decmul():
        if R.random() < 0.5:
            a = F(R.randint(2, 49), 10); b = R.randint(2, 9); c = a * b
            if a.denominator == 1: return None
            q = f'{dec(a)}×{b}＝？'; e = f'{int(a * 10)}×{b}＝{int(a * 10) * b}。その_1/10で_{dec(c)}。'
        else:
            b = R.randint(2, 9); c = F(R.randint(2, 49), 10); a = c * b
            if c.denominator == 1 or a.denominator > 10: return None
            q = f'{dec(a)}÷{b}＝？'; e = f'{dec(c)}×{b}＝{dec(a)}で_たしかめられます。'
        w = [c * 10, c / 10, c + F(1, 10), c - F(1, 10), c + 1, c + F(1, 5)]
        return q, dec(c), [dec(x) for x in w if x > 0 and x != c], e
    G.many(34, decmul)
    G.save()

# ---------- 5年 ----------
def grade5():
    G = Gen(5); R = G.rng
    G.unit('04')
    def decmul5():
        a = F(R.randint(2, 30), 10); b = F(R.choice([2, 3, 4, 5, 6, 7, 8, 9, 15, 25]), 10)   # かたほうは かんたんな数
        if a.denominator == 1 and b.denominator == 1: return None
        c = a * b; ai, bi = dec(a).replace('.', '').lstrip('0'), dec(b).replace('.', '').lstrip('0')
        places = (a.denominator > 1) + (b.denominator > 1)
        e = f'{ai}×{bi}＝{int(ai) * int(bi)}。{{小数点|しょうすうてん}}を_{{左|ひだり}}へ_{places}けた_{{移|うつ}}して_{dec(c)}。'
        w = [c * 10, c / 10, c + F(1, 10), c * 100 if c < 1 else c / 100, c - F(1, 10), c + 1]
        return f'{dec(a)}×{dec(b)}＝？', dec(c), [dec(x) for x in w if x > 0 and x != c], e
    G.many(32, decmul5)
    G.unit('05')
    def decdiv5():
        d = F(R.choice([2, 3, 4, 5, 6, 7, 8, 9, 12, 15, 25]), 10); q_ = F(R.randint(2, 20)); n = d * q_
        if d.denominator == 1 or n.denominator > 100 or q_ == d: return None
        e = f'わる{{数|かず}}が_{{整数|せいすう}}に_なる_ように、りょうほうを_10{{倍|ばい}}。{dec(n * 10)}÷{dec(d * 10)}＝{dec(q_)}。'
        w = [q_ * 10, q_ / 10, q_ + 1, q_ * 100 if q_ < 10 else q_ / 100, q_ - 1 if q_ > 1 else q_ + 2, q_ + F(1, 10)]
        return f'{dec(n)}÷{dec(d)}＝？', dec(q_), [dec(x) for x in w if x > 0 and x != q_], e
    G.many(30, decdiv5)
    G.unit('08')
    def lcmgcd():
        a = R.randint(2, 15); b = R.randint(2, 18)
        if a >= b: return None
        g = gcd(a, b); l = a * b // g
        if R.random() < 0.5:
            if l > 60: return None
            return (f'{a}と_{b}の_{{最小公倍数|さいしょうこうばいすう}}は？', str(l), ints(l, [a * b if a * b != l else l * 2, g if g > 1 else a + b, l * 2, a + b, l + a, l - a if l - a > b else l + b]),
                    f'{b}の_{{倍数|ばいすう}}の_うち、{a}でも_わり{{切|き}}れる_いちばん_{{小|ちい}}さい_{{数|かず}}は_{l}。')
        if g == 1 or b > 60: return None
        return (f'{a}と_{b}の_{{最大公約数|さいだいこうやくすう}}は？', str(g), ints(g, [l, 1, a if a != g else g * 2, g * 2 if a % (g * 2) or b % (g * 2) else g + 1, 2 if g != 2 else 3, b - a if b - a != g else g + 2]),
                f'{a}と_{b}の_りょうほうを_わり{{切|き}}れる_いちばん_{{大|おお}}きい_{{数|かず}}は_{g}。')
    G.many(34, lcmgcd)
    G.unit('09')
    def f2d():
        d = R.choice([2, 4, 5, 8, 10, 20, 25]); n = R.randint(1, d - 1)
        if gcd(n, d) != 1: return None
        c = F(n, d)
        if R.random() < 0.5:
            w = [F(n, 10) if d != 10 else F(n, 100), F(int(str(n) + str(d)), 100), c * 10, c / 10, c + F(1, 10), F(d, 10 * n) if n > 1 else c + F(1, 5)]
            return f'{n}/{d}を_{{小数|しょうすう}}で_{{表|あらわ}}すと？', dec(c), [dec(x) for x in w if x > 0 and x != c], f'{n}÷{d}＝{dec(c)}。'
        dd = dec(c); p = 10 ** len(dd.split('.')[1])
        w = [f'{int(c * p)}/{p * 10}', f'{d}/{n}' if n > 1 else f'{int(c * p)}/{p // 10 or 1}', f'{n + 1}/{d}' if gcd(n + 1, d) == 1 and n + 1 < d else f'{n}/{d + 1}', f'1/{int(c * p)}' if int(c * p) > 1 else None, f'{n}/{d * 2}']
        w = [x for x in w if x and F(x) != c]
        return f'{dd}を_{{分数|ぶんすう}}で_{{表|あらわ}}すと？', f'{n}/{d}', w, f'{dd}＝{int(c * p)}/{p}。' + (f'{{約分|やくぶん}}して_{n}/{d}。' if p != d else '')
    G.many(18, f2d)
    G.unit('10')
    def fracadd():
        b = R.choice([2, 3, 4, 5, 6, 8, 10]); d = R.choice([2, 3, 4, 5, 6, 8, 10])
        if b == d: return None
        a = R.randint(1, b - 1); c_ = R.randint(1, d - 1)
        if gcd(a, b) != 1 or gcd(c_, d) != 1: return None
        x, y = F(a, b), F(c_, d); l = b * d // gcd(b, d)
        if l > 30: return None
        if R.random() < 0.5:
            c = x + y; q = f'{a}/{b}＋{c_}/{d}＝？'; raw = f'{a * l // b}/{l}＋{c_ * l // d}/{l}＝{a * l // b + c_ * l // d}/{l}'
            w = [F(a + c_, b + d), F(a + c_, l), F(c.numerator + 1, c.denominator), F(a + c_, b * d), abs(x - y), F(c.numerator, c.denominator + 1)]
        else:
            if x <= y: return None
            c = x - y; q = f'{a}/{b}−{c_}/{d}＝？'; raw = f'{a * l // b}/{l}−{c_ * l // d}/{l}＝{a * l // b - c_ * l // d}/{l}'
            w = [F(abs(a - c_) or 1, abs(b - d)), F(abs(a - c_) or 1, l), F(c.numerator + 1, c.denominator), x + y, F(c.numerator, c.denominator + 1), F(a, d) if F(a, d) != c else None]
        e = f'{{通分|つうぶん}}して_{raw}。' + (f'{{約分|やくぶん}}して_{fr(c)}。' if c.denominator != l else '')
        return q, fr(c), [fr(v) for v in w if v is not None and v > 0 and v != c], e
    G.many(40, fracadd)
    G.unit('11')
    def mean():
        k = R.randint(3, 5); m = R.randint(4, 30); xs = [m + R.randint(-3, 3) for _ in range(k - 1)]
        last = m * k - sum(xs)
        if last <= 0 or abs(last - m) > 6: return None
        xs.append(last); R.shuffle(xs)
        if len(set(xs)) == 1: return None
        s = sum(xs)
        return (f'{"、".join(map(str, xs))}の_{{平均|へいきん}}は？', str(m), ints(m, [s, max(xs) if max(xs) != m else m + 2, m + 1, m - 1, min(xs) if min(xs) != m else m - 2, s // (k - 1) if s % (k - 1) == 0 else m + 3]),
                f'（{"＋".join(map(str, xs))}）÷{k}＝{s}÷{k}＝{m}。')
    G.many(16, mean)
    G.unit('13')
    def speed():
        k = R.randint(0, 2)
        if k == 0:
            v = R.randint(3, 9) * 10; t = R.randint(2, 6); d = v * t
            return (f'{d}kmを_{t}{{時間|じかん}}で_{{走|はし}}る_{{車|くるま}}の_{{時速|じそく}}は？', f'{{時速|じそく}}{v}km', [f'{{時速|じそく}}{x}km' for x in ints(v, [d * t, d - t, v + 10, v - 10, d + t])],
                    f'{{速|はや}}さ＝{{道|みち}}のり÷{{時間|じかん}}。{d}÷{t}＝{v}。')
        if k == 1:
            v = R.randint(3, 9) * 10 + R.choice([0, 5]); t = R.randint(2, 6); d = v * t
            return (f'{{時速|じそく}}{v}kmで_{t}{{時間|じかん}}_{{走|はし}}ると、{{進|すす}}む_{{道|みち}}のりは？', f'{d}km', [f'{x}km' for x in ints(d, [v + t, v - t, d + v, d - v, d * 10 if d < 100 else d // 10])],
                    f'{{道|みち}}のり＝{{速|はや}}さ×{{時間|じかん}}。{v}×{t}＝{d}。')
        v = R.choice([50, 60, 70, 80, 200, 250]); t = R.randint(3, 12); d = v * t
        return (f'{{分速|ふんそく}}{v}mで_{{進|すす}}む_とき、{d}m_{{進|すす}}むのに_かかる_{{時間|じかん}}は？', f'{t}{{分|ふん}}{{間|かん}}', [f'{x}{{分|ふん}}{{間|かん}}' for x in ints(t, [t + 1, t - 1, t * 10, t + 2, d - v if d - v < 1000 else t + 5])],
                f'{{時間|じかん}}＝{{道|みち}}のり÷{{速|はや}}さ。{d}÷{v}＝{t}。')
    G.many(18, speed)
    G.unit('15')
    def percent():
        k = R.randint(0, 2)
        if k == 0:
            n = R.choice([200, 300, 400, 500, 600, 800, 1000, 1200, 1500, 2000]); p = R.choice([10, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]); c = n * p // 100
            if n * p % 100: return None
            return (f'{n}{{円|えん}}の_{p}％は_いくら？', f'{c}{{円|えん}}', [f'{x}{{円|えん}}' for x in ints(c, [n - c if n - c != c else c + 10, c * 10, c // 10 if c % 10 == 0 else c + 5, n - p, c + n // 10, p])],
                    f'{n}×{dec(F(p, 100))}＝{c}。')
        if k == 1:
            p = R.randint(1, 199)
            c = F(p, 100)
            return (f'{dec(c)}を_{{百分率|ひゃくぶんりつ}}で_{{表|あらわ}}すと？', f'{p}％', [f'{dec(x)}％' for x in [F(p, 10), F(p * 10), c, F(p, 100) * 1000 + 1, F(p + 10)] if x != p],
                    f'{{割合|わりあい}}を_100{{倍|ばい}}すると_{{百分率|ひゃくぶんりつ}}。{dec(c)}×100＝{p}。')
        p = R.randint(1, 150); c = F(p, 100)
        return (f'{p}％を_{{小数|しょうすう}}で_{{表|あらわ}}すと？', dec(c), [dec(x) for x in [c * 10, c / 10, F(p), c * 100 + 1, c + F(1, 10)] if x != c],
                f'{p}÷100＝{dec(c)}。')
    G.many(26, percent)
    G.save()

# ---------- 6年 ----------
def grade6():
    G = Gen(6); R = G.rng
    G.unit('02')
    def xeq():
        k = R.randint(0, 3); t = 'の_xに_あてはまる_{数|かず}は？'
        if k == 0: a = R.randint(3, 60); x = R.randint(2, 60); b = x + a; q = f'x＋{a}＝{b}'; w = [b + a, x + 10, x + 1, x - 1, a]; e = f'{b}−{a}＝{x}。'
        elif k == 1: a = R.randint(3, 40); x = R.randint(a + 1, 90); b = x - a; q = f'x−{a}＝{b}'; w = [abs(b - a) or 1, x + 10, x + 1, x - 1, a]; e = f'{b}＋{a}＝{x}。'
        elif k == 2: a = R.randint(2, 9); x = R.randint(2, 15); b = x * a; q = f'x×{a}＝{b}'; w = [b - a, b * a, b + a, x + 1, x - 1]; e = f'{b}÷{a}＝{x}。'
        else: a = R.randint(2, 9); b = R.randint(2, 12); x = a * b; q = f'x÷{a}＝{b}'; w = [b + a, abs(b - a) or 1, x + a, x - a, b]; e = f'{b}×{a}＝{x}。'
        return q + t, str(x), ints(x, w + [x + 2]), e
    G.many(24, xeq)
    G.unit('03')
    def fmul():
        b = R.randint(2, 7); a = R.randint(1, b - 1); d = R.randint(2, 7); c_ = R.randint(1, d + 1)
        if gcd(a, b) != 1 or gcd(c_, d) != 1 or c_ == d: return None
        x, y = F(a, b), F(c_, d); c = x * y
        if R.random() < 0.25:
            n = R.randint(2, 8); c = x * n; q = f'{a}/{b}×{n}＝？'; w = [F(a, b * n), F(a * n, b * n) + F(1, b), F(a + n, b), c + F(1, b), F(a * n + 1, b)]
            e = f'{{分子|ぶんし}}に_{{整数|せいすう}}を_かけます。{a}×{n}＝{a * n}。' + (f'{{約分|やくぶん}}して_{fr(c)}。' if gcd(a * n, b) != 1 else '')
        else:
            q = f'{a}/{b}×{c_}/{d}＝？'; w = [x / y, F(a + c_, b + d), F(a * c_, b + d), c + F(1, b * d), F(a + c_, b * d), F(c.numerator + 1, c.denominator)]
            e = f'{{分母|ぶんぼ}}どうし、{{分子|ぶんし}}どうしを_かけます。{a * c_}/{b * d}' + (f'を_{{約分|やくぶん}}して_{fr(c)}。' if gcd(a * c_, b * d) != 1 else '。')
        return q, fr(c), [fr(v) for v in w if v > 0 and v != c], e
    G.many(40, fmul)
    G.unit('04')
    def fdiv():
        b = R.randint(2, 7); a = R.randint(1, b + 1); d = R.randint(2, 7); c_ = R.randint(1, d + 1)
        if gcd(a, b) != 1 or gcd(c_, d) != 1 or a == b or c_ == d: return None
        x, y = F(a, b), F(c_, d)
        if R.random() < 0.25:
            n = R.randint(2, 6); c = x / n; q = f'{a}/{b}÷{n}＝？'; w = [x * n, F(a, b + n), c + F(1, b * n), F(a + 1, b * n), F(n, a * b) if a * b != n else None]
            e = f'{{分母|ぶんぼ}}に_{{整数|せいすう}}を_かけます。{a}/{b * n}' + (f'を_{{約分|やくぶん}}して_{fr(c)}。' if gcd(a, b * n) != 1 else '。')
        else:
            c = x / y; q = f'{a}/{b}÷{c_}/{d}＝？'; w = [x * y, y / x, F(a + d, b + c_), c + F(1, b * c_), F(c.numerator + 1, c.denominator)]
            e = f'わる{{数|かず}}の_{{逆数|ぎゃくすう}}を_かけます。{a}/{b}×{d}/{c_}＝{a * d}/{b * c_}' + (f'＝{fr(c)}。' if gcd(a * d, b * c_) != 1 else '。')
        return q, fr(c), [fr(v) for v in w if v is not None and v > 0 and v != c], e
    G.many(40, fdiv)
    G.unit('05')
    def ratio():
        x = R.randint(1, 7); y = R.randint(1, 9)
        if gcd(x, y) != 1 or x == y: return None
        k = R.randint(2, 9)
        eq = lambda p, q_: p * y == q_ * x      # x:y と等しい比か
        if R.random() < 0.55:
            a, b = x * k, y * k
            w = [(y, x), (x + 1, y), (x, y + 1), (a - b if a > b else b - a, b), (x + 1, y + 1), (x * 2 + 1, y * 2)]
            return (f'{a}：{b}を_かんたんに_すると？', f'{x}：{y}', [f'{p}：{q_}' for p, q_ in w if p > 0 and q_ > 0 and not eq(p, q_)],
                    f'りょうほうを_{{最大公約数|さいだいこうやくすう}}の_{k}で_わります。')
        c = y * k; ans = x * k
        return (f'{x}：{y}＝x：{c}の_xに_あてはまる_{{数|かず}}は？', str(ans), ints(ans, [x + (c - y), c - x if c > x else c + x, ans + x, ans - x if ans > x else ans + 1, x + k, c * y // x if (c * y) % x == 0 else ans + 2]),
                f'{y}を_{k}{{倍|ばい}}すると_{c}。{x}も_{k}{{倍|ばい}}して_{ans}。')
    G.many(34, ratio)
    G.unit('07')
    def circle():
        r = R.choice([1, 2, 3, 4, 5, 10, 20]); P = F(314, 100)
        if R.random() < 0.6:
            c = r * r * P; w = [2 * r * P, r * P, 4 * r * r * P, r * r, c / 2, 2 * r * r * P]
            return (f'{{半径|はんけい}}が_{r}cmの_{{円|えん}}の_{{面積|めんせき}}は？', f'{dec(c)}cm²', [f'{dec(x)}cm²' for x in w if x != c],
                    f'{{半径|はんけい}}×{{半径|はんけい}}×3.14。{r}×{r}×3.14＝{dec(c)}。')
        d = 2 * r; c = r * r * P; w = [d * P, d * d * P, r * P, c * 2, d * d]
        return (f'{{直径|ちょっけい}}が_{d}cmの_{{円|えん}}の_{{面積|めんせき}}は？', f'{dec(c)}cm²', [f'{dec(x)}cm²' for x in w if x != c],
                f'{{半径|はんけい}}は_{r}cm。{r}×{r}×3.14＝{dec(c)}。')
    G.many(12, circle)
    G.unit('08')
    def vol():
        s = R.randint(4, 40); h = R.randint(2, 12); v = s * h
        if R.random() < 0.6:
            return (f'{{底面積|ていめんせき}}が_{s}cm²、{{高|たか}}さが_{h}cmの_{{角柱|かくちゅう}}の_{{体積|たいせき}}は？', f'{v}cm³', [f'{x}cm³' for x in ints(v, [s + h, v // 2 if v % 2 == 0 else v + s, v * 2, v + s, v - s])],
                    f'{{底面積|ていめんせき}}×{{高|たか}}さ。{s}×{h}＝{v}。')
        return (f'{{体積|たいせき}}が_{v}cm³で、{{底面積|ていめんせき}}が_{s}cm²の_{{角柱|かくちゅう}}の_{{高|たか}}さは？', f'{h}cm', [f'{x}cm' for x in ints(h, [v - s, h + 1, h - 1, h * 2, v + s, h + 2])],
                f'{{体積|たいせき}}÷{{底面積|ていめんせき}}。{v}÷{s}＝{h}。')
    G.many(14, vol)
    G.unit('09')
    def prop():
        if R.random() < 0.5:
            a = R.randint(2, 12); x = R.randint(2, 12); y = a * x
            return (f'y＝{a}×xで、xが_{x}の_ときの_yの_{{値|あたい}}は？', str(y), ints(y, [a + x, abs(a - x) or 1, y + a, y - a, int(str(a) + str(x))]), f'{a}×{x}＝{y}。')
        x = R.randint(2, 9); y = R.randint(2, 12); a = x * y
        if x == y: return None
        return (f'y＝{a}÷xで、xが_{x}の_ときの_yの_{{値|あたい}}は？', str(y), ints(y, [a * x, a - x, y + 1, y - 1, a + x, y + 2]), f'{a}÷{x}＝{y}。')
    G.many(18, prop)
    G.save()

if __name__ == '__main__':
    for f in (grade1, grade2, grade3, grade4, grade5, grade6): f()
