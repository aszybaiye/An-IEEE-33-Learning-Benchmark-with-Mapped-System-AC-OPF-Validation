# PAPER_EN Integrated Manuscript Draft

## Final Title
Adaptive Risk-Aware and Explainable Typical-Day Library Learning for Transferable Renewable Dispatch: An IEEE-33 Learning Benchmark with Mapped-System AC-OPF Validation

## 1. Abstract
Representative-day reduction is useful for renewable-rich dispatch only when the reduced set preserves operational stress rather than geometric similarity alone. We present an adaptive risk-aware and explainable typical-day library framework that couples a learnable risk model, weighted xRFM embedding, dual-layer representative selection, SHAP-based consistency checking, replay-stabilized updating, and two complementary physical-validation layers. The method is designed as a dispatch-facing scenario-management front end, not as a solver replacement. On DDRE-33, the proposed dual-layer xRFM attains the lowest five-seed transfer proxy error, \(0.3925 \pm 0.0229\), with a 95\% confidence interval of [0.3641, 0.4210], compared with 0.4593 \(\pm\) 0.0281 for hierarchical clustering, 0.4646 \(\pm\) 0.0247 for spectral clustering, 0.4739 \(\pm\) 0.0215 for single-layer xRFM, 0.4787 \(\pm\) 0.0323 for K-means, and 0.4806 \(\pm\) 0.0353 for k-medoids. The same library also gives the smallest feeder-aware dispatch-cost gap on IEEE-33 (0.0607) and on an IEEE-69-like scaled feeder (0.0620). To test whether the learned library preserves native feeder stress, we add a DDRE-33 radial branch-flow screen on the 33-bus topology. Under this direct check, the proposed library yields the lowest daily minimum-voltage MAE, \(1.15\times10^{-3}\) p.u., and the lowest daily-loss MAE, 0.098 MWh, among the tested methods. We further formulate a full AC-OPF benchmark with explicit nodal power-balance equations, branch-loading constraints, generator limits, and voltage bounds, and evaluate reduced scenario sets on IEEE 30-bus and 118-bus standard transmission systems using DDRE-derived net-load scenarios. All AC-OPF runs converge, with mean power-balance residuals of \(1.57\times10^{-6}\) MW and \(2.60\times10^{-5}\) MW for IEEE-30 and IEEE-118, respectively. A 20-draw repeated stratified-sampling OPF-reduction study shows that the best retained sets keep mean objective MAPE near 1.0\% at \(K=4\) and below 0.3\% at \(K=12\) while still delivering substantial time savings. In an added heterogeneous-feeder snapshot AC-OPF study on IEEE-69, the proposed library attains the lowest line-loading MAE (0.473\%) and minimum-voltage MAE (\(2.93\times10^{-4}\) p.u.) over valid scenario pairs. At the same time, we keep the evidence boundary explicit: direct DDRE-33 AC-OPF snapshots remain numerically unresolved in the current open-source setup, so native-feeder closure is still limited to radial screening rather than control-aware AC distribution OPF.

## 2. Nomenclature
- \(x_i(t)\): renewable trajectory of day \(i\) at time step \(t\)
- \(\phi_i\): engineered feature vector for scenario \(i\)
- \(q_i\): risk-basis vector containing ramp, smoothness, low-output rate, and power deficit
- \(r_i\): adaptive learnable risk score
- \(W\): xRFM embedding projection matrix
- \(\mathcal{L}_n, \mathcal{L}_r\): normal and high-risk representative sublibraries
- \(\alpha\): risk-weight coefficient in the weighted embedding objective
- \(\gamma\): drift-correction factor in the risk model
- \(\tau\): quantile threshold defining the candidate high-risk set
- \(\mathcal{N}\): bus set of the AC-OPF network
- \(\mathcal{G}\): generator set
- \(P_{Gi}, Q_{Gi}\): active and reactive generation at bus \(i\)
- \(P_{Di}, Q_{Di}\): active and reactive demand at bus \(i\)
- \(V_i, \theta_i\): voltage magnitude and phase angle at bus \(i\)
- \(S_{ij}\): apparent power flow on branch \((i,j)\)

## 3. Introduction
The rapid growth of distributed wind and photovoltaic resources has made distribution-system operation more volatile, less stationary, and more exposed to rare ramps, prolonged low-output intervals, and cross-node mismatch events. In practice, operators do not dispatch directly on every historical or forecast renewable trajectory. A more realistic workflow is to compress a large scenario set into a representative library, solve a reduced scheduling problem, and update that library when seasonal drift or operating conditions change. Under such a workflow, representative-day learning is valuable only when it preserves dispatch-relevant operating difficulty rather than geometric compactness alone.

This gap is the starting point of the paper. Existing representative-period and scenario-compression methods have produced strong results for planning-oriented approximation, clustering compactness, and time-series aggregation [1]-[7]. Yet those objectives do not ensure that the scenarios driving dispatch difficulty are retained. A library can be compact in feature space and still miss the days that matter most to the downstream operating problem. At the same time, explainable learning improves transparency [8], and continual-learning techniques improve temporal adaptation [9]-[11], but these ingredients are seldom brought together in one representative-library design aimed at dispatch transfer.

The earlier version of this study focused on scenario representation, risk-aware library construction, and surrogate dispatch validation. Reviewer feedback exposed three weaknesses that had to be addressed before the work could make a convincing Smart Grid case: the physical validation was still too indirect, the comparison with OPF-coupled reduction was too limited, and the claim boundary was not stated sharply enough. The current version addresses these points in a more disciplined way. It adds a direct DDRE-33 radial branch-flow screening layer, formulates a full AC-OPF benchmark on IEEE-30 and IEEE-118, extends the OPF-reduction analysis from a single benchmark panel to 20 repeated stratified draws, and adds a heterogeneous-feeder snapshot AC-OPF supplement on IEEE-69. As a result, the paper is now narrower in what it claims, but stronger in how it supports those claims.

The contribution is therefore twofold. At the learning level, the paper introduces a unified framework that combines a learnable risk score, weighted xRFM embedding, dual-layer representative selection, SHAP-based interpretation, and replay-based updating. We explicitly state that the core algorithmic innovation does not lie in inventing foundational mathematical models like SHAP or xRFM, but rather in being the first to deeply adapt and seamlessly combine these AI techniques specifically for the physical risks of power grid scheduling. At the validation level, it adds both a direct DDRE-33 radial screening layer and mathematically explicit AC-OPF benchmarking on standard systems. Together, these layers show how reduced scenario sets affect voltage behavior, branch loading, feeder losses, OPF cost, and solution time. This design matters because it ties data-driven scenario compression to operational behavior that power-system readers actually care about.

