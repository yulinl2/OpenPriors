# OpenPriors — research audit report

> **Auto-generated** from the live pipeline by `report/build_report.py`. Every figure below is computed from the same code paths `make pipeline` runs — do not edit by hand; run `make report` to regenerate. A CI gate fails if this file is stale.

OpenPriors reads a body of mathematical results as one typed *(object, attribute, relation)* graph and runs a closed research loop over it: **discover → predict → evaluate → investigate → experiment**. It situates each result among its priors, finds what it is structurally analogous to in another field, predicts what that analogy implies, tells the sound predictions from the spurious, refines the open ones into research directions, and runs their proposed numerical experiments — every step grounded and CI-gated.

At a glance: **5 literatures**, **12 results**, **40 cross-domain analogies**, **7 judged conjectures**, **4 research directions**, over a unified graph of **215 nodes / 517 edges**.

## 1. The four literatures

| Field | Results | Mean novelty | Most novel (score) |
|---|---|---|---|
| Conformal prediction | 4 | 0.734 | `importance_weighting` (1.000) |
| Optimization | 2 | 0.700 | `banach_contraction` (1.000) |
| Learning theory | 2 | 0.643 | `vc_generalization` (1.000) |
| Concentration | 2 | 0.643 | `mcdiarmid_concentration` (1.000) |
| Online learning | 2 | 0.643 | `online_gradient_descent` (1.000) |

