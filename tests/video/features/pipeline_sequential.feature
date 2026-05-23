Feature: Pipeline Sequential Processing
  The main pipeline processes slides in order, supports checkpoint resume,
  and continues on non-critical failures.

  Scenario: Slides processed in order 01 through N
    Given 3 slides in the slides directory
    When run_video_pipeline is called
    Then slide_01 is processed before slide_02
    And slide_02 is processed before slide_03

  Scenario: Completed clips skipped on restart
    Given a checkpoint with slide_01 clip marked "ok"
    When run_video_pipeline is called again
    Then slide_01 TTS step is not called
    And slide_01 image step is not called
    And slide_01 clip step is not called
    And slide_02 is processed normally

  Scenario: Failed slide logged and pipeline continues
    Given a slide that raises TtsProviderError during TTS
    When run_video_pipeline is called
    Then the error is logged to video_progress.json
    And the next slide is processed
    And the pipeline does not crash

  Scenario: Progress line printed per slide
    Given 5 slides to process
    When run_video_pipeline is called
    Then stdout contains "[1/5]" for the first slide
    And stdout contains "[5/5]" for the last slide

