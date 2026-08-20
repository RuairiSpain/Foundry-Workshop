"""Shared fakes for the Foundry SDK, reused by every lab's test suite.

Solution code never imports this module — it takes a project client (or
a factory) as a constructor argument, and only *tests* hand it one of
these fakes instead of a real Azure client. That boundary is what lets
every lab's tests run offline and free.

Verified against the real, currently-published SDK surface (not just
the version pinned in each lab's requirements.txt): `azure-ai-projects`
2.3.0, `azure-ai-agents` 1.1.0, `azure-ai-contentsafety` 1.0.0. Two
things worth knowing before you extend this module:

1. `AIProjectClient` itself is thin today — `close()`,
   `get_openai_client()`, `send_request()`. Chat completions go through
   the `openai.OpenAI` client `get_openai_client()` returns, not a
   Foundry-specific inference client. `FakeOpenAIClient` below models
   that shape (`.chat.completions.create(...)`), not a Foundry-specific
   one.
2. Agents, threads, messages, runs, files, and vector stores live on a
   *separately-constructed* `azure.ai.agents.AgentsClient(endpoint,
   credential)`, not as a `.agents` property of `AIProjectClient`. Every
   lab's `main()` constructs both clients for real. `FakeAgentsClient`
   below keeps living on `FakeAIProjectClient.agents` anyway — one
   fake object is simpler for a lab's tests to construct than two, and
   nothing in a lab's *tested* code cares which real client an object
   came from, only which methods it exposes. Match the method shapes
   AgentsClient actually has (`.threads.create()`, `.messages.create()`,
   `.messages.list()`, `.runs.create_and_process()`, `.files.upload()`,
   `.vector_stores.create()`) — that's the part solution code calls.

Knowledge bases (Foundry IQ), native long-term memory, and Agent
Applications have no stable typed SDK as of writing this workshop — the
real client reaches them through `AIProjectClient.send_request()`
against a preview REST surface, not generated methods. Their fakes
below are a deliberate pedagogical simplification of that preview
surface, not a stand-in for a typed client that doesn't exist yet. Say
so in the affected labs' READMEs rather than implying otherwise.

If a lab's solution code needs a client call this module doesn't fake
yet, extend the matching Fake*Client class here instead of mocking it
locally in one lab's tests — that's the boilerplate CLAUDE.md asks you
not to duplicate.
"""

from __future__ import annotations

import dataclasses
import itertools
import uuid
from collections.abc import Callable


# ---------------------------------------------------------------------------
# Chat completions (Labs 03, 04, 05) — via the OpenAI-shaped client
# `AIProjectClient.get_openai_client()` returns, not a Foundry-specific
# inference client.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakePromptTokensDetails:
    # Set when a scripted reply represents a prompt-cache hit. Lab 05
    # reads usage.prompt_tokens_details.cached_tokens to prove caching
    # happened — that's where the real OpenAI SDK's usage object puts
    # it, not usage.cached_tokens directly.
    cached_tokens: int = 0


@dataclasses.dataclass
class FakeUsage:
    prompt_tokens: int = 42
    completion_tokens: int = 18
    total_tokens: int = 60
    prompt_tokens_details: FakePromptTokensDetails = dataclasses.field(default_factory=FakePromptTokensDetails)


@dataclasses.dataclass
class FakeMessageContent:
    content: str


@dataclasses.dataclass
class FakeChoice:
    message: FakeMessageContent
    finish_reason: str = "stop"


@dataclasses.dataclass
class FakeChatCompletion:
    choices: list[FakeChoice]
    model: str
    usage: FakeUsage = dataclasses.field(default_factory=FakeUsage)
    id: str = dataclasses.field(default_factory=lambda: f"chatcmpl-{uuid.uuid4().hex[:8]}")


class FakeCompletionsAPI:
    """Stands in for `openai.OpenAI().chat.completions`."""

    def __init__(self, outer: FakeOpenAIClient) -> None:
        self._outer = outer

    def create(self, *, messages: list[dict], model: str | None = None, **kwargs) -> FakeChatCompletion:
        return self._outer._create(messages=messages, model=model, **kwargs)


