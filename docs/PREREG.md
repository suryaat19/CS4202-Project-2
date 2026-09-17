# Pre-registration (DRAFT — not frozen)

Freeze before any full model run: set the status line, commit, and record the hash here.

Status: draft · Frozen at commit: —

## Hypotheses
- **H1a** For form *f* and class *c*: V(f,c) < G(f,c) and L(f,c) < V(f,c), where G = generation
  satisfaction rate, V = chance-corrected detection (d′; 2·(BA−0.5) secondary),
  L = localisation accuracy.
- **H1b** On its own GENERATE outputs, a model's VERIFY verdicts agree with the verifier less
  often than on constructed items; the dominant error is accepting its own invalid outputs.
- **H2** Difficulty ranks by constraint class, not resource level; within padyam,
  seq-choice meters are easier to generate than seq-fixed.
- **H3** REPAIR is hardest for every form; oracle-location repair > location-withheld repair.

## Metrics
VERIFY: d′, false-alarm rate, balanced accuracy, localisation accuracy (on correct rejections),
stratified by attested word, meter class, edit direction.
GENERATE: strict validity (greedy, valid@5 at T=0.7), per-class satisfaction, graded form score,
memorisation flag, OOV rate.
REPAIR: validity, normalised edit distance, meaning preservation, over-repair rate, oracle gap.

## Analysis plan
To be written before freeze (models, protocols, tests, CIs, multiple-comparison handling).
