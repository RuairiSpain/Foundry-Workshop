# Curriculum roadmap

Source of truth for lab order, scope, and prerequisites. Update this file
before you add, reorder, or rename a lab. `curriculum_guard` reads this
file to check every draft.

## Case study

Cascadia Outfitters, an outdoor-gear retailer, builds Trailhead: an AI
assistant ecosystem spanning customer support, order operations, and trip
planning.

**Personas:** Maya (online shopper), Devon (store associate), Priya (trip
planner customer), Sam (platform and security lead).

**Assets in `case-study/`:** `product-catalog.csv`, `return-policy.pdf`,
`store-manual.pdf`, `damaged-gear-photos/`, `receipts-and-specs/`,
`store-ops-configs/`, `trail-database.json`, `mock_orders_api/`,
`swiftship_partner_agent/`.

## Locked decisions

- Azure subscriptions are provisioned one per attendee.
- Lab 22's group-chat orchestration pattern is Magentic.
- Labs 23, 31, and 32 are optional and license-gated.
- Language is Python throughout.

## Format

Each lab lives in `labs/lab-NN-slug/`. See root `CLAUDE.md` for required
folder contents.

## Module 0 — Environment and project setup

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 01 | Meet the Toolkit | — | Install Foundry Toolkit extension; Azure sign-in; Create Project wizard; My Resources view | Toolkit | |
| 02 | Provision by code | 01 | `az login`; `az cognitiveservices account create --kind AIServices --allow-project-management`; `az cognitiveservices account project create`; notebook as a CLI driver | CLI, Notebook | Alt track |

## Module 1 — Models, routing, and tuning

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 03 | Deploy a low-cost model | 01 | Model catalog; model deployment; Model Playground side-by-side compare; View Code | Toolkit | |
| 04 | Model router | 03 | Model router deployment; per-turn dynamic routing; reading routing decisions in trace | Toolkit, Portal | |
| 05 | Tuning model connections | 03 | SDK client against a deployed model; temperature, top_p, max_tokens, seed; prompt caching | Toolkit, SDK | |

## Module 2 — Grounding the assistant

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 06 | Document knowledge base | 01 | File upload; vector store via file search; grounded prompt | Toolkit | |
| 07 | Foundry IQ knowledge base | 06 | Foundry IQ serverless knowledge base; unifying multiple sources; SLA-backed retrieval endpoint | Portal, Toolkit | |

## Module 3 — The single-agent spectrum

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 08 | Prompt agent | 07 | Agent Builder; prompt agent (no-code, fully managed); attaching a knowledge base; Agents Playground | Toolkit | |
| 09 | Classic agent | 03 | Classic agent; threads and runs; Python function tools; multi-turn state | Toolkit | |
| 10 | Tools on Azure Functions | 09 | Azure Functions as a tool host; registering an HTTP tool; agent-to-function auth | Toolkit, Azure Functions | |
| 11 | MCP server and Toolbox | 09 | MCP server scaffold (Tool Catalog); local MCP test; Toolbox registration; tool reuse across agents | Toolkit | |
| 12 | Hosted agent | 09 | Microsoft Agent Framework, single agent only; containerized deployment; hosted agent tracing | Toolkit, Container | |
| 13 | Web-grounded agent | 08, 11 | Web search tool; combining static, live, and tool-based grounding | Toolkit | |

## Module 4 — Quality basics

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 14 | Prompt optimization | 08 | Prompt Optimizer; before/after prompt scoring | Toolkit | |
| 15 | Evaluation, tracing, and debugging | 09, 13 | Eval dataset; batch evaluation (groundedness, relevance, safety); trace-based debugging of a tool call | Toolkit, Portal | |

## Module 5 — Memory, vision, and sandboxed execution

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 16 | Code Interpreter and open-source sandbox | 09 | Managed Code Interpreter tool; wrapping a self-hosted code-execution sandbox as a custom tool | Toolkit, SDK | |
| 17 | Vision-enabled agent | 09 | Multimodal prompt; image upload handling; vision model | Toolkit | |
| 18 | Content Understanding | 17 | Content Understanding service; structured extraction from receipts and specs; feeding extraction into a knowledge base | Portal, Toolkit | |
| 19 | Long-term memory | 09 | Foundry native long-term agent memory (preview); memory vs. thread state | Toolkit | |
| 20 | Cosmos DB-backed memory | 19 | Agent Memory Toolkit; Cosmos DB as memory store; vector, full-text, and hybrid search over memory | SDK, Portal | |

## Module 6 — Multi-agent systems with MAF

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 21 | MAF fundamentals | 12 | MAF's layered SDK: agent loop, workflow, harness; rebuilding a hosted agent locally with MAF | Python SDK | |
| 22 | Workflow orchestration patterns | 21 | `agent_framework.orchestrations`; sequential; concurrent fan-out/fan-in; handoff; Magentic group chat | Python SDK | |
| 23 | GitHub Copilot harness | 21 | GitHub Copilot SDK harness; swapping MAF's harness layer; human-in-the-loop file edits | Python SDK | Requires GitHub Copilot SDK access |
| 24 | Durable Agents and Durable Functions | 22 | Durable Task extension for MAF; deterministic checkpoint and replay; scale-to-zero | Azure Functions | |
| 25 | Agent-to-agent (A2A) | 12 | A2A protocol; cross-process task delegation; delegation-chain tracing | Python SDK | |

## Module 7 — Production, governance, and distribution

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| 26 | Publishing and versioning | 08 | Agent Application; version auto-snapshot; rollback; traffic split | Toolkit, Portal | |
| 27 | Evaluation gates in CI/CD | 15, 26 | Batch evaluation as a pipeline step; blocking publish on regression | SDK, Portal | |
| 28 | Finding expensive, slow, and failing agents | 15 | Fleet-wide log search; OpenTelemetry trace analysis in Azure Monitor; metric-to-trace correlation | Portal | |
| 29 | Responsible AI, policy, and guardrails | 08 | Responsible AI Toolkit; Content Safety filters; AI Red Teaming Agent; project-wide policy | Portal | |
| 30 | Private networking and the AI Gateway | 04 | Foundry control-plane token/TPM limits; Azure API Management as AI Gateway; managed-identity auth; semantic caching; private endpoints | Portal, APIM | |
| 31 | A Teams agent | 09 | M365 Agents Toolkit; publish-to-Teams; channel authentication | M365 Agents Toolkit | Requires M365 tenant admin |
| 32 | Registering in Agent 365 | 26 | Agent 365 control plane; org-wide observe, secure, govern | Portal | Requires Agent 365 licensing |
| 33 | Capstone: the governed multi-agent ecosystem | All prior labs; 23, 31, 32 optional | Composing every prior lab into one operated system | Toolkit, Portal, SDK | |

## Appendix

| Lab | Title | Prereqs | Concepts introduced | Surface | Optional |
|----|-------|---------|----------------------|---------|----------|
| A | Fine-tuning | 03, 15 | Fine-tuning a deployed model; comparing against the router baseline | Toolkit | Time-permitting |