class FakeChatAPI:
    """Stands in for `openai.OpenAI().chat`."""

    def __init__(self, outer: FakeOpenAIClient) -> None:
        self.completions = FakeCompletionsAPI(outer)


class FakeOpenAIClient:
    """Stands in for the real `openai.OpenAI` client
    `AIProjectClient.get_openai_client()` returns."""

    def __init__(self) -> None:
        self._scripted_replies: list[FakeChatCompletion] = []
        self.calls: list[dict] = []
        self.chat = FakeChatAPI(self)
        self.files = FakeFilesAPI()
        self.fine_tuning = FakeFineTuningAPI()

    def queue_reply(
        self, content: str, *, model: str = "cascadia-low-cost", cached_tokens: int = 0, **usage_overrides
    ) -> None:
        """Schedules the next `.chat.completions.create()` call to return `content`."""
        usage = FakeUsage(prompt_tokens_details=FakePromptTokensDetails(cached_tokens=cached_tokens), **usage_overrides)
        self._scripted_replies.append(
            FakeChatCompletion(choices=[FakeChoice(FakeMessageContent(content))], model=model, usage=usage)
        )

    def _create(self, *, messages: list[dict], model: str | None = None, **kwargs) -> FakeChatCompletion:
        self.calls.append({"messages": messages, "model": model, **kwargs})
        if not self._scripted_replies:
            raise AssertionError(
                "FakeOpenAIClient.chat.completions.create() called with no scripted reply queued. "
                "Call queue_reply() in your test before exercising the solution code."
            )
        return self._scripted_replies.pop(0)


# ---------------------------------------------------------------------------
# Foundry IQ knowledge bases (Lab 07) — a separate resource type from
# vector stores: it unifies file and structured sources behind one
# retrieval endpoint, rather than indexing files alone. No stable typed
# SDK as of writing this workshop; a real client reaches this through
# `AIProjectClient.send_request()` against a preview REST surface. This
# fake models the preview surface's shape, not a typed client.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeKnowledgeBase:
    id: str
    name: str
    sources: list[dict]


class FakeKnowledgeBasesClient:
    def __init__(self) -> None:
        self._knowledge_bases: dict[str, FakeKnowledgeBase] = {}
        self._counter = itertools.count(1)

    def create(self, *, name: str, sources: list[dict]) -> FakeKnowledgeBase:
        kb = FakeKnowledgeBase(id=f"kb-{next(self._counter):04d}", name=name, sources=list(sources))
        self._knowledge_bases[kb.id] = kb
        return kb

    def add_source(self, knowledge_base_id: str, source: dict) -> FakeKnowledgeBase:
        """Appends one source to an existing knowledge base (Lab 18)."""
        kb = self._knowledge_bases[knowledge_base_id]
        kb.sources.append(source)
        return kb


# ---------------------------------------------------------------------------
# Agent Applications (Lab 26, reused by Lab 27) — publishing, version
# snapshots, rollback, and traffic splitting. No stable typed SDK as of
# writing this workshop, same caveat as knowledge bases above.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeAgentVersion:
    version: int
    agent_id: str
    notes: str


@dataclasses.dataclass
class FakeAgentApplication:
    id: str
    name: str
    versions: list[FakeAgentVersion]
    traffic_split: dict[int, float]

    def version_numbers(self) -> set[int]:
        return {version.version for version in self.versions}


