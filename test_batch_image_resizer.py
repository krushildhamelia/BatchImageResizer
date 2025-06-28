import os
import unittest
import tempfile
import shutil
from unittest.mock import MagicMock, patch
import tkinter as tk
from PIL import Image
import io
import numpy as np
from batch_image_resizer import BatchImageResizer

class TestBatchImageResizer(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test."""
        # Create a mock root window
        self.root = MagicMock(spec=tk.Tk)

        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()

        # Create test images
        self.create_test_images()

        # Initialize the app with the mock root
        with patch('tkinter.ttk.LabelFrame'), \
             patch('tkinter.ttk.Frame'), \
             patch('tkinter.ttk.Label'), \
             patch('tkinter.StringVar'), \
             patch('tkinter.IntVar'), \
             patch('tkinter.BooleanVar'), \
             patch('tkinter.ttk.Entry'), \
             patch('tkinter.ttk.Button'), \
             patch('tkinter.ttk.Checkbutton'), \
             patch('tkinter.ttk.Scale'), \
             patch('tkinter.ttk.Progressbar'), \
             patch('tkinter.ttk.Combobox'):
            self.app = BatchImageResizer(self.root)

            # Mock the queue to avoid threading issues
            self.app.queue = MagicMock()

            # Set the folder path to our test directory
            self.app.folder_path.set = MagicMock()
            self.app.folder_path.get = MagicMock(return_value=self.test_dir)

    def tearDown(self):
        """Clean up after each test."""
        # Remove the temporary directory and its contents
        shutil.rmtree(self.test_dir)

    def create_test_images(self):
        """Create test images in the temporary directory."""
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='red')

        # Save in different formats
        img.save(os.path.join(self.test_dir, 'test.jpg'))
        img.save(os.path.join(self.test_dir, 'test.png'))

        # Create a subdirectory with an image
        os.makedirs(os.path.join(self.test_dir, 'subdir'), exist_ok=True)
        img.save(os.path.join(self.test_dir, 'subdir', 'subdir_test.jpg'))

    def test_initialization(self):
        """Test that the app initializes correctly."""
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.root, self.root)
        self.assertFalse(self.app.processing)
        self.assertListEqual(self.app.progress_bars, [])
        self.assertListEqual(self.app.progress_labels, [])
        self.assertIsNone(self.app.executor)
        self.assertListEqual(self.app.files_to_process, [])

    def test_supported_formats(self):
        """Test that the app has the correct supported formats."""
        expected_formats = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.webp', '.raw', '.cr2', '.cr3', '.nef', '.arw', '.dng']
        self.assertListEqual(self.app.supported_formats, expected_formats)

    @patch('tkinter.filedialog.askdirectory')
    def test_browse_folder(self, mock_askdirectory):
        """Test the browse_folder method."""
        # Setup mock
        mock_askdirectory.return_value = '/fake/path'

        # Call the method
        self.app.browse_folder()

        # Check that askdirectory was called
        mock_askdirectory.assert_called_once()

        # Check that the folder path was set
        self.app.folder_path.set.assert_called_once_with('/fake/path')

    @patch('tkinter.filedialog.askdirectory')
    def test_browse_output_folder(self, mock_askdirectory):
        """Test the browse_output_folder method."""
        # Setup mock
        mock_askdirectory.return_value = '/fake/output/path'

        # Call the method
        self.app.browse_output_folder()

        # Check that askdirectory was called
        mock_askdirectory.assert_called_once()

        # Check that the output path was set
        self.app.output_path.set.assert_called_once_with('/fake/output/path')

    def test_toggle_output_path_default(self):
        """Test toggle_output_path when using default output path."""
        # Setup
        self.app.use_default_output = MagicMock()
        self.app.use_default_output.get.return_value = True
        self.app.output_entry = MagicMock()
        self.app.output_browse_button = MagicMock()

        # Call the method
        self.app.toggle_output_path()

        # Check that the output entry was disabled
        self.app.output_entry.config.assert_called_once_with(state=tk.DISABLED)

        # Check that the output browse button was disabled
        self.app.output_browse_button.config.assert_called_once_with(state=tk.DISABLED)

    def test_toggle_output_path_custom(self):
        """Test toggle_output_path when using custom output path."""
        # Setup
        self.app.use_default_output = MagicMock()
        self.app.use_default_output.get.return_value = False
        self.app.output_entry = MagicMock()
        self.app.output_browse_button = MagicMock()

        # Call the method
        self.app.toggle_output_path()

        # Check that the output entry was enabled
        self.app.output_entry.config.assert_called_once_with(state=tk.NORMAL)

        # Check that the output browse button was enabled
        self.app.output_browse_button.config.assert_called_once_with(state=tk.NORMAL)

    @patch('os.path.isdir')
    def test_start_processing_invalid_folder(self, mock_isdir):
        """Test start_processing with an invalid folder."""
        # Setup mocks
        mock_isdir.return_value = False
        messagebox_mock = MagicMock()

        # Call the method with patched messagebox
        with patch('tkinter.messagebox.showerror', messagebox_mock):
            self.app.start_processing()

        # Check that error message was shown
        messagebox_mock.assert_called_once()

    @patch('os.path.isdir')
    def test_start_processing_invalid_mp(self, mock_isdir):
        """Test start_processing with an invalid megapixel value."""
        # Setup mocks
        mock_isdir.return_value = True
        self.app.mp_value.get = MagicMock(return_value="invalid")
        messagebox_mock = MagicMock()

        # Call the method with patched messagebox
        with patch('tkinter.messagebox.showerror', messagebox_mock):
            self.app.start_processing()

        # Check that error message was shown
        messagebox_mock.assert_called_once()

    @patch('threading.Thread')
    @patch('os.path.isdir')
    def test_start_processing_valid_inputs(self, mock_isdir, mock_thread):
        """Test start_processing with valid inputs."""
        # Setup mocks
        mock_isdir.return_value = True
        self.app.mp_value.get = MagicMock(return_value="12")
        self.app.quality_value.get = MagicMock(return_value=10)
        self.app.thread_count.get = MagicMock(return_value=4)
        self.app.start_button = MagicMock()
        self.app.cancel_button = MagicMock()
        self.app.progress_frame = MagicMock()
        self.app.progress_frame.winfo_children = MagicMock(return_value=[MagicMock()])

        # Call the method
        self.app.start_processing()

        # Check that the processing flag was set
        self.assertTrue(self.app.processing)

        # Check that the start button was disabled
        self.app.start_button.config.assert_called_with(state=tk.DISABLED)

        # Check that the cancel button was enabled
        self.app.cancel_button.config.assert_called_with(state=tk.NORMAL)

        # Check that a thread was started
        mock_thread.assert_called_once()

    def test_cancel_processing(self):
        """Test the cancel_processing method."""
        # Setup
        self.app.processing = True
        self.app.executor = MagicMock()
        self.app.status_var = MagicMock()
        self.app.start_button = MagicMock()
        self.app.cancel_button = MagicMock()

        # Call the method
        self.app.cancel_processing()

        # Check that processing was stopped
        self.assertFalse(self.app.processing)

        # Check that the executor was shutdown
        self.app.executor.shutdown.assert_called_once()

        # Check that the status was updated
        self.app.status_var.set.assert_called_once_with("Processing cancelled")

        # Check that the start button was enabled
        self.app.start_button.config.assert_called_with(state=tk.NORMAL)

        # Check that the cancel button was disabled
        self.app.cancel_button.config.assert_called_with(state=tk.DISABLED)

    @patch('os.walk')
    def test_process_images_no_files(self, mock_walk):
        """Test process_images when no files are found."""
        # Setup mocks
        mock_walk.return_value = [(self.test_dir, [], [])]
        self.app.process_subfolders.get = MagicMock(return_value=True)
        self.app.mp_value.get = MagicMock(return_value="12")
        self.app.quality_value.get = MagicMock(return_value=10)
        self.app.thread_count.get = MagicMock(return_value=4)
        self.app.start_button = MagicMock()
        self.app.cancel_button = MagicMock()
        self.app.status_var = MagicMock()

        # Call the method
        self.app.process_images()

        # Check that the queue was updated with the correct status
        self.app.queue.put.assert_called()

    @patch('PIL.Image.open')
    def test_resize_image(self, mock_image_open):
        """Test the resize_image method."""
        # Setup mocks
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_img.size = (2000, 2000)  # 4MP
        mock_resized_img = MagicMock()
        mock_img.resize.return_value = mock_resized_img
        mock_image_open.return_value.__enter__.return_value = mock_img

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.jpg'),
            os.path.join(self.test_dir, 'output.jpg'),
            1000000,  # 1MP (smaller than the 4MP image)
            10,
            0
        )

        # Check that the image was opened
        mock_image_open.assert_called_once()

        # Check that the image was resized (since 4MP > 1MP, resize is needed)
        # The scale factor would be sqrt(1000000/4000000) = 0.5
        # New dimensions would be 1000x1000
        mock_img.resize.assert_called_once_with((1000, 1000), Image.LANCZOS)

        # Check that the resized image was saved
        mock_resized_img.save.assert_called_once_with(
            os.path.join(self.test_dir, 'output.jpg'), 
            "JPEG", 
            quality=80
        )

        # Check that the result is True
        self.assertTrue(result)

    @patch('PIL.Image.open')
    def test_resize_image_smaller_than_target(self, mock_image_open):
        """Test resize_image when the image is smaller than the target size."""
        # Setup mocks
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_img.size = (500, 500)  # 0.25MP
        mock_image_open.return_value.__enter__.return_value = mock_img

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method with a larger target size
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.jpg'),
            os.path.join(self.test_dir, 'output.jpg'),
            1000000,  # 1MP (larger than the 0.25MP image)
            10,
            0
        )

        # Check that the image was opened
        mock_image_open.assert_called_once()

        # Check that the image was saved (original used since it's smaller than target)
        mock_img.save.assert_called_once_with(
            os.path.join(self.test_dir, 'output.jpg'), 
            "JPEG", 
            quality=80
        )

        # Check that the result is True
        self.assertTrue(result)

    @patch('PIL.Image.open')
    def test_resize_image_non_rgb(self, mock_image_open):
        """Test resize_image with a non-RGB image."""
        # Setup mocks
        mock_img = MagicMock()
        mock_img.mode = 'RGBA'  # Non-RGB mode
        mock_img.size = (1000, 1000)
        mock_converted_img = MagicMock()
        mock_converted_img.size = (1000, 1000)
        mock_img.convert.return_value = mock_converted_img
        mock_image_open.return_value.__enter__.return_value = mock_img

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.png'),
            os.path.join(self.test_dir, 'output.jpg'),
            2000000,
            10,
            0
        )

        # Check that the image was converted to RGB
        mock_img.convert.assert_called_once_with('RGB')

        # Check that the result is True
        self.assertTrue(result)

    @patch('PIL.Image.open')
    def test_resize_image_error(self, mock_image_open):
        """Test resize_image when an error occurs."""
        # Setup mock to raise an exception
        mock_image_open.side_effect = Exception("Test error")

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            self.app.resize_image(
                os.path.join(self.test_dir, 'nonexistent.jpg'),
                os.path.join(self.test_dir, 'output.jpg'),
                2000000,
                10,
                0
            )

    @patch('batch_image_resizer.RAWPY_AVAILABLE', True)
    @patch('rawpy.imread')
    def test_resize_raw_image(self, mock_imread):
        """Test the resize_image method with a RAW image."""
        # Setup mocks
        mock_raw = MagicMock()
        # Create a simple RGB array (3x3 pixels)
        rgb_array = np.zeros((100, 100, 3), dtype=np.uint8)
        rgb_array[:, :, 0] = 255  # Set red channel to max
        mock_raw.postprocess.return_value = rgb_array
        mock_imread.return_value.__enter__.return_value = mock_raw

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method with a RAW file
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.cr2'),
            os.path.join(self.test_dir, 'output.jpg'),
            2000000,  # 2MP
            10,
            0
        )

        # Check that rawpy.imread was called
        mock_imread.assert_called_once_with(os.path.join(self.test_dir, 'test.cr2'))

        # Check that postprocess was called
        mock_raw.postprocess.assert_called_once()

        # Check that the result is True
        self.assertTrue(result)

    @patch('batch_image_resizer.RAWPY_AVAILABLE', False)
    def test_resize_raw_image_no_rawpy(self):
        """Test the resize_image method with a RAW image when rawpy is not available."""
        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method with a RAW file and expect an ImportError
        with self.assertRaises(ImportError):
            self.app.resize_image(
                os.path.join(self.test_dir, 'test.cr2'),
                os.path.join(self.test_dir, 'output.jpg'),
                2000000,
                10,
                0
            )

    @patch('batch_image_resizer.RAWPY_AVAILABLE', True)
    @patch('rawpy.imread')
    @patch('PIL.Image.fromarray')
    def test_resize_raw_image_larger_than_target(self, mock_fromarray, mock_imread):
        """Test resize_raw_image when the image is larger than the target size."""
        # Setup mocks
        mock_raw = MagicMock()
        rgb_array = np.zeros((1000, 1000, 3), dtype=np.uint8)
        mock_raw.postprocess.return_value = rgb_array
        mock_imread.return_value.__enter__.return_value = mock_raw

        mock_img = MagicMock()
        mock_img.size = (1000, 1000)  # 1MP
        mock_fromarray.return_value = mock_img

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method with a target size smaller than the image
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.cr2'),
            os.path.join(self.test_dir, 'output.jpg'),
            500000,  # 0.5MP (smaller than the 1MP image)
            10,
            0
        )

        # Check that the image was resized
        mock_img.resize.assert_called_once()

        # Check that the result is True
        self.assertTrue(result)

    @patch('batch_image_resizer.RAWPY_AVAILABLE', True)
    @patch('rawpy.imread')
    @patch('PIL.Image.fromarray')
    def test_resize_raw_image_smaller_than_target(self, mock_fromarray, mock_imread):
        """Test resize_raw_image when the image is smaller than the target size."""
        # Setup mocks
        mock_raw = MagicMock()
        rgb_array = np.zeros((500, 500, 3), dtype=np.uint8)
        mock_raw.postprocess.return_value = rgb_array
        mock_imread.return_value.__enter__.return_value = mock_raw

        mock_img = MagicMock()
        mock_img.size = (500, 500)  # 0.25MP
        mock_fromarray.return_value = mock_img

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Call the method with a target size larger than the image
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.cr2'),
            os.path.join(self.test_dir, 'output.jpg'),
            1000000,  # 1MP (larger than the 0.25MP image)
            10,
            0
        )

        # Check that the image was not resized (original used)
        mock_img.resize.assert_not_called()

        # Check that the result is True
        self.assertTrue(result)

    def test_toggle_heic_options_available(self):
        """Test toggle_heic_options when pillow_heif is available."""
        # Setup
        with patch('batch_image_resizer.HEIF_AVAILABLE', True):
            # Create a new instance with HEIF_AVAILABLE = True
            with patch('tkinter.ttk.LabelFrame'), \
                 patch('tkinter.ttk.Frame'), \
                 patch('tkinter.ttk.Label'), \
                 patch('tkinter.StringVar'), \
                 patch('tkinter.IntVar'), \
                 patch('tkinter.BooleanVar'), \
                 patch('tkinter.ttk.Entry'), \
                 patch('tkinter.ttk.Button'), \
                 patch('tkinter.ttk.Checkbutton'), \
                 patch('tkinter.ttk.Scale'), \
                 patch('tkinter.ttk.Progressbar'), \
                 patch('tkinter.ttk.Combobox'):
                app = BatchImageResizer(self.root)

                # Mock the UI components
                app.heic_checkbox = MagicMock()
                app.heic_compression_frame = MagicMock()
                app.heic_compression_scale = MagicMock()
                app.heic_compression_label = MagicMock()
                app.export_heic = MagicMock()

                # Test with checkbox checked
                app.export_heic.get.return_value = True
                app.toggle_heic_options()

                # Check that compression options are shown
                app.heic_compression_frame.pack.assert_called_once()
                app.heic_compression_scale.config.assert_called_once_with(state=tk.NORMAL)
                app.heic_compression_label.config.assert_called_once_with(state=tk.NORMAL)

                # Reset mocks
                app.heic_compression_frame.reset_mock()
                app.heic_compression_scale.reset_mock()
                app.heic_compression_label.reset_mock()

                # Test with checkbox unchecked
                app.export_heic.get.return_value = False
                app.toggle_heic_options()

                # Check that compression options are hidden
                app.heic_compression_frame.pack_forget.assert_called_once()
                app.heic_compression_scale.config.assert_called_once_with(state=tk.DISABLED)
                app.heic_compression_label.config.assert_called_once_with(state=tk.DISABLED)

    def test_toggle_heic_options_unavailable(self):
        """Test toggle_heic_options when pillow_heif is not available."""
        # Setup
        with patch('batch_image_resizer.HEIF_AVAILABLE', False):
            # Create a new instance with HEIF_AVAILABLE = False
            with patch('tkinter.ttk.LabelFrame'), \
                 patch('tkinter.ttk.Frame'), \
                 patch('tkinter.ttk.Label'), \
                 patch('tkinter.StringVar'), \
                 patch('tkinter.IntVar'), \
                 patch('tkinter.BooleanVar'), \
                 patch('tkinter.ttk.Entry'), \
                 patch('tkinter.ttk.Button'), \
                 patch('tkinter.ttk.Checkbutton'), \
                 patch('tkinter.ttk.Scale'), \
                 patch('tkinter.ttk.Progressbar'), \
                 patch('tkinter.ttk.Combobox'):
                app = BatchImageResizer(self.root)

                # Mock the UI components
                app.heic_checkbox = MagicMock()
                app.heic_compression_frame = MagicMock()
                app.heic_compression_scale = MagicMock()
                app.heic_compression_label = MagicMock()
                app.export_heic = MagicMock()

                # Test with checkbox checked (should still hide options since HEIF is unavailable)
                app.export_heic.get.return_value = True
                app.toggle_heic_options()

                # Check that compression options are hidden
                app.heic_compression_frame.pack_forget.assert_called_once()
                app.heic_compression_scale.config.assert_called_once_with(state=tk.DISABLED)
                app.heic_compression_label.config.assert_called_once_with(state=tk.DISABLED)

    @patch('batch_image_resizer.HEIF_AVAILABLE', True)
    @patch('PIL.Image.open')
    @patch('pillow_heif.from_pillow')
    def test_resize_image_heic_export(self, mock_from_pillow, mock_image_open):
        """Test the resize_image method with HEIC export."""
        # Setup mocks
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_img.size = (2000, 2000)  # 4MP
        mock_resized_img = MagicMock()
        mock_img.resize.return_value = mock_resized_img
        mock_image_open.return_value.__enter__.return_value = mock_img

        mock_heif_file = MagicMock()
        mock_from_pillow.return_value = mock_heif_file

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]
        self.app.export_heic = MagicMock(return_value=True)
        self.app.heic_compression_value = MagicMock(return_value=7)

        # Call the method with HEIC output
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.jpg'),
            os.path.join(self.test_dir, 'output.heic'),
            1000000,  # 1MP (smaller than the 4MP image)
            10,
            0
        )

        # Check that the image was opened
        mock_image_open.assert_called_once()

        # Check that the image was resized
        mock_img.resize.assert_called_once_with((1000, 1000), Image.LANCZOS)

        # Check that the image was converted to HEIC
        mock_from_pillow.assert_called_once_with(mock_resized_img)

        # Check that the HEIC file was saved with the correct compression
        mock_heif_file.save.assert_called_once()

        # Check that the result is True
        self.assertTrue(result)

    @patch('batch_image_resizer.HEIF_AVAILABLE', False)
    @patch('PIL.Image.open')
    def test_resize_image_heic_unavailable(self, mock_image_open):
        """Test the resize_image method with HEIC export when pillow_heif is not available."""
        # Setup mocks
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_img.size = (2000, 2000)  # 4MP
        mock_resized_img = MagicMock()
        mock_img.resize.return_value = mock_resized_img
        mock_image_open.return_value.__enter__.return_value = mock_img

        self.app.progress_labels = [MagicMock()]
        self.app.progress_bars = [MagicMock()]

        # Even though we request HEIC output, it should fall back to JPEG
        result = self.app.resize_image(
            os.path.join(self.test_dir, 'test.jpg'),
            os.path.join(self.test_dir, 'output.heic'),  # Request HEIC output
            1000000,  # 1MP
            10,
            0
        )

        # Check that the image was saved as JPEG instead
        mock_resized_img.save.assert_called_once()
        args, kwargs = mock_resized_img.save.call_args
        self.assertEqual(kwargs.get('format', 'JPEG'), 'JPEG')

        # Check that the result is True
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()
