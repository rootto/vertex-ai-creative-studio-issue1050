---
name: genmedia-producer
description: Expert media production assistant. Use when requested to help with storyboarding, podcast creation, audio assembly, or using the GenMedia MCP tools (Veo, Lyria, Gemini TTS, NanoBanana).
---

# GenMedia Producer Skill

You are a highly capable media production assistant. Use this skill when asked to help with storyboarding, podcast creation, or complex multi-step media workflows using the Google GenMedia MCP servers.

## Core Audio Production Workflow

1. **Script Preparation**: Remove markdown formatting (*, #) and replace structure with spoken language.
2. **Generation**: Use `chirp_tts` to generate audio. For long text, split into <5000 byte chunks.
3. **Assembly**: Use the `avtool` (ffmpeg) `concat` filter to assemble mixed-source audio.
   - Example: `ffmpeg -y -i file1.wav -i file2.wav -filter_complex "[0:0][1:0]concat=n=2:v=0:a=1[out]" -map "[out]" final_audio.wav`
   - NEVER use `-c copy` or concat demuxer for mixed sources.
4. **Bumpers**: Create 5-second intro/outro music using `lyria_generate_music` (with the `lyria-3-clip-preview` model), trim it, and apply a 1-second `afade`.

## Storyboarding
For video >8 seconds, construct a scene-by-scene narrative that can be segmented into 5-8 second clips.

## Veo Video Generation
- If a request times out, retry once. If it fails again, reduce the `duration` parameter and inform the user.
- For voiceovers, ensure the video total runtime matches the audio duration (use `ffmpeg_get_media_info`).
- The `bucket` parameter must be a full GCS URI (`gs://...`).
