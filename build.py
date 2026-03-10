# build.py
import PyInstaller.__main__
import os
import shutil
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from config import APP_NAME

def update_installer_iss():
    iss_path = 'installer.iss'
    if not os.path.exists(iss_path):
        return
        
    with open(iss_path, 'r') as f:
        content = f.read()
        
    import re
    content = re.sub(r'#define MyAppName ".*"', f'#define MyAppName "{APP_NAME}"', content)
    content = re.sub(r'#define MyAppExeName ".*"', f'#define MyAppExeName "{APP_NAME}.exe"', content)
    content = re.sub(r'OutputBaseFilename=.*', f'OutputBaseFilename={APP_NAME}_Installer', content)
    
    with open(iss_path, 'w') as f:
        f.write(content)

def build_app():
    if os.path.exists('build'): shutil.rmtree('build')
    if os.path.exists('dist'): shutil.rmtree('dist')

    print(f"Building {APP_NAME} as a portable folder...")
    
    update_installer_iss()
    print("Updated installer.iss with new application name...")

    PyInstaller.__main__.run([
        'src/main.py',
        f'--name={APP_NAME}',
        '--noconsole',
        '--onedir',
        '--paths=src',
        '--icon=assets/icon.ico',
        '--add-data=assets;assets',
        '--runtime-hook=windows_taskbar_hook.py',
        '--clean'
    ])
    
    print("\n\nBuild Complete!")
    print("Now run installer.iss to package the application or run .exe file from the location mentioned below")
    print(f"Location: dist/{APP_NAME}")

if __name__ == "__main__":
    build_app()
