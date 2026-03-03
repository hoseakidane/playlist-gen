Braintrust complete Python SDK reference
Braintrust is an AI evaluation and observability platform that provides logging, tracing, evaluation, prompt management, and production monitoring for LLM applications through a unified Python SDK. This document covers every major API surface so a coding agent can write Braintrust-integrated code without guessing.

1. What is Braintrust
Braintrust is an end-to-end platform for building, evaluating, and monitoring AI applications. 
Braintrust
 It provides traces (complete decision paths for AI interactions), experiments (structured offline evaluations), datasets (versioned test cases), scorers (quality measurement functions), and prompts (version-controlled templates). 
Braintrust
Braintrust
 The core workflow: instrument your app → observe production logs → annotate data → evaluate changes → deploy with confidence. 
Braintrust
Braintrust

Everything is organized into projects, each containing logs, experiments, datasets, prompts, and functions. 
Braintrust +2
 The SDK works identically for production logging and offline evaluation, so instrumentation code written once serves both purposes. 
Braintrust
Braintrust

Source: https://www.braintrust.dev/docs

2. Installation and setup
bash
pip install braintrust openai autoevals
Set environment variables:

bash
export BRAINTRUST_API_KEY="sk-..."       # From https://www.braintrust.dev/app/settings?subroute=api-keys
export OPENAI_API_KEY="sk-..."
Minimal working example:

python
import braintrust
from openai import OpenAI

logger = braintrust.init_logger(project="My Project")
client = braintrust.wrap_openai(OpenAI())

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"},
    ],
)
print(response.choices[0].message.content)
All LLM calls through the wrapped client are automatically logged 
Braintrust
 to the "My Project" project in Braintrust. View traces at the project's Logs tab in the UI.

Alternative — auto-instrumentation (no wrapping needed):

python
import braintrust
import os
os.environ["BRAINTRUST_DEFAULT_PROJECT"] = "My Project"
braintrust.auto_instrument()  # Must be called BEFORE creating OpenAI client

from openai import OpenAI
client = OpenAI()
# All calls now auto-traced
Source: https://www.braintrust.dev/docs/observability

3. Logging
Braintrust logging captures LLM calls as traces (one per request) composed of spans (individual operations). 
Braintrust +3
 Logging is asynchronous and non-blocking by default. 
Braintrust
Braintrust

3.1 OpenAI wrap (automatic logging)
python
from braintrust import init_logger, wrap_openai
from openai import OpenAI

logger = init_logger(project="My Project")
client = wrap_openai(OpenAI())

# Every API call is automatically logged with inputs, outputs, tokens, latency, cost
result = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Explain gravity"}],
)
wrap_openai works with both OpenAI() and AsyncOpenAI(). 
Braintrust +2

Source: https://www.braintrust.dev/docs/guides/traces

3.2 The @traced decorator
Decorator that creates a span for any function, automatically logging arguments as input and the return value as output. 
Braintrust
Braintrust
 It is a no-op when Braintrust is not active. 
Braintrust

python
import braintrust
from openai import OpenAI

logger = braintrust.init_logger(project="My Project")
client = braintrust.wrap_openai(OpenAI())

@braintrust.traced
def summarize(text: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Summarize the following text."},
            {"role": "user", "content": text},
        ],
    )
    return response.choices[0].message.content

# Creates a "summarize" span containing the nested LLM span
result = summarize("Long article text here...")
With custom name and type:

python
@braintrust.traced(name="custom_name", type="task")
def my_function(input_text):
    return process(input_text)
Accessing the current span inside a traced function:

python
@braintrust.traced
def my_function(input_text):
    braintrust.current_span().log(metadata={"custom_key": "value"})
    return result
Source: https://www.braintrust.dev/docs/instrument/custom-tracing

3.3 Manual logging with start_span
Lower-level alternative when you need explicit control: 
braintrust
Braintrust

python
import braintrust

logger = braintrust.init_logger(project="My Project")

span = braintrust.start_span(name="my_operation")
span.log(input="some input", output="some output", metadata={"step": "processing"})
span.end()
Source: https://www.braintrust.dev/docs/reference/sdks/python#start_span

