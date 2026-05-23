Feature: TTS Generation — Text-to-Speech
  The TTS provider synthesizes text into WAV audio files.

  Scenario: Generate WAV from plain text
    Given a TTS provider is initialized
    When provider.generate("你好世界", output_path, "zh-TW") is called
    Then a WAV file is written to output_path
    And the file size is greater than 0 bytes

  Scenario: WAV file written to correct path
    Given a TTS provider is initialized
    When provider.generate("test", Path("/tmp/test.wav"), "zh-TW") is called
    Then the file exists at Path("/tmp/test.wav")

  Scenario: TTS failure raises TtsProviderError
    Given a TTS provider is initialized
    When the underlying TTS API raises an exception
    Then TtsProviderError is raised with the original error as context

  Scenario: Empty text raises ValueError
    Given a TTS provider is initialized
    When provider.generate("", output_path) is called
    Then ValueError is raised

