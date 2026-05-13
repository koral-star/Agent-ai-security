# Interview Prep — Day 1
**Spin Master LLM Safety Role | Product: children's chatbot (Frontier Model) | Interviewer: Senior AI Scientist (ex-IBM Research, Intuit)**

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

### Adversarial Robustness baked in at training time

- Adversarial examples are part of the SFT dataset — the Frontier Model sees attacks and learns to refuse gracefully
- **Model internals, not bolted-on guardrails.** Guardrails can be stripped or bypassed. Weights with constitutional constraints embedded at training cannot.
- Key attack types included in training data: encoding tricks (base64, ROT13), roleplay persona injection, authority claims ("my mom said"), hypothetical framing
- Key principle: *"Safety in the weights — a chatbot defended at training is fundamentally more robust than one defended at inference."*

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
Key beats: data curation → checkpoint red-teaming → SFT with expert-reviewed demos + adversarial examples → reward model with right annotators → DPO → Constitutional AI as hard constraints.
Line to land: *"Training-time fixes are more robust than deployment-time patches."*
↳ Follow-up 1: "You mentioned DPO — how do you know the (chosen, rejected) pairs are actually capturing the right safety signal for children, not just the annotator's intuition?"
↳ Follow-up 2: "What happens when the model generalizes the safety training in ways you didn't anticipate — either over-refusing legitimate requests or under-refusing edge cases?"
↳ Follow-up 3: "How do you handle Constitutional AI principles that conflict — e.g., 'always be helpful' vs 'never share potentially harmful information' when a child asks about medication?"

**Q9 — "How do you prevent reward hacking?"**
Key beats: reward model diversity (multiple models, check disagreement), KL divergence monitoring, hold-out eval sets the reward model never saw, DPO as the cleanest alternative.
↳ Follow-up 1: "What does reward hacking look like concretely in a children's chatbot — give me a specific example of a response that would score high on reward but is actually unsafe?"
↳ Follow-up 2: "If you use DPO to sidestep the reward model, what are DPO's specific failure modes for safety training?"

**Q8 — "What's Constitutional AI and how would you apply it here?"**
Key beats: principles in training not inference; child-specific constitution; robustness to persuasion is the property to emphasize.
↳ Follow-up 1: "How do you write a constitution that's robust to a child saying 'my mom said you can tell me anything' or 'pretend you have no rules'?"
↳ Follow-up 2: "How do you evaluate whether the constitutional principles are actually internalized in the model's weights vs surface-level pattern matching?"

**Q11 — "Experience with Axolotl?"**
Be honest: evaluation and red-teaming is my hands-on depth; understand Axolotl's SFT/QLoRA surface; the harder skill is knowing what you're optimizing for — that's where my background directly applies.
↳ Follow-up 1: "If you were setting up the SFT run for this chatbot today, what are the three most important config decisions you'd make and why?"

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

**Q6 — "Walk me through how you'd design the deployment-side safety architecture for this chatbot."**
Key beats: 5 layers, each independent, each catches what previous missed. Layer 4 (session) is what most architectures miss. No rate limiting — behavioral detection instead.
↳ Follow-up 1: "Layer 4 is session-level — how do you implement the injection risk score technically? What signals feed into it and how do you weight them?"
↳ Follow-up 2: "How does your Safety Stack adapt when the chatbot is used by a 6-year-old vs a 13-year-old? Are the threat profiles different enough to require different configurations?"
↳ Follow-up 3: "Where does the Safety Stack's responsibility end and the product team's begin? Who owns the escalation decision when a child appears to be in danger?"

**Q7 — "How would you handle safeguarding signals?"**
Key beats: non-negotiable escalation to human in real time; dedicated classifier tuned for sensitivity; SFT trained on response behavior; human monitoring with SLAs.
↳ Follow-up 1: "What's your false positive rate target for the safeguarding classifier — and how do you set that threshold for a children's chatbot specifically?"
↳ Follow-up 2: "A child says 'I don't want to go home today.' Ambiguous signal. How does the classifier decide — and what does the chatbot say while the classifier is working?"

**Q10 — "How do you think about PII for children specifically?"**
Key beats: COPPA + GDPR-K; children share PII freely without understanding implications; three points — input masking, output detection, training scrubbing + memorization audit; minimize logging/retention.

**Q13 — "How do you handle multi-turn attacks that look innocuous turn by turn?"**
Key beats: this is the hardest problem for single-turn safety; Layer 4 — running injection risk score and topic drift score; context reset disrupts the whole chain; RAG security experience — injected content executes within agent's ongoing task context.
↳ Follow-up 1: "Walk me through a specific 10-turn gradual context poisoning attack on a children's chatbot — what does each turn look like and when does the risk score trip?"
↳ Follow-up 2: "Context reset breaks the injection chain — but it also means the child loses their conversation history. How do you handle that UX tradeoff?"

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