3.4 Logging user feedback
python
import braintrust

logger = braintrust.init_logger(project="My Project")

@braintrust.traced
def handle_request(query: str):
    result = do_work(query)
    span_id = braintrust.current_span().export()
    return {"result": result, "request_id": span_id}

# Later, when user provides feedback:
def submit_feedback(request_id: str, score: float, comment: str):
    logger.log_feedback(
        id=request_id,
        scores={"correctness": score},
        comment=comment,
    )
3.5 Flushing
python
logger.flush()  # Ensure all pending logs are sent
Set async_flush=False in init_logger() for serverless environments without waitUntil. 
Braintrust
braintrust

Source: https://www.braintrust.dev/docs/guides/traces/customize

4. Evals / Evaluation framework
Every evaluation has three components: data (test cases), task (the AI function to test), and scores (quality measurement functions). 
Braintrust +3

4.1 Basic Eval() usage
python
from braintrust import Eval
from autoevals import Factuality

Eval(
    "Say Hi Bot",                         # Project name
    data=lambda: [                         # Test cases
        {"input": "Foo", "expected": "Hi Foo"},
        {"input": "Bar", "expected": "Hello Bar"},
    ],
    task=lambda input: "Hi " + input,      # Function under test
    scores=[Factuality],                   # Scoring functions
)
4.2 Eval with OpenAI
python
from braintrust import Eval
from autoevals import Factuality
from openai import OpenAI

client = OpenAI()

Eval(
    "QA Bot",
    data=lambda: [
        {"input": "What is the capital of France?", "expected": "Paris"},
        {"input": "What is 2+2?", "expected": "4"},
    ],
    task=lambda input: client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": input}],
    ).choices[0].message.content,
    scores=[Factuality],
    experiment_name="gpt4o-baseline",
    metadata={"model": "gpt-4o"},
    max_concurrency=5,
)
4.3 Eval with a Braintrust dataset
python
from braintrust import Eval, init_dataset
from autoevals import Factuality

Eval(
    "My Project",
    data=init_dataset("My Project", "My Dataset"),
    task=lambda input: call_model(input),
    scores=[Factuality],
)
4.4 Running evals
From CLI (primary method):

bash
braintrust eval my_eval.py
braintrust eval --watch my_eval.py      # Re-run on file changes
braintrust eval --no-send-logs my_eval.py  # Local-only, no data sent
Programmatically:

python
import asyncio
from braintrust import Eval
from autoevals import Factuality

result = Eval(
    "My Project",
    data=lambda: [{"input": "test", "expected": "test"}],
    task=lambda input: input,
    scores=[Factuality],
)
print(result)  # Contains summary with scores, improvements, regressions
4.5 Key Eval() parameters
Parameter	Type	Description
name	str	Project name (required, first positional arg)
data	callable / list / Dataset	Test cases with input, expected, metadata
task	callable	Function: input → output (usually an LLM call)
scores	list	List of scoring functions
experiment_name	str	Custom experiment name
metadata	dict	Key-value metadata for filtering
max_concurrency	int	Max parallel task executions
trial_count	int	Run each input N times for variance
no_send_logs	bool	Run locally without sending to Braintrust
base_experiment_name	str	Experiment to compare against
Source: https://www.braintrust.dev/docs/evaluate/run-evaluations

5. Datasets
Versioned collections of test cases 
Braintrust
 with input (required), expected (optional), and metadata (optional).

5.1 Creating and populating a dataset
python
import braintrust

dataset = braintrust.init_dataset("My App", "Customer Support")

dataset.insert(
    input={"question": "How do I reset my password?"},
    expected={"answer": "Click 'Forgot Password' on the login page."},
    metadata={"category": "authentication", "difficulty": "easy"},
)

dataset.insert(
    input={"question": "What's your refund policy?"},
    expected={"answer": "Full refunds within 30 days of purchase."},
    metadata={"category": "billing"},
)

dataset.flush()
5.2 Reading a dataset
python
dataset = braintrust.init_dataset("My App", "Customer Support")
for row in dataset:
    print(row["input"], row["expected"])
