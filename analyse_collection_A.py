"""Reproduce the Collection A tables of the paper from plain-text exports of the 178 .doc files.
Usage: python analyse_collection_A.py txt/
Tables III (coverage), IV (grounds-located), V (content-free classification), VI (confusion), VII/VIII (alternation),
XI/XII (widened set), XIII (per-connective), XIV (three marker sets), VI-E robustness across splits, VI-F headnote."""
import glob, re, os, sys, collections, math, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import accuracy_score, f1_score
from scipy.stats import fisher_exact, chi2_contingency

def N(t): return re.sub(r'[\u064B-\u0652\u0640]', '', t)          # diacritics and tatweel only
END = re.compile(r'ل[أا]جله|لهذه ال[أا]سباب')                       # ruling formula: first occurrence
OUT = [("quashing", re.compile(r'بنقض')), ("dismissal", re.compile(r'ب?رفض\s*الطلب')), ("inadmissibility", re.compile(r'ب?عدم\s*قبول'))]
HEAD = re.compile(r'باسم جلالة الملك')
GROUNDS = re.compile(r'في ش[أا]ن الوسيل|حيث ينعى')
CONN = {'lakin': r'\bلكن\b', 'hayth allalat': r'حيث عللت', 'hayth qadat': r'حيث قضت',
        'haqqan': r'\bحقا\b', 'maa anna': r'\bمع [أا]ن\b', 'illa anna': r'[إا]لا [أا]ن\b',
        'wal hal anna': r'والحال [أا]ن\b', 'fi hin anna': r'في حين [أا]ن\b'}
PUBLISHED = re.compile('|'.join(CONN[k] for k in ['lakin', 'hayth allalat', 'hayth qadat']))
WIDENED = re.compile('|'.join(CONN.values()))
CLOSING = re.compile(r'عرض[ةه]?\s*للنقض|انعدام\s*التعليل|فساد\s*التعليل|فاسد\s*التعليل|نقصان\s*التعليل|يتعين\s*نقض|مخالف[ةا]?\s*(?:لل)?قانون')
REPAIRED = re.compile(WIDENED.pattern + '|' + CLOSING.pattern)
HEADWORD = re.compile(r'رفض الطلب|\bنقض\b|عدم قبول')

rows = []
for f in sorted(glob.glob(os.path.join(sys.argv[1], '*.txt'))):
    x = N(open(f, encoding='utf-8', errors='replace').read()); e = END.search(x)
    if not e: continue
    labels = [k for k, p in OUT if p.search(x[e.start():])]
    if len(labels) != 1: continue
    body = x[:e.start()]; h = HEAD.search(body); headnote = body[:h.start()] if h else ''
    rows.append(dict(id=os.path.basename(f), y=labels[0], grounds=len(GROUNDS.findall(body)),
                     pub=len(PUBLISHED.findall(body)), wid=len(WIDENED.findall(body)), rep=len(REPAIRED.findall(body)),
                     paras=body.count('\n') + 1, chars=len(body), headword=bool(HEADWORD.search(headnote)),
                     conn={k: len(re.findall(p, body)) for k, p in CONN.items()}))
B = [r for r in rows if r['y'] in ('dismissal', 'quashing')]
D = [r for r in B if r['y'] == 'dismissal']; Q = [r for r in B if r['y'] == 'quashing']
y = np.array([r['y'] == 'quashing' for r in B])   # True = quashing
nd, nq, n = len(D), len(Q), len(B)
print(f"labelled {len(rows)}: dismissal {nd}, quashing {nq}, inadmissibility {len(rows)-n}; binary n = {n}, majority {100*nd/n:.1f}")

def wilson(k, m, z=1.96):
    p = k/m; d = 1+z*z/m; c = (p+z*z/(2*m))/d; h = z*math.sqrt(p*(1-p)/m+z*z/(4*m*m))/d
    return f"{100*p:.1f} [{100*(c-h):.1f}, {100*(c+h):.1f}]"
def boot(pred, B_=5000, seed=0):
    rng = np.random.default_rng(seed); accs = []; f1s = []
    for _ in range(B_):
        i = rng.integers(0, n, n); accs.append(accuracy_score(y[i], pred[i])); f1s.append(f1_score(y[i], pred[i], average='macro'))
    return f"{100*accuracy_score(y,pred):.1f} [{100*np.percentile(accs,2.5):.1f}, {100*np.percentile(accs,97.5):.1f}]  macro-F1 {100*f1_score(y,pred,average='macro'):.1f} [{100*np.percentile(f1s,2.5):.1f}, {100*np.percentile(f1s,97.5):.1f}]"

print("\n-- Table III / XI / XIV: coverage per class (Wilson)")
for k, lab in [('pub', 'published'), ('wid', 'widened'), ('rep', 'widened + closing')]:
    cd = sum(1 for r in D if r[k] > 0); cq = sum(1 for r in Q if r[k] > 0)
    rule = np.array([r[k] == 0 for r in B])
    print(f"  {lab:18s} dismissal {wilson(cd, nd):22s} quashing {wilson(cq, nq):22s} rule {boot(rule)}")
