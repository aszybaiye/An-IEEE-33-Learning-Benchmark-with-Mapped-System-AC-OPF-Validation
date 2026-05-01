# Response Letter to Reviewer-Style Evaluation in `demo17.md`

## Manuscript
- Title: Adaptive Risk-Aware and Explainable Typical-Day Library Learning for Transferable Renewable Dispatch: An IEEE-33 Learning Benchmark with Mapped-System AC-OPF Validation
- Revised manuscript: `PAPER_EN.md`
- Supplementary note: `Supplementary_Note_EN.md`
- Revision tracking matrix: `Revision_Tracking_Matrix_EN.md`
- Review note addressed: `demo17.md`

## Overall Response
We sincerely thank the reviewer for the detailed and constructive evaluation. Following the reviewer-style reassessment in `demo17.md`, we performed a further systematic revision focused on title-scope alignment, claim discipline, methodological positioning, reproducibility clarity, and reviewer traceability. The revised manuscript now makes the validation hierarchy explicit, adds a direct DDRE-33 radial branch-flow screening layer, clarifies why the AC-OPF benchmark on IEEE-30 and IEEE-118 is informative but not equivalent to a full AC distribution OPF on DDRE-33, tightens the interpretation of OPF-reduction results obtained from a fixed stratified benchmark panel, sharpens the novelty statement around methodological coordination rather than primitive novelty, revises the title so that it no longer over-implies DDRE-33 physical closure, adds appendix-level scope-alignment, literature-positioning, and default-hyperparameter summaries, updates supporting output tables to match the new wording, and synchronizes all reviewer-facing files.

## Point-by-Point Responses

### Comment 1: Physical validation is still not fully closed on the core DDRE-33 application object
Response: We agree that the strongest remaining limitation is the lack of a direct AC distribution OPF implementation on DDRE-33 itself. In the present revision, however, we no longer leave the native-feeder concern unanswered. We added a direct DDRE-33 radial branch-flow screening layer using the standard 33-bus topology and the actual MW renewable trajectories at buses 18, 22, 25, and 33. This new layer evaluates daily minimum voltage, maximum branch loading, daily feeder loss, and feasible-step share, and shows that the proposed dual-layer library yields the lowest daily minimum-voltage MAE and the lowest daily-loss MAE among all tested representative libraries. At the same time, we did not overstate this new layer as if it were already a full AC distribution OPF. The manuscript now makes the validation hierarchy explicit throughout: the DDRE-33 radial screen directly checks native-feeder stress preservation, while the IEEE-30/118 AC-OPF study remains a benchmark bridge from DDRE-derived scenario compression to explicit optimization constraints rather than a claim of full DDRE-33 AC-OPF closure. We also retained forward-looking language pointing to direct DDRE-33 AC distribution OPF or control-aware branch-flow/DistFlow validation as the next step.

Locations:
- `PAPER_EN.md`, Abstract
- `PAPER_EN.md`, Section 3
- `PAPER_EN.md`, Section 5.2
- `PAPER_EN.md`, Section 7.1
- `PAPER_EN.md`, Section 8.3
- `PAPER_EN.md`, Section 7.2
- `PAPER_EN.md`, Section 8.4
- `PAPER_EN.md`, Section 8.6
- `PAPER_EN.md`, Section 10
- `Outputs/tables/validation_scope_summary.csv`

Supporting outputs:
- `Outputs/tables/ddre33_direct_validation.csv`
- `Outputs/tables/ddre33_direct_validation_seed.csv`
- `Outputs/tables/ddre33_scenario_physics.csv`
- `Outputs/figures/ddre33_direct_validation.png`
- `Outputs/tables/opf_case_summary.csv`
- `Outputs/tables/validation_scope_summary.csv`
- `Outputs/figures/opf_case_validation.png`

### Comment 2: The manuscript should explain why mapped IEEE-system AC-OPF evidence is still meaningful
Response: We strengthened this justification in both the method and experimental sections. The revised text now explains that standard IEEE systems provide transparent executable constraints, while DDRE-derived injections preserve the renewable-statistical structure of the learned scenarios. This makes the benchmark stronger than proxy-only validation, but still subordinate to future direct distribution-level validation. The revised wording is intentionally calibrated to prevent overclaiming.

Locations:
- `PAPER_EN.md`, Section 5.2
- `PAPER_EN.md`, Section 6.2
- `PAPER_EN.md`, Section 7.2
- `PAPER_EN.md`, Section 8.4

### Comment 3: OPF-reduction evidence is informative but not statistically exhaustive
Response: We agree, and in this revision we moved beyond a single deterministic panel. We retained the original fixed stratified benchmark for exact reproducibility, but we additionally ran four repeated stratified draws with seeds 2026-2029 and summarized the OPF-reduction results with mean, standard deviation, and 95% confidence intervals. The repeated-sampling summaries are now provided in `Outputs/tables/opf_reduction_repeated_summary.csv` and `Outputs/tables/opf_reduction_repeated_best.csv`, and the manuscript discussion has been updated accordingly. The new results show that reduced scenario sets still approximate full AC-OPF behavior with low error, while also making clear that the strongest OPF-driven advantage appears only in part of the design space rather than as universal dominance. We therefore revised the wording from single-panel benchmark evidence to statistically strengthened but still benchmark-bounded comparative evidence.

Locations:
- `PAPER_EN.md`, Section 7.4
- `PAPER_EN.md`, Section 8.5
- `PAPER_EN.md`, Section 8.6
- `PAPER_EN.md`, Section 10
- `Outputs/tables/validation_scope_summary.csv`
- `Outputs/tables/opf_reduction_repeated_results.csv`
- `Outputs/tables/opf_reduction_repeated_summary.csv`
- `Outputs/tables/opf_reduction_repeated_best.csv`
- `Outputs/figures/opf_reduction_repeated.png`

