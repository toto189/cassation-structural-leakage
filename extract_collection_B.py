"""Extract per-ruling structural counts from saved jurisprudence.ma pages (Collection B)."""
import sys, glob, re, csv, os
from bs4 import BeautifulSoup

def norm(t):
    t = re.sub(r'[\u064B-\u0652\u0640]', '', t)
    return (t.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي'))

def field(soup, lab):
    el = soup.find(string=lambda t, l=lab: t and t.strip() == l)
    if not el: return ""
    sib = el.parent.find_next_sibling()
    return sib.get_text(" ", strip=True) if sib else ""

START = re.compile(r'باسم جلاله الملك|وبعد المداوله طبقا للقانون|بناء علي مقال النقض|بناء علي العريضه')
GROUNDS = re.compile(r'في شان الوسيل|في شان السبب|حيث ينعي|حيث تنعي|حيث ينع|حيث تعيب|حيث يعيب')
LAKIN = re.compile(r'\bلكن\b')
LAKIN_HAYTH = re.compile(r'\bلكن[،,]?\s*(?:و)?(?:حيث|ف)')
PUBLISHED = re.compile(r'\bلكن\b|حيث عللت|حيث قضت')
WIDENED = re.compile(PUBLISHED.pattern + r'|\bحقا\b|\bمع ان\b|\bالا ان\b|\bوالحال ان\b|\bفي حين ان\b')
CLOSING = re.compile(r'عرض[هت]?\s*(?:قرارها|قراره|القرار)?\s*للنقض|انعدام التعليل|منعدم التعليل|ناقص التعليل|نقصان التعليل|'
                     r'فاسد التعليل|فساد التعليل|خارقا للفصل|خرقا للفصل|خارقا للماد|خرقا للماد|مخالفا للقانون|'
                     r'غير مرتكز علي اساس|منعدم الاساس|عدم ارتكازه علي اساس')
FULL = re.compile(WIDENED.pattern + '|' + CLOSING.pattern)
OUTCOMES = [("quashing", re.compile(r'بنقض|نقض\s*(?:الق?رار|الحكم)')),
            ("dismissal", re.compile(r'برفض\s*(?:الطلب|طلب)')),
            ("inadmissibility", re.compile(r'بعدم\s*قبول'))]

def process(path):
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    canon = soup.find("link", rel="canonical") or soup.find("meta", property="og:url")
    url = (canon.get("href") or canon.get("content")) if canon else ""
    h = soup.find(string=lambda t: t and "Texte intégral" in t)
    body = h.parent.find_next_sibling().get_text("\n", strip=True) if h else ""
    x = norm(body)
    s = START.search(x)
    corps = x[s.start():] if s else x                       # drop the editorial headnote
    ends = [m.start() for m in re.finditer(r'لهذه الاسباب', corps)]
    if not ends: ends = [m.start() for m in re.finditer(r'لاجله', corps)]
    cut = ends[-1] if ends else len(corps)                   # last occurrence: the ruling formula
    pre, post = corps[:cut], corps[cut:] if ends else corps[-600:]
    labels = [k for k, p in OUTCOMES if p.search(post)]
    kw = field(soup, "Mots clés")
    site = "Cassation" if re.search(r'\bCassation\b', kw) and "Rejet" not in kw else "Rejet" if "Rejet" in kw else ""
    return dict(ref=field(soup, "Réf"), url=url, decision=field(soup, "N° de décision"), date=field(soup, "Date de décision"),
                dossier=field(soup, "N° de dossier"), chambre=field(soup, "Chambre"), issue_site=site,
                issue_auto="/".join(labels), grounds=len(GROUNDS.findall(pre)), lakin=len(LAKIN.findall(pre)),
                lk2=len(LAKIN_HAYTH.findall(pre)), pub=len(PUBLISHED.findall(pre)), wid=len(WIDENED.findall(pre)),
                full=len(FULL.findall(pre)), chars=len(body), start_found=bool(s), end_formula=bool(ends))

if __name__ == "__main__":
    rows = [process(f) for f in sorted(glob.glob(os.path.join(sys.argv[1], "*.html")))]
    w = csv.DictWriter(sys.stdout, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
