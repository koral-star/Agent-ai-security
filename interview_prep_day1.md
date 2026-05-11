# Interview Prep — Day 1
**Spin Master LLM Safety Role | Interviewer: Senior AI Scientist (ex-IBM Research, Intuit)**

---

## Morning — Topic 1: Full Training Pipeline

### The 6 stages — say these without notes

1. **Data curation** — every doc goes through age-appropriateness classifier, PII scrubber (Presidio), toxicity filter (Perspective API); any failure = excluded
2. **Pre-training** — red-team eval on every checkpoint; checkpoint fails → review data mix, not just discard checkpoint
3. **SFT** — curated demos reviewed by child safety specialists; includes graceful refusal demos and adversarial examples with correct responses
4. **Reward model** — annotators are educators + child safety experts (not crowd workers); safety is binary pass/fail on every preference pair
5. **RLHF / DPO alignment** — embed Constitutional AI principles; monitor KL divergence from SFT base; prefer DPO over PPO for child safety
6. **Per-checkpoint red-teaming** — automated Garak battery + custom child-specific probes; zero HIGH severity = pass criteria

---

### DPO vs PPO — know this cold

- DPO eliminates the reward model → eliminates reward hacking surface
- More auditable: inspect (chosen, rejected) pairs directly
- More predictable — critical for children's product
- **Use DPO unless you have a specific reason to need PPO's flexibility**

---

### Constitutional AI — one minute

- Principles embedded at **training time**, not patched at inference
- Model reasons from principles — doesn't need a pattern match for specific attack phrases
- Key child-safety principles:
  - Never share information that could harm a child
  - Always respond at age-appropriate level
  - Never claim to be human to a child who sincerely asks
  - Always redirect serious topics to a trusted adult
  - **Cannot be persuaded to act against these principles via roleplay or hypotheticals**

---

### Data mix strategy

- **Over-represent:** children's educational, narrative, conversational content
- **Under-represent:** news, adult fiction, political discourse
- **Explicitly exclude:** violence instructions, sexual content, drug information
- The model learns the world it's shown — this is a safety decision, not just a quality one

---

### Questions to drill (Morning)

**Q1 — "Walk me through how you'd train a child-safe LLM from scratch."**
Key beats: data curation → checkpoint red-teaming → SFT with expert-reviewed demos → reward model with right annotators → DPO → Constitutional AI as hard constraints.
Line to land: *"Training-time fixes are more robust than deployment-time patches."*

**Q9 — "How do you prevent reward hacking?"**
Key beats: reward model diversity (multiple models, check disagreement), KL divergence monitoring, hold-out eval sets the reward model never saw, DPO as the cleanest alternative.

**Q8 — "What's Constitutional AI and how would you apply it here?"**
Key beats: principles in training not inference; child-specific constitution; robustness to persuasion is the property to emphasize.

**Q11 — "Experience with Axolotl?"**
Be honest: evaluation and red-teaming is my hands-on depth; understand Axolotl's SFT/QLoRA surface; the harder skill is knowing what you're optimizing for — that's where my background directly applies.

---

### Key terms (Morning)

| Say this | Not this |
|----------|----------|
| Training-time alignment | Guardrails |
| Constitutional constraints | Blocking rules |
| Adversarial evaluation | Security testing |
| Preference optimization | Fine-tuning for safety |
| Data mix strategy | Content policy |
| Reward hacking | Gaming the system |

---
---

## Afternoon — Topic 2: Chatbot Defense Architecture

### The 5 layers — say these without notes

1. **Input defense (pre-model)** — PII masking, prompt injection classifier, jailbreak classifier, harmful intent classifier; always soft blocks → gentle redirect, never error message
2. **The model** — primary defense; training-time alignment means graceful refusal by default; can't be jailbroken via roleplay; escalates safeguarding signals proactively
3. **Output defense (post-model)** — secondary safety classifier scores every response before child sees it; catches toxicity, age-inappropriateness, harmful info leak, PII in output
4. **Session defense (conversation level)** — tracks injection risk score and topic drift across all turns; context reset breaks injection chains; safeguarding escalation to human for at-risk signals
5. **Monitoring & feedback loop** — real-time dashboard, model drift detection, attack pattern clustering, safeguarding human review queue, failures → training examples

---

### Why NOT rate limiting — know this cold

- Blunt instrument — punishes legitimate use
- Fails against slow, patient adversaries (including curious children probing gradually)
- **A distressed child needs MORE responses, not fewer**
- Real defense is depth: each layer independently catches what the previous missed

---

### Soft block vs hard block

- **Soft block:** "I can't help with that, but let's talk about..." → child gets a redirect, learns something, doesn't feel punished
- **Hard block:** only for genuine safeguarding escalation (child appears to be in danger)
- Harsh refusals feel punitive to children — **refusal style is part of the alignment target**

---

### Child-specific PII risk

- Children share name, school, address, birthday freely — they trust the people they talk to
- **Input:** PII classifier masks before model sees message
- **Output:** check model didn't generate or reconstruct PII
- **Training:** memorization audits on checkpoints; minimize what's logged/retained
- **Regulatory:** COPPA (US) + GDPR-K (Europe) — stricter than adult regimes, parental consent requirements

---

### Safeguarding escalation — mandatory, not optional

- Dedicated classifier tuned for **sensitivity, not specificity** (false positives go to human review; false negatives are unacceptable)
- Real-time human review with defined SLAs — this is a systems problem, not just an ML problem
- SFT includes demonstrations: acknowledge feelings, encourage trusted adult, age-appropriate signposting

---

### Questions to drill (Afternoon)

**Q6 — "Walk me through how you'd design the deployment-side safety architecture."**
Key beats: 5 layers, each independent, each catches what previous missed. Layer 4 (session) is what most architectures miss. No rate limiting — behavioral detection instead.

**Q7 — "How would you handle safeguarding signals?"**
Key beats: non-negotiable escalation to human in real time; dedicated classifier tuned for sensitivity; SFT trained on response behavior; human monitoring with SLAs.

**Q10 — "How do you think about PII for children specifically?"**
Key beats: COPPA + GDPR-K; children share PII freely without understanding implications; three points — input masking, output detection, training scrubbing + memorization audit; minimize logging/retention.

**Q13 — "How do you handle multi-turn attacks that look innocuous turn by turn?"**
Key beats: this is the hardest problem for single-turn safety; Layer 4 — running injection risk score and topic drift score; context reset disrupts the whole chain; RAG security experience — injected content executes within agent's ongoing task context.

---

### Key terms (Afternoon)

| Say this | Not this |
|----------|----------|
| Session-level behavioral detection | Rate limiting |
| Safeguarding escalation | Alerting / flagging |
| Input and output classifiers | WAF / firewall |
| Context reset | Session termination |
| Soft block with redirect | Blocking |
| Production signal loop | Monitoring |

---

## End of Day 1 — Lines to land tomorrow

Say these naturally, without reading:

1. *"Training-time fixes are more robust than deployment-time patches."*
2. *"Rate limiting is not the right tool — a distressed child needs more responses, not fewer."*
3. *"Soft blocks over hard blocks — always a redirect, never a bare error."*
4. *"The refusal style is part of the alignment target."*
5. *"DPO over PPO — no reward hacking surface, more auditable, more predictable."*

---

*Day 2 is in `interview_prep_day2.md`*