class FakeAgentApplicationsClient:
    def __init__(self) -> None:
        self._apps: dict[str, FakeAgentApplication] = {}
        self._counter = itertools.count(1)

    def create(self, *, name: str, agent_id: str, notes: str = "") -> FakeAgentApplication:
        version = FakeAgentVersion(version=1, agent_id=agent_id, notes=notes)
        app = FakeAgentApplication(
            id=f"app-{next(self._counter):04d}", name=name, versions=[version], traffic_split={1: 100.0}
        )
        self._apps[app.id] = app
        return app

    def get(self, app_id: str) -> FakeAgentApplication:
        return self._apps[app_id]

    def publish_version(self, app_id: str, *, agent_id: str, notes: str = "") -> FakeAgentVersion:
        """Publishes a new version. New versions get 100% of traffic by
        default — the same default the real Portal uses."""
        app = self._apps[app_id]
        next_number = len(app.versions) + 1
        version = FakeAgentVersion(version=next_number, agent_id=agent_id, notes=notes)
        app.versions.append(version)
        app.traffic_split = {next_number: 100.0}
        return version

    def set_traffic_split(self, app_id: str, split: dict[int, float]) -> FakeAgentApplication:
        app = self._apps[app_id]
        unknown = set(split) - app.version_numbers()
        if unknown:
            raise ValueError(f"Unknown version(s): {sorted(unknown)}")
        total = sum(split.values())
        if abs(total - 100.0) > 1e-6:
            raise ValueError(f"Traffic split must sum to 100, got {total}")
        app.traffic_split = dict(split)
        return app

    def rollback(self, app_id: str, *, to_version: int) -> FakeAgentApplication:
        app = self._apps[app_id]
        if to_version not in app.version_numbers():
            raise ValueError(f"Unknown version: {to_version}")
        app.traffic_split = {to_version: 100.0}
        return app


# ---------------------------------------------------------------------------
# Content Safety (Lab 29) — verified against `azure-ai-contentsafety`
# 1.0.0's `ContentSafetyClient.analyze_text()`: it takes an
# `AnalyzeTextOptions(text=...)` and returns a result whose
# `categories_analysis` is a list of {category, severity} entries, not
# a flat dict — different services score different category sets, so a
# list is honest about that; a flat dict would imply every text gets
# scored on the same fixed categories.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeAnalyzeTextOptions:
    """Stands in for `azure.ai.contentsafety.models.AnalyzeTextOptions`."""

    text: str


@dataclasses.dataclass
class FakeTextCategoryAnalysis:
    """Stands in for one entry in `AnalyzeTextResult.categories_analysis`."""

    category: str
    severity: int


@dataclasses.dataclass
class FakeAnalyzeTextResult:
    """Stands in for `azure.ai.contentsafety.models.AnalyzeTextResult`."""

    categories_analysis: list[FakeTextCategoryAnalysis]


class FakeContentSafetyClient:
    def __init__(self) -> None:
        self._scripted: dict[str, dict[str, int]] = {}
        self.calls: list[str] = []

    def script_result(self, text: str, severities: dict[str, int]) -> None:
        """`severities` keys are category names, e.g. "Hate", "Violence",
        "SelfHarm", "Sexual" — the real `TextCategory` enum values."""
        self._scripted[text] = severities

    def analyze_text(self, options: FakeAnalyzeTextOptions) -> FakeAnalyzeTextResult:
        self.calls.append(options.text)
        severities = self._scripted.get(options.text, {"Hate": 0, "Violence": 0, "SelfHarm": 0, "Sexual": 0})
        return FakeAnalyzeTextResult(
            categories_analysis=[
                FakeTextCategoryAnalysis(category=category, severity=severity)
                for category, severity in severities.items()
            ]
        )


# ---------------------------------------------------------------------------
# Native long-term memory (Lab 19) — facts persisted per user, outside
# any one thread. No stable typed SDK as of writing this workshop, same
# caveat as knowledge bases above.
# ---------------------------------------------------------------------------


class FakeMemoryClient:
    """Stands in for Foundry's native long-term agent memory store."""

    def __init__(self) -> None:
        self._facts: dict[str, list[str]] = {}

    def remember(self, user_id: str, fact: str) -> None:
        self._facts.setdefault(user_id, []).append(fact)

    def recall(self, user_id: str) -> list[str]:
        return list(self._facts.get(user_id, []))


