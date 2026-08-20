"""Shared fakes for the Foundry SDK, reused by every lab's test suite.

Solution code never imports this module — it takes a project client (or
a factory) as a constructor argument, and only *tests* hand it one of
these fakes instead of a real `azure.ai.projects.AIProjectClient`. That
boundary is what lets every lab's tests run offline and free.

Verified against the `azure-ai-projects` surface shape as of writing
this workshop. If a lab's solution code needs a client call this module
doesn't fake yet, extend the matching Fake*Client class here instead of
mocking it locally in one lab's tests — that's the boilerplate CLAUDE.md
asks you not to duplicate.
"""

from __future__ import annotations

import dataclasses
import itertools
import uuid
from collections.abc import Callable


# ---------------------------------------------------------------------------
# Chat completions (Labs 03, 04, 05)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeUsage:
    prompt_tokens: int = 42
    completion_tokens: int = 18
    total_tokens: int = 60
    # Set when a scripted reply represents a prompt-cache hit. Lab 05
    # reads this field to prove caching happened.
    cached_tokens: int = 0


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


class FakeChatCompletionsClient:
    """Stands in for `AIProjectClient.inference.get_chat_completions_client()`."""

    def __init__(self) -> None:
        self._scripted_replies: list[FakeChatCompletion] = []
        self.calls: list[dict] = []

    def queue_reply(self, content: str, *, model: str = "cascadia-low-cost", **usage_overrides) -> None:
        """Schedules the next `.complete()` call to return `content`."""
        usage = FakeUsage(**usage_overrides)
        self._scripted_replies.append(
            FakeChatCompletion(choices=[FakeChoice(FakeMessageContent(content))], model=model, usage=usage)
        )

    def complete(self, *, messages: list[dict], model: str | None = None, **kwargs) -> FakeChatCompletion:
        self.calls.append({"messages": messages, "model": model, **kwargs})
        if not self._scripted_replies:
            raise AssertionError(
                "FakeChatCompletionsClient.complete() called with no scripted reply queued. "
                "Call queue_reply() in your test before exercising the solution code."
            )
        return self._scripted_replies.pop(0)


# ---------------------------------------------------------------------------
# Files and vector stores (Labs 06, 07)
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeUploadedFile:
    id: str
    filename: str


@dataclasses.dataclass
class FakeVectorStore:
    id: str
    name: str
    file_ids: list[str]


class FakeFilesClient:
    def __init__(self) -> None:
        self._files: dict[str, FakeUploadedFile] = {}
        self._counter = itertools.count(1)

    def upload(self, *, file_path: str) -> FakeUploadedFile:
        file = FakeUploadedFile(id=f"file-{next(self._counter):04d}", filename=file_path.rsplit("/", 1)[-1])
        self._files[file.id] = file
        return file


class FakeVectorStoresClient:
    def __init__(self) -> None:
        self._stores: dict[str, FakeVectorStore] = {}
        self._counter = itertools.count(1)

    def create(self, *, name: str, file_ids: list[str]) -> FakeVectorStore:
        store = FakeVectorStore(id=f"vs-{next(self._counter):04d}", name=name, file_ids=list(file_ids))
        self._stores[store.id] = store
        return store


# ---------------------------------------------------------------------------
# Foundry IQ knowledge bases (Lab 07) — a separate resource type from
# vector stores: it unifies file and structured sources behind one
# retrieval endpoint, rather than indexing files alone.
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
# snapshots, rollback, and traffic splitting. Separate from
# FakeAgentsClient, since an agent and its published Agent Application
# are different resources in Foundry too.
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
# Content Safety (Lab 29) — per-category severity scoring on a piece of
# text, separate from the chat completions client since it's a distinct
# Azure AI service, not a model call.
# ---------------------------------------------------------------------------


class FakeContentSafetyClient:
    def __init__(self) -> None:
        self._scripted: dict[str, dict[str, int]] = {}
        self.calls: list[str] = []

    def script_result(self, text: str, severities: dict[str, int]) -> None:
        self._scripted[text] = severities

    def analyze_text(self, text: str) -> dict[str, int]:
        self.calls.append(text)
        return self._scripted.get(text, {"hate": 0, "violence": 0, "self_harm": 0, "sexual": 0})


