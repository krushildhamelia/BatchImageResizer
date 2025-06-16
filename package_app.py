import os
import sys
import subprocess
import platform

def main():
    """
    Script to package the Batch Image Resizer application as a standalone executable
    using PyInstaller.
    """
    print("Packaging Batch Image Resizer as a standalone application...")

    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("PyInstaller is already installed.")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Determine the appropriate command based on the platform
    system = platform.system()
    if system == "Windows":
        print("Detected Windows platform.")
        cmd = ["pyinstaller", "--onefile", "--windowed", "--name", "BatchImageResizer", 
               "batch_image_resizer.py"]
    else:
        print(f"Detected {system} platform.")
        cmd = ["pyinstaller", "--onefile", "--windowed", "--name", "BatchImageResizer", 
               "batch_image_resizer.py"]
    
    # Run PyInstaller
    print("Running PyInstaller with the following command:")
    print(" ".join(cmd))
    subprocess.check_call(cmd)
    
    # Output information
    dist_dir = os.path.join(os.getcwd(), "dist")
    print("\nPackaging complete!")
    print(f"The standalone executable can be found in: {dist_dir}")
    
    if system == "Windows":
        exe_path = os.path.join(dist_dir, "BatchImageResizer.exe")
        print(f"Executable: {exe_path}")
    else:
        exe_path = os.path.join(dist_dir, "BatchImageResizer")
        print(f"Executable: {exe_path}")
    
    print("\nYou can distribute this executable to any compatible system.")
    print("Users won't need to install Python or any dependencies to run it.")

if __name__ == "__main__":
    main()