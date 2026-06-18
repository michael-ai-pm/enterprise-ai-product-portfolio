# Enterprise AI Strategy and Operating Model
## A worked example of how to run a portfolio of production AI products

**Document type:** AI Strategy and Operating Model (worked example)
**Audience:** Anyone evaluating how a senior AI Product Manager thinks about portfolio strategy, operating model design, governance, and unit economics for production AI
**Author:** Michael, Ai Senior Product Manager (Data and AI Platform)
**Status:** Public v1.0

---

## 1. Executive Summary

Most AI product portfolios don't fail because the models are weak. They fail because the organisation running them treats AI as a collection of disconnected experiments, each with its own tooling, its own governance assumptions, and its own definition of success. The result is 20 pilots that look impressive in demos and generate almost no traceable value. I have seen this pattern close enough to know how quickly it solidifies into something expensive and difficult to unwind.

The fix isn't more pilots. It's one platform, one lifecycle from intake to retirement, one governance framework, and one FinOps model, applied consistently across every product in the portfolio. That is the argument this document makes.

The worked example uses a fictional studios business called MetroStudios. The choice of domain is deliberate. The content production lifecycle is end-to-end and visible, which makes the portfolio decisions feel concrete rather than abstract. But the patterns themselves are domain-agnostic. The intake-to-retirement lifecycle, the six-gate operating model, the multi-team RACI, the EU AI Act classification approach, and the cost-floor FinOps model all transfer without modification to a bank, a healthcare insurer, a consultancy, or a frontier lab's enterprise deployment programme.

The worked example illustrates how a fictional studios business operationalises AI across its full content production lifecycle by building a single Data and AI Platform that supports a portfolio of 12 products at varying maturity levels. The platform converts AI capability into measurable business outcomes. It is governed by a single operating model that spans Product, Data, Engineering, Legal, Cyber, and Vendor Management.

Success is measured on 3 outcomes regardless of industry.

The first is operational efficiency: time and cost reduction across the workflows the portfolio targets. 
The second is commercial value: demonstrable revenue uplift or margin gain in the business lines the portfolio supports. 
The third is responsible adoption: zero high-severity incidents under the EU AI Act framework, with 100% of in-production use cases covered by approved governance artefacts.

This document sets out the strategy, the 12-product portfolio, the operating model from intake to retirement, the governance framework, the value framework, and the three-year roadmap.

---
## 2. Strategic Context

### 2.1 Why now

Three forces converge in 2026 that make this the right moment to operationalise AI at portfolio level, rather than continuing to run isolated experiments. I would make the same argument regardless of the industry.

The first force is production readiness. Generative and agentic AI have crossed the threshold for the workflows that dominate enterprise operations: research, summarisation, structured generation, classification and tagging, triage, and decision support. A year ago it was reasonable to treat these capabilities as experimental. It is no longer reasonable.

The second force is the visible cost of fragmentation. Across industries, organisations are running 20 or more shadow AI tools per business unit, with no governance, no eval baseline, and no FinOps oversight. The cost isn't the tools themselves. It's the duplicated effort, the legal exposure, the audit findings, and the loss of cross-product learning that accumulates when every team runs its own stack.

The third force is regulation. The EU AI Act is live and applies to a wider range of enterprise use cases than most organisations have acknowledged: any decision support touching employment, credit, healthcare, content moderation, or biometrics, as well as vendor-provided general-purpose models. Operating without a governance framework is a commercial risk, not just a legal one.

In the worked example, these 3 forces show up concretely. Production-ready capability exists for research and tagging across the content lifecycle. Adoption of casting and post-production tools is already fragmented across business units. And EU AI Act exposure on casting triage and AVOD personalisation is real and unmanaged.

### 2.2 What we are not doing

Scope discipline is as important as the strategy itself. To avoid the trap of "AI everywhere, value nowhere," this platform explicitly doesn't attempt to build 12 products in parallel. The portfolio is sequenced, and the sequencing is revisited quarterly.

It doesn't replace human judgement in decisions that materially affect people. In the studios example, that means casting, commissioning, and compliance. The platform supports those decisions. Human accountability is preserved at every approval gate.

It doesn't mandate a single vendor or model. Vendor diversity is part of the resilience strategy, and the reasons for that are covered in the vendor section of this document.

### 2.3 Target outcomes

