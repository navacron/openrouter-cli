# TODO

Implemented so far: `video generate --frame-image`/`--frame-position`, `video wait`, `embed`,
`rerank`, `models info`, `providers list`, `generation info`.

## Open question: `orouter models validate`

Unclear what behavior beyond `models info` this should add (existence check? supported-parameter
validation against a specific request shape?). Clarify intent with the user before implementing.
