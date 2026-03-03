import braintrust
from autoevals import LLMClassifier
from braintrust import Eval, init_dataset, Score
from pydantic import BaseModel, Field
from main import run_agent, DEFAULT_SYSTEM_PROMPT, DEFAULT_MODEL

project = braintrust.projects.create(name="PlaylistGenerator")


class ModelParam(BaseModel):
    value: str = Field(default=DEFAULT_MODEL, description="Model to use for the agent")


class SystemPromptParam(BaseModel):
    value: str = Field(
        default=DEFAULT_SYSTEM_PROMPT,
        description="System prompt for the playlist agent",
    )


def task(input: dict, hooks):
    user_input = input.get("user_request")
    params = hooks.parameters or {}
    # --dev mode extracts .value from Pydantic params; normal mode passes raw classes
    model = params.get("model") if isinstance(params.get("model"), str) else DEFAULT_MODEL
    system_prompt = (
        params.get("system_prompt")
        if isinstance(params.get("system_prompt"), str)
        else DEFAULT_SYSTEM_PROMPT
    )
    return run_agent(user_input, model=model, system_prompt=system_prompt)

# -- Shared scorer config --

VARIETY_PROMPT = """Evaluate the variety of this playlist based on artist and genre diversity.

Playlist: {{output}}

A great playlist has songs from many different artists and multiple genres.
A poor playlist repeats artists or stays in a single genre.

Pick the best choice:
(a) High variety — multiple distinct artists AND genres represented
(b) Moderate variety — some diversity but noticeable repetition
(c) Low variety — mostly the same artist"""

VARIETY_CHOICE_SCORES = {"a": 1.0, "b": 0.5, "c": 0.0}


def _playlist_length_score(output: dict) -> float:
    playlist = output.get("playlist") if isinstance(output, dict) else None
    if not playlist:
        return 0.0
    duration = playlist.get("total_duration_min", 999)
    return 1.0 if duration <= 30 else 0.0


# -- Local scorers (for `braintrust eval`) --

variety_scorer = LLMClassifier(
    name="Variety",
    prompt_template=VARIETY_PROMPT,
    choice_scores=VARIETY_CHOICE_SCORES,
    model="gpt-4o-mini",
)


def playlist_length_scorer(output: dict):
    return Score(name="PlaylistLength", score=_playlist_length_score(output))


# -- Pushable scorers (for `braintrust push` online scoring) --


class PlaylistLengthInput(BaseModel):
    output: dict


project.scorers.create(
    name="Variety",
    slug="variety",
    description="Evaluates artist and genre diversity in a playlist",
    model="gpt-4o-mini",
    use_cot=True,
    choice_scores=VARIETY_CHOICE_SCORES,
    messages=[{"role": "user", "content": VARIETY_PROMPT}],
)

project.scorers.create(
    name="PlaylistLength",
    slug="playlist-length",
    description="Checks if playlist is under 30 minutes",
    handler=_playlist_length_score,
    parameters=PlaylistLengthInput,
)

Eval(
    name="PlaylistGenerator",
    task=task,
    data=init_dataset(project="PlaylistGenerator", name="InputExamples"),
    scores=[variety_scorer, playlist_length_scorer],
    parameters={
        "model": ModelParam,
        "system_prompt": SystemPromptParam,
    },
)
