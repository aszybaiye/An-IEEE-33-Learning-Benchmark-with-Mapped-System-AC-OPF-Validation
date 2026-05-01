# Supplementary Note for the Revised Manuscript

## S1. Validation Scope
The revised package now contains four validation layers:

1. DDRE-33 representative-day learning validation  
   - outputs: `main_results.csv`, `main_results_with_ci.csv`, `ablation_results.csv`, `generalization_results.csv`
2. Feeder-aware dispatch-cost surrogate validation  
   - outputs: `physical_dispatch_results.csv`, `physical_dispatch_validation.png`
3. Direct DDRE-33 radial branch-flow screening  
   - outputs: `ddre33_scenario_physics.csv`, `ddre33_direct_validation.csv`, `ddre33_direct_validation_seed.csv`, `ddre33_direct_validation.png`
4. Explicit AC-OPF validation on mapped standard systems  
   - outputs: `opf_case_summary.csv`, `opf_case_results.csv`, `opf_reduction_results.csv`, `opf_best_methods.csv`, `opf_case_validation.png`, `opf_reduction_comparison.png`
5. Repeated-sampling OPF-reduction robustness analysis  
   - outputs: `opf_case_results_repeated.csv`, `opf_reduction_repeated_results.csv`, `opf_reduction_repeated_summary.csv`, `opf_reduction_repeated_best.csv`, `opf_reduction_repeated.png`

The first layer validates learning quality, the second adds feeder-oriented operational evidence, the third directly screens DDRE-33 feeder stress on the native 33-bus topology, the fourth verifies reduced scenario sets under full AC-OPF constraints on IEEE-30 and IEEE-118 with DDRE-derived injections, and the fifth adds repeated-sampling uncertainty summaries for the OPF reduction comparison. The third layer materially narrows the native-feeder evidence gap, but it is still a branch-flow-style security screen rather than a control-aware AC distribution OPF. The fourth layer is intentionally described as a benchmark bridge to explicit optimization constraints, not as a full AC distribution OPF closure on DDRE-33 itself. The fifth layer strengthens robustness claims but still remains benchmark-bounded because it is based on repeated stratified draws under the same released benchmark design. The current validation hierarchy is summarized in `Outputs/tables/validation_scope_summary.csv`.

## S2. Literature Positioning
The revised manuscript distinguishes four families of related work:

- geometry-oriented representative-day methods
- problem-driven scenario reduction
- direct data-driven OPF or scheduling surrogates
- interpretable and continual-learning-enhanced representative libraries

The present work now sits between geometry-oriented learning and OPF-coupled validation. It is not a full replacement for multiperiod OPF, but it is more operationally grounded than purely geometric compression because reduced scenario sets are tested through explicit AC-OPF.

To make this boundary easier to inspect, the package includes `Outputs/tables/literature_positioning_summary.csv`, which condenses the relationship between geometry-oriented representative-day learning, problem-driven scenario reduction, direct OPF learning, and the present dispatch-facing front-end formulation.

The package also includes `Outputs/tables/scope_alignment_summary.csv`, which aligns the revised title, the DDRE-33 learning benchmark, the mapped IEEE-system AC-OPF validation layer, and the paper-level claim boundary in one compact view.

## S3. Key New Files
- `Outputs/tables/main_results_with_ci.csv`
- `Outputs/tables/opf_case_summary.csv`
- `Outputs/tables/opf_reduction_results.csv`
- `Outputs/tables/opf_best_methods.csv`
- `Outputs/tables/literature_positioning_summary.csv`
- `Outputs/tables/validation_scope_summary.csv`
- `Outputs/tables/default_hyperparameters.csv`
- `Outputs/tables/scope_alignment_summary.csv`
- `Outputs/tables/ddre33_scenario_physics.csv`
- `Outputs/tables/ddre33_direct_validation.csv`
- `Outputs/tables/ddre33_direct_validation_seed.csv`
- `Outputs/tables/opf_case_results_repeated.csv`
- `Outputs/tables/opf_reduction_repeated_results.csv`
- `Outputs/tables/opf_reduction_repeated_summary.csv`
- `Outputs/tables/opf_reduction_repeated_best.csv`
- `Outputs/figures/ddre33_direct_validation.png`
- `Outputs/figures/opf_case_validation.png`
- `Outputs/figures/opf_reduction_comparison.png`
- `Outputs/figures/opf_reduction_repeated.png`
- `Revision_Tracking_Matrix_EN.md`
- `Revision_Log_EN.md`

## S4. Benchmark Notes
The direct DDRE-33 radial screening layer uses the standard 33-bus radial topology together with the actual MW renewable profiles at buses 18, 22, 25, and 33. A backward-forward branch-flow sweep records daily minimum voltage, maximum branch loading, feeder loss, and feasible-step share for each scenario.

The AC-OPF benchmark uses DDRE-derived net-load scaling on IEEE-30 and IEEE-118. Renewable variability is mapped as negative net load on selected PQ buses, and every scenario is solved with explicit generator, voltage, and branch constraints. Post-solve checks record power-balance residual, branch-limit violation, and voltage-limit violation.

The OPF reduction benchmark uses one fixed stratified panel of 18 scenarios and should therefore be interpreted as benchmark-specific comparative evidence rather than as a repeated-sampling statistical estimate. This wording is synchronized with the manuscript discussion and conclusion.

## S5. Parameter and Reproducibility Notes
To improve auditability, the revised package now includes `Outputs/tables/default_hyperparameters.csv`. This file lists the default values of the main learning and validation parameters referenced in the manuscript, including \(K\), \(\alpha\), \(\gamma\), \(\tau\), the five benchmark seeds, the OPF scenario-panel size, and the retained scenario counts used in the reduction study.

## S6. Scope-Alignment Note
To reduce ambiguity between the learning benchmark and the validation layers, the revised title now names DDRE-33 as the learning benchmark and AC-OPF as a mapped-system validation layer, while the package separately documents the new direct DDRE-33 radial screen. This editorial change is documented in `Outputs/tables/scope_alignment_summary.csv` and mirrored in the manuscript appendix.
