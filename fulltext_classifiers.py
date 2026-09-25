"""Table IX: full-text reference classifiers on Collection A, 20 x stratified 5-fold CV (seeds 0-19).
Usage: python fulltext_classifiers.py lr|svm full|masked   (run from the folder containing txt/ exports of the .doc files)"""
import glob,re,numpy as np,sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score,f1_score
def N(t): return re.sub(r'[\u064B-\u0652\u0640]','',t).replace('أ','ا').replace('إ','ا').replace('آ','ا')
START=re.compile(r'باسم جلالة الملك|و?\s*بعد المداولة طبقا للقانون')
OUT=[("q",re.compile(r'بنقض|نقض\s*(?:الق?رار|الحكم)')),("d",re.compile(r'برفض\s*(?:الطلب|طلب)')),("i",re.compile(r'بعدم\s*قبول'))]
MASK=re.compile(r'\bلكن\b|حيث عللت|حيث قضت|\bحقا\b|\bمع ان\b|\bالا ان\b|\bوالحال ان\b|\bفي حين ان\b|عرض[ةه]?\s*(?:قرارها|قراره|القرار)?\s*للنقض|انعدام\s*التعليل|منعدم التعليل|ناقص التعليل|نقصان\s*التعليل|فاسد التعليل|فساد\s*التعليل|خارقا للفصل|خرقا للفصل|مخالفا للقانون|غير مرتكز على اساس|منعدم الاساس|يتعين\s*نقض|واجب\s*النقض')
which=sys.argv[1]; masked=sys.argv[2]=='masked'
X=[];y=[]
for f in sorted(glob.glob('txt/*.txt')):
    x=N(open(f,encoding='utf-8',errors='replace').read()); s=START.search(x); corps=x[s.start():] if s else x
    ends=[m.start() for m in re.finditer(r'لهذه الاسباب',corps)] or [m.start() for m in re.finditer(r'لاجله',corps)]
    if not ends: continue
    pre,post=corps[:ends[-1]],corps[ends[-1]:]
    h=[k for k,p in OUT if p.search(post)]
    if h in (['q'],['d']): X.append(MASK.sub(' ',pre) if masked else pre); y.append(h[0])
y=np.array(y)
model=(lambda: make_pipeline(TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True),LogisticRegression(max_iter=3000,class_weight='balanced'))) if which=='lr' else (lambda: make_pipeline(TfidfVectorizer(analyzer='char_wb',ngram_range=(2,5),min_df=2,sublinear_tf=True),LinearSVC(class_weight='balanced')))
accs=[];f1s=[]
for seed in range(20):
    skf=StratifiedKFold(5,shuffle=True,random_state=seed); pa=np.empty(len(X),dtype=object)
    for tr,te in skf.split(X,y):
        m=model(); m.fit([X[i] for i in tr],y[tr]); pa[te]=m.predict([X[i] for i in te])
    accs.append(accuracy_score(y,pa)); f1s.append(f1_score(y,pa,average='macro'))
print(f"{which:3s} {sys.argv[2]:6s} n={len(X)} d={(y=='d').sum()} acc {100*np.mean(accs):.1f} ± {100*np.std(accs):.1f}  F1 {100*np.mean(f1s):.1f} ± {100*np.std(f1s):.1f}")
