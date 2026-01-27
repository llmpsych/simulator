# Benchmark Changelog

## 2025-12-07: Ollama options to prevent repetition loops

### Problem

Patient simulator (qwen3:30b) was repeating identical messages from turn 3 onwards in longer conversations. Also observed role confusion where patient would flip to helper role after ~8 turns.

### Root Causes Identified

1. **Context window too small**: Ollama defaults to 2048 tokens. Long conversations exceed this, causing context truncation and loss of earlier turns.

2. **No repetition penalty**: Without penalty, models fall into "high-probability loops" where repeated phrases become the most likely next token.

3. **Default sampling**: Standard sampling can lead to deterministic, repetitive outputs.

### Solution

Added three Ollama API options to `call_ollama()`:

```python
options = {
    "num_ctx": 32768,      # Increase context window from 2048 to 32k
    "repeat_penalty": 1.1, # Penalize repeated tokens
    "mirostat": 2,         # Adaptive sampling (Mirostat 2.0)
}
```

### References

- **Context window**: [Specifying Ollama's Context Window Size](https://atlassc.net/2025/01/15/specifying-ollama-s-context-window-size) — "By default, Ollama uses a context window of 2048 tokens."

- **Repetition loops**: [Why Do LLMs Generate Repetitive Outputs?](https://ai.stackexchange.com/questions/47318/why-do-llms-generate-repetitive-outputs-during-text-generation) — "This usually happens when the model falls into a high-probability loop."

- **Repetition penalty**: [A Practical Guide to LLM Parameters](https://aicosoft.com/ai-system-design/a-practical-guide-to-llm-parameters-temperature-top-p-and-more) — "Start with a Repetition Penalty of 1.1, incrementing by 0.05."

- **Mirostat**: [7 LLM Decoding Strategies](https://langcopilot.com/posts/2025-07-02-decoding-strategies-for-large-language-models) — "Mirostat is an adaptive sampling method designed to maintain a target level of perplexity... helps avoid both repetitive and incoherent outputs."

### Testing Results

10-turn test with these options:

**Improvements:**
- No role confusion (patient stayed in character all 10 turns)
- Minor token-level variation observed ("next hour" → "next minute" → "next second")

**Still present:**
- Patient repeating from turn 4 onwards
- Bot also repeating identical response structure

**Hypothesis:** The repetition may be a feedback loop — bot's repetitive responses give patient nothing new to respond to, causing patient to repeat, which causes bot to repeat. This is a conversational dynamics issue, not purely a sampling issue.

**Next steps to investigate:**
- Try different patient model
- Increase repeat_penalty further
- Add explicit variation guidance to patient prompt
