# Governance and Risk Framework
## A worked example of how to govern a portfolio of production AI products

**Document type:** Governance and Risk Framework (worked example)
**Audience:** Anyone evaluating how a senior AI Product Manager classifies, governs, and controls a portfolio of production AI products across risk tiers
**Author:** Michael, Ai Senior Product Manager (Data and AI Platform)
**Status:** Public v1.0

---

## About this document

This is the governance companion to the Strategy and Operating Model document. That document sets out the portfolio, the six-gate operating model, and where governance decisions sit in the lifecycle. This one does the next layer of work. It takes the risk classification, the HITL patterns, and the vendor and data controls that the Strategy document names, and it specifies what each of them actually obligates the organisation to build and own.

I have kept the worked example consistent throughout. The 12 products are the fictional MetroStudios portfolio, the same set used in the Strategy and Architecture documents. The classifications and patterns are domain-agnostic. The same shape applies to a bank, a healthcare insurer, a consultancy, or a frontier lab's enterprise deployment programme.

How to read it by interest:

- If you care about **EU AI Act classification and obligations**, section 1 maps each tier to its concrete deliverables.
- If you care about **human oversight design**, section 2 assigns every product a HITL pattern and specifies what each pattern obligates.
- If you care about **auditability and incident response**, section 3 covers the audit log schema and the kill switch design.
- If you care about **vendor and data risk**, sections 4 and 5 cover the AI-specific vendor failure modes and the tier-driven data handling rules.

---

## 1. Classification and Resulting Obligations

Every product in the portfolio is classified against EU AI Act risk tiers at Gate 2, and the full classification table with rationales lives in the Strategy and Operating Model document, section 6.1. I'm not going to repeat that table here. Repeating it would split the source of truth, and the first time a classification changes I would have to remember to update it in 2 places. The classification belongs in one document. This document does the next piece of work: what each tier actually obligates the organisation to do.

That distinction matters because a risk tier on its own is just a label. The label is only useful once it maps to concrete, ownable obligations. A product classified high-risk doesn't need a heavier governance process in the abstract. It needs a conformity assessment, a logging design, a defined human oversight pattern, a fairness eval, and in some cases registration in the EU database. Those are specific deliverables with named owners and gate checkpoints. The table below is that mapping.

I want to be direct about one thing before the table. The 4 tiers are not a single ladder where each rung is a softer version of the one above. Prohibited, high-risk, limited risk, and minimal risk are overlapping categories. A system can be high-risk and also carry Article 50 transparency obligations at the same time. Limited risk isn't a gentler high-risk. It means one specific thing: transparency obligations apply, and nothing else does. The obligations table reflects that. A product can appear against more than one obligation set where the Act applies both.

### 1.1 Obligations by tier

| Risk tier | Resulting obligations | Where it bites in our operating model | Products carrying this tier |
|---|---|---|---|
| Prohibited | The use case can't be built or deployed. No mitigation makes it permissible. | Caught and rejected at Gate 1 intake. Never reaches discovery. | None in the current portfolio. The Gate 1 filter exists so it stays that way. |
| High-risk (Annex III) | Conformity assessment before deployment. Technical documentation and record-keeping. Logging of system activity. Defined human oversight. Fairness and bias testing. Registration in the EU database for the relevant categories. Post-market monitoring. | Classification confirmed by Legal at Gate 2. Conformity assessment and fairness eval are Gate 4 build deliverables. Human oversight (Pattern C) is mandatory, not optional. | Casting Submission Triage (Annex III, employment). Face Tagging / Recognition where it identifies individuals (Annex III, biometrics). Compliance and Edit Review where the deployment territory brings it into a regulated Annex III area. |
| Limited risk (Article 50) | Transparency disclosure. The person interacting with or affected by the system must be told that AI is involved. No conformity assessment, no fairness eval, no registration. | Disclosure requirement is a Gate 4 design item. Verified at Gate 5 rollout before any external exposure. | AVOD Optimisation (viewer-facing recommender and personalisation). Compliance and Edit Review carries this floor even where it doesn't reach high-risk. |
| Minimal risk | No mandatory obligations under the Act. Internal governance still applies: audit logging, eval thresholds, and the HITL pattern matched to internal risk. | Governed entirely by the internal operating model, not the Act. The internal risk classification, not the EU tier, drives the HITL and audit design. | Sales Market Intelligence, Object Recognition (DAM), and all remaining products. |

### 1.2 Why the obligations sit at these gates

