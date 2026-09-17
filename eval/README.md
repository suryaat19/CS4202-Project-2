# Evaluation harness (next)

Loads `data/<form>/*.jsonl`, renders prompts from `tasks/`, calls models, parses outputs,
scores with `verifiers/`, and writes `results/runs/<run_id>/`.
Track 0 = benchmark (no tools). Track I = inference-time interventions, reported separately.
