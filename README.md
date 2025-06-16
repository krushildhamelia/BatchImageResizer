# Batch Image Resizer

A Python application with a graphical user interface for batch resizing images to specific megapixel sizes while maintaining aspect ratio.

## Features

- User-friendly GUI for selecting folders containing images
- Option to process subfolders
- Support for various image formats (JPG, PNG, RAW, GIF, WEBP, etc.)
- Customizable export settings:
  - Megapixel size (2MP to 64MP)
  - Image quality (1-12)
- Parallel processing with multiple threads
- Progress tracking for each thread
- Load balancing to optimize processing
- Exports all images as JPG format
- Maintains aspect ratio during resizing

## Requirements

- Python 3.6+
- Required libraries:
  - Pillow (PIL Fork) for image processing
  - rawpy for processing RAW image files
  - tkinter for GUI
  - concurrent.futures for parallel processing

## Installation

### Using as a Python Script

1. Clone this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application:
   ```
   python batch_image_resizer.py
   ```

### Standalone Application

Pre-built standalone executables are available for Windows and Linux in the releases section.

## How to Use

1. Launch the application
2. Select the source folder containing images
3. Choose whether to include subfolders
4. Set the desired megapixel size for the output images
5. Adjust the quality setting (higher values = better quality but larger file size)
6. Set the number of parallel processing threads (default: 4)
7. Click "Start Processing" to begin
8. Monitor progress in the application window
9. Processed images will be saved in an "output" subfolder within the source directory

## Running Tests

Before building or making changes to the application, it's recommended to run the tests to ensure everything is working correctly:

1. Make sure you have installed all dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the tests using the provided script:
   ```
   python run_tests.py
   ```

3. Verify that all tests pass. The output should show the test results with details about each test case.

The test suite covers:
- UI components and interactions
- Image processing functionality for both standard and RAW images
- Error handling and edge cases
- Output directory functionality

## Building from Source

To create a standalone executable:

1. Run the tests to ensure everything is working correctly (see "Running Tests" section above)

2. Install PyInstaller:
   ```
   pip install pyinstaller
   ```

3. Build the executable:
   ```
   pyinstaller --onefile --windowed batch_image_resizer.py
   ```

Alternatively, you can use the provided package_app.py script:
   ```
   python package_app.py
   ```

## License

MIT License
