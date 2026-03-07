# build.py
import PyInstaller.__main__
import os
import shutil

def build_app():
    # Clean previous builds
    if os.path.exists('build'): shutil.rmtree('build')
    if os.path.exists('dist'): shutil.rmtree('dist')

    print("Building SignaturePDF as a portable folder...")

    PyInstaller.__main__.run([
        'src/main.py',
        '--name=SignaturePDF',
        '--noconsole',  # Don't show terminal window
        '--onedir',     # Create a folder instead of a slow one-file exe
        '--clean'
    ])
    
    print("\n\nBuild Complete!")
    print("Your application is ready to be zipped and distributed.")
    print("Location: dist/SignaturePDF")

if __name__ == "__main__":
    build_app()