### Comment 4: Methodological novelty remains integration-oriented and needs sharper positioning
Response: We accepted this point and sharpened the manuscript in two ways. First, we added explicit mechanism-oriented explanation for why risk weighting and the dual-layer library are needed beyond pure clustering quality: the risk term shifts representation pressure toward dispatch-difficult days, and the dual-layer library protects rare but operationally important tail scenarios from being absorbed into normal clusters. Second, we added a compact literature-positioning summary in the appendix and synchronized `Outputs/tables/literature_positioning_summary.csv` so that the reader can see more clearly how this work differs from geometry-oriented aggregation, problem-driven reduction, and direct OPF learning. The revised novelty statement emphasizes coordinated use and transparent boundaries rather than primitive novelty.

Locations:
- `PAPER_EN.md`, Section 3
- `PAPER_EN.md`, Section 4
- `PAPER_EN.md`, Section 5.1
- `PAPER_EN.md`, Appendix B / Table A1
- `PAPER_EN.md`, Section 10
- `Outputs/tables/literature_positioning_summary.csv`

### Comment 5: The role of SHAP and the KKT-inspired selector should be stated more precisely
Response: We revised the manuscript to clarify that SHAP is used as a diagnostic consistency check rather than an optimization variable in the learning objective. We also clarified that `opf_kkt_active_set` is KKT-inspired rather than exact-dual-driven, because it groups near-binding constraint signatures as a practical active-set proxy rather than clustering exact dual multipliers. These two edits aim to improve methodological precision and prevent interpretive ambiguity.

Locations:
- `PAPER_EN.md`, Section 5.3
- `PAPER_EN.md`, Section 6.2
- `PAPER_EN.md`, Section 8.2

### Comment 6: The paper should distinguish more clearly between application scope and front-end scenario-management scope
Response: We revised the introduction, practical-impact section, and conclusion so that the paper is presented more clearly as an interpretable and updateable scenario-management front end for renewable dispatch. The new wording makes clear that the method is not positioned as a universal solver-facing replacement. This reduces tension between the DDRE-33-centered learning narrative and the mapped IEEE-system validation layer.

Locations:
- `PAPER_EN.md`, Section 3
- `PAPER_EN.md`, Section 8.6
- `PAPER_EN.md`, Section 9
- `PAPER_EN.md`, Section 10

### Comment 7: The title still creates tension with the validation object and should better reflect the actual evidence scope
Response: We accepted this point and revised the title to reduce the implied mismatch between the DDRE-33 learning benchmark and the mapped IEEE-system AC-OPF validation layer. The new title explicitly identifies DDRE-33 as the learning benchmark and AC-OPF as a mapped-system validation layer. We also added an appendix scope-alignment summary and a synchronized output table so that the title scope, learning scope, validation scope, and evidence boundary are visible in one place.

Locations:
- `PAPER_EN.md`, Title
- `PAPER_EN.md`, Section 3
- `PAPER_EN.md`, Section 7.1
- `PAPER_EN.md`, Appendix B / Table A3
- `Outputs/tables/scope_alignment_summary.csv`

### Comment 8: Data presentation and reproducibility should be easier to audit
Response: We added appendix-level positioning and default-hyperparameter summaries so that key benchmark settings do not remain scattered across the paper. We also created a new output table, `Outputs/tables/default_hyperparameters.csv`, and referenced it directly in the DDRE benchmark subsection and appendix. This revision complements the existing confidence intervals, convergence discussion, and reproducibility package by making the current release easier to inspect and reproduce.

Locations:
- `PAPER_EN.md`, Section 7.1
- `PAPER_EN.md`, Appendix A
- `PAPER_EN.md`, Appendix B / Table A2
- `Outputs/tables/default_hyperparameters.csv`

### Comment 9: Discussion, conclusion, and reviewer-facing materials should be more explicit and synchronized
Response: We rewrote the discussion and conclusion once more to align the evidence boundary with the claims, and we synchronized all supporting files accordingly. `Supplementary_Note_EN.md` now explains the expanded validation hierarchy, including the direct DDRE-33 radial screening layer, the repeated-sampling OPF-reduction summary, the scope-alignment aid, the literature-positioning aid, benchmark-specific interpretation, and parameter-summary files. `Revision_Tracking_Matrix_EN.md` and `Revision_Log_EN.md` have been updated to reflect the present revision round and to document the newly added DDRE-33 validation outputs, repeated-sampling OPF outputs, appendix wording changes, and output-table changes.

Locations:
- `PAPER_EN.md`, Section 8.6
- `PAPER_EN.md`, Section 10
- `PAPER_EN.md`, Appendix A-C
- `Supplementary_Note_EN.md`
- `Revision_Tracking_Matrix_EN.md`
- `Revision_Log_EN.md`
- `Outputs/tables/ddre33_direct_validation.csv`
- `Outputs/figures/ddre33_direct_validation.png`
- `Outputs/tables/scope_alignment_summary.csv`
- `Outputs/tables/opf_reduction_repeated_summary.csv`
- `Outputs/tables/opf_reduction_repeated_best.csv`

## Closing Statement
We believe the revised manuscript now responds to the reviewer’s concerns in a more disciplined and transparent way. The paper does not claim to have solved every remaining limitation; instead, it now states those limitations directly while sharpening the justification, positioning, and reproducibility of the current contribution. In particular, the package now includes both a direct DDRE-33 radial screening layer and a mapped-system AC-OPF layer, which together improve operational grounding without overstating the present scope. The manuscript, appendix, output tables, supplementary note, tracking matrix, and revision log have all been synchronized to reflect this final scope.