5.3 Using a dataset in Eval
python
from braintrust import Eval, init_dataset
from autoevals import Factuality

Eval(
    "My App",
    data=init_dataset("My App", "Customer Support"),
    task=lambda input: answer_question(input["question"]),
    scores=[Factuality],
)
5.4 init_dataset() parameters
Parameter	Type	Description
project	str	Project name
name	str	Dataset name
description	str	Optional description
version	str / int	Pin to a specific version
project_id	str	Project ID (alternative to name)
Source: https://www.braintrust.dev/docs/guides/datasets

6. Scoring functions
Scorers evaluate output quality, returning scores between 0 and 1. 
Braintrust
Braintrust

6.1 Built-in scorers (autoevals library)
bash
pip install autoevals
Complete list of key scorers:

Scorer	Import	Type	Description
Factuality	from autoevals import Factuality	LLM-based	Factual accuracy vs reference
ClosedQA	from autoevals import ClosedQA	LLM-based	Answer quality without expected
Battle	from autoevals import Battle	LLM-based	Comparative A/B evaluation
Summary	from autoevals import Summary	LLM-based	Summarization quality
Translation	from autoevals import Translation	LLM-based	Translation quality
ExactMatch	from autoevals import ExactMatch	Deterministic	Exact string equality
Levenshtein	from autoevals import Levenshtein	Deterministic	Edit distance similarity
NumericDiff	from autoevals import NumericDiff	Deterministic	Numeric similarity
JSONDiff	from autoevals import JSONDiff	Deterministic	JSON structural comparison
ValidJSON	from autoevals import ValidJSON	Deterministic	JSON validation + schema
EmbeddingSimilarity	from autoevals.string import EmbeddingSimilarity	Embedding	Semantic similarity
ListContains	from autoevals import ListContains	Semantic	List overlap evaluation
Moderation	from autoevals import Moderation	API-based	Content safety check
RAGAS scorers (for RAG): AnswerCorrectness, AnswerRelevancy, AnswerSimilarity, ContextPrecision, ContextRecall, ContextRelevancy, Faithfulness — all from autoevals.ragas. 
braintrust +2

6.2 Using built-in scorers
python
from autoevals import Factuality

# Standalone usage
evaluator = Factuality()
result = evaluator(
    output="People's Republic of China",
    expected="China",
    input="Which country has the highest population?",
)
print(f"Score: {result.score}")        # 1.0
print(f"Rationale: {result.metadata['rationale']}")

# In Eval
from braintrust import Eval
Eval("My Project",
    data=lambda: [{"input": "Capital of France?", "expected": "Paris"}],
    task=lambda input: "Paris",
    scores=[Factuality],
)
6.3 Custom scoring functions
Scorer signature: receives output, expected, input, metadata → returns a number (0–1) or a dict with name/score.

python
from braintrust import Eval

def exact_match(output, expected, **kwargs):
    return {
        "name": "exact_match",
        "score": 1 if output == expected else 0,
    }

def conciseness(output, **kwargs):
    return {
        "name": "conciseness",
        "score": 1 if len(output.split()) <= 200 else 0,
    }

Eval("My Project",
    data=lambda: [{"input": "Hi", "expected": "Hello"}],
    task=lambda input: "Hello",
    scores=[exact_match, conciseness],
)
6.4 LLM-as-a-judge scoring
python
from autoevals.llm import LLMClassifier

toxicity_scorer = LLMClassifier(
    name="toxicity",
    prompt_template="Is this text toxic? Text: {{output}}\nAnswer 'toxic' or 'not_toxic'.",
    choice_scores={"toxic": 0, "not_toxic": 1},
)

result = toxicity_scorer("This is a friendly message")
print(result.score)  # 1.0
Push custom scorers to Braintrust for reuse:

python
import braintrust

project = braintrust.projects.create(name="my-project")

@project.scorers.create(
    name="Language match",
    slug="language-match",
    description="Check if output and expected are the same language",
)
def language_match(output: str, expected: str):
    from langdetect import detect
    return 1.0 if detect(output) == detect(expected) else 0.0
