# Gemini Feedback — Gaps to Review Saturday Evening

Study ONLY this file on Saturday. Short, targeted, nothing else.

---

## TOPIC 1: Training Pipeline

**Weak — Axolotl config (haven't used it hands-on)**
If asked, say: "I haven't used Axolotl hands-on, but I know the key config decisions —
sequence length for conversational data, LoRA rank for safety-critical fine-tuning,
dataset composition ratio (70/30 safe/adversarial), and eval callbacks every N steps."

**Partial — DPO over PPO (missed two points)**
Add these to your answer:
- DPO is more **auditable** — you can inspect every chosen/rejected pair directly. This matters for regulated child products.
- DPO failure mode: if a scenario isn't covered in the preference pairs, the model has no signal at all. PPO generalizes more; DPO is only as good as its dataset.

**Gap — KL Divergence (missed entirely)**
After alignment, you monitor KL divergence from the SFT base to detect drift.
Too safe = model becomes "braindead" and refuses everything. Too loose = unsafe.
Key line: "We monitor KL divergence to keep the model in the safe-but-useful range."

**Gap — Data Provenance (missed entirely)**
Stage 1 (data curation) isn't just content filtering — you also track *where* data came from.
Unknown or low-trust sources = poisoning risk even if the content looks clean.
Key line: "For children's products, source provenance is as important as content quality."

**Gap — Age persona bypass (missed entirely)**
A 12-year-old can claim to be 7 to get a younger (more permissive) filter applied.
The classifier needs to detect persona misrepresentation, not just the stated age.
Key line: "Age-persona spoofing is a real attack vector — we can't trust self-reported age."

---

## TOPIC 2: Chatbot Defense Architecture

*(Add gaps here after completing Topic 2 with Gemini)*

---

## TOPIC 3: Evaluation & Red-Teaming

*(Add gaps here after completing Topic 3 with Gemini)*

---

## TOPIC 4: Adversarial Robustness & Research

*(Add gaps here after completing Topic 4 with Gemini)*

---

## TOPIC 5: Fit & Closing

*(Add gaps here after completing Topic 5 with Gemini)*