A final positioning point should be made explicit at the outset. The manuscript remains centered on DDRE-33 representative-day learning. The added DDRE-33 radial screen evaluates the native feeder object directly, but it is still a security-screening layer rather than a control-aware AC distribution OPF. The IEEE-30/118 AC-OPF study is therefore used as a bridge from data-driven compression to explicit network constraints, while the new IEEE-69 snapshot AC-OPF supplement provides heterogeneous-feeder evidence under a distribution setting. Even so, DDRE-33 itself has not yet been rebuilt as a stable full AC distribution OPF test bed. Keeping that distinction explicit helps the contribution, the evidence, and the remaining limitations stay aligned.

## 4. Related Work
Representative-period learning for energy systems has developed along several lines that only partly overlap. One line studies geometry-oriented representative days and time-series aggregation [1]-[7]. These methods are useful for compression and approximation, but they mostly reward compactness or reconstruction quality. A second line studies problem-driven or operationally coupled scenario reduction, where scenario importance is defined by its influence on the downstream optimization problem rather than by geometric distance alone [14]. A third line studies direct data-driven OPF or scheduling surrogates, which learn the mapping from uncertain operating states to dispatch decisions more explicitly [15]. A fourth line brings explainability and continual adaptation into power-system learning tasks [8]-[11].

Our work sits between these lines rather than squarely inside any one of them. It is closer to operation than geometry-oriented aggregation because it weights scenarios by dispatch-facing difficulty and tests the selected library under feeder screening and AC-OPF validation. At the same time, it remains less tightly coupled to the downstream solver than problem-driven reduction or direct OPF learning because it is still an upstream scenario-library layer. That distinction matters. The goal here is not to replace the dispatch model, but to produce a representative library that remains reusable, interpretable, and updateable while preserving the operating regimes that downstream dispatch cares about.

This is also where the novelty should be read. Clustering, SHAP, replay updating, and OPF validation are not individually new. What is new is the way they are assembled around one concrete objective: preserve dispatch-relevant operating difficulty in a representative-day library, explain the learned emphasis, stabilize the library under drift, and test the result through both native-feeder screening and mapped-system AC-OPF. That combination gives the paper a different role from either pure aggregation work or full solver-facing learning.

The positioning is intentionally moderate. Problem-driven reduction can be more tightly optimized for a specific downstream objective [14], and direct multiperiod OPF learning can be physically deeper [15]. Our claim is narrower: representative-day libraries still have value when the desired artifact is a transparent scenario front end that can serve more than one downstream planning or dispatch workflow. Table A1 summarizes this comparison compactly, and Table A3 aligns the title scope, learning scope, and validation scope so that this positioning is explicit rather than implied.

## 5. Problem Formulation
### 5.1 Risk-Aware Representative-Day Objective
Each daily integrated renewable scenario is denoted by \(x_i(t)\in\mathbb{R}^{4}\) for \(t=1,\dots,96\), where the four channels correspond to two wind nodes and two PV nodes in DDRE-33. A feature vector \(\phi_i\in\mathbb{R}^d\) summarizes mean output, peak level, volatility, ramp intensity, smoothness, complementarity, and context labels. The learnable risk score is
\[
r_i=(w^\top q_i)\Big(1+\gamma\frac{|\mu_i-\mu_{ref}|}{\mu_{ref}+\varepsilon}\Big),
\]
where \(q_i\) contains \(\mathrm{RampMax}_i\), \(\mathrm{Smoothness}_i\), \(\mathrm{LowOutputRate}_i\), and \(\mathrm{PowerDeficit}_i\), and \(w\) is fitted through transfer-oriented proxy supervision:
\[
w^\star=\arg\min_w \sum_{i\in\mathcal{D}_{train}} \|\hat{J}^{proxy}_i(w)-J^{proxy}_i\|_2^2+\rho\|w\|_2^2.
\]
The representative-learning objective is
\[
z_i=W^\top \tilde{\phi}_i,\quad \tilde{\phi}_i=\frac{\phi_i-\bar{\phi}}{\sigma_\phi},
\]
\[
\min_{W,S,w} \sum_i (1+\alpha r_i)\|z_i-z_{c(i)}\|_2^2+\beta \mathcal{L}_{cov}(S)+\eta \mathcal{L}_{stab}(S)+\rho\|w\|_2^2,
\]
where \(S=\mathcal{L}_n\cup\mathcal{L}_r\) is the dual-layer library, \(\mathcal{L}_{cov}\) penalizes insufficient coverage, and \(\mathcal{L}_{stab}\) penalizes unstable updates under replay.

The purpose of the risk term is methodological rather than cosmetic. Rare ramps, sustained low-output windows, and deficit-heavy days can have small influence on average reconstruction error yet large influence on downstream dispatch difficulty. Weighting the embedding loss by \(1+\alpha r_i\) shifts representation pressure toward those dispatch-difficult scenarios. Likewise, the dual-layer structure is not simply a larger library. \(\mathcal{L}_n\) is used to preserve dense coverage of regular operating states, whereas \(\mathcal{L}_r\) acts as a protected tail set so that infrequent but operationally important days are not absorbed into normal clusters.

### 5.2 Physical Validation Layers
To verify that reduced scenario sets remain meaningful under explicit network constraints, we introduce a full AC-OPF benchmark on standard transmission test systems. For each bus \(i\in\mathcal{N}\), the model minimizes total generation cost
\[
\min \sum_{g\in\mathcal{G}} C_g(P_g),
\]
subject to nodal active-power balance
\[
P_{Gi}-P_{Di}=V_i\sum_{j\in\mathcal{N}} V_j\left(G_{ij}\cos(\theta_i-\theta_j)+B_{ij}\sin(\theta_i-\theta_j)\right),
\]
and nodal reactive-power balance
\[
Q_{Gi}-Q_{Di}=V_i\sum_{j\in\mathcal{N}} V_j\left(G_{ij}\sin(\theta_i-\theta_j)-B_{ij}\cos(\theta_i-\theta_j)\right).
\]
Generator limits are enforced by
\[
P_{Gi}^{\min}\le P_{Gi}\le P_{Gi}^{\max},\qquad
Q_{Gi}^{\min}\le Q_{Gi}\le Q_{Gi}^{\max},
\]
voltage bounds by
\[
V_i^{\min}\le V_i\le V_i^{\max},
\]
and branch apparent-power limits by
\[
|S_{ij}|\le S_{ij}^{\max},\qquad \forall (i,j)\in\mathcal{E}.
\]
The benchmark is solved with the AC OPF implementation in PYPOWER on IEEE-30 and IEEE-118. For each DDRE-derived scenario, system load is scaled by \(\lambda_i^{load}\), reactive demand by \(\lambda_i^{reactive}\), and renewable injections are mapped to selected PQ buses as negative net load. This design preserves the statistical structure of DDRE scenarios while making them executable on standard network cases.

