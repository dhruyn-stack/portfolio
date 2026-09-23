# AI-assisted title/abstract screening — validated on a published systematic review

**Result:** on a published systematic review, this first-pass screener kept **all 37 studies the review finally
included** (recall 100%, 95% CI 90.6–100%) and removed an estimated **75%** of records from manual reading.
Every record it keeps or marks "unsure" is still read by a medically trained human.

| | Result |
|---|---|
| Studies the review finally included, kept by the screener | **37 / 37** (95% CI 90.6–100%) |
| Excluded records correctly removed (random sample of 200) | 156 / 200 = 78.0% (95% CI 71.8–83.2%) |
| Estimated share of all 881 records removed from manual reading | **≈ 75%** |
| Records sent to the human as "unsure" | 7 |

## The benchmark
- Review: Meijboom RW, Gardarsdottir H, Egberts TCG, Giezen TJ. *Patients Retransitioning from Biosimilar TNFα
  Inhibitor to the Corresponding Originator After Initial Transitioning to the Biosimilar: A Systematic Review.*
  BioDrugs 2022;36:27–39 (PMID 34870802). The paper reports: "Of 994 screened publications, 37 were included."
- Data: the open SYNERGY study-selection dataset (`Meijboom_2021`, CC0, github.com/asreview/synergy-dataset):
  882 unique records, 37 labelled as final inclusions.
- Provenance check, done before any criteria were written: 32 of the 37 labelled inclusions appear in the paper's
  own reference list, so the labels really belong to this review.

## Method
1. Eligibility criteria were written from the paper's stated objective and methods **before** any record was
   screened, and frozen with checksums.
2. Recall-first decision rule: INCLUDE if a record could plausibly meet every criterion, UNSURE if information is
   missing, EXCLUDE only when a criterion clearly fails. INCLUDE and UNSURE both go to the human.
3. Model: `qwen3.8-27b` (via Groq), one record per call. 238 records had no abstract and were judged on title alone.
4. Evaluation set: all 37 inclusions plus a random sample of 200 of the 844 exclusions (fixed seed). Recall is
   exact for this review; specificity and workload are estimates from the sample.

## What went wrong on the way (kept on purpose)
- **A first attempt on a different benchmark was discarded.** Its labels turned out to belong to a different review
  question than the paper they were linked to (only 2 of that paper's 50 references were in the dataset). Scores on
  it measured the mismatch, not screening skill. The provenance check above exists because of that.
- **The model planned first could not run** (its free daily quota was used up by that first attempt). The switch to
  `qwen3.8-27b` and to the sampled design was recorded before this run started; prompt and criteria were unchanged.
- **A small local 7B model, run on all 881 records, kept only 30 of the 37 inclusions** (recall 81%). Model size
  matters for medical screening; the small model is not used for real work.

## Limits — read before relying on the number
- One review, one topic. It shows how this pipeline behaved here, not everywhere.
- With 37 inclusions the interval is wide: true recall could be as low as ~91%.
- For a new review the right practice is a pilot: screen your first ~100 records both ways, compare, then decide.
- The screener never decides alone and never writes review text.
