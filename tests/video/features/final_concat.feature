Feature: Final Concatenation — Merge All Clips
  The concat step merges intro + slide clips + outro into a single mp4.

  Scenario: Clips concatenated as intro plus slides plus outro
    Given intro_clip.mp4, clip_01.mp4, clip_02.mp4, and outro_clip.mp4
    When concat_clips(intro, [clip_01, clip_02], outro, output) is called
    Then output.mp4 exists
    And the output duration equals sum of all input durations

  Scenario: BGM mixed when bgm_file is set
    Given a BGM file at bgm_path
    When concat_clips(intro, clips, outro, output, bgm_file=bgm_path) is called
    Then ffmpeg is called with BGM mixing arguments

  Scenario: No BGM when bgm_file is null
    Given bgm_file is None
    When concat_clips(intro, clips, outro, output) is called
    Then ffmpeg is called without BGM-related arguments

  Scenario: Output mp4 exists and is non-zero size
    Given valid input clips
    When concat_clips is called
    Then output.mp4 file size is greater than 0 bytes

  Scenario: Empty slides list raises ValueError
    Given an empty slide_clips list
    When concat_clips(intro, [], outro, output) is called
    Then ValueError is raised

