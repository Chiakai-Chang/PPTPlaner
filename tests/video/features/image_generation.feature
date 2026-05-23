Feature: Image Generation — Frame Rendering
  The image provider generates PNG frames from slide content.

  Scenario: Generate PNG with title and bullets
    Given an image provider is initialized
    When provider.generate("Title", ["bullet 1", "bullet 2"], output_png) is called
    Then a PNG file is written to output_png

  Scenario: Dimensions match config 1920x1080
    Given an image provider is initialized
    When provider.generate("Title", [], output_png, 1920, 1080) is called
    Then PIL.Image.open(output_png).size equals (1920, 1080)

  Scenario: Image failure raises ImageProviderError
    Given an image provider is initialized
    When the underlying image generation raises an exception
    Then ImageProviderError is raised with the original error as context

  Scenario: Output path parent created if missing
    Given an image provider is initialized
    When provider.generate("Title", [], Path("/tmp/subdir/test.png")) is called
    And the parent directory /tmp/subdir does not exist
    Then the directory is created automatically
    And the PNG file is written successfully