Deploy: braintrust push scorer.py

Source: https://www.braintrust.dev/docs/evaluate/write-scorers, https://www.braintrust.dev/docs/reference/autoevals/python

7. Prompts
Version-controlled prompt templates that can be created in the UI or SDK, then loaded in code.

7.1 Creating prompts via SDK
python
import braintrust

project = braintrust.projects.create(name="SupportChatbot")

project.prompts.create(
    name="Brand Support",
    slug="brand-support",
    description="Brand-aligned support prompt",
    model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are a cheerful assistant for Sunshine Co. Use a positive tone.",
        },
        {"role": "user", "content": "{{{input}}}"},
    ],
    if_exists="replace",
)
Deploy: braintrust push prompt.py

Templates use Mustache syntax: {{variable}} for escaped, {{{variable}}} for unescaped. 
Braintrust +2

7.2 Using prompts in code — invoke() (recommended)
python
from braintrust import invoke

result = invoke(
    project_name="SupportChatbot",
    slug="brand-support",
    input={"input": "Why did my package disappear?"},
)
print(result)
Pin to a version or environment:

python
# Specific version
result = invoke(project_name="My Project", slug="summarizer", version="5878bd218351fb8e", input={"text": "..."})

# Environment
result = invoke(project_name="My Project", slug="summarizer", environment="production", input={"text": "..."})

# Streaming
result = invoke(project_name="My Project", slug="summarizer", input={"text": "..."}, stream=True)
for chunk in result:
    print(chunk)
7.3 Using prompts with load_prompt() + OpenAI
python
from openai import OpenAI
from braintrust import init_logger, load_prompt, wrap_openai

logger = init_logger(project="My Project")
client = wrap_openai(OpenAI())

def run_prompt(text: str):
    prompt = load_prompt("My Project", "summarizer")
    # .build() returns a dict compatible with OpenAI's API
    return client.chat.completions.create(**prompt.build(text=text))
load_prompt() parameters:

Parameter	Type	Description
project	str	Project name
slug	str	Prompt slug
version	str / int	Pin to specific version
environment	str	Load from environment (dev/staging/production)
defaults	dict	Default template variable values
Source: https://www.braintrust.dev/docs/evaluate/write-prompts, https://www.braintrust.dev/docs/deploy/prompts

8. Projects
Projects are the top-level organizational unit. Each project contains logs, experiments, datasets, prompts, and functions.

python
import braintrust

# Projects are auto-created when initializing experiments or loggers
experiment = braintrust.init("my-project", experiment="my-experiment")

# Or explicit creation
project = braintrust.projects.create(name="my-project")
Project hierarchy:

Organization
└── Project ("My Chatbot")
    ├── Logs (production traces)
    ├── Experiments (evaluation runs)
    ├── Datasets (versioned test cases)
    ├── Prompts (version-controlled templates)
    └── Functions (tools, scorers, workflows)
Source: https://www.braintrust.dev/docs/admin/projects

9. Experiments
An experiment is a permanent record created each time you run Eval(). It captures all inputs, outputs, scores, metadata, timing, token usage, cost, and git metadata.

9.1 Creating experiments
python
from braintrust import Eval
from autoevals import Factuality

# Each call creates a new experiment
Eval("My Project",
    data=lambda: [{"input": "test", "expected": "answer"}],
    task=lambda input: call_model(input),
    scores=[Factuality],
    experiment_name="gpt4o-v2",
    metadata={"model": "gpt-4o", "prompt_version": "v2"},
)
9.2 Comparing experiments
Braintrust automatically compares experiments by matching test cases on the input field. The UI shows score deltas, improvements, and regressions. 
Braintrust

9.3 Low-level experiment logging
python
import braintrust

experiment = braintrust.init(project="My Project", experiment="manual-test")
for item in test_data:
    output = my_model(item["input"])
    experiment.log(
        input=item["input"],
        output=output,
        expected=item["expected"],
        scores={"accuracy": 1.0 if output == item["expected"] else 0.0},
        metadata={"model": "gpt-4o"},
    )