# ---------------------------------------------------------------------------
# Native long-term memory (Lab 19) — facts persisted per user, outside
# any one thread. Separate from FakeAgentsClient's threads/messages,
# since real Foundry memory outlives any single thread too.
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
# Content Understanding (Lab 18) — structured extraction from documents
# and images, separate from both file search and knowledge bases.
# ---------------------------------------------------------------------------


class FakeContentUnderstandingClient:
    """Stands in for an Azure Content Understanding analyzer client."""

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
# Agents, threads, runs (Labs 08, 09, 10)
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


class FakeAgentsClient:
    """Stands in for `AIProjectClient.agents`.

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

    def create_thread(self) -> FakeThread:
        thread = FakeThread(id=self._next_id("thread"))
        self._threads[thread.id] = thread
        self._messages[thread.id] = []
        return thread

    def create_message(self, *, thread_id: str, role: str, content: str) -> FakeThreadMessage:
        message = FakeThreadMessage(id=self._next_id("msg"), thread_id=thread_id, role=role, content=content)
        self._messages[thread_id].append(message)
        return message

    def create_and_process_run(
        self,
        *,
        thread_id: str,
        agent_id: str,
        tool_executor: Callable[[str, dict], object] | None = None,
    ) -> FakeRun:
        run = FakeRun(id=self._next_id("run"), thread_id=thread_id, agent_id=agent_id)
        for tool_name, tool_args in self._tool_call_script.get(agent_id, []):
            result = tool_executor(tool_name, tool_args) if tool_executor else None
            run.tool_calls_made.append((tool_name, tool_args))
            run.tool_calls_made[-1] = (tool_name, {"args": tool_args, "result": result})
        reply = self._final_reply_script.get(agent_id, "(no scripted reply configured)")
        self.create_message(thread_id=thread_id, role="assistant", content=reply)
        return run

    def list_messages(self, *, thread_id: str) -> list[FakeThreadMessage]:
        return list(self._messages[thread_id])

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
# Fine-tuning (Appendix A) — Foundry's fine-tuning API was still in
# preview as of writing this workshop, so this fake models the shape
# every fine-tuning API in this family shares (submit a job against a
# training file, poll until it succeeds or fails, get back a deployable
# model name) rather than one verified against a stable public SDK.
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class FakeFineTuningJob:
    id: str
    base_model: str
    training_file_id: str
    suffix: str
    status: str = "queued"
    fine_tuned_model: str | None = None


class FakeFineTuningClient:
    def __init__(self) -> None:
        self._jobs: dict[str, FakeFineTuningJob] = {}
        self._status_script: dict[str, list[str]] = {}
        self._counter = itertools.count(1)

    def script_status_sequence(self, job_id: str, statuses: list[str]) -> None:
        """Schedules the status a job reports on each successive `get()`
        call, e.g. `["running", "running", "succeeded"]`."""
        self._status_script[job_id] = list(statuses)

    def create(self, *, base_model: str, training_file_id: str, suffix: str) -> FakeFineTuningJob:
        job = FakeFineTuningJob(
            id=f"ft-{next(self._counter):04d}", base_model=base_model, training_file_id=training_file_id, suffix=suffix
        )
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> FakeFineTuningJob:
        job = self._jobs[job_id]
        script = self._status_script.get(job_id)
        if script:
            job.status = script.pop(0)
            if job.status == "succeeded":
                job.fine_tuned_model = f"{job.base_model}-ft-{job.suffix}"
        return job


# ---------------------------------------------------------------------------
# Top-level client (what solution code actually receives in tests)
# ---------------------------------------------------------------------------


class FakeInference:
    def __init__(self, chat_client: FakeChatCompletionsClient) -> None:
        self._chat_client = chat_client

    def get_chat_completions_client(self) -> FakeChatCompletionsClient:
        return self._chat_client


class FakeAIProjectClient:
    """Stands in for `azure.ai.projects.AIProjectClient`."""

    def __init__(self) -> None:
        self.inference = FakeInference(FakeChatCompletionsClient())
        self.agents = FakeAgentsClient()
        self.files = FakeFilesClient()
        self.vector_stores = FakeVectorStoresClient()
        self.knowledge_bases = FakeKnowledgeBasesClient()
        self.content_understanding = FakeContentUnderstandingClient()
        self.memory = FakeMemoryClient()
        self.agent_applications = FakeAgentApplicationsClient()
        self.content_safety = FakeContentSafetyClient()
        self.fine_tuning = FakeFineTuningClient()
