import os
import sys
import shutil
import subprocess
from pathlib import Path

# Configuration
APP_NAME = "SignaturePDFTool"
MAIN_SCRIPT = "main.py"  # Your main Python file
POPPLER_PATH = r"C:\poppler-24.08.0\Library\bin"  # Adjust to your Poppler path
ICON_PATH = None  # Set to your .ico file path if you have one

def check_requirements():
    """Check if all required tools and files are available"""
    print("Checking requirements...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("✓ PyInstaller installed")
    
    # Check if main script exists
    if not os.path.exists(MAIN_SCRIPT):
        print(f"✗ Main script '{MAIN_SCRIPT}' not found")
        return False
    print(f"✓ Main script found: {MAIN_SCRIPT}")
    
    # Check if Poppler exists
    if not os.path.exists(POPPLER_PATH):
        print(f"✗ Poppler path not found: {POPPLER_PATH}")
        print("Please update POPPLER_PATH in this script to point to your Poppler installation")
        return False
    print(f"✓ Poppler found: {POPPLER_PATH}")
    
    return True

def create_spec_file():
    """Create PyInstaller spec file with custom configuration"""
    
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Data files to include
added_files = [
    (r'C:\\poppler-24.08.0\\Library\\bin', 'poppler/bin'),
]

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'PyPDF2',
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'pdf2image',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib.utils',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_PATH if ICON_PATH else ""}',
    onefile=True,  # Enable single-file executable
)
'''
    
    with open(f"{APP_NAME}.spec", "w") as f:
        f.write(spec_content)
    
    print(f"✓ Created spec file: {APP_NAME}.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # Build using spec file
    cmd = [sys.executable, "-m", "PyInstaller", f"{APP_NAME}.spec"]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Build successful!")
        
        # Check if executable was created
        exe_path = os.path.join("dist", f"{APP_NAME}.exe")
        if os.path.exists(exe_path):
            print(f"✓ Executable created: {exe_path}")
            print(f"✓ Executable size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
            return True
        else:
            print("✗ Executable not found in dist folder")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def create_distribution():
    """Create a clean distribution folder"""
    print("Creating distribution...")
    
    dist_folder = f"{APP_NAME}_Distribution"
    if os.path.exists(dist_folder):
        shutil.rmtree(dist_folder)
    
    os.makedirs(dist_folder)
    
    # Copy executable
    exe_source = os.path.join("dist", f"{APP_NAME}.exe")
    exe_dest = os.path.join(dist_folder, f"{APP_NAME}.exe")
    shutil.copy2(exe_source, exe_dest)
    
    # Create README
    readme_content = f"""# {APP_NAME}

## About
Signature PDF Tool - A standalone application for adding signatures to PDF documents.

## Usage
1. Double-click {APP_NAME}.exe to run the application
2. Browse and select your PDF file
3. Browse and select your signature image (PNG, JPG, JPEG)
4. Select the page where you want to add the signature
5. Drag and drop the signature on the preview to position it
6. Resize the signature by dragging the corners
7. Adjust the scale using the slider if needed
8. Click "Save PDF" to create the signed document

## Features
- Drag and drop signature positioning
- Resize signatures by dragging corners
- Scale adjustment slider
- Preview of PDF pages
- Support for multiple image formats
- Transparent signature support

## System Requirements
- Windows 7 or later (64-bit)
- No additional software installation required

## Notes
- The application is completely standalone and portable
- All dependencies including Poppler are bundled
- No internet connection required
- Created with PyInstaller

## Version Information
- Built on: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Python version: {sys.version}
"""
    
    with open(os.path.join(dist_folder, "README.txt"), "w") as f:
        f.write(readme_content)
    
    print(f"✓ Distribution created: {dist_folder}")
    return dist_folder

def main():
    """Main build process"""
    print(f"Building {APP_NAME} executable...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n✗ Requirements check failed. Please fix the issues above.")
        return False
    
    print("\n" + "=" * 50)
    
    # Create spec file
    create_spec_file()
    
    print("\n" + "=" * 50)
    
    # Build executable
    if not build_executable():
        print("\n✗ Build process failed.")
        return False
    
    print("\n" + "=" * 50)
    
    # Create distribution
    dist_folder = create_distribution()
    
    print("\n" + "=" * 50)
    print("BUILD COMPLETE!")
    print(f"✓ Your executable is ready in: {dist_folder}")
    print(f"✓ Main executable: {dist_folder}/{APP_NAME}.exe")
    print("\nYou can now copy this folder to any Windows machine and run the executable.")
    
    return True

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)