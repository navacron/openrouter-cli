# TODO

Deferred command groups, not yet implemented. The `openrouter` SDK (v0.11.3) already exposes all
of these - signatures below were confirmed by inspecting the installed package directly
(`python -c "import openrouter.X as m, inspect; print(inspect.signature(m.Y.z))"`), so
implementation should mostly be: add an `sdk_adapter.py` method following the existing pattern
(wrap in `self._call(...)`, return a small dataclass), then a Typer command in `commands/`.

## `video generate --frame-image` (image-to-video) + `orouter video wait`

- **frame images**: `video_generation.generate(..., frame_images=[{"type": "image_url", "image_url": {"url": ...}, "frame_type": "first_frame" | "last_frame"}])`.
  `frame_type` distinguishes first vs. last frame. Reuse `mime_utils.build_content_part(path, "image", mime)`
  for the `image_url` part and add `frame_type` alongside. Should be a repeatable `--frame-image PATH` +
  `--frame-position first|last` pair of options added to the existing `video generate` command, not a
  separate command.
- **`orouter video wait <job_id> --output ... [--poll-interval] [--timeout]`**: standalone version of the
  `--wait` polling loop already in `commands/video.py generate()`, for jobs that were submitted without
  `--wait`. Just calls `polling.poll_until_done` + `adapter.video_download` directly on an existing job id -
  no new adapter method needed.

## `orouter embed`

`embeddings.generate(input=<str or list[str]>, model=..., dimensions=None, encoding_format="float"|"base64", input_type=None) -> CreateEmbeddingsResponse`.
Command should accept one or more `--input` (repeatable, like `image edit`'s `--input`) or read from stdin.

## `orouter rerank`

`rerank.rerank(query=<str>, documents=[<str>, ...], model=..., top_n=None) -> CreateRerankResponse`.
`documents` items can be a plain string or `{"text": ..., "image": ...}` (at least one of the two) -
plain strings cover the common case. Command: `--query`, repeatable `--document`, `--top-n`.

## `orouter models info <author>/<slug>`

`models.get(author=<str>, slug=<str>) -> ModelResponse`. Command needs to split the model id argument on
the first `/` into author/slug before calling.

## `orouter providers list`

`providers.list() -> ListProvidersResponse`. No parameters - straightforward read-only listing, same shape
as `image models` / `video models`.

## `orouter generation info <id>`

`generations.get_generation(id=<str>) -> GenerationResponse`. Metadata/cost lookup for a past chat/image/video
generation by its id (e.g. the `id` field already present in `analyze`'s raw JSON output).

## Open question: `orouter models validate`

Unclear what behavior beyond `models info` this should add (existence check? supported-parameter
validation against a specific request shape?). Clarify intent with the user before implementing.