print("  grounds marker    dismissal", wilson(sum(1 for r in D if r['grounds'] > 0), nd), "quashing", wilson(sum(1 for r in Q if r['grounds'] > 0), nq))
gl = [r for r in B if r['grounds'] > 0]
print(f"-- Table IV: grounds located: dismissals {sum(1 for r in gl if r['y']=='dismissal')} with reply {sum(1 for r in gl if r['y']=='dismissal' and r['pub']>0)}; quashings {sum(1 for r in gl if r['y']=='quashing')} with reply {sum(1 for r in gl if r['y']=='quashing' and r['pub']>0)}")

print("\n-- Table V: content-free classification")
print("  majority       ", boot(np.zeros(n, bool)))
def cv20(X):
    accs = []; f1s = []
    for seed in range(20):
        pred = np.empty(n, bool)
        for tr, te in StratifiedKFold(5, shuffle=True, random_state=seed).split(X, y):
            m = LogisticRegression(class_weight='balanced', max_iter=2000).fit(X[tr], y[tr]); pred[te] = m.predict(X[te])
        accs.append(accuracy_score(y, pred)); f1s.append(f1_score(y, pred, average='macro'))
    return f"{100*np.mean(accs):.1f} ± {100*np.std(accs):.1f}  macro-F1 {100*np.mean(f1s):.1f} ± {100*np.std(f1s):.1f}"
print("  length only    ", cv20(np.array([[r['chars']] for r in B], float)))
print("  4 counts       ", cv20(np.array([[r['grounds'], r['pub'], r['paras'], r['chars']] for r in B], float)))
rule = np.array([r['pub'] == 0 for r in B])
tp = sum(1 for r in D if r['pub'] > 0); fn = nd-tp; fp = sum(1 for r in Q if r['pub'] > 0); tn = nq-fp
sens = tp/nd; spec = tn/nq; mcc = (tp*tn-fp*fn)/math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))
OR, p = fisher_exact([[tp, fn], [fp, tn]]); chi2, _, _, _ = chi2_contingency([[tp, fn], [fp, tn]], correction=False)
print(f"-- Table VI: confusion {tp} {fn} / {fp} {tn}; sensitivity {100*sens:.1f} specificity {100*spec:.1f} balanced {50*(sens+spec):.1f} MCC {mcc:.3f}; Fisher OR {OR:.1f} p {p:.1e}; chi2 {chi2:.1f} phi {math.sqrt(chi2/n):.3f}")
Xtr, Xte, ytr, yte = train_test_split(np.arange(n), y, test_size=0.30, stratify=y, random_state=5)
pr = rule[Xte]; print(f"-- held-out 70/30 (seed 5): n_test {len(Xte)}, accuracy {100*accuracy_score(yte,pr):.1f}, macro-F1 {100*f1_score(yte,pr,average='macro'):.1f}")

print("\n-- Tables VII/VIII: alternation")
print(f"  grounds D/Q {sum(r['grounds'] for r in D)} {sum(r['grounds'] for r in Q)}; replies (published) {sum(r['pub'] for r in D)} {sum(r['pub'] for r in Q)}; replies (widened) {sum(r['wid'] for r in D)} {sum(r['wid'] for r in Q)}")
print("  replies per ruling D", dict(collections.Counter(min(r['pub'], 4) for r in D)), "Q", dict(collections.Counter(min(r['pub'], 4) for r in Q)))
print("\n-- Table XIII: each connective alone (coverage D, Q, rule accuracy)")
for k in CONN:
    cd = sum(1 for r in D if r['conn'][k] > 0); cq = sum(1 for r in Q if r['conn'][k] > 0)
    acc = sum(1 for r in B if (r['conn'][k] == 0) == (r['y'] == 'quashing'))
    print(f"  {k:14s} {100*cd/nd:5.1f} {100*cq/nq:5.1f} {100*acc/n:5.1f}")
print("\n-- VI-E robustness: repaired set on 20 random halves")
covs = []; accs = []
for seed in range(20):
    _, te = train_test_split(np.arange(n), test_size=0.5, stratify=y, random_state=seed)
    covs.append(np.mean([B[i]['rep'] > 0 for i in te if y[i]])); accs.append(np.mean([(B[i]['rep'] == 0) == y[i] for i in te]))
print(f"  quashing coverage {100*np.mean(covs):.1f} ± {100*np.std(covs):.1f}; rule accuracy {100*np.mean(accs):.1f} ± {100*np.std(accs):.1f}")
hw = sum(1 for r in B if r['headword']); print(f"\n-- VI-F headnote: {100*hw/n:.1f} per cent of headnotes contain an outcome word")