The placement is deliberate. The classification has to be confirmed at Gate 2 because, as the Strategy document argues, misclassifying a high-risk use case as minimal is the most expensive governance mistake in enterprise AI. But the classification is only the trigger. The obligations it sets in motion, the conformity assessment, the fairness eval, the logging design, the human oversight pattern, are build-phase work. They land at Gate 4. If they were treated as a Gate 5 launch checklist instead, they would be discovered too late to design properly, and the product would either ship non-compliant or slip its date while the team retrofits oversight that should have been built in from the start.

One product is worth calling out, because it shows why the classification turns on a detail rather than a category. Face Tagging is minimal risk as pure detection, where the system tags that a face is present without ever identifying whose face it is. The same product becomes high-risk the moment it performs one-to-many identification across the asset library, which is remote biometric identification under Annex III. The obligations are completely different on either side of that line. This is exactly why classification is a Gate 2 decision made per deployment, not a one-time label fixed to the product name.

---

## 2. Human-in-the-Loop Patterns

The 3 HITL patterns are defined in the Strategy and Operating Model document, section 6.2. I'm not going to restate the definitions. What I'll do here is the part that document deliberately left out: assign every one of the 12 products to a pattern, say why, and specify what each pattern obligates in design terms. A pattern name on its own doesn't build anything. The obligations are where the design work sits.

One principle drives every assignment. The pattern matches the actual risk of a wrong output reaching the outside world, not the regulatory tier and not the perceived sophistication of the AI. A minimal-risk product can still warrant a firm review gate if a bad output is commercially expensive. A high-risk product earns the heaviest pattern because the cost of a missed error is a person harmed, not just a relationship damaged.

### 2.1 The patterns and what they obligate

**Pattern A, suggestion only.** The AI surfaces options. The human selects. Nothing reaches an external party without a deliberate human choice. The design obligation is light but specific. The UI must label the output as AI-generated and unverified. There must be no path that auto-sends or auto-shares. The audit log records what was surfaced and what the human did with it.

**Pattern B, draft and approve.** The AI generates a draft. The human reviews it and nothing is actioned or sent before sign-off. The design obligation adds an explicit approval step that can't be skipped, a visible diff between the AI draft and the approved version where the human edits it, and a sign-off record naming who approved and when.

**Pattern C, two-stage human review.** The AI generates, a first reviewer approves, and a second reviewer spot-checks at a defined sampling rate. The design obligation is the heaviest. Two distinct reviewer roles that can't be the same person, a defined and configurable sampling rate for the second review, and a fairness-relevant audit trail because every product carrying Pattern C is high-risk under the Act. The second reviewer isn't redundancy for its own sake. It is the layer that catches the systematic error the first reviewer normalises.

### 2.2 The 12 products mapped

| Product | Pattern | Why this pattern |
|---|---|---|
| Script Coverage Assistant | A | Internal development input. A weak read costs a second opinion, not an external harm. The writer or exec always decides. |
| YouTube and Social Trend Analyser | A | Research signal only. Feeds human judgement on what to commission. No output leaves the building on its own. |
| Sales Market Intelligence Agent | A | Prepares an executive to pitch. The agent doesn't make the decision, it informs one. Internal risk is medium, so the UI labelling and no-auto-send rule matter, but a heavier gate would add friction without reducing real risk. |
| Object Recognition (DAM) | A | Tags non-person objects. A wrong tag is a metadata correction. The librarian confirms ambiguous tags. |
| Production Budget Assistant | B | Produces a draft budget that informs a real financial commitment. A number that ships unreviewed becomes a planning error. Draft and approve forces the producer to own the figure. |
| Subtitle and Translation Automation | B | Generates a draft translation that an audience will see. The human reviewer signs off before it reaches a viewer. A mistranslation that ships is a public error, so it can't be Pattern A. |
| Music and Rights Clearance Assistant | B | Drafts a clearance position. A wrong call has legal and cost consequences, so a rights specialist approves before anything is relied on. |
| Content Catalogue Integration | B | Proposes catalogue mappings that affect downstream systems. A human approves the merge before it propagates. |
| AI Agent Studio for DAM workflows | B | Orchestrates DAM actions that change stored assets. Draft and approve keeps a human between the agent and any irreversible change. |
| AVOD Optimisation | B plus transparency | A viewer-facing recommender. It carries the Article 50 disclosure obligation from section 1, and a human owns the ranking policy and approves changes to it. The disclosure is the new design item the other Pattern B products don't carry. |
| Casting Submission Triage Agent | C | High-risk, Annex III employment. A missed or biased filtering of a candidate is a person harmed. Two-stage review with a fairness-relevant audit trail is mandatory, not a judgement call. |
| Compliance and Edit Review Assistant | C | Content review and moderation, territory-dependent up to high-risk. Where it reaches the regulated tier, the stakes of a missed error justify a second reviewer. Classified per deployment, so the pattern steps down to B only where the classification genuinely does. |

