## SignaturePDF
A Python application for adding signatures to PDF documents using a graphical interface with drag-and-drop functionality.
Features

Load a PDF and preview its pages.
Add a signature image to specific pages with adjustable position and scale.
Save signature positions for multiple pages.
Process single pages or all pages with saved positions.
Drag-and-drop signature placement with resizing capabilities.

## Requirements

Python 3.6+
Dependencies listed in requirements.txt

## Installation

1. Clone the repository
2. `cd SignaturePDF` 


Create a virtual environment and activate it:
```
python -m venv .venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate.ps1
```

Install dependencies:`pip install -r requirements.txt`


## Usage

Run the application: `python src/main.py`

## Installer

1. Download the latest `.exe` installer from [here](https://github.com/himangshusingh/SignaturePDF/releases) 
2. Run the installer: `SignaturePDF_Installer.exe` 

#### Follow the GUI instructions:
- Select a PDF file, signature image, and output folder.
- Choose a page, position the signature, and save the position.
- Repeat for other pages if needed.
- Click "Save Single Page" or "Save All Positioned" to generate the output PDF.


`requirements.txt`: Lists dependencies.

Notes

- Ensure the signature image is in PNG or JPEG format with a transparent background for best results.
- Page numbers are 0-indexed in the application.
- The output PDF will be saved in the specified folder with a default filename based on the input PDF.

---
