# Task_012 Output — config.yaml video section added

## Summary
Appended complete video configuration section to `config.yaml` following VIDEO_PIPELINE_SPEC.md Section 5.

## Configuration Added
- **video.enabled**: `false` (opt-in by default)
- **video.backend**: `"basic"` (PIL + ffmpeg, no ComfyUI)
- **video.tts**: Edge-TTS provider with voice `zh-TW-HsiaoChenNeural`
- **video.image**: `none` provider (text overlay only)
- **video.intro**: 8s default YouTube intro
- **video.outro**: 12s default YouTube outro with CTA
- **video.resolution**: `1920x1080`
- **video.fps**: `30`
- **video.bgm**: disabled by default (`null`)
- **video.bgm_volume**: `0.15`

## Verification
```bash
python -c "import yaml; cfg = yaml.safe_load(open('config.yaml')); assert 'video' in cfg; assert cfg['video']['enabled'] == False; print('OK')"
```

## Files Modified
- `config.yaml` — appended video section after `agent_execution_retries`

## Status
REVIEW