# ---------------------------------------------------------------------------
# Content Understanding (Lab 18) — the real `azure-ai-contentunderstanding`
# 1.2.0b3 client is a long-running-operation API
# (`begin_analyze`/`begin_analyze_binary`, returning a poller), which
# this fake simplifies to a single synchronous call — a lab-scale
# simplification of the polling loop, not a shape this module got
# wrong. Say so in Lab 18's README rather than implying `analyze()` is
# the real method name.
# ---------------------------------------------------------------------------


class FakeContentUnderstandingClient:
    """Stands in for a (simplified, non-polling) Content Understanding analyzer client."""

    def __init__(self) -> None:
        self._scripted_results: dict[str, dict] = {}
        self.calls: list[dict] = []

    def script_result(self, file_path: str, result: dict) -> None:
        self._scripted_results[file_path] = result

    def analyze(self, *, file_path: str, schema: dict) -> dict:
        self.calls.append({"file_path": file_path, "schema": schema})
        if file_path not in self._scripted_results:
            raise AssertionError(
                f"FakeContentUnderstandingClient.analyze() called for {file_path!r} with no scripted "
                "result. Call script_result() in your test first."
            )
        return self._scripted_results[file_path]


# ---------------------------------------------------------------------------
# Agents (Labs 08, 09, 10) plus files and vector stores (Labs 06, 07) —
# verified against `azure-ai-agents` 1.1.0's `AgentsClient`. Real
# construction is `AgentsClient(endpoint, credential)`, separate from
# `AIProjectClient` — see this module's docstring. `create_agent()`'s
# keyword arguments (`model`, `name`, `instructions`, `tools`,
# `tool_resources`) already matched the real signature; threads,
# messages, runs, files, and vector stores are real *sub-clients*
# (`.threads`, `.messages`, `.runs`, `.files`, `.vector_stores`) with
# their own method names, not flat methods on `AgentsClient` itself.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeAgent:
    id: str
    name: str
    model: str
    instructions: str
    tools: list[dict] = dataclasses.field(default_factory=list)
    tool_resources: dict | None = None


@dataclasses.dataclass
class FakeThread:
    id: str


@dataclasses.dataclass
class FakeThreadMessage:
    id: str
    thread_id: str
    role: str
    content: str


