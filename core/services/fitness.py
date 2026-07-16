from core.services.combinations import gaps


def fitness(ch, est):
    ns, es = ch
    s = sum(ns)
    gs = gaps(ns)
    p = 30 if 110 <= s <= 160 else 15 if 90 <= s <= 170 else -20
    p += 20 if sum(n % 2 == 0 for n in ns) in (2, 3) else 0
    p += 20 if sum(n <= 25 for n in ns) in (2, 3) else 0
    p -= 35 if gs.count(1) >= 3 else 0
    p += 15 if len(set(gs)) >= 3 else 0
    p -= 15 if max(gs) > 25 else 0
    p += 2 * len(set(ns) & set(est['quentes'])) + len(set(ns) & set(est['frios']))
    return p