The 3 horizons below set the direction. The measures are deliberately concrete, because vague outcomes are the first sign that an organisation isn't serious about tracking value.

By the end of Year 1, 4 products should be in production and 8 in discovery or pilot. The measures are the number of active products and the eval pass rates at each gate.

By the end of Year 2, a portfolio-wide eval framework should be in place and a FinOps baseline established. The measures are cost per use case and value tracked per product.

By the end of Year 3, the AI Platform should be the default rail for any new enterprise initiative. The measure is the percentage of new initiatives launched on the platform rather than outside it.

---
## 3. The AI Portfolio

The portfolio I'm describing here has 12 products. They map to the stages of an end-to-end operational lifecycle, and that structure is deliberate. The principle isn't specific to a studios business. Any enterprise can apply the same approach to its own value chain: loan origination through to default management for a bank, patient intake through to discharge and follow-up for a healthcare provider, lead through to renewal for a B2B SaaS business. The worked example uses a fictional studios business called MetroStudios because it gives the decisions a concrete shape. The product names change. The logic behind sequencing, gating, and retiring them doesn't.

### 3.1 Lifecycle map

| Lifecycle stage | Product |
|---|---|
| Development | Script Coverage Assistant |
| Development | YouTube and Social Trend Analyser |
| Pre-production | Production Budget Assistant |
| Pre-production | Casting Submission Triage Agent |
| Production | Music and Rights Clearance Assistant |
| Post-production | AI Object and Face Tagging (DAM) |
| Post-production | Compliance and Edit Review Assistant |
| Asset management | AI Agent Studio for DAM workflows |
| Asset management | Content Catalogue Integration |
| Localisation | Subtitle and Translation Automation |
| Distribution and Monetisation | AVOD Optimisation |
| Sales | Sales Market Intelligence Agent |

### 3.2 How sequencing decisions get made

Every product in the portfolio is scored on 4 criteria, reviewed quarterly: business value, technical feasibility, regulatory risk, and team readiness. Nothing enters the build phase without scores against all 4. That isn't a bureaucratic gate for its own sake. It's the thing that stops a team spending 6 weeks building a product that legal could never approve, or that the business unit won't adopt because the underlying data isn't ready.

Products are also explicitly retired. This is the part most portfolio documents leave out, because retirement feels like failure. I don't think it is. A product should leave the portfolio when its value falls below the unit-cost floor, when vendor risk crosses a threshold that cannot be remediated, or when a successor product reaches parity. Keeping a product alive past that point does not protect the business. It just makes the portfolio harder to manage and harder to fund.

### 3.3 Year 1 priority products

Not everything moves at once. The Year 1 split is:

**Tier 1 (build to production):** Sales Market Intelligence Agent, AI Object and Face Tagging, Subtitle and Translation Automation, Casting Submission Triage Agent.

**Tier 2 (pilot):** Production Budget Assistant, YouTube and Social Trend Analyser.

**Tier 3 (discovery only):** Script Coverage, Music Clearance, Compliance Review, AVOD Optimisation, AI Agent Studio, Content Catalogue Integration.

The Tier 1 selection isn't arbitrary. These 4 products have the clearest value baseline, the most tractable data situation, and the lowest regulatory complexity relative to the business impact. They are also the 4 that demonstrate the widest spread of the platform's capabilities: research and synthesis, metadata extraction, language localisation, and document triage. Proving those 4 in production gives you the evidence base to fund everything else.

---
## 4. The Operating Model (Intake to Retirement)

A single end-to-end process governs every AI product in the portfolio, regardless of which business unit sponsors it or which vendor stack it runs on. The process has 6 gates. Nothing moves between them without explicit approval and documented evidence.

I want to be direct about why a six-gate process is necessary. The organisations I have seen struggle with AI at scale aren't struggling because they lack ideas or talent. They are struggling because individual teams make good local decisions that create bad portfolio-level outcomes. One team buys a vector database that another team has already evaluated and rejected. A high-risk use case gets treated as minimal risk at Gate 2 because no one checked. A product slips into production without a service owner. The gates below are designed specifically to prevent those failure modes, not to slow things down.

### 4.1 Gate 1: Intake and Triage

Any person in the organisation can submit an idea through a standard intake form. Triage runs weekly and applies a three-question filter.

The first question is whether the underlying problem is real and quantified. Vague statements of opportunity don't pass. If the team can't say what the baseline cost or time is, the idea goes back for more definition.