summary = experiment.summarize()
print(summary)
9.4 Hill climbing (no expected outputs)
python
from braintrust import Eval, BaseExperiment
from autoevals import Battle

Eval("Say Hi Bot",
    data=BaseExperiment(),  # Uses previous experiment's output as expected
    task=lambda input: "Hi " + input,
    scores=[Battle.partial(instructions="Which response said 'Hi'?")],
)
Source: https://www.braintrust.dev/docs/evaluate, https://www.braintrust.dev/docs/guides/experiments/interpret

10. Online evaluation and production logging
Production traces are scored automatically in the background with zero impact on request latency. 
Braintrust +2

10.1 Production logging pattern
python
import braintrust
from openai import OpenAI

logger = braintrust.init_logger(project="My App")
client = braintrust.wrap_openai(OpenAI())

@braintrust.traced
def handle_request(user_input: str):
    result = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_input}],
    )
    output = result.choices[0].message.content
    braintrust.current_span().log(
        input=user_input,
        output=output,
        metadata={"user_id": "user-123"},
    )
    return output
10.2 Online scoring rules
Configured in the Braintrust UI under Settings → Project → Automations: 
braintrust
Braintrust

Click + Create rule
Select scorers (autoevals or custom pushed scorers)
Set sampling rate (e.g., 10% for high-volume apps) 
braintrust
Braintrust
Set scope: Trace or Span
Add SQL filters to target specific spans 
Braintrust
Scoring runs asynchronously as spans complete. Results appear as child spans in your logs. 
Braintrust +4

Source: https://www.braintrust.dev/docs/observe/score-online

11. AI Proxy (Gateway)
A unified API gateway providing access to 100+ models (OpenAI, Anthropic, Google, etc.) through a single OpenAI-compatible interface with caching, load balancing, and logging. 
braintrust
Braintrust

Note: The AI Proxy is being replaced by the Gateway (/docs/deploy/gateway). The proxy endpoints still work. 
Braintrust

11.1 Basic proxy usage
python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://api.braintrust.dev/v1/proxy",
    api_key=os.environ["BRAINTRUST_API_KEY"],
)

# Use any model through the same interface
response = client.chat.completions.create(
    model="gpt-4o",  # or "claude-3-5-sonnet-latest", "gemini-2.5-flash", etc.
    messages=[{"role": "user", "content": "What is a proxy?"}],
    seed=1,  # Activates caching (temperature=0 or seed set)
)
print(response.choices[0].message.content)
11.2 Proxy with caching control
python
client = OpenAI(
    base_url="https://api.braintrust.dev/v1/proxy",
    api_key=os.environ["BRAINTRUST_API_KEY"],
    default_headers={
        "x-bt-use-cache": "always",       # "auto" | "always" | "never"
        "Cache-Control": "max-age=172800", # 2-day TTL
    },
)
11.3 Proxy with full tracing
python
import braintrust
from openai import OpenAI

logger = braintrust.init_logger(project="My App")
client = braintrust.wrap_openai(
    OpenAI(
        base_url="https://api.braintrust.dev/v1/proxy",
        api_key=os.environ["BRAINTRUST_API_KEY"],
    )
)
# Requests go through proxy (caching, load balancing) AND get traced
Key proxy headers:

Header	Values	Purpose
x-bt-use-cache	auto / always / never	Control caching
x-bt-cache-ttl	seconds (max 604800)	Set cache TTL
x-bt-parent	project_id:... or project_name:...	Enable logging
Source: https://www.braintrust.dev/docs/deploy/ai-proxy

