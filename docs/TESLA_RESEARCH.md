# Tesla internships and project selection

Research checked: **10 November 2026**. Prepared for **Ahmad Essam Abdelaziz**.
Official listings can close or change. Some Tesla job pages rendered only a title/location shell;
detailed requirements below were available in search-indexed versions of Tesla's own listings.
Verify the current application page before applying. This is a skills-fit assessment, not an
eligibility determination or a prediction of employer interest.

## General requirements

Tesla's [internship page](https://www.tesla.com/careers/internships) asks for enrollment during
the placement, full-time on-site availability for at least 12 weeks, and authorization to work
in the host country. Sponsorship may be available; this does not promise sponsorship for a
particular candidate or role. [Intern resources](https://www.tesla.com/careers/intern-resources)
recommend applying early. Recent graduates should generally use full-time openings instead.

Ahmad's reported AI BSc and 2027 graduation make related-degree requirements plausible. Exact
graduation month, continuing enrollment, availability for the whole placement, relocation and work
authorization remain unverified. Check the host-country work authorization requirement separately
from degree eligibility; do not infer it from a degree or graduation date.

## Relevant roles

| Priority | Official role / location | Requirements and work | Fit and remaining evidence |
|---|---|---|---|
| 1 | [Core Infrastructure, Winter/Spring 2027, req 285085](https://www.tesla.com/careers/search/job/internship-ai-software-engineer-core-infrastructure-winter-spring-2027-285085), Palo Alto | May 2027–May 2028 graduation range; Python/Go, Linux, concurrency, infrastructure and data stores. Builds inference/simulation/evaluation workflows, observability and reliable backends. | Strong overlap with evaluation and reliability projects; FleetSlice supplies paired regression tests and reporting. Cluster operations and PostgreSQL/Redis remain separate skills to prove. |
| 2 | [Inference Infrastructure, Summer 2027, req 289254](https://www.tesla.com/careers/search/job/289254), Palo Alto | Starts around May; 12 weeks / 40 hours on-site. Listed graduation range August–December 2027. Python plus systems, job orchestration and ML workload familiarity. | Good direction for Python/backend experience; exact graduation window could exclude an earlier 2027 graduation. This prototype does not demonstrate hardware fleet orchestration. |
| 3 | [SI Data Infrastructure, Winter/Spring 2027, req 282292](https://www.tesla.com/careers/search/job/internship-software-engineer-si-data-infrastructure-winter-spring-2027-282292), Palo Alto | May 2027–May 2028 graduation range; application languages, Linux/networking/storage, databases and automation. Works on fleet data collection and processing. | Data validation, traceability and failure curation fit. Distributed ingestion, cloud cost and fleet-scale reliability need more evidence. |
| 4 | [Machine Learning Intern, Generative SI Applications, req 287334](https://www.tesla.com/careers/search/job/machine-learning-intern-generative-si-applications-m-f-d-gigafactory-berlin-brandenburg-287334), Berlin | Six months, full-time; upload portfolio with CV. Shipped useful software, independent ownership, English, web skills; TypeScript/React/Node are advantages. | Ahmad's full-stack apps and agents may be a more direct fit than this driving tool. Demonstrated users and measured impact matter; do not claim users without evidence. |
| 5 | [Charging Data Modeling ML Engineer, Winter/Spring 2027, req 281940](https://www.tesla.com/de_DE/careers/search/job/internship-charging-data-modeling-machine-learning-engineer-winter-spring-2027-281940), Palo Alto | Quantitative degree, May 2027–May 2028 graduation; Python, SQL and statistical/ML analysis. Fleet/charging optimization, simulation, time-series and geospatial work. | Good AI/data overlap. A charging optimization project would be more direct for this role. |

The [AI Platforms integration role, req 277009](https://www.tesla.com/careers/search/job/internship-software-integration-engineer-ai-platforms-winter-spring-2027-277009)
also exists, but asks for substantially more modern C++, embedded/real-time systems and vehicle
protocol experience. Ahmad's AVR vehicle work is useful context, not evidence of that entire stack.
No matching UK software internship was confirmed in this research; this is not evidence none exist.

## Why this problem matters to Tesla

Tesla's public [AI / robotics page](https://www.tesla.com/AI) describes evaluation infrastructure
for tracking improvements and preventing regressions, as well as perception, trajectory planning,
and efficient inference. Core Infrastructure listings connect evaluation workloads with dependable
backend tooling. These sources support selecting a validation tool as a relevant portfolio problem.
They do not establish that Tesla wants this exact implementation.

## Candidate projects considered

These are qualitative judgments about Ahmad's background and a feasible initial build.

| Idea | Strength | Constraint | Decision |
|---|---|---|---|
| Slice-aware motion forecast regression tool | Connects Python, evaluation, reliability and public autonomy data; has an inspectable failure demonstration | Needs honest statistical limits; is not a self-driving system | Selected: FleetSlice |
| Charging-aware fleet scheduler | Direct energy/fleet optimization relevance | Strong validation needs realistic demand, queues, service constraints and fair baselines | Good next specialization |
| Lightweight visual defect detector | Connects computer vision to manufacturing | Common project; domain shift and factory labels are difficult | Less distinctive initial choice |
| General Tesla chatbot | Quick full-stack/LLM demonstration | Weak evidence of autonomy/data infrastructure skill | Lower priority for selected target roles |

FleetSlice's useful property is that a model update cannot earn a favorable result merely by
improving an aggregate average. Adequately sampled motion slices can independently flag a regression,
and low-evidence cases remain inconclusive. This is an engineering contribution Ahmad can explain,
test, extend and demonstrate without access to Tesla's private data or hardware.

## Application use

For infrastructure roles, lead with reproducible evaluation, strict data contracts, CI gates,
failure triage and the real-data reproduction. For Berlin applied AI, lead with an existing shipped
full-stack product and user impact; present FleetSlice as additional engineering evidence.

Suggested fact-based project description, after understanding and reproducing it:

> Built a Python motion-forecast regression evaluator with paired scene bootstrap intervals,
> history-based scenario slices, failure triage, and offline trajectory reports; validated the
> workflow on public Argoverse 2 scenes and a controlled hidden-regression fixture.

Do not claim Tesla use, production fleet scale, trained deep models, safety certification, or an
accuracy improvement based on injected fixture predictions. Use measured outputs in EXPERIMENTS.md
when discussing results. Add your own extension and be ready to explain the formulas and limitations.

## Technical primary sources

- [Argoverse 2 data and terms](https://www.argoverse.org/av2.html)
- [Official motion forecasting guide](https://argoverse.github.io/user-guide/tasks/motion_forecasting.html)
- [Official AV2 serialization/schema implementation](https://github.com/argoverse/av2-api/blob/main/src/av2/datasets/motion_forecasting/scenario_serialization.py)
- [Official Argoverse displacement metric implementation](https://github.com/argoverse/argoverse-api/blob/master/argoverse/evaluation/eval_forecasting.py)

There is no claim of algorithmic novelty. The differentiation is a cohesive, small, reproducible
regression workflow and transparent interpretation, rather than a new motion prediction model.