The second question is whether AI is actually the right intervention. Many problems that get submitted as AI use cases are better solved by a workflow change, a data quality fix, or a simple automation. Forcing this question at intake saves significant build investment.

The third question is whether the use case falls under prohibited or high-risk EU AI Act categories. Catching this at Gate 1 prevents the situation where a team builds for 4 weeks before legal is consulted.

Outcome: the use case is rejected, parked for a future quarter, or progressed to discovery.

### 4.2 Gate 2: Discovery and Value Proof

Discovery runs for 2 to 4 weeks. The output is a one-page value proof. One page is a constraint, not a suggestion. A longer document at this stage usually means the team hasn't yet made a decision; they have listed options. The one-page format forces clarity on: the user and their job to be done, the baseline cost or time, the expected improvement, the data availability, the model class, and the top 3 risks.

The EU AI Act classification happens here. This is the most important governance decision the product will ever go through, because it determines the governance load for the rest of its lifecycle. Getting it wrong is expensive, and I cover why in the governance section.

### 4.3 Gate 3: Investment Case

Discovery outputs feed into a formal investment case reviewed by the AI Portfolio Council. The case must include a build-versus-buy recommendation, a vendor shortlist if buying, eval criteria with target thresholds, a cost model with three-year total cost of ownership, and the EU AI Act classification confirmed by legal.

I want to be specific about the eval thresholds. They are agreed at Gate 3, before any build starts. This isn't standard practice in most of the organisations I have seen, and it's the main reason evaluation is treated as a post-hoc exercise rather than a production gate. If you don't agree the threshold before you build, you will always find a reason why the current output is "close enough." Agreeing it upfront removes that rationalisation.

### 4.4 Gate 4: Build and Eval

The build phase is engineering-led. The PM owns 5 things during this phase: the eval framework setup, the data contracts with upstream systems, the human-in-the-loop design, the change management plan for the business unit, and the delivery backlog. That last responsibility means working with Engineering to define acceptance criteria per sprint, prioritising iteration cycles based on eval findings, and surfacing blockers to the Portfolio Council before they become delays.

No build is considered complete without a passing eval scorecard against the thresholds agreed at Gate 3. A product that has been built but not evaluated is not ready for Gate 5. It is ready for more iteration.

### 4.5 Gate 5: Rollout

Rollout is staged, with an explicit group definition before it starts. A shadow-mode period is mandatory for any use case that touches commercial decisions, which in the MetroStudios example means casting, commissioning, and AVOD. In shadow mode the agent runs in full but the output is reviewed without acting on it. This is how you find the failure modes that your golden set didn't surface.

The rollout expands only when metrics clear their thresholds: adoption rate, eval drift, support tickets, and override rate. Override rate is particularly important. If users are consistently editing or ignoring the agent's output, that is a signal either that the quality isn't there yet, or that the change management hasn't worked. Both are solvable. Neither is visible without measuring.

### 4.6 Gate 6: Operate and Retire

Every product in production has 4 things assigned: a named service owner, an eval refresh cadence, a FinOps owner, and documented retirement triggers. The retirement triggers are what make this a lifecycle rather than just a launch process.

A product enters formal retirement review when any of the following apply: its cost-to-value ratio crosses 1:2 over two consecutive quarters, the vendor fails to remediate eval drift within the agreed SLA, a regulatory change reclassifies the use case as high-risk, or a successor product reaches parity.

I treat retirement as a healthy portfolio signal, not a failure signal. The first product we retire demonstrates that the lifecycle works end to end. That is worth more to the organisation's confidence in the operating model than keeping a marginal product running to avoid the optics of shutting something down.

### 4.7 Portfolio cadence

The rhythm that keeps all 6 gates moving is:

- Weekly intake triage. 
- Bi-weekly eval drift review across all in-production products. 
- Monthly AI Portfolio Council covering Gate 3 and Gate 5 approvals and any retirement decisions. 
- Quarterly strategy refresh, vendor review, and FinOps review.

The monthly council is the heartbeat. Without it, Gate 3 cases queue up and block builds, and retirement decisions get deferred indefinitely. Booking the council as a fixed monthly commitment, not an ad hoc meeting, is what makes the cadence real.

---
## 5. Multi-Team Operating Model

