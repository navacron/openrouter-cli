# Stick-Figure Explainer Video Recipe

End-to-end recipe for turning a topic into a narrated stick-figure video using `orouter`
+ ffmpeg. Worked example below is the "Vikings Were Surprisingly Obsessed With Hygiene" video
(`viking_video/`).

## Known-good models (verified working)

| Purpose | Model | Notes |
|---|---|---|
| Script writing | `anthropic/claude-sonnet-5` | |
| Image generation | `google/gemini-3.1-flash-image` | Returns PNG **or** JPEG bytes depending on prompt/model choice - see gotcha below. |
| Text-to-speech | `microsoft/mai-voice-2` | Requires `--voice en-US-AriaNeural` (`alloy` etc. → `Provider returned 400`) and `--format mp3`. |

TTS models that looked promising but didn't work at time of writing - retry occasionally,
providers change:
- `openai/tts-1`, `openai/tts-1-hd`, `openai/gpt-4o-mini-tts` - not in this OpenRouter catalog (`does not exist`).
- `google/gemini-3.1-flash-tts-preview` - valid model, but only accepts `--format pcm`, and was returning `500` from the provider.
- `x-ai/grok-voice-tts-1.0` - valid model per OpenRouter routing, but provider returned `404` (not live yet).

There's no CLI/SDK command to *list* TTS models (no `models.list` category covers them) - the
only way to find a working one is to try candidates with `OPENROUTER_DEBUG=1` and read the
actual HTTP status:
- `does not exist` (400 from OpenRouter itself) → wrong slug, keep guessing.
- `Provider returned 400` → slug is right, request params (usually `--voice`) are wrong.
- `Provider returned 404`/`500` → slug is right, provider integration is currently down.

## Steps

### 1. Write the script

```bash
orouter chat "Write a short, punchy narration script (about 45-60 seconds when read aloud,
~120-150 words) for a stick-figure explainer video titled '<TITLE>'. Break it into 5-7 numbered
scenes. Each scene should have a 'NARRATION:' line (exact words to be spoken, no stage directions
mixed in) and a one-line 'VISUAL:' description of what the stick-figure animation shows for that
beat. Output ONLY the numbered scenes in that format, no intro or outro commentary." \
  --model anthropic/claude-sonnet-5 --max-tokens 1000 > script.txt
```

### 2. Derive image prompts from the script

Feed the whole script back to a chat model and ask for one image prompt per scene, with a fixed
style baked into every prompt so the images look consistent as a set:

```bash
SCRIPT_CONTENT=$(cat script.txt)
orouter chat "Here is a numbered scene script for a stick-figure explainer video:

${SCRIPT_CONTENT}

For each numbered scene, write one image-generation prompt that will produce a consistent
stick-figure illustration matching that scene's VISUAL description. Style requirements to bake
into every prompt: minimalist black stick-figure line art, thick clean outlines, on a plain flat
off-white background, simple flat color accents only where mentioned, no text or letters in the
image, consistent simple art style across all scenes, 16:9 composition. Output ONLY a numbered
list (matching the scene numbers) of the final image prompts, one per line, no extra commentary." \
  --model anthropic/claude-sonnet-5 --max-tokens 1200 > image_prompts.txt
```

### 3. Generate one image per scene

`image_prompts.txt` has a blank line between numbered entries (chat models tend to double-space
lists) - loop over it and skip empty lines, or you'll burn calls on empty prompts:

```bash
mkdir -p images
i=0
while IFS= read -r line; do
  [ -z "$line" ] && continue
  i=$((i+1))
  prompt=$(echo "$line" | sed -E 's/^[0-9]+\.\s*//')
  num=$(printf "%02d" "$i")
  orouter image generate --prompt "$prompt" --model google/gemini-3.1-flash-image \
    --output "images/scene_${num}.png"
done < image_prompts.txt
```

**Gotcha:** `orouter image generate` writes the raw returned bytes to whatever extension you pass
via `--output`, without checking the model's actual returned format
(`io_utils.py:save_b64_images`, ~line 10-19 - doesn't consult `ImageResult.media_types`). The
model sometimes returns JPEG bytes even when the file is named `.png`, which silently breaks
ffmpeg's PNG decoder later and truncates the video. Always verify after generating:

```bash
for f in images/scene_*.png; do echo -n "$f: "; file -b "$f"; done
```

If any say "JPEG image data" instead of "PNG image data", re-encode them to real PNGs in place:

```bash
for f in images/scene_02.png images/scene_04.png; do   # whichever came back mislabeled
  ffmpeg -y -i "$f" -frames:v 1 "${f%.png}_fixed.png" && mv "${f%.png}_fixed.png" "$f"
done
```

(Longer-term fix: pass `--output-format png` explicitly on every `image generate` call to force
the model to return PNG, or patch `io_utils.py` to pick the extension from the real media type.)

### 4. Generate narration audio

Extract just the `NARRATION:` lines from the script (strip the numbering/labels/VISUAL lines),
join into one block, and synthesize:

```bash
grep "NARRATION:" script.txt | sed -E 's/^[0-9]+\. NARRATION: //' > narration_lines.txt
paste -sd' ' narration_lines.txt > narration.txt

orouter audio speak "$(cat narration.txt)" \
  --voice en-US-AriaNeural --model microsoft/mai-voice-2 --format mp3 --output narration.mp3
```

Check the actual duration - you'll need it for step 5:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 narration.mp3
```

### 5. Time each image to its narration line, build the concat list

Equal-duration-per-image looks choppy when scenes have very different line lengths. Weight each
scene's on-screen time by its share of the total word count instead:

```python
words = [11, 14, 18, 11, 18, 13, 11]        # word count per scene's NARRATION line
total_duration = 39.24                       # from ffprobe above
total_words = sum(words)
durs = [round(w / total_words * total_duration, 3) for w in words]

with open("concat_list.txt", "w") as f:
    for i, d in enumerate(durs, start=1):
        f.write(f"file 'images/scene_{i:02d}.png'\n")
        f.write(f"duration {d}\n")
    # ffmpeg concat demuxer quirk: the LAST file's duration directive is ignored unless
    # the last file is repeated once more with no duration after it.
    f.write(f"file 'images/scene_{len(durs):02d}.png'\n")
```

### 6. Stitch with ffmpeg

```bash
ffmpeg -y \
  -f concat -safe 0 -i concat_list.txt \
  -i narration.mp3 \
  -vf "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p" \
  -c:v libx264 -pix_fmt yuv420p \
  -c:a aac -b:a 192k \
  -shortest \
  final_video.mp4
```

`scale`+`pad` letterboxes every image to 1280x720 regardless of native aspect ratio; `-shortest`
caps output length at the audio track.

**Always verify the output duration matches the narration** - a silent truncation (e.g. from the
mislabeled-JPEG gotcha in step 3) will produce a shorter-than-expected file with no error:

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 final_video.mp4
```

## Known repo bugs surfaced by this workflow

1. ~~`sdk_adapter.py` had no HTTP timeout, so slow endpoints (image/video gen) hit httpx's 5s
   default, got treated as a retryable connection error, and silently retried for up to an hour.~~
   Fixed: `sdk_adapter.py` now passes `timeout_ms=120_000` when constructing the `OpenRouter`
   client.
2. `io_utils.save_b64_images()` doesn't check the actual returned media type before writing -
   see the gotcha in step 3. Not yet fixed.
