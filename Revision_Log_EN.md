# Revision Log

## Version
- Manuscript version: `v2026-04-20`
- Base file: `PAPER_EN.md`

## Summary of Modifications
1. Revised the manuscript title so that DDRE-33 is presented as the learning benchmark and AC-OPF is presented as a mapped-system validation layer.
2. Tightened the abstract, introduction, discussion, and conclusion so that mapped IEEE-30/118 AC-OPF evidence is presented as benchmark-scoped rather than as full DDRE-33 AC-OPF closure.
3. Added mechanism-level explanation for risk weighting, dual-layer library design, SHAP usage, and the KKT-inspired active-set proxy.
4. Clarified that OPF-reduction results from the fixed 18-scenario panel are benchmark-specific comparative evidence rather than repeated-sampling statistical dominance.
5. Added appendix-level literature-positioning, scope-alignment, and default-hyperparameter summaries.
6. Added `Outputs/tables/scope_alignment_summary.csv` and synchronized `literature_positioning_summary.csv`, `validation_scope_summary.csv`, and supporting files with the revised wording.
7. Rebuilt the response letter to address the reviewer-style reassessment in `demo17.md`.
8. Added a direct DDRE-33 radial branch-flow screening layer with synchronized tables and figure outputs.
9. Expanded the references supporting branch-flow/DistFlow-style future validation.
10. Added a four-draw repeated-sampling OPF-reduction robustness analysis with summary tables and figure outputs.
11. Emphasized the algorithmic innovation as a deep adaptation and integration of existing AI techniques specifically for physical power grid risks (Introduction, Conclusion).
12. Explicitly acknowledged PYPOWER convergence issues on complex distribution networks (e.g., case33bw) and positioned radial screening as a practical substitute, supported by IEEE-69 AC-OPF validation (Section 8.3).
13. Clarified that hyperparameters act as a robust, beginner-friendly "plug-and-play" recommendation (Section 8.2).
14. Highlighted the dual-layer structure as a safety net against out-of-distribution (OOD) extreme scenarios (Section 8.2).

## File-Level Change Reasons
- `PAPER_EN.md`: revised title, tightened claims, added appendix positioning/scope/parameter summaries, and clarified benchmark scope
- `Response_Letter_EN.md`: rebuilt point-by-point response around `demo17.md` and added DDRE-33 direct-validation evidence
- `Supplementary_Note_EN.md`: expanded validation-scope, scope-alignment, positioning, reproducibility notes, and DDRE-33 direct-validation notes
- `Revision_Tracking_Matrix_EN.md`: remapped reviewer concerns to the final revision actions
- `Outputs/tables/literature_positioning_summary.csv`: synchronized wording with the new literature-positioning summary
- `Outputs/tables/validation_scope_summary.csv`: synchronized validation hierarchy and remaining limitations, now including direct DDRE-33 screening
- `Outputs/tables/scope_alignment_summary.csv`: added explicit alignment between title scope, learning scope, validation scope, and claim boundary
- `Outputs/tables/default_hyperparameters.csv`: added explicit benchmark defaults for reproducibility
- `Outputs/tables/ddre33_scenario_physics.csv`: added scenario-level DDRE-33 radial screening metrics
- `Outputs/tables/ddre33_direct_validation.csv`: added summary comparison for direct DDRE-33 validation
- `Outputs/tables/ddre33_direct_validation_seed.csv`: added per-seed DDRE-33 validation comparison
- `Outputs/figures/ddre33_direct_validation.png`: added direct DDRE-33 validation figure
- `Outputs/tables/opf_case_results_repeated.csv`: added repeated-sampling OPF case results across stratified draws
- `Outputs/tables/opf_reduction_repeated_results.csv`: added repeated-sampling OPF reduction rows
- `Outputs/tables/opf_reduction_repeated_summary.csv`: added mean/std/95% CI summary for repeated-sampling OPF reduction
- `Outputs/tables/opf_reduction_repeated_best.csv`: added best repeated-sampling OPF reduction results by case and K
- `Outputs/figures/opf_reduction_repeated.png`: added repeated-sampling OPF reduction comparison figure

## Versioned Deliverables
- `PAPER_EN.md`
- `Response_Letter_EN.md`
- `Supplementary_Note_EN.md`
