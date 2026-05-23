Feature: Checkpoint — Pipeline Progress Persistence
  The checkpoint module persists pipeline progress to disk so interrupted
  runs can resume without reprocessing completed slides.

  Scenario: Initial state creation
    Given a new session with session_id "test_001"
    When the Checkpoint is initialized
    Then video_progress.json is created
    And slides dict is empty
    And intro status is "pending"
    And outro status is "pending"

  Scenario: Mark step done
    Given a Checkpoint instance
    When mark("slide_01", "tts", "ok") is called
    Then checkpoint["slides"]["slide_01"]["tts"] equals "ok"

  Scenario: Mark step failed with error message
    Given a Checkpoint instance
    When mark("slide_01", "image", "failed", "timeout error") is called
    Then checkpoint["slides"]["slide_01"]["image"] equals "failed"
    And errors list contains an entry for slide_01 image step

  Scenario: Resume skips completed slides
    Given a checkpoint with slide_01 clip marked "ok"
    When the checkpoint is loaded via load_or_create
    Then is_done("slide_01", "clip") returns True

  Scenario: Concurrent session isolation
    Given two Checkpoint instances writing to the same file
    When multiple mark() calls are made sequentially
    Then all updates persist correctly without data loss

