# AI-assisted title/abstract screening — validated on two published systematic reviews

**Result:** on two published systematic reviews, this first-pass screener kept **37 of 37** and **30 of 33** of the
studies each review finally included. It removed an estimated 75% and 91% of records from manual reading.
The second result (recall 90.9%) is **below the ~95% recall usually required**, so on that review the screener could not be
the only screener: the excluded pile would need a human second screen. Every record it keeps or marks "unsure" is still
read by a medically trained human.

| | Review 1: Meijboom 2022 (biosimilars) | Review 2: van der Waal 2023 (older adults with cancer) |
|---|---|---|
| Included studies kept by the screener (recall) | **37 / 37 = 100%** (95% CI 90.6–100%) | **30 / 33 = 90.9%** (95% CI 76.4–96.9%) |
| Excluded records correctly removed (random sample of 200) | 156 / 200 = 78.0% (95% CI 71.8–83.2%) | 184 / 200 = 92.0% (95% CI 87.4–95.0%) |
| Estimated share of all records removed from manual reading | ≈ 75% of 881 | ≈ 91% of 1,962 |
| Records sent to the human as "unsure" | 7 | 16 |

## The benchmarks
- Review 1: Meijboom RW, Gardarsdottir H, Egberts TCG, Giezen TJ. *Patients Retransitioning from Biosimilar TNFα
  Inhibitor to the Corresponding Originator After Initial Transitioning to the Biosimilar: A Systematic Review.*
  BioDrugs 2022;36:27–39 (PMID 34870802). SYNERGY dataset `Meijboom_2021`: 882 unique records, 37 final inclusions.
- Review 2: van der Waal MS et al. *A meta-analysis on the role older adults with cancer favour in treatment decision
  making.* J Geriatr Oncol 2023;14(1):101383 (PMID 36243627). SYNERGY dataset `van_der_Waal_2022`: 1,962 records
  retrieved, 33 final inclusions.
- Data: the open SYNERGY study-selection collection (CC0, github.com/asreview/synergy-dataset).
- Provenance check, done before any criteria were written: the labelled inclusions were matched to each paper's own
  reference list (32 of 37 for review 1; 33 of 33 for review 2), so the labels really belong to these reviews.

## Method (identical for both reviews)
1. Eligibility criteria were written from the paper's stated objective and methods **before** any record was
   screened, and frozen with checksums in a timestamped log.
2. Recall-first decision rule: INCLUDE if a record could plausibly meet every criterion, UNSURE if information is
   missing, EXCLUDE only when a criterion clearly fails. INCLUDE and UNSURE both go to the human.
3. Model: `qwen3.8-27b` (via Groq), one record per call. Records without an abstract were judged on title alone.
4. Evaluation set: every included study plus a random sample of 200 excluded records (fixed seed). Recall is exact;
   specificity and workload are estimates from the sample.

## Why review 2 missed 3 studies
All three were qualitative studies. My pre-written criteria told the screener to exclude "purely qualitative" designs,
but the review's authors included them because they reported Control Preference Scale data. The criteria were frozen
before screening and were not changed afterwards, so 90.9% stands as the result. The lesson is about criteria as much as
the model: pilot the criteria on the first ~100 records before trusting any screener.

## What else went wrong on the way (kept on purpose)
- **A first attempt on a different benchmark was discarded.** Its labels do not match the paper they are linked to
  (only 2 of that paper's 50 references were in the dataset). The SYNERGY maintainers had already recorded this in
  their issue #163 and said they will exclude that dataset from the upcoming SYNERGY Plus release. The provenance check
  above exists because of it.
- **The model planned first could not run** (its free daily quota was used up by that first attempt). The switch to
  `qwen3.8-27b` and to the sampled design was recorded before review 1 was screened; prompt and criteria were unchanged.
- **A small local 7B model, run on all 881 records of review 1, kept only 30 of the 37 inclusions** (recall 81%).
  Model size matters for medical screening; the small model is not used for real work.

## Limits — read before relying on the numbers
- Two reviews, two topics. They show how this pipeline behaved here, not everywhere.
- With 33–37 inclusions per review the intervals are wide.
- For a new review the right practice is a pilot: screen your first ~100 records both ways, compare, then decide.
- The screener never decides alone and never writes review text.
