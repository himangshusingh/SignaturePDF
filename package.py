#!/usr/bin/env python3
"""
Build script for PDF Signature App
This script creates a spec file and builds the executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def create_spec_file():
    """Create optimized spec file for the PDF Signature App"""
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define the main script path
script_path = 'signpdf.py'  # Your main script file

a = Analysis(
    [script_path],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Tkinter and GUI
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.ttk',
        'tkinter.constants',
        'tkinter.font',
        
        # PDF processing
        'PyPDF2',
        'PyPDF2._merger',
        'PyPDF2._reader',
        'PyPDF2._writer',
        'PyPDF2.xmp',
        'PyPDF2.generic',
        'PyPDF2.utils',
        'PyPDF2.pdf',
        'PyPDF2.filters',
        
        # PyMuPDF
        'fitz',
        'fitz.fitz',
        'fitz.utils',
        
        # ReportLab
        'reportlab.pdfgen.canvas',
        'reportlab.lib.utils',
        'reportlab.lib.colors',
        'reportlab.lib.units',
        'reportlab.pdfbase',
        'reportlab.pdfbase.pdfmetrics',
        'reportlab.rl_config',
        
        # PIL/Pillow
        'PIL.Image',
        'PIL.ImageTk',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'PIL.ImageOps',
        'PIL._imaging',
        
        # Core Python modules needed
        'io',
        'pathlib',
        'os',
        'sys',
        'time',
        
        # XML modules (required by PyPDF2)
        'xml',
        'xml.etree',
        'xml.etree.ElementTree',
        'xml.etree.cElementTree',
        'xml.dom',
        'xml.dom.minidom',
        'xml.parsers',
        'xml.parsers.expat',
        
        # Email modules (required by urllib/reportlab)
        'email',
        'email.mime',
        'email.mime.base',
        'email.mime.text',
        'email.mime.multipart',
        'email.encoders',
        'email.utils',
        
        # HTTP/URL modules (required by reportlab)
        'http',
        'http.client',
        'urllib',
        'urllib.request',
        'urllib.parse',
        'urllib.error',
        
        # Other required modules
        'base64',
        'hashlib',
        'struct',
        'binascii',
        'zlib',
        'collections',
        'itertools',
        'functools',
        'operator',
        'weakref',
        'copy',
        'tempfile',
        'shutil'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude only truly unnecessary modules
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',
        'pytest',
        'setuptools',
        'wheel',
        'pip',
        'conda',
        'tornado',
        'zmq',
        'sqlite3',
        'requests',
        'django',
        'flask',
        'fastapi',
        'selenium',
        'opencv',
        'cv2',
        'pdf2image'  # Removed as it's no longer used
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SignaturePDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression for smaller size
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: icon='icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SignaturePDF'
)
'''
    
    # Write spec file
    with open('signaturepdf.spec', 'w') as f:
        f.write(spec_content)
    
    print("✓ Spec file 'signaturepdf.spec' created successfully")

def check_dependencies():
    """Check if required tools are installed"""
    print("Checking dependencies...")
    
    try:
        import PyInstaller
        print("✓ PyInstaller is installed")
    except ImportError:
        print("✗ PyInstaller not found. Installing...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        print("✓ PyInstaller installed")
    
    # Check if main script exists
    if not os.path.exists('signpdf.py'):
        print("✗ Main script 'signpdf.py' not found in current directory")
        return False
    else:
        print("✓ Main script 'signpdf.py' found")
    
    return True

def clean_previous_builds():
    """Clean previous build artifacts"""
    print("Cleaning previous builds...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Removed {dir_name}")
    
    # Clean spec files except the one we're about to create
    for spec_file in Path('.').glob('*.spec'):
        if spec_file.name != 'signaturepdf.spec':
            spec_file.unlink()
            print(f"✓ Removed {spec_file}")

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    
    try:
        # Run PyInstaller with the spec file
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', '--noconfirm', 'signaturepdf.spec']
        
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Build completed successfully!")
            print(f"Executable location: {os.path.abspath('dist/SignaturePDF')}")
            
            # Check if executable was created
            exe_path = Path('dist/SignaturePDF/SignaturePDF.exe')
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✓ Executable size: {size_mb:.2f} MB")
            
            return True
        else:
            print("✗ Build failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Build error: {e}")
        return False

def create_launcher_script():
    """Create a simple launcher script for easier testing"""
    launcher_content = '''@echo off
echo Starting PDF Signature Tool...
cd /d "%~dp0"
if exist "dist\\SignaturePDF\\SignaturePDF.exe" (
    start "" "dist\\SignaturePDF\\SignaturePDF.exe"
) else (
    echo Error: SignaturePDF.exe not found in dist\\SignaturePDF\\
    pause
)
'''
    
    with open('launch_app.bat', 'w') as f:
        f.write(launcher_content)
    
    print("✓ Launcher script 'launch_app.bat' created")

def main():
    """Main build process"""
    print("=== PDF Signature App Build Script ===")
    print()
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("✗ Dependency check failed. Please fix the issues and try again.")
        return
    
    print()
    
    # Step 2: Clean previous builds
    clean_previous_builds()
    print()
    
    # Step 3: Create spec file
    create_spec_file()
    print()
    
    # Step 4: Build executable
    success = build_executable()
    print()
    
    if success:
        # Step 5: Create launcher
        create_launcher_script()
        print()
        
        print("🎉 Build completed successfully!")
        print()
        print("Next steps:")
        print("1. Test the app by running: launch_app.bat")
        print("2. Or navigate to: dist/SignaturePDF/SignaturePDF.exe")
        print("3. The entire 'dist/SignaturePDF' folder can be distributed")
        print()
        print("Note: Make sure to include the entire 'SignaturePDF' folder")
        print("when distributing, as it contains all required dependencies.")
    else:
        print("❌ Build failed. Please check the error messages above.")

if __name__ == "__main__":
    main()