### 2.3 The pattern is a floor, not a ceiling

Two points on how to read the table. First, the pattern is the minimum. A business unit can run a heavier review during early rollout, for instance shadow mode on a Pattern A product, and step down to the assigned pattern once the eval evidence supports it. Nobody steps below the assigned pattern without a documented classification change.

Second, the 2 high-risk products are the only ones where the pattern is non-negotiable. Everywhere else the assignment follows from internal risk, which the business unit owns and can argue. Casting Triage and Compliance Review carry Pattern C because the Act requires human oversight on Annex III systems, and that requirement doesn't bend to a local convenience argument.

---

## 3. Audit Logging and Kill Switch Design

The audit log and the kill switch are the 2 controls that make every claim in this document enforceable rather than aspirational. A HITL pattern you can't evidence is a HITL pattern you can't defend in an incident. A kill switch you have never tested is a kill switch that fails when you need it. Both are specified at Gate 4, before any product goes live, for exactly that reason.

### 3.1 What every product logs

Every product in production writes to a single centralised audit log, not a per-product log. One schema, one retention policy, one place to look when a claim is later questioned. The minimum record for any product captures the input, or an input hash where the input itself is sensitive, the retrieval sources used, the model output, the human action taken on that output, the identity of the human, and the timestamp. This is the chain that lets you answer the only question that matters after an incident: where did this specific claim come from, and who signed it off.

The schema is fixed, not configurable per product, because the moment teams can choose what to log, the high-risk products are the ones most likely to under-log, and those are the products where the log matters most. Configurability is the enemy here.

### 3.2 What the high-risk products log on top

Pattern C products carry an extended record because their obligations are heavier. On top of the minimum, they log both reviewer identities and their decisions separately, the sampling decision for the second review, meaning whether this case was selected for spot-check and why, and the fairness-relevant attributes needed for the bias eval, held under the access controls the data classification requires. Retention is 24 months across the board, which covers the post-market monitoring window for the Annex III products and is long enough to investigate a drift pattern that only becomes visible over several quarters.

### 3.3 Kill switch design

Eval drift detection runs continuously across every in-production product. When drift crosses the threshold for a product, a named operator can disable that product globally within 15 minutes through the Platform admin console. Three design decisions make this real rather than nominal.

First, the operator is a named role with a rotation, not a job title that might be vacant. For the Sales Agent the rotation runs across the AI Platform and Sales Ops leads. Every product names its operators at Gate 4. An unnamed operator means nobody is on the hook at 2 in the morning.

Second, the triggers are documented in advance, not improvised during the incident. The standing triggers are a hallucination or error-rate breach in the online evals, a detected licence or data breach on a source, and a vendor outage requiring fallback. A documented trigger is what lets an operator act without waiting for a meeting.

Third, and this is the one most organisations skip, the kill switch is tested before the product goes live and on a scheduled cadence after. A kill switch that has only ever been described in a document is an assumption, not a control. The test is part of the Gate 5 rollout checklist.

### 3.4 The scope boundary

One honest limit. Global disablement within 15 minutes is the v1 mechanism. It is blunt. It takes the whole product down rather than isolating the failing component, and for a high-stakes incident that bluntness is correct, because a fast certain stop beats a slow precise one when a person could be harmed. A more granular per-component circuit breaker is a v2 design item. I am naming it here rather than implying the v1 switch is more surgical than it is.

---

## 4. Vendor Risk

The 6 due-diligence areas and the three-tier vendor structure are specified in the Strategy and Operating Model document, sections 6.4 and 8. I'm not going to restate them. What this section does is narrower and AI-specific. A vendor in an AI portfolio carries failure modes that a normal software vendor doesn't, and the governance controls have to be designed against those modes, not against generic procurement risk.

There are 3 AI-specific vendor risks the standard due-diligence list doesn't fully catch on its own.

The first is the silent model change. A vendor updates the model behind a stable API name, and the behaviour shifts without a version bump you can see. For most software this would be a bug fix. For a production AI product it can move your hallucination rate, your citation correctness, or your output format overnight, and the first place it shows up is an eval drift alert, not a vendor notice. The control is that eval drift detection treats an unexplained behaviour shift as a kill-switch trigger in its own right, and the FinOps and quality owners are alerted to check for a vendor-side change within the same 48-hour window the Strategy document already requires for pricing changes. The exit plan is what gives you somewhere to go if the change isn't remediated, and a self-hosted model gateway is what makes that exit fast. When the production model runs behind a gateway rather than a hardcoded SDK call, switching to the failover provider is a config change applied in minutes, not a redeploy. The architecture choice and the governance control are the same decision seen from two angles.

