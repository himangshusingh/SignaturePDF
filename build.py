# build.py
import PyInstaller.__main__
import os
import shutil

def build_app():
    if os.path.exists('build'): shutil.rmtree('build')
    if os.path.exists('dist'): shutil.rmtree('dist')

    print("Building SignaturePDF as a portable folder...")

    PyInstaller.__main__.run([
        'src/main.py',
        '--name=SignaturePDF',
        '--noconsole',
        '--onedir',
        '--paths=src',
        '--icon=assets/icon.ico',
        '--add-data=assets/icon.ico;assets',
        '--runtime-hook=windows_taskbar_hook.py',
        '--clean'
    ])
    
    print("\n\nBuild Complete!")
    print("Now run installer.iss to package the application or run .exe file from the location mentioned below")
    print("Location: dist/SignaturePDF")

if __name__ == "__main__":
    build_app()
