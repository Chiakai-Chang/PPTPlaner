Feature: Clip Composition — Per-Slide Video Assembly
  The clip step combines a PNG image and WAV audio into an mp4 clip.

  Scenario: PNG plus WAV produces mp4 clip
    Given a PNG image at image_path
    And a WAV audio file at wav_path
    When compose_clip(image_path, wav_path, output_mp4) is called
    Then an mp4 file is written to output_mp4

  Scenario: Clip duration matches WAV duration
    Given a WAV file with 10 seconds of audio
    When compose_clip(image_path, wav_path, output_mp4) is called
    Then the output mp4 duration is approximately 10 seconds

  Scenario: ffmpeg not in PATH raises RuntimeError
    Given ffmpeg is not available in PATH
    When compose_clip(image_path, wav_path, output_mp4) is called
    Then RuntimeError is raised with message "ffmpeg not found in PATH"
    And the message suggests installing ffmpeg

  Scenario: ffmpeg failure raises ClipCompositionError
    Given ffmpeg returns a non-zero exit code
    When compose_clip(image_path, wav_path, output_mp4) is called
    Then ClipCompositionError is raised