The second is model provenance and training-data exposure. Where a vendor will disclose it, provenance matters because a model trained on data with unclear rights can pull the organisation into an IP exposure it didn't create. This is why provenance is one of the 6 due-diligence areas and why it is confirmed at Gate 3, before the build commits to a vendor, not after.

The third is the shared-failure-mode risk on the eval judge. This is the one I flagged as an open question in the architecture document. If the model that judges output quality shares a provider with the model that produces it, a single vendor-side failure can degrade both at once, and the judge waves through the exact errors it should catch. The governance position is that the eval judge should be sourced independently of the production model wherever the cost allows, and where it can't, the shared dependency is documented as a known risk with a manual human spot-check compensating for it.

Across all 3, the exit plan is the load-bearing control. The Strategy document already makes a documented exit plan mandatory for every Tier 1 and Tier 2 relationship. The governance point is that for AI vendors the exit plan isn't a legal formality you file and forget. It is the thing that converts a vendor changing their model, discontinuing a version, or having an incident from an emergency into a managed migration. A multi-vendor Tier 1 policy is what makes the exit plan executable rather than theoretical, because a qualified alternative already exists.

---

## 5. Data Handling

Data handling in this operating model binds to the risk tiers from section 1, not to a single blanket policy. The classification decides the obligations, and that is as true for data as it is for human oversight.

### 5.1 The tier-driven rules

For minimal-risk products, the rule is the internal data policy and nothing more from the Act. The Sales Market Intelligence Agent is the clearest case. It processes no personal data. Broadcaster relationship and commercial intelligence are classified as Confidential under the internal data policy, storage is in-region, and that is the full obligation. The architecture document specifies this at the product level. The governance point is that minimal risk doesn't mean minimal care. The Confidential classification still drives access control, residency, and retention.

For high-risk products, the data handling is heavier because the Act requires it. Casting Triage processes candidate data, which is personal data in an Annex III employment context. That triggers a DPIA before any build, owned by Legal, fairness-relevant attributes held under restricted access purely for the bias eval, and a documented lawful basis for the processing. None of that is optional, and none of it is a product-team decision. It is a Legal accountability, which is exactly why the Strategy RACI puts the use of personal and talent data under Legal as accountable, not Product.

For limited-risk products, the data rule follows the transparency obligation. AVOD Optimisation processes viewing behaviour to personalise. The obligation is disclosure, and the data handling supports it: the viewer is told personalisation is happening, and the data used to personalise is held under the residency and retention rules the internal policy sets.

### 5.2 The rules that apply regardless of tier

Three data rules hold across every product, whatever its tier.

Data residency follows the user. UK data stays in the UK, EU data stays in the EU, per the residency policy. This isn't negotiable per product because a single misplaced store can undo the compliance position of the whole portfolio.

No production personal data flows to a vendor for training. Where a vendor relationship could expose data to model training, that is closed off in the contract terms covered by the vendor due diligence. The default is that the organisation's data trains nobody's model but its own.

Retention is bounded and documented per product, defaulting to the 24-month audit retention for the log itself, with the underlying source data held only as long as the product genuinely needs it. Indefinite retention is a liability, not an asset.

### 5.3 Where data handling meets the audit log

The two connect deliberately. The audit log from section 3 is itself a data store, and a high-risk product's log carries fairness-relevant attributes that are more sensitive than the product's ordinary inputs. So the log inherits the strictest access controls of any data the product touches, not the loosest. A log built to demonstrate compliance that itself breaches the data policy would be self-defeating, and that failure mode is easy to walk into if the log is treated as plumbing rather than as governed data.

---

## 6. What This Framework Is For

A governance framework earns its place only if it changes what gets built, not if it sits beside the build as documentation. Every section here is designed to bite at a specific gate. The classification and its obligations bite at Gate 2 and Gate 4. The HITL pattern is a Gate 4 design constraint. The audit schema and the kill switch are Gate 4 deliverables tested at Gate 5. The vendor and data controls are Gate 3 commitments confirmed before any build starts.

The single thread running through all of it is that the obligation follows the risk, and the risk is decided early and deliberately. The most expensive governance mistakes in enterprise AI aren't caused by weak controls. They are caused by good controls applied too late, after the classification was wrong or the oversight was bolted on. This framework exists to make the decision at the point where it is still cheap to act on.
