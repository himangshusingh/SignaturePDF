# SignaturePDF

### A simple tool to sign pdf securely locally

-----

- To run the executable, download `.zip` file from releases and run the Signpdf.exe in it.
- Don't remove the `_internal` folder it contains the binary
- Best practice would be keep this folder somewhere and create a desktop shortcut to run it without tampering the `_internal_` folder.
- I am still working on building an installer which will take care of all the above process in the future. 



Steps to run code
1. Run `python install -r requirements.txt`
2. Run the `signpdf.py` file
3. Select the input pdf
4. Select the signature or the image you want on the pdf, the image should of the format `.jpg , .jpeg , .png`
5. Specify the output folder, the output filename by default is `input_file_name`_signed.pdf