12. Python SDK API reference
12.1 Top-level functions
Function	Description
braintrust.Eval(name, data, task, scores, ...)	Define and run an evaluation
braintrust.EvalAsync(...)	Async variant of Eval
braintrust.init(project, experiment, ...)	Initialize an experiment, returns Experiment
braintrust.init_logger(project, ...)	Initialize a production logger
braintrust.init_dataset(project, name, ...)	Initialize/create a dataset
braintrust.wrap_openai(client)	Wrap OpenAI client for auto-tracing
braintrust.wrap_anthropic(client)	Wrap Anthropic client for auto-tracing
braintrust.wrap_litellm(module)	Wrap litellm module for tracing
braintrust.traced	Decorator to trace a function
braintrust.current_span()	Get the currently active span
braintrust.current_experiment()	Get the currently active experiment
braintrust.current_logger()	Get the currently active logger
braintrust.start_span(name, type, parent, ...)	Low-level span creation
braintrust.update_span(exported, event)	Update a span using exported string
braintrust.log(event)	Log an event to the current experiment
braintrust.flush()	Flush pending logs to server
braintrust.load_prompt(project, slug, ...)	Load a prompt template
braintrust.invoke(project_name, slug, input, ...)	Invoke a Braintrust function/prompt
braintrust.login(api_key, ...)	Authenticate (called automatically)
braintrust.auto_instrument()	Auto-instrument all AI library calls
braintrust.init_function(project_name, slug)	Load a function for use as task/scorer
braintrust.summarize()	Summarize current experiment
12.2 Key classes
Experiment — returned by braintrust.init():

python
experiment = braintrust.init(project="My Project")
experiment.log(input=..., output=..., expected=..., scores=..., metadata=...)
experiment.summarize()
experiment.flush()
experiment.close()
Dataset — returned by braintrust.init_dataset():

python
dataset = braintrust.init_dataset(project="My Project", name="My Dataset")
dataset.insert(input=..., expected=..., metadata=...)
dataset.update(id=record_id, metadata=...)
dataset.delete(record_id)
dataset.flush()
for row in dataset:
    print(row)
Span — accessible via current_span() or start_span():

python
span = braintrust.current_span()
span.log(input=..., output=..., scores=..., metadata=..., metrics=..., tags=...)
span.start_span(name="child", type="tool")  # Create child span
span.export()     # Serialize for distributed tracing
span.end()        # End the span
span.id           # Unique span identifier
span.permalink()  # URL to view in Braintrust UI
Span loggable fields: input, output, expected, scores (dict of str→float 0-1), metadata (dict), metrics (tokens, latency), tags (list of str), error. 
Braintrust
Braintrust

Span types: "llm", "task", "function", "tool", "eval"

12.3 Eval() complete parameter reference
Parameter	Type	Description
name	str	Project name (required)
data	callable / list / Dataset	Test cases (required)
task	callable	Function under test (required)
scores	list[callable]	Scoring functions (required)
experiment_name	str	Custom experiment name
metadata	dict	Key-value metadata
max_concurrency	int	Max parallel executions
trial_count	int	Runs per input
no_send_logs	bool	Local-only mode
base_experiment_name	str	Compare against this experiment
is_public	bool	Public visibility
timeout	float	Timeout in seconds
description	str	Experiment description
project_id	str	Project ID (alternative to name)
parameters	dict	Config values editable in playground
enable_cache	bool	Enable span cache (default True)
error_score_handler	callable	Custom handler for errored scores
Source: https://www.braintrust.dev/docs/reference/sdks/python

13. Tracing
13.1 Nested spans (automatic)
Spans automatically nest when traced functions call other traced functions:

python
import braintrust
from openai import OpenAI

logger = braintrust.init_logger(project="My Project")
client = braintrust.wrap_openai(OpenAI())

@braintrust.traced
def retrieve(query: str):
    # Simulated retrieval
    return ["doc1", "doc2"]

@braintrust.traced
def generate(query: str, context: list):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"Context: {context}"},
            {"role": "user", "content": query},
        ],
    ).choices[0].message.content

@braintrust.traced
def rag_pipeline(query: str):
    docs = retrieve(query)       # Child span 1
    answer = generate(query, docs)  # Child span 2 (contains nested LLM span)
    return answer

# Creates trace: rag_pipeline → retrieve, generate → LLM call
result = rag_pipeline("What is quantum computing?")
13.2 Context propagation
Braintrust uses async-friendly context variables — no need to pass span objects through the call stack:

python
@braintrust.traced
def deeply_nested_function():
    # Access current span from anywhere in the call stack
    braintrust.current_span().log(metadata={"deep": True})
    return "result"
13.3 Distributed tracing
When traces span multiple services, use span.export() to serialize context:

python
import braintrust

# Service A: Export span context
@braintrust.traced
def service_a_handler():
    span_export = braintrust.current_span().export()
    # Pass span_export to Service B via HTTP header, message queue, etc.
    response = requests.post("http://service-b/process",
        headers={"X-Trace-ID": span_export},
        json={"data": "..."},
    )
    return response.json()

# Service B: Resume under parent span
def service_b_handler(request):
    parent_export = request.headers.get("X-Trace-ID")
    with braintrust.start_span(name="service_b", parent=parent_export) as span:
        result = do_work()
        span.log(output=result)
        return result
13.4 Wrapping a custom LLM as an LLM span
python
@braintrust.traced(type="llm", name="Custom LLM")
def call_custom_llm(prompt: str):
    result = my_custom_llm(prompt)
    braintrust.current_span().log(
        input=[{"role": "user", "content": prompt}],
        output=result.text,
        metrics={
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "tokens": result.usage.total_tokens,
        },
    )
    return result.text
Setting type="llm" enables LLM duration metrics in the UI.

Source: https://www.braintrust.dev/docs/instrument/custom-tracing, https://www.braintrust.dev/docs/instrument/advanced-tracing

14. Human review and annotations
Braintrust provides built-in human review workflows for evaluating AI outputs, providing ground truth, and curating datasets.

14.1 Setup
Configure human review scores in Settings → Project → Human review:

Score Type	Description
Categorical	Predefined options with assigned scores (0–100%)
Continuous	Slider control, numeric 0–100%
Free-form	String values written to metadata
14.2 Review workflow
Navigate to the Review page in your project
Select data type: Log spans, Experiment spans, or Dataset rows
Score each item using configured review scores
Add comments and tags
Click Complete review and continue
Press "r" or the expand icon for dedicated Review Mode (optimized for batch review). Rows can be assigned to team members who receive email notifications. Views include Table, Kanban (Backlog/Pending/Complete columns), Timeline, and Thread layouts.

14.3 Capturing production user feedback (programmatic)
python
import braintrust

logger = braintrust.init_logger(project="My App")

# After user provides feedback on a response:
logger.log_feedback(
    id=span_id,              # From span.export() during the original request
    scores={"user_rating": 1.0},  # Thumbs up = 1.0, thumbs down = 0.0
    comment="Very helpful response",
    metadata={"user_id": "user-123"},
)
User-feedback-scored logs can then be filtered (e.g., scores.user_rating > 0.8) and added to evaluation datasets.

Source: https://www.braintrust.dev/docs/annotate/human-review

15. Tools and function calling
15.1 Automatic tool call logging
When using wrap_openai(), OpenAI function/tool calls are automatically captured as spans showing tool name, arguments, output, and duration.

python
import braintrust
from openai import OpenAI
import json

logger = braintrust.init_logger(project="Tool Demo")
client = braintrust.wrap_openai(OpenAI())

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
            "type": "object",
            "properties": {"location": {"type": "string"}},
            "required": ["location"],
        },
    },
}]

@braintrust.traced
def run_with_tools(user_message: str):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": user_message}],
        tools=tools,
    )
    message = response.choices[0].message
    if message.tool_calls:
        tool_results = []
        for tc in message.tool_calls:
            result = json.dumps({"temperature": 72, "conditions": "sunny"})
            tool_results.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })
        final = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_message}, message, *tool_results],
            tools=tools,
        )
        return final.choices[0].message.content
    return message.content

result = run_with_tools("What's the weather in SF?")
15.2 Custom tool span tracing
python
@braintrust.traced(type="tool", name="search_database")
def search_database(query: str, top_k: int = 3):
    braintrust.current_span().log(metadata={"query": query, "top_k": top_k})
    results = [{"id": 1, "text": "Result for: " + query}]
    return results
15.3 Defining reusable Braintrust tools
python
import braintrust
from pydantic import BaseModel
from typing import Literal