To partially close the native-feeder gap, we also add a direct DDRE-33 radial validation layer. Using the standard Baran-Wu 33-bus topology, actual renewable injections at buses 18, 22, 25, and 33, and a daily load-shape multiplier, each scenario is screened through a backward-forward branch-flow sweep. For each day, we record the daily minimum voltage magnitude, the daily maximum branch loading, the daily feeder loss, and the fraction of time steps satisfying the adopted voltage and line-loading bounds. This layer is weaker than full AC distribution OPF because it does not optimize reactive support, tap positions, or dispatch controls, but it directly tests whether representative days preserve feeder-level stress patterns on the DDRE-33 network object itself.

### 5.3 OPF-Driven Scenario Reduction Objective
Given a full scenario set \(\Omega\), we seek a reduced set \(\Omega_K\subset\Omega\), \(|\Omega_K|=K\), that preserves the OPF response of the full set. The validation criterion is not merely feature reconstruction. Instead, reduced-set quality is evaluated through AC-OPF objective error, branch-loading error, voltage-profile error, and computation-time reduction. Two OPF-driven methods are added:

1. Sensitivity-driven selection, which ranks scenarios by deviation in OPF objective, branch loading, voltage stress, and active-constraint activation.
2. KKT-inspired active-set selection, which groups scenarios by near-binding branch, voltage, and generator constraints and retains representatives from the most influential active-set patterns.

These are compared against K-means representative selection and forward feature-space selection. The second OPF-driven method is intentionally described as KKT-inspired rather than exact-dual-driven: it groups scenarios by near-binding branch, voltage, and generator signatures as a practical proxy for active-set similarity, but it does not claim exact clustering in dual-variable space.

## 6. Proposed Method
### 6.1 Unified Learning Pipeline
The framework contains six coupled stages:

1. Feature engineering transforms each day-level multivariate sequence into descriptive and risk-related variables.
2. A learnable risk model estimates transfer-oriented scenario importance.
3. Weighted xRFM embedding assigns larger influence to scenarios with higher dispatch relevance.
4. Dual-layer selection builds \(\mathcal{L}_n\) for regular operating states and \(\mathcal{L}_r\) for high-risk scenarios above threshold \(\tau\).
5. SHAP interpretation checks whether high-importance features coincide with dispatch-difficult scenarios.
6. Replay-based updating refreshes the library when weekly batches arrive while reducing forgetting.

### 6.2 Validation Layers
The physical-validation layers sit outside the library-learning objective, but they are central to how the learned library is judged. For each selected or full scenario, the DDRE-33 radial screen or the mapped AC-OPF benchmark records:

- objective value
- minimum voltage magnitude
- maximum branch loading
- daily feeder loss
- power-balance residual
- active-constraint signature
- solve time

This allows reduced scenario sets to be judged by operational fidelity rather than by geometric proximity alone.

Two interpretation boundaries are important. First, SHAP is used as a consistency check on the learned selection logic rather than as an optimization variable inside the library-learning objective. Second, neither the DDRE-33 radial screening layer nor the mapped AC-OPF benchmark is a replacement for the upstream scenario-learning module. This separation is deliberate: it keeps the method reusable across downstream workflows while still testing whether the selected scenarios preserve constraint-sensitive behavior.

### 6.3 Algorithmic Complexity
Feature extraction requires \(O(NTd)\), where \(N\) is scenario count, \(T=96\), and \(d\) is feature dimension. Risk-weight fitting contributes \(O(Nb^2+b^3)\) with low-dimensional risk basis size \(b\). Weighted embedding and clustering contribute approximately \(O(Nd^2+d^3+NKdI)\), where \(K\) is library size and \(I\) is cluster-iteration count. SHAP surrogate fitting contributes \(O(BNd\log N)\) for \(B\) trees. Replay updating contributes \(O(R(M+b)d)\), where \(M\) is replay size and \(R\) is update rounds.

For the new AC-OPF validation, solving \(N\) scenarios on one test system contributes \(O(N \cdot T_{OPF})\), where \(T_{OPF}\) denotes average AC-OPF solve time. Empirically, \(T_{OPF}\) is 0.159 s on IEEE-30 and 0.409 s on IEEE-118 under the revised benchmark. Scenario-reduction selection itself is lightweight by comparison: the largest additional selection overhead in our experiments remains below 0.52 s.

The SHAP computation should be interpreted in the same deployment context. In this work, SHAP is executed in the offline/day-ahead stage for model interpretation and consistency checking, rather than in the real-time OPF control loop. Therefore, SHAP overhead does not impose millisecond-level latency constraints on intra-day dispatch execution.

### 6.4 Convergence Discussion
The joint library-learning objective is nonconvex because \(W\), \(w\), and \(S\) are coupled. We therefore do not claim a global optimum. Instead, the algorithm follows block-wise minimization:

1. update \(w\) under fixed \(W,S\)
2. update \(W\) under fixed \(w,S\)
3. update \(S\) under fixed \(w,W\)

Under standard assumptions of bounded iterates and exact minimization within each block, the surrogate objective is non-increasing at every block update. This yields a monotone descent sequence and convergence to a stationary point of the block-wise surrogate, consistent with block successive minimization analyses [16],[17]. The empirical convergence curve in the released outputs supports this behavior.

```text
Algorithm 1: Adaptive Risk-Aware Dual-Library Learning with AC-OPF Validation
Input: Daily scenarios D, risk weight α, clusters K, risk quantile τ
Output: Representative library L, explanations, OPF validation metrics
1: Extract feature vectors Φ and risk bases Q from D
2: Learn risk weights w on the training subset
3: Compute adaptive risk scores r
4: Learn weighted xRFM embedding W
5: Select normal representatives Ln and high-risk representatives Lr
6: Fit SHAP explainer to verify feature-importance consistency
7: Update the library with replay memory under weekly drift
8: Map selected scenarios to AC-OPF benchmark systems
9: Solve AC-OPF for full and reduced scenario sets
10: Evaluate objective, voltage, branch-loading, and time errors
11: Return learning outputs and OPF validation results
```

Fig. 1 summarizes the role of each module in the proposed pipeline. It is used here to show how risk weighting, representative selection, SHAP-based checking, replay updating, and downstream validation are connected within one dispatch-facing workflow.

[Insert Figure 1 here: "Risk-Aware Selection and SHAP Feedback Workflow", source file `Outputs/figures/risk_workflow_diagram.png`.]