The platform isn't a team. That distinction matters more than it sounds. A team can be disbanded, deprioritised, or reorganised away. A coordinated operating capability across 8 functions is structurally harder to dissolve because it is embedded in how the organisation already works.

### 5.1 Functions and accountabilities

The 8 functions below are the canonical set for any regulated enterprise running an AI portfolio. The names vary by industry. In a bank, Cyber becomes the CISO Office. In a large consultancy, Vendor Management becomes Procurement and Third-Party Risk. The accountabilities don't change, regardless of what the function is called.

| Function                          | Owns                                                                                                                                 |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Product (AI Platform)             | Strategy, roadmap, intake, governance facilitation, portfolio KPIs, delivery backlog during build phases                             |
| Data Engineering                  | Ingestion pipelines, data contracts, retrieval infrastructure                                                                        |
| ML Engineering                    | Model integration, evals infrastructure, observability                                                                               |
| Platform Engineering              | Shared services: auth, audit, logging, rate limiting, cost telemetry                                                                 |
| Business Units                    | Use case sponsorship, change management, adoption (in the worked example: Drama, Entertainment, Factual, Sport, Distribution, Sales) |
| Legal and Privacy                 | Risk classification, DPIAs, contract review, IP and rights                                                                           |
| Cyber and Information Security    | Threat modelling, data classification, vendor security review                                                                        |
| Vendor Management and Procurement | Vendor due diligence, commercial terms, exit planning                                                                                |

### 5.2 Decision rights

Three RACI areas need to be made explicit. In my experience, these are the 3 that generate the most ambiguity and the most expensive delays when they are left undefined.

The first is model choice. Product is accountable. ML Engineering is responsible for the technical evaluation. Cyber and Legal are consulted because model choice has security and data processing implications that most engineering teams underweight. Procurement is informed.

The second is the use of customer or talent data. Legal is accountable here, not Product. This matters because in regulated industries, "I thought it was fine" isn't a defensible position when a DPIA was skipped. Product is responsible for execution. Data Engineering is consulted on what is technically feasible. The business unit is informed.

The third is product retirement. The AI Portfolio Council is accountable for the decision. Product is responsible for preparing the case. Business Unit and Vendor Management are consulted because retirement has adoption and contract implications they need to manage. Everyone is informed.

### 5.3 Interface to business units

The "central AI team builds, business unit ignores" pattern is the single most common failure mode I have seen in enterprise AI programmes, across every industry. The fix isn't better communication. It's changing the accountability structure. Every business unit consuming AI capability has a named AI champion who sits on the AI Portfolio Council and owns adoption KPIs within their unit. When the champion's objectives include adoption, the conversation about rollout stops being "here is what we built for you" and becomes "here is what we are building together."

In the MetroStudios worked example, the business units are the Studios verticals: Drama, Entertainment, Factual, Sport, Distribution, and Sales. In a bank they would be Retail, Commercial, Wealth, and Markets. In a healthcare insurer they would be Claims, Underwriting, Member Services, and Provider Network. The shape is identical in every case: named champions, adoption targets in their objectives, success stories socialised before any attempt to scale.

---
## 6. Governance and Risk Framework

### 6.1 EU AI Act alignment

Every product is classified at Gate 2 against EU AI Act risk tiers. I want to be direct about why this happens at Gate 2 and not later: misclassifying a high-risk use case as minimal is the **single most expensive governance mistake in enterprise AI**. A product that has been built, evaluated, and launched under the wrong classification doesn't just need a governance document added retrospectively. It may need fundamental changes to the human-in-the-loop design, the audit logging, the fairness eval framework, and the vendor contracts. Catching the classification early isn't a bureaucratic nicety. It is a cost control decision.

The classification approach generalises across industries. Any product touching employment, credit, healthcare, education, biometrics, or content moderation triggers high-risk obligations regardless of the domain.

One framing point matters before the table. The 4 tiers aren't a single ladder. The Act treats prohibited, high-risk, limited risk, and minimal risk as overlapping categories, not mutually exclusive rungs. A system can be high-risk and also carry Article 50 transparency obligations at the same time. Limited risk isn't a softer version of high-risk. It is a specific label that means one thing: transparency obligations apply, and nothing else does. I'm deliberate about that wording because a reader who knows the Act will notice if it's used loosely.

The table below shows how the 12 MetroStudios products land.

