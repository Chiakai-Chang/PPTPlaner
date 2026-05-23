# Recipe: Task_010 — HTML Templates: Intro + Outro

## 1. Objective
Create two professional YouTube-style HTML templates for intro and outro video clips. Templates are rendered by playwright (1920x1080 viewport) and must look great as static video frames.

## 2. Input Sources
- case/00_Constitution/core.md
- docs/research/VIDEO_PIPELINE_SPEC.md — Section 7 (Jinja2 template variables)

## 3. Output Specification

### video/templates/yt_intro_default.html
A clean, professional intro frame containing:
- Background: dark gradient (deep blue/navy, e.g. #0D1B2A to #1B2838)
- Channel name: large, centered, white, sans-serif font
- Tagline: smaller, centered, light blue or gray
- Video title: medium size, centered, below tagline, slightly dimmer
- Optional logo: if {{ logo_path }} is non-empty, show as <img> top-left or centered
- Jinja2 variables: {{ channel_name }}, {{ tagline }}, {{ logo_path }}, {{ video_title }}, {{ duration_sec }}

### video/templates/yt_outro_default.html
A clean outro frame containing:
- Same background style as intro
- "感謝收看" (Thank you for watching) or equivalent header
- CTA text: {{ cta_text }} — prominent, centered
- Subscribe hint: if {{ subscribe_hint }}, show a styled "▶ 訂閱" button-like element
- Next video text: if {{ next_video_text }} non-empty, show in smaller text below
- Channel name: bottom of frame
- Jinja2 variables: {{ channel_name }}, {{ cta_text }}, {{ subscribe_hint }}, {{ next_video_text }}, {{ duration_sec }}

Both templates:
- Must be exactly 1920x1080 at playwright default zoom (set body width/height to 1920px x 1080px)
- All fonts from system (system-ui, sans-serif) — no Google Fonts CDN
- All CSS inline in <style> tag
- No external JS libraries
- Valid HTML5

## 4. Local Definition of Done
- [ ] video/templates/yt_intro_default.html exists and is valid HTML5
- [ ] video/templates/yt_outro_default.html exists and is valid HTML5
- [ ] All Jinja2 variables listed in spec are present in templates
- [ ] Body dimensions set to 1920px x 1080px in CSS
- [ ] No external CDN URLs in templates
- [ ] Visual: dark background, white/light text, readable at video resolution

## 5. Constraints
- No external CDN (no Google Fonts, no Bootstrap, no jQuery)
- Must render correctly even when logo_path is empty string
- Jinja2 delimiters: {{ variable }}, {% if condition %}...{% endif %}

## 6. Escalation Trigger
Escalate if playwright cannot render the template at 1920x1080 without scrollbars (overflow issue).