*Novelty = 1 − best-prior structural coverage (a prior must be no larger than the result it covers, so a descendant can't 'explain away' its ancestor).*

## 2. Reasoning lineage

Each field's development line, recovered from grounded structure alone (no citation metadata) — objects are results, the relation is *extends*, attributes are the residual novelty:

- **Conformal prediction**: `weighted_conformal` → `arxiv-2006.06138-main` (novelty 0.222)
- **Conformal prediction**: `split_conformal` → `weighted_conformal` (novelty 0.714)
- **Optimization**: `banach_contraction` → `gd_strong_convexity` (novelty 0.400)
- **Learning theory**: `vc_generalization` → `margin_generalization` (novelty 0.286)
- **Concentration**: `mcdiarmid_concentration` → `bernstein_concentration` (novelty 0.286)
- **Online learning**: `online_gradient_descent` → `online_strong_convexity` (novelty 0.286)

## 3. Cross-domain analogies

Discovered by the structure-mapping engine with **roles read from CAUSE structure, unsupervised** — no hand-coded correspondences. Each edge aligns a structural-property/guarantee pair across two literatures:

| A | B | SME score | correspondences |
|---|---|---|---|
| `margin_generalization` | `bernstein_concentration` | 17.0 | the_bound↔the_bound; the_class↔the_func; the_dim↔the_inputs |
| `margin_generalization` | `online_strong_convexity` | 17.0 | the_bound↔the_bound; the_class↔the_losses; the_dim↔the_horizon |
| `bernstein_concentration` | `online_strong_convexity` | 17.0 | the_bound↔the_bound; the_dev↔the_gap; the_func↔the_losses |
| `gd_strong_convexity` | `margin_generalization` | 12.0 | kappa↔the_dim; the_bound↔the_class; the_map↔the_risk |
| `gd_strong_convexity` | `vc_generalization` | 12.0 | kappa↔the_dim; the_bound↔the_class; the_map↔the_risk |
| `gd_strong_convexity` | `bernstein_concentration` | 12.0 | kappa↔the_inputs; the_bound↔the_func; the_map↔the_seq |
| `gd_strong_convexity` | `mcdiarmid_concentration` | 12.0 | kappa↔the_inputs; the_bound↔the_func; the_map↔the_seq |
| `gd_strong_convexity` | `online_gradient_descent` | 12.0 | kappa↔the_horizon; the_bound↔the_losses; the_map↔the_play |
| `gd_strong_convexity` | `online_strong_convexity` | 12.0 | kappa↔the_horizon; the_bound↔the_losses; the_map↔the_play |
| `margin_generalization` | `mcdiarmid_concentration` | 12.0 | the_bound↔the_bound; the_class↔the_func; the_dim↔the_inputs |
| `vc_generalization` | `bernstein_concentration` | 12.0 | the_bound↔the_bound; the_class↔the_func; the_dim↔the_inputs |
| `vc_generalization` | `mcdiarmid_concentration` | 12.0 | the_bound↔the_bound; the_class↔the_func; the_dim↔the_inputs |

*(showing the 12 highest-scoring of 40 analogies.)*

## 4. Discovered structural roles

The role each functor plays is *discovered* from its position in the `CAUSE` glue (premise vs. conclusion, arity), not declared. The shared **`PC::2`** (structural-property) role is what makes the four fields analogous:

| Functor | Role |
|---|---|
| `BOUNDED_DIFFERENCES` | `ROLE::P::2` |
| `BOUNDED_GRADIENTS` | `ROLE::P::2` |
| `BOUNDED_MARTINGALE` | `ROLE::PC::2` |
| `CONCENTRATION` | `ROLE::C::2` |
| `CONTRACTION` | `ROLE::PC::2` |
| `COVERAGE` | `ROLE::C::2` |
| `CURVATURE_BOUND` | `ROLE::P::2` |
| `EXCHANGEABLE` | `ROLE::P::1` |
| `FINITE_VC` | `ROLE::P::2` |
| `GENERALIZATION` | `ROLE::C::2` |
| `LIKELIHOOD_RATIO` | `ROLE::P::3` |
| `LINEAR_CONVERGENCE` | `ROLE::C::2` |
| `MARGIN_BOUND` | `ROLE::P::2` |
| `NO_REGRET` | `ROLE::PC::2` |
| `STRONG_CONVEXITY_BOUND` | `ROLE::P::2` |
| `SUBLINEAR_REGRET` | `ROLE::C::2` |
| `UNIFORM_CONVERGENCE` | `ROLE::PC::2` |
| `VARIANCE_BOUND` | `ROLE::P::2` |
| `WEIGHTED_EXCHANGEABLE` | `ROLE::PC::2` |

## 5. Conjectures and verdicts

Candidate inferences projected across an analogy (Epic P), then judged by an in-session sub-agent behind a deterministic grounding gate (Epic Q):

- **C1** — _plausible_: The conformal prediction/calibration procedure has a fixed point in the sense of a self-consistent prediction set.
  - reasoning: Full (transductive) conformal prediction is genuinely a self-consistency construction: a candidate label y is included in the set iff augmenting the data with (x,y) and recomputing nonconformity scores leaves y non-extreme, which is exactly a fixed-point/consistency condition on the augmented empirical distribution. The analogy is more an apt re-description than a Banach contraction, however, since conformal's self-consistency is a thresholding condition, not the unique attractor of an iterated kappa-Lipschitz map, and uniqueness/contraction need not hold. So the projected fixed point lands on a real existing structure but the mechanism (contraction with kappa<1) does not transfer.
- **C2** — _uncertain_: An importance/likelihood-ratio reweighting between distributions underlies control of a contraction map's modulus.
  - reasoning: There is a legitimate but narrow correspondence: in Markov-chain and MDP theory the contraction modulus of the transition/Bellman operator is governed by overlap between distributions, and change-of-measure / Radon-Nikodym (likelihood-ratio) bounds appear in concentrability coefficients and Dobrushin/Doeblin coupling conditions that yield geometric contraction. But generic Banach contraction (e.g., gradient descent on a strongly convex smooth function, kappa=1-mu/L) has a modulus set by curvature/conditioning with no reweighting structure at all, so the projection is false as a general claim. It is a real phenomenon in distribution-coupling settings and a non-sequitur elsewhere, hence genuinely interesting only when restricted.
- **C3** — _implausible_: A finite-capacity / complexity-control premise underlies weighted exchangeability and hence conformal coverage.
  - reasoning: This conflates two unrelated mechanisms: conformal coverage follows from the symmetry/exchangeability of the rank statistic and holds in finite samples for ANY (even infinite-capacity or adversarially complex) score function, with no VC or capacity assumption whatsoever — that distribution-free property is conformal's defining selling point. Weighted exchangeability (Tibshirani et al.) is an algebraic property of the joint law under reweighting, not a uniform-convergence condition, so finite VC dimension is neither necessary nor sufficient for it. The structure-mapping put capacity control in the slot of the property that earns the guarantee, but in conformal the guarantee is earned by exchangeability instead, so the projection is largely spurious.
- **C4** — _uncertain_: The ERM / uniform-convergence operator has a fixed point.
  - reasoning: Uniform convergence is a concentration statement (sup over a class of |empirical - true risk|), not an operator with a domain mapped to itself, so fixed point is not even type-correct for it. There is a real but different sense in which the projection lands: many learning algorithms ARE fixed-point iterations — gradient descent/EM/self-consistent estimating equations converge to a stationary point of the empirical risk, and population risk minimizers satisfy first-order fixed-point conditions. So the conjecture is false as literally about the uniform-convergence operator but points at a true adjacent fact about risk-minimization dynamics.
- **C5** — _uncertain_: The no-regret online play has a fixed point - a limit object the play converges to.
  - reasoning: The Banach projection invents a unique attracting fixed point for the iterates of no-regret play, and as a general claim this is false: no-regret guarantees control time-averaged loss, not iterate convergence, and last-iterate behavior of OGD/FTRL in games generically cycles or diverges (zero-sum bilinear games being the canonical counterexample). What actually converges is a different object: the empirical distribution of play converges to the set of coarse correlated equilibria (a set, not a Banach fixed point), and in single-objective OCO the averaged iterate converges to the minimizer via online-to-batch. However, in restricted regimes the projection is literally correct: for strongly monotone games or a fixed strongly convex loss, the OGD update operator is a genuine contraction and its Banach fixed point (the equilibrium/minimizer) attracts the last iterate. So the conjecture is a real phenomenon under curvature/monotonicity assumptions but conflates averaged-play limit sets with contraction fixed points in general.
- **C6** — _plausible_: The weighted conformal calibration procedure is a no-regret play: bounded loss gradients over the reweighted calibration data drive no-regret behavior of the calibration/test procedure.
  - reasoning: This projection lands almost exactly on adaptive conformal inference: Gibbs and Candes recast conformal calibration under distribution shift as an online (sub)gradient descent on the pinball/quantile loss, where the gradient is bounded by max(alpha, 1-alpha), and it is precisely this bounded-gradient structure that yields regret bounds and long-run coverage guarantees without exchangeability. Subsequent work makes the no-regret framing explicit, treating online conformal as an OCO problem with regret and dynamic-regret guarantees. The engine's causal skeleton CAUSE(bounded gradients, no regret) is the correct OGD mechanism transplanted to the correct neighboring literature. The main defect is in the bindings: the target paper (Lei & Candes 2020) is a batch procedure, and the likelihood-ratio weights are fixed density ratios, not learned iterates achieving regret - the true no-regret object is the adaptively updated quantile/coverage level, not the_weights. So the specific instantiation is type-loose, but the claim it points at is established mathematics.
- **C7** — _uncertain_: A curvature (strong-convexity) bound causes the offline gradient-descent map to behave as a no-regret play with modulus kappa.
  - reasoning: The statement is type-incorrect as written: 'no-regret' is a property of a sequential player facing a stream of adversarial losses, not of a fixed offline gradient-descent map, so NO_REGRET(the_map, kappa) does not parse as a theorem. But the causal skeleton points at a true and well-known correspondence: strong convexity (a curvature bound with modulus kappa) simultaneously makes online gradient descent achieve O(log T) regret and makes the offline GD map a kappa-dependent contraction with linear convergence - the same curvature quantity drives both, and online-to-batch conversion turns the log-regret bound into an O(log T / T) batch convergence rate. Read charitably, the conjecture is the regret-to-convergence bridge with the wrong type on the conclusion; read literally, it attributes a regret property to a deterministic operator. The modulus kappa is genuinely the shared parameter, which is why this projection half-lands.

## 6. Research directions

The *uncertain*-judged conjectures refined into precise, citation-grounded programs (Epic Y):

### C2 — narrow
- **Precise statement**: In Markov-chain/MDP settings, the contraction modulus of a Markovian operator is controlled by a likelihood-ratio/change-of-measure quantity: Dobrushin's ergodic coefficient and Doeblin's minorization condition (P(x,.) >= beta*nu(.)) yield geometric contraction with modulus (1-beta) in total variation, and in approximate dynamic programming the L2(mu)-contraction modulus of the projected Bellman operator is governed by concentrability coefficients C = sup ||d(P^pi rho)/d mu||_inf, i.e. a sup of Radon-Nikodym derivatives between the visitation distribution and the sampling distribution mu.
- **Open question**: Is there a sharp, non-trivial CHARACTERIZATION (not just an upper bound) of the L2(mu) contraction modulus of the projected Bellman operator Pi_mu T^pi in terms of a likelihood-ratio functional -- i.e. does the modulus equal (or is two-sided-bounded by) gamma times a measure of mismatch between mu and the discounted visitation distribution d^pi, rather than the loose sup-norm concentrability C that can be infinite even when the operator is contractive?
- **Next step**: Attempt to prove a two-sided bound gamma * f(mu, d^pi) <= ||Pi_mu T^pi||_{L2(mu) Lip} <= gamma * g(mu, d^pi), where f,g are explicit divergence-like functionals (e.g. chi-square divergence chi^2(d^pi||mu) or a spectral mismatch ratio lambda_max(Sigma_{d^pi}/Sigma_mu)) of the Radon-Nikodym derivative d(d^pi)/dmu; test tightness numerically on small finite MDPs (random chains, ~20 states) by comparing the empirically estimated operator Lipschitz modulus against the candidate functionals across a sweep of sampling distributions mu.

### C4 — promising
- **Precise statement**: The 'fixed point' core is type-correct not for the uniform-convergence statement itself but for the empirical-risk MINIMIZER: many M-estimators are defined by an estimating-equation/self-consistency fixed point, T_n(theta) = theta where T_n is the empirical map (e.g. the EM operator, the Newton/gradient map of a smooth empirical objective, or the proximal/contraction map of a regularized problem), and uniform convergence is what transfers properties of the population fixed point theta* (T(theta*)=theta*) to the empirical fixed point theta_n.
- **Open question**: Can uniform-convergence rates be packaged as a quantitative perturbation bound on fixed points: given that the empirical operator T_n is uniformly close to the population operator T (sup ||T_n - T|| <= eps_n with high probability) and T is a local contraction with modulus kappa<1 near theta*, does ||theta_n - theta*|| <= eps_n/(1-kappa) hold with the SAME high probability, and what is the weakest uniform-convergence/stability condition on the operator class {T_theta} (as opposed to the loss class) that yields it?
- **Next step**: Prove a 'fixed-point uniform convergence' theorem: define the operator class F = {theta -> grad_theta ell(.,theta)} or the EM map, bound its Rademacher complexity / establish a uniform ||T_n - T||_inf <= eps_n bound, and combine with Banach perturbation (||theta_n-theta*|| <= eps_n/(1-kappa)) to get a finite-sample fixed-point error; instantiate concretely for Gaussian-mixture EM to recover the Balakrishnan-Wainwright-Yu rate purely from an operator-class uniform-convergence argument, then identify whether operator-class complexity can be strictly smaller than loss-class complexity.

### C5 — promising
- **Precise statement**: The type-correct core of C5 is a regime dichotomy for the limit objects of no-regret play. In multi-agent settings, the guaranteed limit object of no-regret dynamics is set-valued and statistical: the empirical distribution of joint play converges to the set of coarse correlated equilibria; there is in general no attracting fixed point of the iterates, and for bilinear zero-sum games the last iterate of vanilla OGD provably cycles or diverges (Poincare recurrence). The skolem fixed point becomes a real object exactly when the game operator F is mu-strongly monotone and L-Lipschitz: then for step size eta < 2*mu/L^2 the OGD update z -> z - eta*F(z) is a Banach contraction with modulus sqrt(1 - 2*eta*mu + eta^2*L^2) < 1, and the unique Nash equilibrium is its fixed point, attracting the last iterate geometrically. Between these poles (merely monotone operators, constrained sets, non-monotone games) the behavior of the vanilla last iterate is governed by the spectrum of the Jacobian I - eta*DF(z*) at equilibrium: eigenvalues inside the unit disk give local contraction, eigenvalues on the unit circle give rotation/recurrence. The sharpened claim is therefore: 'no-regret play has an attracting fixed point iff the linearized OGD map at equilibrium is a local contraction, with strong monotonicity as the global sufficient condition; otherwise the correct limit object is the CCE set of averaged play.' The research direction is to characterize the phase boundary between these regimes, especially under constraints and in non-monotone games, where neither pole applies cleanly.
- **Open question**: For vanilla fixed-step projected OGD on a constrained game with a monotone-but-not-strongly-monotone (or locally non-monotone) operator, characterize exactly - in terms of the spectrum of the projected linearization at equilibrium and the geometry of the active constraint face - when the last iterate converges for all initializations versus enters recurrence. In particular: is spectral radius strictly less than 1 of the projected Jacobian I - eta*DF(z*) restricted to the tangent cone both necessary and sufficient for local last-iterate convergence, and does constraint projection ever convert a recurrent unconstrained dynamic into a convergent one at positive measure of initializations?
- **Next step**: A pure-numpy sweep on parametrized two-player quadratic games: operator F(z) = (mu*I + gamma*S)z + b with S skew-symmetric, sweeping mu in [0, 1] (strong-monotonicity dial) and gamma (rotation dial), plus box constraints toggled on/off. For each (mu, gamma, eta) cell, run vanilla projected OGD from random initializations, record last-iterate distance to equilibrium and averaged-play distance to the CCE set, and separately compute the spectral radius of the (projected) linearized map. Plot the empirical convergence/cycling phase diagram against the predicted spectral-radius-equals-1 curve; the interesting cells are constrained ones where the active face changes the effective Jacobian. This directly mirrors the C2 finite-MDP sweep in scale: a few hundred lines, minutes of compute, and it either confirms or breaks the necessity direction of the conjectured spectral characterization.

### C7 — narrow
- **Precise statement**: The type-correct core of C7 is that a single curvature modulus mu (equivalently condition number kappa = L/mu) simultaneously drives two theorems of different type, connected by a lossy bridge. Online: OGD with step 1/(mu*t) on any adversarial sequence of mu-strongly-convex losses has regret at most (G^2/(2*mu))(1 + log T) (Hazan-Agarwal-Kale), and this log T is tight. Offline: the fixed map x -> x - eta*grad f(x) on a single mu-strongly-convex, L-smooth f with eta <= 1/L is a (1 - mu*eta)-contraction, giving geometric last-iterate convergence. Online-to-batch conversion transports the first to the second but only up to O(log T / T) suboptimality of the averaged iterate - exponentially weaker than the contraction rate - so the analogy engine's CAUSE arrow is correct about the shared modulus but wrong to suggest the regimes are equivalent: adversarial regret provably cannot certify geometric convergence. The sharpened program is to quantify the interpolation between the two poles: for loss sequences that are all mu-strongly convex with minimizers drifting with path length P_T, the last iterate of constant-step OGD tracks at a rate 'geometric contraction plus kappa-dependent drift term,' recovering linear convergence when P_T = 0 and dynamic-regret behavior when P_T grows. The open frontier is whether one parameter-free algorithm can sit at both poles simultaneously without knowing which regime it is in.
- **Open question**: Does there exist a single parameter-free online algorithm that, on any adversarial sequence of mu-strongly-convex losses (mu unknown), guarantees O((G^2/mu) log T) regret, and additionally, whenever the sequence is eventually a fixed smooth strongly convex f, has last iterate converging geometrically at a rate polynomial in the true kappa - with a matching lower bound showing what degradation of the geometric rate (if any) is the necessary price of adversarial robustness? The question is genuinely open because existing curvature-adaptive methods (MetaGrad-style) control averaged regret only, and known last-iterate geometric guarantees all require knowing step sizes tied to mu and L in advance.
- **Next step**: A numpy experiment on quadratics f_t(x) = 0.5*(x - c_t)' H (x - c_t) with H of condition number kappa in {1, 10, 100}: three regimes - fixed c_t (offline pole), drifting c_t with controlled path length P_T, and adversarially alternating c_t. Run (a) OGD with eta_t = 1/(mu*t), (b) constant-step OGD with eta = 1/L, and (c) a simple curvature-adaptive candidate (e.g., a doubling-trick hedge over a geometric grid of step sizes, or coin-betting), logging both cumulative regret and last-iterate error. Verify the predicted log T / T versus geometric versus contraction-plus-P_T rates, then measure whether the adaptive candidate's last-iterate rate on the fixed-loss regime degrades with kappa faster than the informed constant-step baseline - that degradation curve is direct evidence for or against a price-of-robustness lower bound. This is the same scale as the C4 Gaussian-mixture-EM experiments: small, deterministic, and it turns the open question's quantitative form into a measurable exponent.

## 7. Numerical experiments

Three research directions carried through to computation, in pure Python (project doctrine):

### C2 — contraction modulus vs. change-of-measure (finite MDP)

On random 6-state Markov chains (γ=0.9), the L2(μ) contraction modulus of the projected Bellman operator, as the weighting μ moves away from the stationary d:

| χ²(d‖μ) | L2(μ) modulus |
|---|---|
| 0.0000 | 0.9000 |
| 0.0450 | 0.9169 |
| 0.1539 | 0.9567 |
| 0.3252 | 1.0167 |
| 0.5868 | 1.1022 |
| 1.0131 | 1.2281 |

At μ=d the modulus is exactly γ=0.9 (Bertsekas–Tsitsiklis, ‖P‖_L2(d)=1); it rises monotonically with the χ² mismatch until the operator is no longer a contraction.

### C4 — fixed-point uniform convergence (Gaussian-mixture EM)

On the Balakrishnan–Wainwright–Yu symmetric 2-Gaussian-mixture EM operator M(θ)=E[X·tanh(Xθ/σ²)] (θ*=3.0, σ=1.0): population fixed point M(θ*)=θ* recovered as 3.000000, local contraction modulus κ=0.0210<1. The Banach bound ‖θ̂ₙ−θ*‖ ≤ εₙ/(1−κ) holds for every sample:

| n | εₙ (sup‖Mₙ−M‖) | fixed-point error | bound εₙ/(1−κ) | εₙ·√n |
|---|---|---|---|---|
| 100 | 0.0841 | 0.0827 | 0.0859 | 0.841 |
| 200 | 0.0618 | 0.0607 | 0.0632 | 0.875 |
| 400 | 0.0413 | 0.0406 | 0.0422 | 0.826 |
| 800 | 0.0243 | 0.0238 | 0.0248 | 0.686 |
| 1600 | 0.0234 | 0.0230 | 0.0239 | 0.936 |

The fixed-point error tracks the bound within a few percent and decays at the 1/√n uniform-convergence rate — recovering the BWY guarantee from an operator-class argument.

### C5 — OGD convergence/recurrence phase diagram vs. the spectral radius

Direction C5 — generated, judged *uncertain*, and refined in the same loop — proposed testing whether vanilla OGD's last-iterate behaviour on two-player quadratic games F(z)=(μI+γS)z+b is governed by the spectral radius ρ of the linearized map (η=0.1, 2000 steps):

| μ | γ | ρ (spectral) | empirical rate | phase |
|---|---|---|---|---|
| 1.00 | 0.50 | 0.9014 | 0.9014 | converge |
| 1.00 | 1.00 | 0.9055 | 0.9055 | converge |
| 1.00 | 2.00 | 0.9220 | 0.9220 | converge |
| 0.50 | 0.50 | 0.9513 | 0.9513 | converge |
| 0.50 | 1.00 | 0.9552 | 0.9552 | converge |
| 0.50 | 2.00 | 0.9708 | 0.9708 | converge |
| 0.20 | 0.50 | 0.9813 | 0.9813 | converge |
| 0.20 | 1.00 | 0.9851 | 0.9851 | converge |
| 0.20 | 2.00 | 1.0002 | 1.0002 | boundary |
| 0.10 | 0.50 | 0.9913 | 0.9913 | converge |
| 0.10 | 1.00 | 0.9950 | 0.9950 | boundary |
| 0.10 | 2.00 | 1.0100 | 1.0100 | diverge |
| 0.00 | 0.50 | 1.0012 | 1.0012 | boundary |
| 0.00 | 1.00 | 1.0050 | 1.0050 | boundary |
| 0.00 | 2.00 | 1.0198 | 1.0198 | diverge |

The empirical per-step rate equals ρ in every cell (the OGD map is a scaled rotation); the Banach condition η<2μ/L² is exactly ρ<1; and at the bilinear pole the averaged play converges toward the equilibrium (dist 0.07) while the last iterate wanders away (dist 5.12) — no attracting fixed point, exactly the C5 dichotomy.

## Reproducibility

```
make setup        # pinned deps, pure-Python
make pipeline     # the unified graph + discover/predict/evaluate
make experiment   # the C2 + C4 numerical experiments
make report       # regenerate this file
make test         # every epic's unit tests + integration
```