| Product                          | Risk tier                                                      | Rationale                                                                                                                                                                                                                                                                                                                                                              |
| -------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Casting Submission Triage        | High-risk (Annex III, employment)                              | AI used in the recruitment or selection of candidates is an Annex III employment use case. Triggers conformity assessment, logging, human oversight, and fairness testing. Mandatory HITL.                                                                                                                                                                             |
| AVOD Optimisation                | Limited risk (Article 50 transparency)                         | A recommender and personalisation system. Not high risk, but where AI curated content reaches viewers, the relevant Article 50 disclosure applies.                                                                                                                                                                                                                     |
| Compliance and Edit Review       | Limited to high-risk, territory-dependent                      | Content review and moderation. The tier depends on whether the deployment territory or use brings it into a regulated Annex III area. Classified per deployment at Gate 2.                                                                                                                                                                                             |
| Sales Market Intelligence        | Minimal risk                                                   | Internal research support. No automated decision making affecting individuals, no biometric processing.                                                                                                                                                                                                                                                                |
| Object Recognition (DAM)         | Minimal risk                                                   | Tags scenes, props, locations, and other non-person objects. No biometric data is processed and no decision affects individuals. No Annex III trigger.                                                                                                                                                                                                                 |
| Face Tagging / Recognition (DAM) | High-risk (Annex III, biometrics) if it identifies individuals | "One to many" facial identification across an asset library is remote biometric identification under Annex III. Triggers conformity assessment, logging, human oversight, and EU database registration. Pure face detection that never identifies who the person is falls outside this and is minimal risk. The classification turns on identification, not detection. |
| All others                       | Minimal risk                                                   | No automated decision-making affecting individuals and no biometric processing.                                                                                                                                                                                                                                                                                        |

### 6.2 Human-in-the-loop requirements

Three HITL patterns are defined in this operating model, each mandatory for the corresponding risk tier. The patterns are deliberately named by what the human does, not by how intrusive the AI involvement is, because "human in the loop" is otherwise vague enough to mean almost nothing.

Pattern A is suggestion only. The AI surfaces options and the human selects. No output reaches an external party without a deliberate human choice. This covers the Sales Market Intelligence Agent and the YouTube Trend Analyser.

Pattern B is draft and approve. The AI generates a draft, the human reviews it, and nothing is actioned or sent externally before sign-off. This covers the Production Budget Assistant and Subtitle Translation.

Pattern C is two-stage human review. The AI generates, a first reviewer approves, and a second reviewer spot-checks at a defined sampling rate. This covers Casting Triage and Compliance Review, where the stakes of a missed error are high enough to warrant redundancy in the human review layer.

### 6.3 Audit, observability and kill switches

Every product in production writes to a centralised audit log. The log captures the input hash, retrieval sources used, model output, human action taken, and timestamp. This isn't optional and it isn't configurable per product. The audit log is how the organisation demonstrates compliance, responds to incidents, and investigates eval drift when it is detected.

Eval drift detection runs continuously across in-production products. When drift crosses threshold, the named kill-switch operator for that product can disable it globally within 15 minutes via the Platform admin console. The operator list and the trigger criteria are documented at Gate 4 before any product goes live. A kill switch that hasn't been tested before an incident is a kill switch that will fail during one.

### 6.4 Vendor risk

Vendor due diligence covers 6 areas:

- data residency
- sub-processor disclosure
- model provenance, where the vendor will disclose it
- security certifications (ISO 27001 and SOC 2 Type 2 as a minimum)
- incident response SLA
- exit terms

No vendor is approved without a documented exit plan that includes data retrieval and a successor migration path.

The exit plan requirement sounds like overhead until the first time a vendor changes their pricing, discontinues a model version, or has a security incident. At that point, a documented exit plan is the difference between a managed transition and an emergency.

---

## 7. Value and FinOps Framework

One of the things I have observed across AI programmes is that value measurement tends to get treated as something to set up after the product ships. The cost of that delay is that by the time a product is in production, there is no baseline. Without a baseline, there is no delta. Without a delta, the case for continued investment becomes a conversation about opinions rather than evidence. This framework is designed to prevent that.

### 7.1 Value taxonomy

Every product has one primary value type, agreed at Gate 3 before any build starts. The taxonomy has 4 categories.

