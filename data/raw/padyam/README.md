# Raw padyam source

`padyalu_t1.tsv` — 4,651 padyams (columns `padyam_text`, `padyam_type`), from the
Chandassu dataset (Boddu Sri Pavan et al., MIT;
https://huggingface.co/datasets/BodduSriPavan111/chandassu). Kept as received.

Known issues (cleaned by `verifiers.padyam.normalize`, not in this file):
- 1,134 rows contain the Excel artifact `_x000D_`; 305 rows contain stray `\` before `న`.
- Line breaks are not paada breaks (most teytageethi rows have 2 lines; 165 seesamu rows have 1).
- **No `satakam` column.** Replace this file with a TSV export of the upstream CSV that keeps
  `satakam`; the builders read it automatically (column names are auto-detected).