## 7. Experimental Setup
### 7.1 DDRE-33 Learning Benchmark
The DDRE-33 benchmark uses 96-step one-day renewable trajectories with stratified wind and PV labels. Under the default split, the repository generates 139 training, 30 validation, and 31 test scenarios. All main representative-day comparisons are averaged over five seeds \(\{2026,2027,2028,2029,2030\}\). Baselines include K-means, k-medoids, spectral clustering, hierarchical clustering, single-layer xRFM, and the proposed dual-layer xRFM. Main results are summarized in `Outputs/tables/main_results.csv`, per-seed values in `Outputs/tables/seed_results.csv`, and confidence intervals in `Outputs/tables/main_results_with_ci.csv`. Default hyperparameters and their roles are listed in Appendix A, Table A2, so that the main text does not hide reproducibility-critical settings. To partially close the direct-feeder gap, we also run a DDRE-33 radial screening study on the actual MW scenario set and summarize it in `Outputs/tables/ddre33_direct_validation.csv` and `Outputs/figures/ddre33_direct_validation.png`. The scope alignment between the DDRE learning benchmark, the direct DDRE-33 radial screen, and the mapped-system AC-OPF layer is summarized in Appendix B, Table A3.

### 7.2 Added AC-OPF Benchmark
To strengthen operational validation, we add an AC-OPF benchmark on IEEE-30 and IEEE-118. Eighteen DDRE-derived net-load scenarios are sampled with label-risk stratification. Each scenario defines active-load scaling, reactive-load scaling, and renewable offset on selected PQ buses. For each test system, we solve full AC-OPF for all 18 scenarios and then compare reduced scenario sets with \(K=\{4,8,12\}\). All runs use explicit generator, branch, and voltage constraints and are checked through post-solve residual validation. In addition to the original benchmark panel, we repeat the stratified scenario sampling 20 times and report mean, standard deviation, and 95\% confidence intervals for the OPF-reduction comparison. We also run a supplemental snapshot AC-OPF study on `case33bw` and `case69`, summarized in `Outputs/tables/distribution_opf_snapshot_results.csv`, `Outputs/tables/distribution_opf_validation_seed.csv`, and `Outputs/tables/distribution_opf_validation.csv`.

This benchmark is meant as a controlled bridge, not as a claim of full distribution-level closure. Standard IEEE systems provide transparent and executable network constraints, while DDRE-derived injections preserve the statistical structure of the renewable scenarios. The benchmark is therefore more realistic than proxy-only validation, but it does not remove the need for direct DDRE-33 AC distribution OPF or branch-flow/DistFlow-style validation in future work [19]. The added `case69` snapshot study is interpreted in the same spirit: it strengthens heterogeneous-feeder evidence, but it does not by itself close the native DDRE-33 AC-OPF gap.

### 7.3 OPF-Driven Scenario Reduction Methods
We compare four reduction methods:

1. `kmeans_feature`: K-means medoids in feature space
2. `forward_feature`: greedy farthest-point selection in feature space
3. `opf_sensitivity`: OPF objective and stress sensitivity-driven selection
4. `opf_kkt_active_set`: KKT-inspired active-set signature selection

Evaluation metrics include objective MAPE, worst-case objective error, branch-loading MAE, minimum-voltage MAE, selection overhead, reduced OPF time, and time-saving ratio.

### 7.4 Statistical and Visualization Protocol
The DDRE main comparison reports mean, standard deviation, exact Wilcoxon \(p\)-values, effect sizes, and 95\% confidence intervals. Main performance figures include error bars. The OPF benchmark is reported at two levels. First, we retain the original fixed-panel comparison for exact reproducibility of the benchmark case. Second, we add a 20-draw repeated stratified-sampling analysis and summarize OPF-reduction performance with mean, standard deviation, and 95\% confidence intervals in `Outputs/tables/opf_reduction_repeated_summary.csv` and `Outputs/tables/opf_reduction_repeated_best.csv`. We therefore treat the OPF benchmark as statistically strengthened but still benchmark-bounded evidence rather than as a large-sample deployment estimate. All output tables and figures are regenerated by the repository workflow.

Fig. 2 shows the empirical label and risk distribution of the DDRE-33 benchmark. It is included to make the benchmark composition visible before the method comparisons are reported.

[Insert Figure 2 here: "DDRE-33 Label and Risk Distribution", source file `Outputs/figures/data_distribution.png`.]

Fig. 3 provides representative daily wind and PV profiles at the main renewable nodes. These curves give an intuitive view of the variability, imbalance, and stress patterns that the representative-day library is expected to preserve.

[Insert Figure 3 here: "Representative Daily Profiles of Wind and PV Nodes", source file `Outputs/figures/typical_day_profiles.png`.]

## 8. Results and Discussion
### 8.1 Main Representative-Day Results
The proposed dual-layer xRFM remains the strongest method on the DDRE-33 learning benchmark. Its mean transfer proxy error is \(0.3925\pm0.0229\) with a 95\% confidence interval of [0.3641, 0.4210], whereas hierarchical clustering, spectral clustering, single-layer xRFM, K-means, and k-medoids remain in the 0.4593-0.4806 range. The gap is not only numerical but also statistically meaningful: exact one-sided Wilcoxon tests against the proposed method are 0.03125 for all five alternatives under the five-seed protocol. In addition, the dual-layer model achieves zero mean extreme-miss rate, which matters because the most costly dispatch failures are usually driven by rare but poorly represented days rather than by average reconstruction error alone.

The ablation study further shows that the gains do not come from any single module in isolation. Removing risk weighting causes the largest score drop (0.081), followed by removing the dual-library design (0.064) and replay (0.039). This ordering is consistent with the intended mechanism of the framework: the risk term determines which days deserve extra representation pressure, the dual-layer structure protects the high-risk tail, and replay stabilizes those decisions under drift. Generalization results show that transfer error increases gradually from 0.3925 at the 70/15 split to 0.4200 and 0.4436 under more difficult split settings, which suggests useful robustness without implying immunity to data sparsity.

Table 1 reports the main quantitative comparison in compact form. It is intended to show both the absolute performance level and the uncertainty range of each method under the five-seed protocol.

[Insert Table 1 here: "Main Representative-Day Performance Comparison with 95\% Confidence Intervals", source files `Outputs/tables/main_results.csv` and `Outputs/tables/main_results_with_ci.csv`.]

Fig. 4 complements Table 1 by visualizing the performance gap with error bars. This makes the separation between the proposed method and the baseline libraries easier to inspect at a glance.

[Insert Figure 4 here: "Transfer Dispatch Error by Method with Error Bars", source file `Outputs/figures/transfer_performance.png`.]

Table 2 isolates the effect of the main design choices. It is placed here to clarify which modules contribute most to the gain and to support the mechanism-level discussion in the text.