Cost reduction covers time saved, headcount equivalent freed up, and error rate reduction. This is the most common value type in the Year 1 portfolio, and also the easiest to measure because the baseline is usually available in operational data.

Revenue uplift covers new revenue generated, deal velocity improved, and average deal size increased. The Sales Market Intelligence Agent is the clearest example in this portfolio. The measurement requires coordination with Sales Ops to attribute pitch outcomes to briefing quality, which is why the Level 3 eval framework is set up before the product goes live.

Risk reduction covers compliance incidents avoided and audit findings reduced. This value type is harder to quantify because the baseline is counterfactual, but it is defensible with reference to historic incident rates and cost-per-incident data.

Strategic optionality covers capability enabled for future products. I include this category reluctantly. It is the value type most likely to be used to justify a product that has no clear near-term return. I require explicit written justification any time a product is classified here, because "we need it for the future" has ended more AI programmes than it has saved.

### 7.2 Unit economics

Every product reports unit economics monthly. The 4 metrics are cost per inference (model API cost plus retrieval plus observability), cost per user per month calculated on active users only, cost per business unit per month, and value generated against the documented baseline.

The active-user-only constraint on the second metric matters. Reporting cost per registered user rather than cost per active user is how programmes systematically understate the real cost of a product that most people have stopped using.

### 7.3 The cost floor

A product enters formal retirement review when its cost-to-value ratio crosses 1:2 over two consecutive quarters. Two consecutive quarters is not an arbitrary choice. A single bad quarter can reflect a data quality issue or a model update from a vendor. Two consecutive quarters at the same ratio is a signal about the product itself.

The cost floor is what protects the portfolio from accumulating products that look impressive in demos but are losing money quietly in production. Every AI portfolio I have seen without a cost floor has the same problem: a long tail of products in a permanent state of "we should probably improve this" that never get improved and never get retired.

### 7.4 FinOps tooling

Cost telemetry is owned by Platform Engineering and surfaced through a single dashboard accessible to Product, Finance, and business unit leads. Vendor pricing changes are surfaced to the FinOps owner within 48 hours of the change being announced or detected. The 48-hour requirement exists because vendor price changes directly affect the cost-floor calculation for every product using that vendor, and delayed awareness means delayed action.

## 8. Vendor Strategy

### 8.1 Build vs buy default

The default is to buy general-purpose capabilities: LLM access, vector storage, observability. We build where the capability encodes proprietary knowledge or workflow logic specific to the business. The line matters because vendors should not own the organisation's differentiation. If the thing that makes your AI product valuable can be replicated by a competitor buying the same vendor, you have not built a product. You have bought access to one.

That sounds obvious. In practice, most enterprise AI programmes blur this line by building bespoke infrastructure around commodity capabilities, then discover they have spent 6 months of engineering on something a managed service would have provided in a week. The build vs buy default is the decision that prevents that.

### 8.2 Vendor portfolio

I use a three-tier structure. Tier 1 covers strategic vendors for LLM access and model hosting, capped at 2 to 3 relationships. Multi-vendor at this tier is not a preference, it is a policy. A single LLM provider at Tier 1 creates pricing dependency, removes the ability to run A-B tests at model level, and leaves you exposed if that provider changes their terms or degrades a model version. Two providers at Tier 1 cost almost nothing extra to maintain and buy significant optionality. What makes that policy executable rather than aspirational is a self-hosted model gateway sitting in front of both. Without it, multi-vendor means two integrations and two code paths to keep in sync. With it, the providers are config behind a single stable interface, and switching or load-balancing between them is an operational decision, not an engineering project.

Tier 2 covers specialist vendors for specific capabilities: transcription, object tagging, viewing data analytics, rights metadata. These are selected per use case, not centrally mandated. The number varies between 5 and 8 active relationships depending on the portfolio stage.

Tier 3 is intentionally open. Short-term pilots and proof-of-value engagements with explicit exit dates. A Tier 3 vendor that does not graduate to Tier 2 within one portfolio cycle is terminated, not renewed by default.

### 8.3 Exit planning

Every Tier 1 and Tier 2 relationship has a documented exit plan. It is reviewed annually and must be confirmed before any renewal. The exit plan covers 3 things: how we retrieve our data, how long a migration would take, and which successor or alternative is already qualified. This is not a legal formality. It is the single most effective way to maintain negotiating leverage with a vendor who knows you are dependent on them.

---

