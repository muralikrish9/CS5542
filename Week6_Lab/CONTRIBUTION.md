# CONTRIBUTION.md — Week 6 Lab

## CS 5542 · Team Promptocalypse · Murali Ediga

---

## Personal Responsibilities and Implemented Components

### 1. Agent Architecture Design
Designed the overall ReAct (Reason + Act) agent loop implemented in `agent.py`. This
includes the multi-turn message construction, tool dispatch logic, `MAX_ITERATIONS` guard,
and the `AgentLog` dataclass for tracking reasoning steps, latency, and token usage.

### 2. Tool Implementation (`tools.py`)
Implemented all five agent tools:
- `query_snowflake` — Snowflake connector with read-only SQL guard
- `retrieve_documents` — TF-IDF retrieval over the Week 2 cybersecurity corpus
- `compute_statistics` — descriptive analytics with optional group-by
- `summarize_text` — extractive TF-IDF centroid summarization
- `list_tables` — schema discovery via SHOW TABLES

### 3. Tool Schema Definition (`tool_schemas.py`)
Authored all five OpenAI-format function calling schemas with accurate descriptions,
parameter types, and required field specifications to guide the LLM's tool selection.

### 4. Streamlit Agent Interface (`streamlit_app.py`)
Extended the Week 5 dashboard to include:
- Persistent chat history via `st.session_state`
- Loading indicator during agent execution
- Per-response metrics display (latency, iterations, tokens)
- Expandable tool call logs with DataFrame rendering for tabular results
- Sidebar with quick-access example questions

### 5. Evaluation Design and Reporting (`task4_evaluation_report.md`)
Designed three evaluation scenarios (simple / medium / complex) and ran them against
the live system. Documented accuracy, latency, tool usage, and failure analysis.

### 6. Antigravity IDE Integration (`task1_antigravity_report.md`)
Used Google Antigravity IDE throughout development for code review, architecture
analysis, and improvement suggestions. Documented the three prompting sessions and
assessed accepted vs. deferred recommendations.

---

## Commits and Pull Requests

All commits are under `muralikrish9/CS5542` on the `main` branch. Key commits:
- `Week6_Lab/tools.py` — initial tool implementation
- `Week6_Lab/tool_schemas.py` — function calling schemas
- `Week6_Lab/agent.py` — ReAct agent loop
- `Week6_Lab/streamlit_app.py` — chat interface
- `Week6_Lab/task1_antigravity_report.md` — IDE reflection
- `Week6_Lab/task4_evaluation_report.md` — evaluation report

---

## Reflection

**Technical contributions:**  
The most technically challenging part was correctly implementing the multi-turn tool
calling loop. The Groq API uses the same OpenAI function calling format, but the message
structure requires careful handling — each assistant message containing `tool_calls` must
be followed by corresponding `tool` role messages with matching `tool_call_id` values.
Getting this right required careful reading of the API spec and testing against live
edge cases (empty tool calls, malformed JSON arguments, API errors mid-loop).

**Learning outcomes:**  
- Gained practical understanding of ReAct agent architecture and its limitations
  (primarily the context window filling up on complex multi-step tasks)
- Experienced the tradeoff between sparse (TF-IDF) and dense retrieval firsthand —
  synthetic category names exposed exactly where TF-IDF breaks down
- Learned that Streamlit's `st.session_state` requires careful initialization to avoid
  `KeyError` on first render

**What I'd do differently:**  
Replace the extractive `summarize_text` tool with a direct Groq call for generative
summarization. The TF-IDF centroid approach works but is clearly the system's weakest
component. Two lines of Groq API code would outperform it significantly.
