# Convert all files in jpg type files and copy in a new folder
import os
from pathlib import Path
# from typing import re

import base45
import zlib
import flynn

import fitz as fitz
from PIL import Image
from pyzbar import pyzbar
import shutil


def preprocess_files(in_dir, out_dir):
    # make the output jpgs folder if it does not already exists
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    list_filename = []  # save file names in a list for later use

    # iterate through each file in the folder
    for file in os.listdir(in_dir):

        # remove default extension at the end of filename
        list_filename.append(file.rsplit('.', 1)[0])
        if file.lower().endswith(".png") or file.lower().endswith("jpeg"):
            im1 = Image.open(os.path.join(in_dir, file))
            if im1.mode in ("RGBA", "P"):
                im1 = im1.convert("RGB")

            # remove default extension at the end of filename and add '.jpg' at the end
            file = file.rsplit('.', 1)[0] + '.jpg'
            im1.save(os.path.join(out_dir, file))

        elif file.lower().endswith(".pdf"):
            pdffile = os.path.join(in_dir, file)
            doc = fitz.open(pdffile)
            page = doc.load_page(0)  # number of page
            pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72))

            # remove default extension at the end of filename and add '.jpg' at the end
            file = file.rsplit('.', 1)[0] + '.jpg'
            pix.save(os.path.join(out_dir, file))

        # if it is already a JPG, make a copy and save it in the jpgs folder
        elif file.lower().endswith(".jpg"):
            im1 = Image.open(os.path.join(in_dir, file))
            im1.save(os.path.join(out_dir, file))

    return list_filename


def processing(out_dir, file_list):
    # List of Dictionaries Containing Data of Each image file as key
    samples = []

    # To get response from the API
    response_object = None
    for file in file_list:
        img_src = "{}/{}.jpg".format(out_dir, file)

        # Api Call

        qr_pil = Image.open(img_src)
        data = ''
        for index in range(0, len(pyzbar.decode(qr_pil))):  # pdf has 2 bar codes. Only one of them is correct.
            qr_data_zlib_b45 = pyzbar.decode(qr_pil)[index].data
            if "b'HC1" in str(qr_data_zlib_b45):
                qr_data_zlib = base45.b45decode(qr_data_zlib_b45[4:])
                qr_data = zlib.decompress(qr_data_zlib)
                (_, (headers1, headers2, cbor_data, signature)) = flynn.decoder.loads(qr_data)
                data = flynn.decoder.loads(cbor_data)

                name = data[-260][1]["nam"]["gn"]
                familyName = data[-260][1]["nam"]["fn"]
                numberOfDoses = data[-260][1]["v"][0]["dn"]
                manufacturerNumber = data[-260][1]["v"][0]["ma"]
                manufacturerName = manufacturer_code(manufacturerNumber)

                sample_data = {
                    "name": name,
                    "familyName": familyName,
                    "numberOfDoses": numberOfDoses,
                    "manufacturerName": manufacturerName,
                }
                samples.append(sample_data)

    return samples


def manufacturer_code(argument):
    switcher = {
        "ORG-100001699": "AstraZeneca",
        "ORG-100030215": "Phizer/Biontech Manufacturing",
        "ORG-100001417": "Janssen-Cilag International",
        "ORG-100031184": "Moderna Biotech Spain",
        "ORG-100006270": "Curevac",
        "ORG-100013793": "CanSino",
        "ORG-100020693": "China Sinopharm International",
        "ORG-100010771": "Sinopharm Weiqida Europe Pharmaceutical",
        "ORG-100024420": "Sinopharm Zhijun (Shenzhen) Pharmaceutical",
        "ORG-100032020": "Novavax",
        "ORG-100001981": "Serum Institute Of India Private Limited",
        "Gamaleya-Research-Institute": "Gamaleya-Research-Institute",
        "Sinovac-Biotech": "Sinovac-Biotech",
        "Vector-Institute": "Vector-Institute",
        "Fiocruz": "Fiocruz",
        "ORG-100007893": "R-Pharm",
        "ChumakovFederalScientific-Center": "Chumakov Federal Scientific Center",
        "Bharat-Biotech": "Bharat-Biotech",
        "ORG-100023050": "Gulf Pharmaceutical Industries"
    }

    # get() method of dictionary data type returns
    # value of passed argument if it is present
    # in dictionary otherwise second argument will
    # be assigned as default value of passed argument
    return switcher.get(argument, "unknown vaccine company")


def delete_folder(dir):
    shutil.rmtree(dir)


def execute_script(output_name):
    # in_dir = "/home/kai/git/fwaa/media"
    import os.path
    from pathlib import Path

    # Build paths inside the project like this: BASE_DIR / 'subdir'.
    BASE_DIR = Path(__file__).resolve().parent.parent
    BASE_DIR = os.path.join(BASE_DIR, 'media')

    in_dir = os.path.join(BASE_DIR)
    base_dir = Path(in_dir)
    base_dir = base_dir.parent.absolute()

    print("-----Initiating Script-----")
    out_dir = "{}/temp".format(base_dir)

    file_list = preprocess_files(in_dir=in_dir, out_dir=out_dir)

    samples = processing(out_dir=out_dir, file_list=file_list)

    from upload_process.sheet_writer import writer
    try:
        sheet = writer(output_name)
    except:
        return "Sheet Not Found"

    for sample in samples:
        sheet.insert_row(list(sample.values()), 2)

    delete_folder(out_dir)
    delete_folder(in_dir)

    print(samples)

    return None