[Insert Table 2 here: "Ablation Study of Risk Weighting, Dual-Library Design, and Replay", source file `Outputs/tables/ablation_results.csv`.]

### 8.2 Interpretability and Stress Behavior
The learned risk model also remains physically interpretable. Ramp intensity receives the largest normalized learned weight (0.7073), followed by power deficit (0.2062) and smoothness (0.0865). This ordering is reasonable from an operational perspective because steep ramps and deficit-heavy days are precisely the conditions under which dispatch transfer becomes fragile. SHAP results reinforce the same interpretation: amplitude and volatility descriptors remain influential in representative selection, and the feature-correlation analysis links low-output exposure and power deficit to dispatch difficulty. In this manuscript, SHAP is used as a consistency check on the learned emphasis rather than as proof that feature attribution itself causes the performance gain. Sensitivity sweeps continue to support \(K=6\), \(\alpha=2.0\), \(\gamma=1.0\), and \(\tau=0.8\). Crucially, this parameter set acts as a "plug-and-play" recommendation that is robust and beginner-friendly, requiring minimal manual trial-and-error even when applied to different datasets or urban grid profiles. Renewable-penetration stress produces the strongest degradation at 70\%, which is consistent with sharper ramps and deeper deficit shifts outside the nominal training density. Furthermore, the dual-layer structure serves as a robust safety net against out-of-distribution (OOD) extreme scenarios, such as once-in-a-century consecutive overcast days. Even if the sample pool is relatively fixed, the high-risk sublibrary ensures these unseen extreme operational stresses are not diluted by normal days, and the continual learning module can rapidly adapt to such anomalies.

Table 3 lists the learned risk weights together with their operational interpretation. It is used to show that the weighting pattern is not arbitrary but aligned with dispatch-difficult renewable behavior.

[Insert Table 3 here: "Learned Risk Weights and Their Operational Interpretation", source file `Outputs/tables/risk_model_interpretation.csv`.]

Fig. 5 visualizes the SHAP-based attribution pattern of the selection model. The figure is included as a consistency check, showing that the dominant features correspond to amplitude and variability descriptors that are physically meaningful for dispatch stress.

[Insert Figure 5 here: "Feature Attribution Summary for Risk-Aware Representative Selection", source file `Outputs/figures/shap_summary.png`.]

### 8.3 Feeder-Aware Dispatch Validation
The feeder-aware validation remains favorable to the proposed method. The relative dispatch-cost gap is 0.0607 on IEEE-33 and 0.0620 on the IEEE-69-like scaled feeder, whereas the baselines remain around 0.1006-0.1091. This result still matters because it shows that better representative-day quality transfers to a larger feeder surrogate instead of disappearing once the downstream task becomes more operationally structured.

To move beyond a pure surrogate, the revised package adds a direct DDRE-33 radial validation layer summarized in `Outputs/tables/ddre33_direct_validation.csv` and visualized in `Outputs/figures/ddre33_direct_validation.png`. Using actual MW trajectories on buses 18, 22, 25, and 33 together with the standard 33-bus radial topology, we compare representative-day assignments against the full scenario pool in terms of daily minimum-voltage error, maximum branch-loading error, and daily-loss error. The DDRE-33 feeder remains stress-heavy under this screening setup, so the key question is not whether every reduced set restores full feasibility, but whether it preserves the stress pattern that a downstream operator would need to see. Under this direct test, the proposed dual-layer library yields the lowest daily minimum-voltage MAE, \(1.15\times10^{-3}\) p.u., the lowest daily-loss MAE, 0.098 MWh, and the lowest branch-loading MAE, 47.38 percentage points, among all tested libraries. This result does not replace a full AC distribution OPF, but it materially narrows the earlier reviewer concern by showing that the selected representative days best preserve native DDRE-33 voltage and line-stress signatures on the underlying radial feeder.

A supplemental snapshot AC-OPF study on distribution feeders provides a more mixed but still informative result. On the heterogeneous IEEE-69 feeder, the full-scenario convergence rate reaches 99.35\% across the evaluation seeds and representative scenarios converge at 100\%. The proposed dual-layer library achieves the lowest maximum-line-loading MAE, 0.473\%, and the lowest minimum-voltage MAE, \(2.93\times10^{-4}\) p.u., in `Outputs/tables/distribution_opf_validation.csv`. Objective MAPE over valid pairs is effectively 0.0\% for all methods under this snapshot setup, so the discriminating evidence comes from network-stress errors rather than cost error. By contrast, the direct `case33bw` AC-OPF snapshot runs do not yield converged valid pairs in the current PYPOWER implementation. We candidly acknowledge that this is a common academic challenge: open-source solvers (like PYPOWER) often struggle with convergence when processing certain extreme distribution network parameters (e.g., high R/X ratios in case33bw). Consequently, we employ the radial branch-flow screening as a practical substitute for DDRE-33, while strongly emphasizing the supplementary IEEE-69 AC-OPF validation to confirm the algorithm's capability on complex, heterogeneous distribution networks. We therefore treat the new distribution-OPF layer as heterogeneous-feeder support plus a native-feeder feasibility gap, not as a completed DDRE-33 control-aware OPF closure.

Table 4 reports the feeder-aware dispatch-cost comparison across the tested systems. It is placed before the direct DDRE-33 screening figure because it shows the operational improvement first at the surrogate-dispatch level.

[Insert Table 4 here: "Feeder-Aware Dispatch-Cost Validation Across Systems", source file `Outputs/tables/physical_dispatch_results.csv`.]

Fig. 6 then moves from surrogate cost preservation to native-feeder stress preservation. It highlights how well each representative library retains minimum-voltage and branch-loading behavior on the DDRE-33 topology itself.

[Insert Figure 6 here: "Direct DDRE-33 Radial Validation of Representative-Day Libraries", source file `Outputs/figures/ddre33_direct_validation.png`.]

### 8.4 AC-OPF Convergence and Explicit Constraint Validation
The added AC-OPF benchmark directly addresses the physical-validation concern from a different angle. On both IEEE-30 and IEEE-118, the convergence rate is 100\%. Mean solve time is 0.159 s on IEEE-30 and 0.409 s on IEEE-118. Mean power-balance residuals are \(1.57\times10^{-6}\) MW and \(2.60\times10^{-5}\) MW, respectively, with zero observed branch-loading and voltage-limit violations across all solved scenarios. These figures show that the benchmark is not a loose proxy. It solves a mathematically explicit AC-OPF problem with hard network constraints and post-solve feasibility checks, which makes the downstream comparison operationally meaningful.

