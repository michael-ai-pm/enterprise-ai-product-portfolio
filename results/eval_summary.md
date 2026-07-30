# Evaluation results

Generated 30 July 2026 from `results\eval_runs.jsonl`. 56 section observations across 4 repeats.

Every number here was produced on the OpenRouter free tier, which is a development path and not the production model. Treat the rates as measurements of this configuration, not of the design.

## Metrics, overall and by repeat

| Metric | Overall | Run 1 (n=18) | Run 2 (n=18) | Run 3 (n=18) | Run 4 (n=2) | Spread |
|---|---|---|---|---|---|---|
| Citation rate | 100% | 100% | 100% | 100% | 100% | 100% every run |
| Citation validity | 100% | 100% | 100% | 100% | 100% | 100% every run |
| Refusal accuracy | 81% | 75% | 92% | 75% | 100% | 75% to 100%, sd 12pp |
| False refusal rate | 42% | 50% | 50% | 33% | 0% | 0% to 50%, sd 24pp |
| Retry rate | 4% | 6% | 6% | 0% | 0% | 0% to 6%, sd 3pp |
| Quality warning rate | 0% | 0% | 0% | 0% | 0% | 0% every run |

Spread is what this harness was built for. A single pass would have reported one number per metric and told you nothing about whether it holds. Three scenarios run repeatedly was chosen over ten scenarios run once for exactly that reason.

## Where the failures actually are

The aggregate rates above hide the shape of the problem, which is the reason this breakdown exists. Failures are not spread evenly across sections, they are concentrated.

| Scenario | Section | Expected answerable | Answered |
|---|---|---|---|
| bbc-drama | 1. Territory snapshot | False | 0/3 |
| bbc-drama | 2. Broadcaster slate | True | 3/3 |
| bbc-drama | 3. Competing formats | True | 0/3 |
| bbc-drama | 4. Trend signals | False | 0/3 |
| bbc-drama | 5. Format fit | False | 2/3 |
| bbc-drama | 6. Risks and counterarguments | False | 0/3 |
| c4-quiz | 1. Territory snapshot | False | 0/4 |
| c4-quiz | 2. Broadcaster slate | True | 3/4 |
| c4-quiz | 3. Competing formats | True | 2/3 |
| c4-quiz | 4. Trend signals | False | 2/3 |
| c4-quiz | 5. Format fit | False | 1/3 |
| c4-quiz | 6. Risks and counterarguments | False | 0/3 |
| sky-thriller | 1. Territory snapshot | False | 0/3 |
| sky-thriller | 2. Broadcaster slate | True | 3/3 |
| sky-thriller | 3. Competing formats | True | 0/3 |
| sky-thriller | 4. Trend signals | False | 0/3 |
| sky-thriller | 5. Format fit | False | 2/3 |
| sky-thriller | 6. Risks and counterarguments | False | 0/3 |

### What the Reviewer caught

- `sky-thriller` section 2, repeat 1: first attempt failed on invented_citation, retry produced `answered` with 3 citation(s).
- `c4-quiz` section 4, repeat 2: first attempt failed on missing_citation, retry produced `insufficient_sources` with 0 citation(s).

## Refusal accuracy runs in both directions

Refusal accuracy and false refusal rate are reported together on purpose. An agent that refuses every section scores one hundred per cent on the first and is useless. The golden set carries both answerable and unanswerable sections so that the second metric can catch that.

## What this harness does not measure

Plan quality. The plans are generated once and committed, so every repeat runs against the same plan and plan-stage variance is excluded by construction. That is a deliberate trade for repeat observations within the time available, and it means a planning regression would not show up here. A planner eval is a separate instrument and it does not exist yet.

Claim support. The Reviewer's tier-two check, whether a cited source actually backs the claim, is off in these runs because it would break the twelve-call cap in section 7. Citation validity here confirms that a cited file was among the retrieved evidence, which is a weaker claim than the source supporting the sentence.
