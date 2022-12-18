import _io
import io
import os
import sys

import PyPDF2
import pytesseract

import sqlite_manager

poppler_path = r'C:\Program Files\poppler-22.04.0-hea5ffa9_2\Library\bin'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def get_uid(file) -> int:
    return int(file)


def ocr_files(input_folder: str, output_folder: str, starting_index: int) -> None:
    print("Converting all files in " + input_folder + "...")

    '''
    Get all available files in the given directory
    and append them to the set object "all_files."
    '''
    all_files = []
    all_subdirectories = []
    for (path, dirs, files) in os.walk(input_folder):
        for file in files:
            path: str
            all_subdirectories.append(path.removeprefix(input_folder).replace("\\", ""))
            file = os.path.join(path, file)
            all_files.append(file)

    # Ensure that there is >1 file in the given input folder
    num_files = all_files.__len__()
    if num_files < 1:
        print(input_folder + " either has no files or doesn't exist.")
        print("Exiting program.")
        sys.exit()

    all_subdirectories.sort(key=get_uid)
    actual_starting_index = all_subdirectories.index(str(starting_index))

    '''
    Use PyTesseract to OCR (Optical Character Recognition)
    every file, and add it to the PDF Writer object.
    '''
    failed_files = 0

    for i in range(actual_starting_index + 1, len(all_files)):

        file = all_files[i]

        fixed_file_name = file[file.find("\\") + 1:file.find(".")]
        fixed_file_name.replace("\\", "/")

        uid = int(fixed_file_name[:4])

        if sqlite_manager.is_scanned(uid):
            print(f"({i}/{num_files}) Done.")
            continue

        subdir = f'{output_folder}/{uid}'
        if not os.path.isdir(subdir):
            os.mkdir(subdir)

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

            print(f"({i}/{num_files}) Skipping {file}; {str(e)}")
            failed_files += 1

        '''
        Open the PDF file for writing, truncating the file first and opening
        it in binary mode. Write the recognized page above to a new document.
        '''
        output_file = f'{output_folder}/{fixed_file_name}.pdf'

        page_to_write: _io.BufferedWriter
        with open(output_file, "wb") as page_to_write:
            pdf_writer.write(page_to_write)

        print(f"({i}/{num_files}) Successfully converted {file}")
        sqlite_manager.scan(uid)

    num_files = all_files.__len__()
    num_converted = num_files - failed_files

    print()
    print("Conversion complete!")
    print(f"Successfully converted {num_converted}/{num_files} input file(s) into (a) searchable pdf document(s).")