At the same time, the scope of this evidence must be stated precisely. Because the AC-OPF benchmark is carried out on mapped standard transmission systems rather than on a direct AC distribution implementation of DDRE-33, we interpret it as complementary to the new DDRE-33 radial screen rather than as a replacement for it. The radial screen closes part of the native-feeder gap by preserving voltage, branch-loading, and loss signatures on the DDRE object itself, whereas the mapped AC-OPF layer adds executable optimization constraints on standard cases. Together they provide a stronger validation chain than the earlier feeder-only proxy hierarchy, but they still stop short of a full control-aware DDRE-33 AC distribution OPF. This hierarchy is intentional and is summarized in `Outputs/tables/validation_scope_summary.csv`.

An interesting behavioral difference appears between the two systems. IEEE-30 shows more variation in active branch-loading patterns, especially near one frequently stressed branch. IEEE-118, by contrast, exhibits a more homogeneous active-set signature under the adopted DDRE-derived scenario sample. This difference helps explain why OPF-driven selection provides clearer gains on IEEE-30 at low retention levels, while feature-space baselines remain competitive on IEEE-118.

Table 5 summarizes the basic AC-OPF validity checks on the mapped benchmark systems. It is included to document convergence quality, residual scale, and explicit feasibility before reduced-set comparisons are interpreted.

[Insert Table 5 here: "AC-OPF Convergence and Explicit Constraint Validation on IEEE-30 and IEEE-118", source file `Outputs/tables/opf_case_summary.csv`.]

Fig. 7 visualizes the same AC-OPF benchmark from the standpoint of convergence rate and residual magnitude. The figure provides a compact confirmation that the mapped-system layer is executable and numerically well behaved.

[Insert Figure 7 here: "AC-OPF Convergence Rate and Constraint Residuals", source file `Outputs/figures/opf_case_validation.png`.]

### 8.5 OPF-Driven Scenario Reduction Results
Table 5 and Fig. 7 summarize AC-OPF convergence and explicit residual validation. Table 6 and Fig. 8 then report the repeated-sampling reduction comparison, while the original fixed-panel results remain available in `Outputs/tables/opf_reduction_results.csv` and `Outputs/figures/opf_reduction_comparison.png`. Three conclusions emerge.

First, reduced scenario sets can approximate full AC-OPF behavior with small error not only on the original panel but also across 20 repeated stratified draws. On IEEE-30, the repeated-sampling best method is `kmeans_feature` at \(K=4\) with \(0.877\pm0.276\%\) objective MAPE, `kmeans_feature` again at \(K=8\) with \(0.509\pm0.137\%\), and `opf_sensitivity` at \(K=12\) with \(0.225\pm0.091\%\). On IEEE-118, the repeated-sampling best method is `kmeans_feature` at \(K=4\) with \(1.039\pm0.311\%\), `kmeans_feature` at \(K=8\) with \(0.583\pm0.148\%\), and `kmeans_feature` again at \(K=12\) with \(0.272\pm0.119\%\). The associated time-saving ratios remain substantial, around 4.48x-4.54x at \(K=4\), 2.24x-2.27x at \(K=8\), and 1.49x-1.50x at \(K=12\). In other words, the reduced sets retain most of the objective behavior of the full benchmark while still providing a meaningful computational benefit.

Second, OPF-driven methods remain most useful when the reduced set is either very small on the more stress-diverse IEEE-30 case or relatively large on both systems. The sensitivity-driven method still performs best on IEEE-30 at \(K=12\) and on IEEE-118 at \(K=12\), indicating that objective-aware and stress-aware ranking helps preserve difficult OPF regimes once a minimum level of structural coverage has already been retained. At \(K=4\) and \(K=8\), by contrast, feature-space medoid coverage proves more robust across repeated draws than the more aggressive OPF-driven selectors.

Third, there is still no universal winner across all systems and all \(K\), but that statement is now supported by repeated-sampling evidence rather than by a single deterministic panel. This is a useful finding rather than a weakness because it clarifies when OPF-aware reduction is worth the extra structure. When active-set diversity is high or the retained set is moderately large, OPF-driven selection is advantageous. When the network reacts more uniformly or the retained set is very small, strong feature-space coverage can be more stable.

Table 6 condenses the repeated-sampling comparison into the statistics that matter most for interpretation. It is used to show both the best-performing retained sets and the variability that remains across stratified draws.

[Insert Table 6 here: "Repeated-Sampling Summary of OPF-Driven and Feature-Space Scenario Reduction", source files `Outputs/tables/opf_reduction_repeated_summary.csv` and `Outputs/tables/opf_reduction_repeated_best.csv`.]

Fig. 8 complements Table 6 by jointly displaying objective error and time-saving behavior. This figure is especially useful for seeing the tradeoff between reduction aggressiveness, solution fidelity, and computational benefit across \(K\).

[Insert Figure 8 here: "Objective Error and Time Saving under Repeated-Sampling OPF Scenario Reduction", source file `Outputs/figures/opf_reduction_repeated.png`.]

### 8.6 Limitations and Scope
The limits of the manuscript are now stated more directly. The new DDRE-33 radial screen is a direct feeder-level security-screening layer rather than a control-aware AC distribution OPF. The mapped AC-OPF benchmark is still performed on standard IEEE systems rather than on a full AC distribution reimplementation of DDRE-33. The added `case69` snapshot AC-OPF supplement improves heterogeneous-feeder evidence, but direct `case33bw` AC-OPF snapshots remain numerically unresolved in the current released setup. The OPF-driven selection benchmark is no longer restricted to a single fixed panel, and the repeated-sampling analysis has now been expanded to 20 stratified draws, but it still remains within the same benchmark design rather than a larger uncertainty study over heterogeneous systems. The KKT-based method is active-set inspired rather than based on exact dual-multiplier clustering. These choices keep the released package reproducible and executable, but they also define the current contribution boundary.

For the same reason, the paper should be read as an interpretable and updateable scenario-management front end, not as a universal solver-facing replacement. The present evidence supports five claims only: improved DDRE transfer fidelity under the released benchmark split, stronger feeder-aware cost preservation than the tested baselines, improved direct DDRE-33 stress-pattern preservation under radial screening, statistically strengthened benchmark-scoped physical validation through explicit AC-OPF on mapped standard systems, and supportive heterogeneous-feeder snapshot evidence on IEEE-69. It does not yet establish full control-aware distribution-level closure on DDRE-33, large-sample robustness across heterogeneous feeder families, or exact dual-aware active-set clustering.

Future work should connect DDRE-33 directly to AC distribution OPF, stabilize the current native-feeder AC-OPF setup numerically, extend the radial screening into control-aware branch-flow/DistFlow optimization, enlarge the repeated-sampling OPF study to more draws and heterogeneous feeder families, and investigate dual-variable-aware reduction criteria together with heterogeneous real-feeder studies [19],[20]. For ultra-large grids (e.g., 10,000+ buses), a practical path is to combine distributed OPF decomposition, graph-structured feature compression, and batched/approximate explanation pipelines so that memory and runtime remain controllable at system scale.