project = braintrust.projects.create(name="calculator")

class CalculatorInput(BaseModel):
    op: Literal["add", "subtract", "multiply", "divide"]
    a: float
    b: float

def calculator(op, a, b):
    match op:
        case "add": return a + b
        case "subtract": return a - b
        case "multiply": return a * b
        case "divide": return a / b

project.tools.create(
    handler=calculator,
    name="Calculator",
    slug="calculator",
    description="A simple calculator",
    parameters=CalculatorInput,
)
Deploy: braintrust push calculator.py

Tools can be attached to prompts — Braintrust auto-handles the tool call loop (up to 5 iterations).

Source: https://www.braintrust.dev/docs/core/functions/tools

Quick-reference: common patterns
Pattern A — Production logging with OpenAI
python
import braintrust
from openai import OpenAI

logger = braintrust.init_logger(project="My App")
client = braintrust.wrap_openai(OpenAI())

@braintrust.traced
def answer(question: str) -> str:
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": question}],
    ).choices[0].message.content
Pattern B — Evaluation with autoevals
python
from braintrust import Eval
from autoevals import Factuality, Levenshtein

Eval("My Project",
    data=lambda: [{"input": "Capital of France?", "expected": "Paris"}],
    task=lambda input: call_model(input),
    scores=[Factuality, Levenshtein],
)
Pattern C — Load and use a managed prompt
python
from braintrust import init_logger, load_prompt, wrap_openai
from openai import OpenAI

logger = init_logger(project="My Project")
client = wrap_openai(OpenAI())
prompt = load_prompt("My Project", "my-prompt-slug")
result = client.chat.completions.create(**prompt.build(user_input="Hello"))
Pattern D — Dataset → Eval pipeline
python
import braintrust
from braintrust import Eval, init_dataset
from autoevals import Factuality

# Create dataset
ds = braintrust.init_dataset("My Project", "Golden Set")
ds.insert(input={"q": "What is AI?"}, expected={"a": "Artificial Intelligence"})
ds.flush()

# Run eval against dataset
Eval("My Project",
    data=init_dataset("My Project", "Golden Set"),
    task=lambda input: answer_question(input["q"]),
    scores=[Factuality],
)

Source URL index
Topic	URL
Documentation home	https://www.braintrust.dev/docs
Tracing quickstart	https://www.braintrust.dev/docs/observability
Custom tracing	https://www.braintrust.dev/docs/instrument/custom-tracing
Advanced tracing	https://www.braintrust.dev/docs/instrument/advanced-tracing
Customize traces	https://www.braintrust.dev/docs/guides/traces/customize
Run evaluations	https://www.braintrust.dev/docs/evaluate/run-evaluations
Write scorers	https://www.braintrust.dev/docs/evaluate/write-scorers
Autoevals reference	https://www.braintrust.dev/docs/reference/autoevals/python
Datasets guide	https://www.braintrust.dev/docs/guides/datasets
Write prompts	https://www.braintrust.dev/docs/evaluate/write-prompts
Deploy prompts	https://www.braintrust.dev/docs/deploy/prompts
Playgrounds	https://www.braintrust.dev/docs/evaluate/playgrounds
Online scoring	https://www.braintrust.dev/docs/observe/score-online
AI Proxy	https://www.braintrust.dev/docs/deploy/ai-proxy
Gateway	https://www.braintrust.dev/docs/deploy/gateway
Tools	https://www.braintrust.dev/docs/core/functions/tools
Human review	https://www.braintrust.dev/docs/annotate/human-review
Project settings	https://www.braintrust.dev/docs/admin/projects
Python SDK reference	https://www.braintrust.dev/docs/reference/sdks/python
OpenAI integration	https://www.braintrust.dev/docs/integrations/ai-providers/openai
Prompt versioning cookbook	https://www.braintrust.dev/docs/cookbook/recipes/PromptVersioning
Eval SDK quickstart	https://www.braintrust.dev/docs/start/eval-sdk
Experiment interpretation	https://www.braintrust.dev/docs/guides/experiments/interpret
