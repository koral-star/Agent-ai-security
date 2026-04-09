---
name: appsec-llm-dos-analyzer
description: Analyzes AI/LLM applications for Denial of Service attack surfaces. Covers token flooding, recursive prompt loops, embedding API cost attacks, unbounded agent iterations, and resource exhaustion via tool calls. Maps OWASP LLM04 risks and provides rate limiting, budget enforcement, and circuit breaker patterns.
---

Analyze the specified code or architecture for LLM Denial of Service (DoS) vulnerabilities (OWASP LLM04).

## Analysis Scope

### 1. Token Flooding Attacks
- Is there a maximum input token limit enforced before sending to the LLM API?
- Can a user submit arbitrarily large documents, file uploads, or conversation histories?
- Is the context window filled by user-controlled content, causing expensive requests?
- Are there limits on the number of turns in a conversation session?
- Is there per-user token consumption tracking and throttling?

### 2. Recursive & Infinite Loop Attacks
- Can a prompt cause the model to generate output that, when fed back as input, causes another generation (recursive loop)?
- Is there a maximum agent iteration / step count enforced?
- Can an injected instruction cause an agent to loop indefinitely (`while True: search_web(...)`)? 
- Is there a wall-clock timeout on agent execution, not just a step count?
- Are self-referential tool calls detected and blocked (tool A calls tool B which calls tool A)?

### 3. Embedding API Cost Attacks
- Is there a rate limit on embedding generation requests?
- Can a user trigger bulk re-embedding of large document sets without authorization?
- Is there a per-user quota on embedding API calls?
- Are vector similarity searches bounded in scope (max documents searched)?

### 4. Tool Call Resource Exhaustion
- Can an agent call expensive external tools (web search, code execution, DB queries) without per-session limits?
- Is there a maximum tool call count per session?
- Are long-running tools (code execution, shell commands) subject to timeouts?
- Can a tool call trigger a cascade of further tool calls beyond the original budget?
- Are external API calls from tools rate-limited to prevent upstream DoS?

### 5. Cost Amplification Attacks
- Can an attacker craft a prompt that causes disproportionately large output generation?
  - Example: "Write a 10,000 word essay on each of the following 50 topics..."
- Is there a maximum output token limit enforced?
- Are streaming responses subject to the same token limits as non-streaming?
- Are batch processing endpoints protected from submitting millions of items?

### 6. Memory & Storage Exhaustion
- Can a user fill the vector database by embedding unlimited documents?
- Is there a per-user storage quota in the knowledge base?
- Can conversation memory grow without bound across sessions?
- Are there cleanup / TTL policies on stored embeddings and conversation history?

### 7. Concurrency Attacks
- Is there a maximum concurrent request limit per user?
- Can a user open unlimited parallel agent sessions?
- Are there global concurrency limits to protect shared infrastructure?

## Defensive Patterns to Apply

```python
# Token budget enforcement
MAX_INPUT_TOKENS = 8_000
MAX_OUTPUT_TOKENS = 2_000

def safe_llm_call(messages: list, user_id: str) -> str:
    total_tokens = count_tokens(messages)
    if total_tokens > MAX_INPUT_TOKENS:
        raise ValueError(f"Input exceeds {MAX_INPUT_TOKENS} token limit")
    
    # Per-user daily budget check
    if get_user_daily_tokens(user_id) > USER_DAILY_TOKEN_BUDGET:
        raise RateLimitError("Daily token budget exceeded")
    
    response = llm.complete(messages, max_tokens=MAX_OUTPUT_TOKENS)
    track_user_tokens(user_id, total_tokens + response.usage.total_tokens)
    return response

# Agent step limiter
class BudgetedAgent:
    MAX_STEPS = 15
    MAX_TOOL_CALLS = 20
    TIMEOUT_SECONDS = 120
    
    def run(self, task: str):
        steps = 0
        tool_calls = 0
        start = time.time()
        
        while True:
            if steps >= self.MAX_STEPS:
                raise AgentBudgetExceeded("Max steps reached")
            if tool_calls >= self.MAX_TOOL_CALLS:
                raise AgentBudgetExceeded("Max tool calls reached")
            if time.time() - start > self.TIMEOUT_SECONDS:
                raise AgentBudgetExceeded("Execution timeout")
            
            action = self.think(task)
            if action.is_done:
                return action.result
            
            result = self.execute_tool(action)
            tool_calls += 1
            steps += 1
```

## Output Format

For each finding:
1. **Severity**: CRITICAL / HIGH / MEDIUM / LOW
2. **DoS Type**: (e.g., Token Flooding, Recursive Loop, Cost Amplification)
3. **Location**: file:line or component
4. **Attack Scenario**: How an attacker triggers the DoS and what the impact is (cost, unavailability)
5. **Remediation**: Budget enforcement code, rate limiting config, or architectural fix

End with a **Cost Attack Surface Map** — all unbounded resource consumption paths, estimated cost per attack, and a **Rate Limiting Configuration** for the application.
