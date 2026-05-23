Feature: Bookend Generation — Intro and Outro Clips
  The bookend step renders Jinja2 HTML templates into intro/outro video clips.

  Scenario: Intro clip generated from template and config
    Given a valid Jinja2 intro template at template_path
    And config dict with channel_name, tagline, video_title
    When generate_bookend_clip(template_path, config, output_mp4, 8) is called
    Then an mp4 clip is written to output_mp4
    And the clip duration is approximately 8 seconds

  Scenario: Outro clip generated from template and config
    Given a valid Jinja2 outro template at template_path
    And config dict with cta_text, subscribe_hint, channel_name
    When generate_bookend_clip(template_path, config, output_mp4, 12) is called
    Then an mp4 clip is written to output_mp4
    And the clip duration is approximately 12 seconds

  Scenario: Missing logo path handled gracefully
    Given an intro template with logo_path set to empty string
    When generate_bookend_clip is called
    Then the template renders without error
    And no broken image appears in the output

  Scenario: Missing template file raises FileNotFoundError
    Given template_path does not exist
    When generate_bookend_clip(template_path, config, output_mp4, 8) is called
    Then FileNotFoundError is raised

