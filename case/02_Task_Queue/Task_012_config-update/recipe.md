# Recipe: Task_012 — config.yaml: Add video: Section

## 1. Objective
Append the complete video: configuration section to config.yaml. Must be backward-compatible (all new keys have defaults; video.enabled defaults to false).

## 2. Input Sources
- case/00_Constitution/core.md
- docs/research/VIDEO_PIPELINE_SPEC.md — Section 5 (full config.yaml schema)
- config.yaml — read existing file to find correct insertion point (end of file)

## 3. Output Specification
Append to config.yaml exactly the video: section from VIDEO_PIPELINE_SPEC.md Section 5.
The appended block must start with a comment separator and end with a newline.

Template (copy exactly from SPEC Section 5):
```yaml
# ============================================================
#  影片輸出設定 (Video Output Settings)
#  預設全部關閉，不影響現有使用者
# ============================================================
video:
  enabled: false
  backend: "basic"
  pixelle_video_url: "http://localhost:8000"
  tts:
    provider: "edge-tts"
    language: "zh-TW"
    edge_tts_voice: "zh-TW-HsiaoChenNeural"
    edge_tts_speed: "+0%"
    fish_speech_url: "http://localhost:8080"
    fish_speech_reference_audio: null
  image:
    provider: "none"
    comfyui_url: "http://localhost:8188"
    comfyui_workflow: "image_flux.json"
    runninghub_api_key: ""
    runninghub_workflow: "image_flux.json"
    prompt_prefix: ""
    width: 1920
    height: 1080
  resolution: "1920x1080"
  fps: 30
  bgm_file: null
  bgm_volume: 0.15
  intro:
    enabled: true
    duration_sec: 8
    channel_name: "我的頻道"
    channel_logo: null
    tagline: "每週更新 | 歡迎訂閱"
    video_title: ""
    template: "yt_intro_default"
  outro:
    enabled: true
    duration_sec: 12
    cta_text: "如果這個影片有幫助，請按讚並訂閱！"
    subscribe_hint: true
    next_video_text: ""
    template: "yt_outro_default"
```

## 4. Local Definition of Done
- [ ] config.yaml loads without YAML parse error after change
- [ ] yaml.safe_load(config.yaml)["video"]["enabled"] == False
- [ ] yaml.safe_load(config.yaml)["video"]["tts"]["provider"] == "edge-tts"
- [ ] All existing config keys unchanged (diff shows only additions)
- [ ] New section starts after existing content, separated by blank line

## 5. Constraints
- READ config.yaml first before modifying
- Append only — do NOT rewrite or reorganize existing content
- Preserve existing file encoding (UTF-8)

## 6. Escalation Trigger
Escalate if config.yaml has existing video: key that conflicts with this addition.