## 9. Three-Year Roadmap

### 9.1 Year 1: Foundation

Year 1 is about proving the operating model works, not about maximising the number of products in production. That distinction matters. Organisations that push 10 products to pilot in Year 1 and then discover they have no eval framework, no governance artefacts, and no FinOps baseline have moved fast in the wrong direction.

The 4 priorities are: stand up the AI Portfolio Council with real decision rights, ship 4 Tier 1 products to production with passing eval scorecards, establish the FinOps baseline and governance artefacts for the full portfolio, and onboard Tier 1 and Tier 2 vendors with documented exit plans in place from day one.

By the end of Year 1, the operating model should be demonstrably real. If the portfolio council meets, if products pass evals before going live, if costs are tracked per product per month, the foundation is in place regardless of how many products are running.

### 9.2 Year 2: Scale

Year 2 moves the Tier 2 products from pilot to production and introduces the capability that makes the platform genuinely valuable at scale: cross-product retrieval. A shared knowledge layer across products means the second and third products benefit from the retrieval infrastructure built for the first. The unit economics of each new product improve. The platform starts to pay for itself.

Two other things happen in Year 2 that are less visible but equally important. The FinOps function matures from tracking costs reactively to modelling them predictively, which means pricing discussions with Tier 1 vendors happen from a position of knowledge rather than surprise. And the first scheduled product retirement demonstrates that the lifecycle works end-to-end. Retiring a product that has fallen below the cost floor is not a failure. It is the proof that the operating model has teeth.

### 9.3 Year 3: Platform

By Year 3, the platform becomes the default rail for any new enterprise initiative that requires AI. That is a different position from being a team that builds AI products on request. It means new use cases are evaluated through the intake process rather than being spun up independently, which is how you prevent the shadow AI fragmentation problem from recurring.

The interesting work in Year 3 is cross-product agentic workflows. In the MetroStudios context, that means a trend signal from the Trend Analyser triggering the commissioning agent, which triggers the Production Budget Assistant. The same pattern applies in any domain: a fraud signal triggering an underwriting agent, a patient intake event triggering a triage and scheduling workflow. The platform infrastructure built in Years 1 and 2 makes these workflows possible without starting from scratch each time.

External-facing AI products are also in scope for Year 3 where the business case supports them, but only under an explicit transparency framework. Viewer-facing personalisation, for instance, carries disclosure obligations under the EU AI Act. The governance work done in Year 1 makes those obligations manageable rather than blocking.

---

## 10. Key Risks and Mitigations

I want to be direct about something before presenting this section as a table. Most enterprise AI risk registers are written to satisfy a governance process, not to describe the risks that actually kill programmes. The 6 risks below are the ones I have seen damage or destroy AI portfolios in practice. The mitigations are not theoretical. They are the specific design decisions I have built into the operating model above.

The table format is useful for a quick scan. The commentary below each risk is what the table does not have room for.

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Shadow AI adoption outpaces governance | High | Medium | Make the platform path easier than the shadow path. Time-to-pilot under 6 weeks. |
| Vendor pricing changes break unit economics | Medium | High | Multi-vendor policy at Tier 1. Quarterly FinOps review. |
| Eval drift in high-risk products not detected in time | Medium | High | Continuous eval monitoring, mandatory HITL for high-risk products, kill switch within 15 minutes. |
| Business units do not adopt | High | High | Named champions, adoption KPIs in their objectives, success stories before scale. |
| Regulatory change reclassifies a product | Medium | Medium | Quarterly regulatory review, all products designed for graceful downgrade. |
| Talent shortage in ML engineering | High | Medium | Partnership with Tier 1 vendors for embedded engineering capacity in Year 1. |

The shadow AI risk is listed as medium impact because the damage is diffuse rather than acute. You do not lose a single incident. You lose months of duplicated effort, accumulate legal exposure in small increments, and miss the cross-product learning that only happens when products share an infrastructure. The mitigation is counter-intuitive: you do not stop people using shadow tools by banning them. You stop them by making the platform path faster and less painful than going around it.

The business unit adoption risk is listed as high likelihood because it is the default outcome if you do not deliberately design against it. Central AI teams that build without named business unit champions, without adoption KPIs embedded in objectives, and without documented success stories before scaling have a consistent failure mode: they produce technically correct products that nobody uses. The fix is not a better product. It is a different operating model.
