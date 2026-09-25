# Supplementary material — Outcome-Revealing Discourse Structure in Moroccan Cassation Rulings

Anonymised for review. Texts of the rulings are not redistributed.

## Files
- `collection_B_per_ruling_counts.csv` — one row per ruling of Collection B (144 pages: 104 commercial-chamber, 39 civil-chamber, 1 personal-status).
  Columns: portal reference (`ref`), the portal page of the ruling (`url`, so that each ruling can be opened and its counts checked against the text), decision number, date, file number, chamber, publisher outcome tag (`issue_site`),
  automatic label from the ruling formula (`issue_auto`), number of grounds markers, reply-marker counts under the
  published set (`pub`; `lakin` = the single connective alone; `lk2` = connective followed by the recital particle),
  the widened set (`wid`) and the widened-plus-closing set (`full`), body length in characters, and whether the
  opening formula and the ruling formula were located.
- `extract_collection_B.py` — reads the saved portal pages, cuts the editorial headnote and the ruling formula,
  applies the three marker sets and the labelling rule, writes the CSV above.
- `analyse.py` — recomputes the quantitative Collection B results reported in Tables XV–XVIII from the CSV: coverage per
  outcome class with Wilson intervals, content-free rule accuracy, confusion matrix, balanced accuracy, MCC.
- `collection_A_per_ruling_counts.csv` — one row per document of Collection A (178): whether the ruling formula was found, automatic label, grounds-marker count, reply-marker counts under the published, widened and repaired sets, paragraph and character counts, and whether the headnote contains an outcome word.
- `collection_A_manual_check.csv` — the stratified sample of 30 Collection A rulings read by one author, with the manual and automatic labels (30/30 agreement).
- `analyse_collection_A.py` — reproduces the quantitative results reported in Tables III–VIII and XI–XIV, the robustness check of Section VI-E and the headnote check of Section VI-F from plain-text exports of the .doc files: `python analyse_collection_A.py txt/`. Seeds: bootstrap 0, cross-validation 0-19, held-out split 5, random halves 0-19.
- `fulltext_classifiers.py` — reproduces Table IX (20 x stratified 5-fold CV, seeds 0-19) from plain-text exports of the Collection A documents.

## Source documents
- Collection A (178 .doc files) was retrieved in 2024 from the Adala portal of the Moroccan Ministry of Justice, whose jurisprudence section is no longer online. The rulings are public judicial decisions, anonymised at source; the files are not included here because their original terms of distribution cannot be verified now that the portal is offline. The authors can make them available to the editor for verification of the reported figures, on the same confidential basis as this review material.
- Collection B (144 pages) is available from jurisprudence.ma at the URL given for each ruling in `collection_B_per_ruling_counts.csv`, read from each page's canonical link. The pages are not included: the portal's terms of use permit research use but not redistribution. To re-run the extraction, save each page as HTML into a folder (file name = first 80 characters of the URL slug, as `extract_collection_B.py` expects; the portal blocks rapid automated requests, so download slowly or save the pages manually) and run the script on that folder; the authors verified before submission that this regenerates `collection_B_per_ruling_counts.csv` exactly.

## Reproduce
    pip install beautifulsoup4
    python extract_collection_B.py html/ > collection_B_per_ruling_counts.csv
    python analyse.py collection_B_per_ruling_counts.csv

Python 3.12 with beautifulsoup4, numpy, scipy, scikit-learn; no GPU. Text export of the .doc files: `soffice --headless --convert-to txt:Text --outdir txt *.doc`. The analysis scripts run in seconds; `fulltext_classifiers.py` takes a few minutes.
