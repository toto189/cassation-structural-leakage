"""Recompute the Collection B tables of the paper (Tables XV to XVIII) from the per-ruling counts."""
import sys, csv, math

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n; c = (p + z*z/(2*n)) / d
    h = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (100*(c-h), 100*(c+h))

def report(S, name):
    D = [r for r in S if r['issue_auto'] == 'dismissal']; Q = [r for r in S if r['issue_auto'] == 'quashing']
    print(f"\n{name}: n={len(S)} dismissals={len(D)} quashings={len(Q)} majority={100*len(D)/len(S):.1f}")
    for k, lab in [('lakin', 'published (lakin)'), ('lk2', 'lakin + recital particle'), ('pub', 'published, all three'),
                   ('wid', 'widened'), ('full', 'widened + closing')]:
        cd = sum(1 for r in D if int(r[k]) > 0); cq = sum(1 for r in Q if int(r[k]) > 0)
        acc = sum(1 for r in S if (int(r[k]) == 0) == (r['issue_auto'] == 'quashing'))
        print(f"  {lab:26s} coverage dism {100*cd/len(D):5.1f} [{wilson(cd,len(D))[0]:.1f},{wilson(cd,len(D))[1]:.1f}]"
              f"  quash {100*cq/len(Q):5.1f} [{wilson(cq,len(Q))[0]:.1f},{wilson(cq,len(Q))[1]:.1f}]"
              f"  rule accuracy {100*acc/len(S):5.1f} [{wilson(acc,len(S))[0]:.1f},{wilson(acc,len(S))[1]:.1f}]")
    for col, lab in [('pub', 'published set, three connectives'), ('lakin', 'principal connective alone')]:
      tp = sum(1 for r in D if int(r[col]) > 0); fn = len(D) - tp
      fp = sum(1 for r in Q if int(r[col]) > 0); tn = len(Q) - fp
      sens = tp/(tp+fn); spec = tn/(tn+fp); den = (tp+fp)*(tp+fn)*(tn+fp)*(tn+fn)
      mcc = (tp*tn - fp*fn) / math.sqrt(den) if den else 0.0
      print(f"  confusion ({lab}): {tp} {fn} / {fp} {tn}; sensitivity {100*sens:.1f} specificity {100*spec:.1f}"
            f" balanced accuracy {50*(sens+spec):.1f} MCC {mcc:.3f}")
    g = [r for r in S if int(r['grounds']) > 0]
    print(f"  grounds marker located: dismissals {sum(1 for r in g if r['issue_auto']=='dismissal')} quashings {sum(1 for r in g if r['issue_auto']=='quashing')}")
    print(f"  mean grounds dism/quash {sum(int(r['grounds']) for r in D)/len(D):.2f} / {sum(int(r['grounds']) for r in Q)/len(Q):.2f};"
          f" mean replies {sum(int(r['lakin']) for r in D)/len(D):.2f} / {sum(int(r['lakin']) for r in Q)/len(Q):.2f}")
    tags = [r for r in S if r['issue_site'] in ('Rejet', 'Cassation')]
    ok = sum(1 for r in tags if (r['issue_site'] == 'Rejet') == (r['issue_auto'] == 'dismissal'))
    print(f"  publisher tags: {ok}/{len(tags)} agree with the automatic label")

rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8')))
for r in rows:  # accept either the Arabic labels of the working CSV or the English ones
    r['issue_auto'] = {'نقض': 'quashing', 'رفض': 'dismissal'}.get(r['issue_auto'], r['issue_auto'])
binary = [r for r in rows if r['issue_auto'] in ('dismissal', 'quashing')]
report([r for r in binary if r['chambre'] == 'Commerciale'], "Commercial chamber")
report([r for r in binary if r['chambre'] == 'Civile'], "Civil chamber")