@dataclasses.dataclass
class FakeRun:
    id: str
    thread_id: str
    agent_id: str
    status: str = "completed"
    tool_calls_made: list[tuple[str, dict]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class FakeUploadedFile:
    id: str
    filename: str


@dataclasses.dataclass
class FakeVectorStore:
    id: str
    name: str
    file_ids: list[str]


class FakeThreadsClient:
    """Stands in for `AgentsClient.threads`."""

    def __init__(self, agents: FakeAgentsClient) -> None:
        self._agents = agents

    def create(self) -> FakeThread:
        thread = FakeThread(id=self._agents._next_id("thread"))
        self._agents._threads[thread.id] = thread
        self._agents._messages[thread.id] = []
        return thread


class FakeMessagesClient:
    """Stands in for `AgentsClient.messages`."""

    def __init__(self, agents: FakeAgentsClient) -> None:
        self._agents = agents

    def create(self, thread_id: str, *, role: str, content: str) -> FakeThreadMessage:
        message = FakeThreadMessage(id=self._agents._next_id("msg"), thread_id=thread_id, role=role, content=content)
        self._agents._messages[thread_id].append(message)
        return message

    def list(self, thread_id: str, *, order: str = "asc") -> list[FakeThreadMessage]:
        """`order` is accepted for signature parity with the real
        `MessagesOperations.list()` (default "desc" there — newest
        first). This fake always stores messages oldest-first and
        returns them in that order regardless of `order`, so solution
        code should pass `order="asc"` explicitly rather than rely on
        this fake's storage order matching a real service's default.
        """
        return list(self._agents._messages[thread_id])


class FakeRunsClient:
    """Stands in for `AgentsClient.runs`.

    Real automatic tool execution goes through a `toolset` of real
    callables, resolved inside the service call. This fake keeps the
    simpler, explicit `tool_executor` callback Lab 09 introduced —
    close enough in spirit (the run still calls into your real tool
    function, not a mocked one) without reimplementing `ToolSet`.
    """

    def __init__(self, agents: FakeAgentsClient) -> None:
        self._agents = agents

    def create_and_process(
        self, thread_id: str, *, agent_id: str, tool_executor: Callable[[str, dict], object] | None = None
    ) -> FakeRun:
        run = FakeRun(id=self._agents._next_id("run"), thread_id=thread_id, agent_id=agent_id)
        for tool_name, tool_args in self._agents._tool_call_script.get(agent_id, []):
            result = tool_executor(tool_name, tool_args) if tool_executor else None
            run.tool_calls_made.append((tool_name, {"args": tool_args, "result": result}))
        reply = self._agents._final_reply_script.get(agent_id, "(no scripted reply configured)")
        self._agents.messages.create(thread_id, role="assistant", content=reply)
        return run


class FakeAgentFilesClient:
    """Stands in for `AgentsClient.files`."""

    def __init__(self) -> None:
        self._files: dict[str, FakeUploadedFile] = {}
        self._counter = itertools.count(1)

    def upload(self, *, file_path: str, purpose: str = "assistants") -> FakeUploadedFile:
        file = FakeUploadedFile(id=f"file-{next(self._counter):04d}", filename=file_path.rsplit("/", 1)[-1])
        self._files[file.id] = file
        return file


class FakeAgentVectorStoresClient:
    """Stands in for `AgentsClient.vector_stores`."""

    def __init__(self) -> None:
        self._stores: dict[str, FakeVectorStore] = {}
        self._counter = itertools.count(1)

    def create(self, *, name: str, file_ids: list[str]) -> FakeVectorStore:
        store = FakeVectorStore(id=f"vs-{next(self._counter):04d}", name=name, file_ids=list(file_ids))
        self._stores[store.id] = store
        return store


class FakeAgentsClient:
    """Stands in for `azure.ai.agents.AgentsClient`.

    Tool-calling labs script two things per agent: which tools the run
    should invoke (`script_tool_calls`), and what the agent says once
    those tool results come back (`script_final_reply`). The run then
    calls into your *real* tool functions through `tool_executor`, so
    the tool implementation itself is never mocked — only the model's
    decision to call it.
    """

    def __init__(self) -> None:
        self._agents: dict[str, FakeAgent] = {}
        self._threads: dict[str, FakeThread] = {}
        self._messages: dict[str, list[FakeThreadMessage]] = {}
        self._tool_call_script: dict[str, list[tuple[str, dict]]] = {}
        self._final_reply_script: dict[str, str] = {}
        self._counter = itertools.count(1)
        self.threads = FakeThreadsClient(self)
        self.messages = FakeMessagesClient(self)
        self.runs = FakeRunsClient(self)
        self.files = FakeAgentFilesClient()
        self.vector_stores = FakeAgentVectorStoresClient()

    def _next_id(self, prefix: str) -> str:
        return f"{prefix}-{next(self._counter):04d}"

    def script_tool_calls(self, agent_id: str, calls: list[tuple[str, dict]]) -> None:
        self._tool_call_script[agent_id] = calls

    def script_final_reply(self, agent_id: str, content: str) -> None:
        self._final_reply_script[agent_id] = content

    def create_agent(
        self,
        *,
        model: str,
        name: str,
        instructions: str,
        tools: list[dict] | None = None,
        tool_resources: dict | None = None,
    ) -> FakeAgent:
        agent = FakeAgent(
            id=self._next_id("agent"),
            name=name,
            model=model,
            instructions=instructions,
            tools=tools or [],
            tool_resources=tool_resources,
        )
        self._agents[agent.id] = agent
        return agent

    def get_agent(self, agent_id: str) -> FakeAgent:
        return self._agents[agent_id]

    @property
    def thread_count(self) -> int:
        """Number of threads created so far. Lets a test confirm a fresh
        thread was used per call without reaching into private state."""
        return len(self._threads)

    @property
    def last_thread_id(self) -> str:
        """ID of the most recently created thread. Lets a test inspect
        the thread a just-completed call used, without reaching into
        private state."""
        return next(reversed(self._threads))


# ---------------------------------------------------------------------------
# Fine-tuning (Appendix A) — verified against `openai` 2.54.0's
# `client.fine_tuning.jobs` (`create(model=, training_file=, suffix=)`,
# `retrieve(job_id)`), reached through the same `get_openai_client()`
# every other chat-completions call in this workshop uses — Azure OpenAI
# exposes fine-tuning through the OpenAI-compatible endpoint, not a
# Foundry-specific one. Whether a given Foundry deployment has
# fine-tuning enabled is still worth confirming with your instructor;
# that's a capability question, not an SDK-shape one.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeUploadedTrainingFile:
    """Stands in for the `FileObject` `client.files.create()` returns."""

    id: str
    filename: str


class FakeFilesAPI:
    """Stands in for `openai.OpenAI().files`."""

    def __init__(self) -> None:
        self._counter = itertools.count(1)

    def create(self, *, file, purpose: str) -> FakeUploadedTrainingFile:
        filename = file.rsplit("/", 1)[-1] if isinstance(file, str) else "training-data.jsonl"
        return FakeUploadedTrainingFile(id=f"file-{next(self._counter):04d}", filename=filename)


@dataclasses.dataclass
class FakeFineTuningJob:
    id: str
    model: str
    training_file: str
    suffix: str
    status: str = "queued"
    fine_tuned_model: str | None = None


class FakeFineTuningJobsAPI:
    """Stands in for `openai.OpenAI().fine_tuning.jobs`."""

    def __init__(self) -> None:
        self._jobs: dict[str, FakeFineTuningJob] = {}
        self._status_script: dict[str, list[str]] = {}
        self._counter = itertools.count(1)

    def script_status_sequence(self, job_id: str, statuses: list[str]) -> None:
        """Schedules the status a job reports on each successive
        `retrieve()` call, e.g. `["running", "running", "succeeded"]`."""
        self._status_script[job_id] = list(statuses)

    def create(self, *, model: str, training_file: str, suffix: str) -> FakeFineTuningJob:
        job = FakeFineTuningJob(
            id=f"ftjob-{next(self._counter):04d}", model=model, training_file=training_file, suffix=suffix
        )
        self._jobs[job.id] = job
        return job

    def retrieve(self, job_id: str) -> FakeFineTuningJob:
        job = self._jobs[job_id]
        script = self._status_script.get(job_id)
        if script:
            job.status = script.pop(0)
            if job.status == "succeeded":
                job.fine_tuned_model = f"{job.model}-ft-{job.suffix}"
        return job


class FakeFineTuningAPI:
    """Stands in for `openai.OpenAI().fine_tuning`."""

    def __init__(self) -> None:
        self.jobs = FakeFineTuningJobsAPI()


# ---------------------------------------------------------------------------
# Top-level client (what solution code actually receives in tests)
# ---------------------------------------------------------------------------


class FakeAIProjectClient:
    """Stands in for `azure.ai.projects.AIProjectClient`, extended with
    an `.agents` attribute for test convenience even though the real
    `AgentsClient` is constructed separately — see this module's
    docstring.
    """

    def __init__(self) -> None:
        self._openai_client = FakeOpenAIClient()
        self.agents = FakeAgentsClient()
        self.knowledge_bases = FakeKnowledgeBasesClient()
        self.content_understanding = FakeContentUnderstandingClient()
        self.memory = FakeMemoryClient()
        self.agent_applications = FakeAgentApplicationsClient()
        self.content_safety = FakeContentSafetyClient()

    def get_openai_client(self, *, agent_name: str | None = None, **kwargs) -> FakeOpenAIClient:
        return self._openai_client
