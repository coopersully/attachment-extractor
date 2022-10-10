import io
import os
import sys

import PyPDF2
import pytesseract

poppler_path = r'C:\Program Files\poppler-22.04.0-hea5ffa9_2\Library\bin'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

if __name__ == '__main__':

    input_folder = "raw"
    output_folder = "scanned"

    print()
    print("Converting all files in " + input_folder + "...")

    '''
    Get all available files in the given directory
    and append them to the set object "all_files."
    '''
    all_files = []
    for (path, dirs, files) in os.walk(input_folder):
        for file in files:
            file = os.path.join(path, file)
            all_files.append(file)

    # Ensure that there is >1 file in the given input folder
    num_files = all_files.__len__()
    if num_files < 1:
        print(input_folder + " either has no files or doesn't exist.")
        print("Exiting program.")
        sys.exit()

    '''
    Use PyTesseract to OCR (Optical Character Recognition)
    every file, and add it to the PDF Writer object.
    '''
    failed_files = 0
    i = 0
    for file in all_files:

        fixed_file_name = file[file.find("\\") + 1:file.find(".")]

        i += 1
        pdf_writer = PyPDF2.PdfFileWriter()
        try:
            page = pytesseract.image_to_pdf_or_hocr(file, extension='pdf')
            pdf = PyPDF2.PdfFileReader(io.BytesIO(page))
            pdf_writer.addPage(pdf.getPage(0))
        except Exception as e:

            '''
            If this is the first failed file, print a newline
            char for better formatting in the terminal window.
            '''
            if failed_files == 0:
                print()

            print(f"({ i }/{ num_files }) Skipping { file }; { str(e) }")
            failed_files += 1

        '''
        Open the PDF file for writing, truncating the file first and opening
        it in binary mode. Write the recognized page above to a new document.
        '''
        output_file = output_folder + "/" + fixed_file_name + ".pdf"
        with open(output_file, "wb") as page_to_write:
            pdf_writer.write(page_to_write)

        print(f"({ i }/{ num_files }) Successfully converted { file }")

    num_files = all_files.__len__()
    num_converted = num_files - failed_files

    print()
    print("Conversion complete!")
    print(f"Successfully converted { num_converted }/{ num_files } input file(s) into (a) searchable pdf document(s).")