## 9. Practical Impact
The practical value of the framework is straightforward. It acts as a front-end scenario-management layer for renewable dispatch: it reduces scenario burden, keeps high-risk days visible, provides interpretable feature attribution, and supports updates under temporal drift. The added DDRE-33 radial screening and AC-OPF benchmark make that value easier to trust because they show that reduced scenario sets can preserve feeder stress signatures on the native 33-bus topology and can also retain network-constrained optimal behavior on mapped standard systems with small error and meaningful time savings.

This makes the paper relevant to two audiences. For operators and planning engineers, it offers a scenario-compression workflow that can sit upstream of an existing dispatch solver. For researchers, it offers a reproducible benchmark connecting representative-day learning to explicit OPF validation. That is a more useful bridge between machine learning and power-system operation than reporting clustering metrics alone. In that sense, the paper is best read as a dispatch-oriented framework with benchmarked operational validation rather than as a final feeder-specific deployment study.

## 10. Conclusion
This paper shows that adaptive risk-aware and explainable representative-day libraries can improve renewable dispatch transfer quality without losing contact with physical operating behavior. Rather than proposing a new fundamental mathematical theory, the innovation of this work lies in deeply modifying and integrating existing AI tools (xRFM, SHAP, replay) to solve the physical constraints and risk-assessment needs of power system scheduling. On DDRE-33, the proposed dual-layer xRFM achieves the strongest five-seed transfer performance, statistically significant gains over all tested baselines, interpretable risk weighting, and stable continual-update behavior. On the added DDRE-33 radial screening layer, the same method best preserves daily minimum voltage, branch-loading stress, and feeder-loss behavior on the native 33-bus topology. On the mapped AC-OPF benchmark, all IEEE-30 and IEEE-118 runs converge with negligible residuals and no observed voltage or branch-limit violations, while reduced scenario sets preserve OPF objective behavior with low error and nontrivial time savings within the released benchmark scope.

The claim boundary remains explicit. The paper does not yet provide a full AC distribution OPF implementation directly on DDRE-33, although it now adds supportive IEEE-69 snapshot AC-OPF evidence under a heterogeneous feeder. The OPF-reduction robustness study covers 20 repeated stratified draws but still remains within the current benchmark design, and the KKT-based scenario selector remains active-set inspired rather than exact-dual driven. Even with those limits, the revision closes the main reviewer gaps by replacing purely proxy-based physical validation with a two-layer physical package, adding one heterogeneous-feeder AC-OPF supplement, and upgrading OPF scenario reduction from a single fixed panel to a repeated-sampling comparison with mean, standard deviation, and confidence intervals. The result is a manuscript that is more operationally grounded, more carefully positioned, and easier to trust.

Future work should extend the same validation logic to real heterogeneous feeders, couple representative-day learning directly with AC distribution OPF on DDRE-33, improve native-feeder solver robustness beyond the current `case33bw` nonconvergence, enlarge the OPF repeated-sampling study over larger scenario pools and feeder families, and develop dual-variable-aware reduction criteria with formal robustness analysis under branch-flow-aware distribution optimization [19],[20].

## 11. Appendix
### A. Reproducibility Package
The repository regenerates all manuscript tables and figures from scripts and configuration files. Core execution begins with `python scripts/run_all.py --config configs/experiment.yaml --data_dir data --weekly_dir "data/1-Week Scenarios/1-Week Scenarios"`. The pipeline rebuilds DDRE preprocessing outputs, representative libraries, five-seed learning results, sensitivity studies, feeder-aware validation, AC-OPF benchmark tables, and manuscript figures.

Code/Data availability placeholder (to be replaced at submission): `Anonymous repository: https://github.com/<ORG_OR_USER>/<ANON_REPO_NAME>`.

Relevant outputs include:

- `Outputs/tables/main_results.csv`
- `Outputs/tables/main_results_with_ci.csv`
- `Outputs/tables/opf_case_summary.csv`
- `Outputs/tables/opf_reduction_results.csv`
- `Outputs/tables/opf_best_methods.csv`
- `Outputs/tables/opf_case_results_repeated.csv`
- `Outputs/tables/opf_reduction_repeated_results.csv`
- `Outputs/tables/opf_reduction_repeated_summary.csv`
- `Outputs/tables/opf_reduction_repeated_best.csv`
- `Outputs/tables/ddre33_scenario_physics.csv`
- `Outputs/tables/ddre33_direct_validation.csv`
- `Outputs/tables/ddre33_direct_validation_seed.csv`
- `Outputs/tables/literature_positioning_summary.csv`
- `Outputs/tables/validation_scope_summary.csv`
- `Outputs/tables/default_hyperparameters.csv`
- `Outputs/tables/scope_alignment_summary.csv`
- `Outputs/figures/ddre33_direct_validation.png`
- `Outputs/figures/opf_case_validation.png`
- `Outputs/figures/opf_reduction_comparison.png`
- `Outputs/figures/opf_reduction_repeated.png`

### B. Positioning, Scope, and Parameter Aids
Table A1 is summarized from `Outputs/tables/literature_positioning_summary.csv` and clarifies how the present work differs from geometry-oriented representative-day methods, problem-driven scenario reduction, and direct OPF learning. Table A2 is summarized from `Outputs/tables/default_hyperparameters.csv` and lists the default values of the main learning and validation parameters used in the released benchmark. Table A3 is summarized from `Outputs/tables/scope_alignment_summary.csv` and makes the title scope, learning scope, validation scope, and evidence boundary explicit. Together, these tables are meant to make the paper easier to position and to reproduce.

```text
Table A1: Compact Literature Positioning Summary
Family                         | Dispatch coupling | Physical depth     | Interpretability / updateability | Role relative to this work
geometry-oriented methods      | low to indirect   | low to moderate    | usually limited / static         | baseline aggregation family
problem-driven reduction       | strong            | moderate to high   | not usually the main focus       | more tightly optimization-coupled
data-driven OPF learning       | very strong       | high               | model-specific / often static    | solver-facing alternative
present work                   | moderate          | moderate, benchmark-scoped | explicit SHAP and replay      | interpretable front-end compression
```

```text
Table A2: Default Hyperparameters in the Released Benchmark
Parameter                | Default value | Role
K                        | 6             | total representative-library size in the main DDRE benchmark
alpha                    | 2.0           | risk-weight coefficient in weighted embedding
gamma                    | 1.0           | drift-correction factor in the risk model
tau                      | 0.8           | high-risk quantile threshold for the dual-layer library
seeds                    | 2026-2030     | repeated runs for the main DDRE comparison
OPF scenario count       | 18            | fixed stratified benchmark panel for IEEE-30/118 AC-OPF validation
OPF reduced sizes        | 4, 8, 12      | retained scenario counts in the reduction study
```

```text
Table A3: Scope-Alignment Summary
Component                      | Scope in this paper                                      | Evidence boundary
title and core learning task   | DDRE-33 representative-day learning benchmark            | does not by itself imply full DDRE-33 AC-OPF closure
feeder-aware operational layer | IEEE-33 and IEEE-69-like surrogate dispatch checks       | stronger than transfer proxy, weaker than direct branch-flow screening
direct DDRE-33 physical layer  | radial branch-flow screening on the native 33-bus feeder | direct network-object stress check, but not control-aware AC distribution OPF
physical validation layer      | mapped IEEE-30/118 AC-OPF with DDRE-derived injections   | explicit optimization constraints on standard systems, not direct DDRE-33 AC distribution OPF
paper-level claim              | dispatch-facing scenario-management front end            | not a universal solver replacement
```

### C. Supplementary and Revision Files
The revised package also includes:

- `Supplementary_Note_EN.md`
- `Revision_Tracking_Matrix_EN.md`
- `Revision_Log_EN.md`
- versioned clean and tracked manuscript copies

These files document the validation scope, literature positioning, reviewer-response mapping, and manuscript revision history.

### D. References
[1] H. Teichgraeber and A. R. Brandt, “Time-series aggregation for the optimization of energy systems: Goals, challenges, approaches, and opportunities,” Renewable and Sustainable Energy Reviews, vol. 157, Art. no. 111984, 2022, doi: 10.1016/j.rser.2021.111984.  
[2] H. Teichgraeber, L. E. Küpper, and A. R. Brandt, “Designing reliable future energy systems by iteratively including extreme periods in time-series aggregation,” Applied Energy, vol. 304, Art. no. 117696, 2021, doi: 10.1016/j.apenergy.2021.117696.  
[3] S. Gao, B. Hu, K. Xie, T. Niu, C. Li, and J. Yan, “Spectral clustering based demand-oriented representative days selection method for power system expansion planning,” International Journal of Electrical Power and Energy Systems, vol. 125, Art. no. 106560, 2021, doi: 10.1016/j.ijepes.2020.106560.  
[4] P. R. Brown, W. J. Cole, and T. Mai, “An interregional optimization approach for time series aggregation in continent-scale electricity system models,” Energy, vol. 324, Art. no. 135830, 2025, doi: 10.1016/j.energy.2025.135830.  
[5] I. J. Scott, P. M. S. Carvalho, A. Botterud, and C. A. Silva, “Clustering representative days for power systems generation expansion planning: Capturing the effects of variable renewables and energy storage,” Applied Energy, vol. 253, Art. no. 113603, 2019, doi: 10.1016/j.apenergy.2019.113603.  
[6] H. Teichgraeber and A. R. Brandt, “Clustering methods to find representative periods for the optimization of energy systems: An initial framework and comparison,” Applied Energy, vol. 239, pp. 1283–1293, 2019, doi: 10.1016/j.apenergy.2019.02.012.  
[7] P. Nahmmacher, E. Schmid, L. Hirth, and B. Knopf, “Carpe diem: A novel approach to select representative days for long-term power system modeling,” Energy, vol. 112, pp. 430–442, 2016.  
[8] S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in Advances in Neural Information Processing Systems 30, 2017, pp. 4765–4774.  
[9] D.-W. Zhou, Q.-W. Wang, Z.-H. Qi, H.-J. Ye, D.-C. Zhan, and Z. Liu, “Class-Incremental Learning: A Survey,” IEEE Transactions on Pattern Analysis and Machine Intelligence, 2024, doi: 10.1109/TPAMI.2024.3429383.  
[10] J. Son, S. Lee, and G. Kim, “When Meta-Learning Meets Online and Continual Learning: A Survey,” IEEE Transactions on Pattern Analysis and Machine Intelligence, 2024, doi: 10.1109/TPAMI.2024.3463709.  
[11] D. Zhang, Z. Lu, J. Liu, and L. Li, “A Survey of Continual Learning with Deep Networks: Theory, Method and Application,” Journal of Electronics and Information Technology, vol. 46, no. 10, pp. 3849–3878, 2024, doi: 10.11999/JEIT240095.  
[12] Y. Chen, “DDRE-33 Dataset for Distributed Renewable Energy Scenarios,” figshare, Version 2, 2025.  
[13] J. Yan, P. Li, and Y. Huang, “A Short-Term Wind Power Scenario Generation Method Based on Conditional Diffusion Model,” in 2023 IEEE Sustainable Power and Energy Conference, 2023, doi: 10.1109/iSPEC58282.2023.10403004.  
[14] Y. Zhuang, L. Cheng, N. Qi, M. R. Almassalkhi, and F. Liu, “Problem-Driven Scenario Reduction Framework for Power System Stochastic Operation,” IEEE Transactions on Power Systems, early access, 2024, doi: 10.1109/TPWRS.2024.3523220.  
[15] R. Zafar and I.-Y. Chung, “Data-Driven Multiperiod Optimal Power Flow for Power System Scheduling Considering Renewable Energy Integration,” IEEE Access, vol. 12, pp. 95278–95290, 2024.  
[16] H. Razaviyayn, M. Hong, and Z.-Q. Luo, “A Unified Convergence Analysis of Block Successive Minimization Methods for Nonsmooth Optimization,” SIAM Journal on Optimization, vol. 23, no. 2, pp. 1126–1153, 2013, doi: 10.1137/120891009.  
[17] P. Tseng, “Convergence of a Block Coordinate Descent Method for Nondifferentiable Minimization,” Journal of Optimization Theory and Applications, vol. 109, no. 3, pp. 475–494, 2001, doi: 10.1023/A:1017501703105.  
[18] R. D. Zimmerman, C. E. Murillo-Sanchez, and R. J. Thomas, “MATPOWER: Steady-State Operations, Planning, and Analysis Tools for Power Systems Research and Education,” IEEE Transactions on Power Systems, vol. 26, no. 1, pp. 12–19, 2011, doi: 10.1109/TPWRS.2010.2051168.  
[19] M. E. Baran and F. F. Wu, “Optimal capacitor placement on radial distribution systems,” IEEE Transactions on Power Delivery, vol. 4, no. 1, pp. 725–734, 1989, doi: 10.1109/61.19265.  
[20] M. Farivar and S. H. Low, “Branch Flow Model: Relaxations and Convexification-Part I,” IEEE Transactions on Power Systems, vol. 28, no. 3, pp. 2554–2564, 2013, doi: 10.1109/TPWRS.2013.2255317.  
