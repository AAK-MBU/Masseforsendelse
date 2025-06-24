import re
import io
import os

import argparse

from pypdf import PdfReader, PdfWriter, PageObject
from tqdm import tqdm
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def main(root_path, add_log=1):
    """Main function to split PDF"""
    add_log = add_log == 1

    print(f"path is set to {root_path}")

    collected_pdf_path = os.path.join(
        root_path, "breve samlet.pdf"
    )
    if add_log:
        list_path = os.path.join(
            root_path, "log samlet.xlsx"
        )
        df = pd.read_excel(list_path, "Ark1")  # Fix path to input df

    print("Opening files...")
    output_directory = os.path.join(root_path, "udsendte_dokumenter")
    os.makedirs(output_directory, exist_ok=True)
    pdf_reader = PdfReader(collected_pdf_path)
    pdf_writer = PdfWriter()

    error_list = []
    double_tjnr = []

    # Step 3: Iterate through each page in the collected PDF
    pages = pdf_reader.pages
    print("Handling pdf pages...")
    for page in tqdm(pages):
        text = page.extract_text()

        tj_nr = extract_match(text, r"Tj.nr.:?\s*(\d+)")
        tj_nr = str(int(tj_nr))
        if add_log:
            df['Tjenestenummer'] = df['Tjenestenummer'].astype(str).str.replace(".0", "")
            df['Tidspunkt'] = pd.to_datetime(df['Tidspunkt'])
            if (
                (tj_nr) and (tj_nr in df['Tjenestenummer'].values)
            ):

                row = df[df['Tjenestenummer'].astype(str) == tj_nr].iloc[0]
                ssn = row['CPR']

                if row['Antal'] > 1:
                    # print(f"{row["Modtager Digital Post"]} har flere tjenestenumre")
                    double_tjnr.append(ssn)

                # Create the info box PDF
                box_pdf = create_info_box(row)

                # Add the box to the PDF page
                modified_page = add_box_to_page(page, box_pdf)

                # Save the modified page as a separate PDF
                modified_pdf_path = os.path.join(output_directory, f'{ssn.replace("-", "")}_med_log.pdf')
                pdf_writer = PdfWriter()
                pdf_writer.add_page(modified_page)
                with open(modified_pdf_path, 'wb') as output_pdf_file:
                    pdf_writer.write(output_pdf_file)
            elif tj_nr not in df["Tjenestenummer"].astype(str).values:
                error_list.append(tj_nr)
                # print(f"Tjenestenummer {tj_nr} ikke fundet i listen")

    if add_log:
        with open(os.path.join(
            output_directory, "error_list.txt"
        ), "w", encoding="utf-8") as f:
            f.write("\n".join([str(i) for i in error_list]))
        with open(os.path.join(
            output_directory, "double_tjnr.txt"
        ), "w", encoding="utf-8") as f:
            f.write("\n".join([str(i) for i in double_tjnr]))

        print(f"Errors: {len(error_list)}")
        print(f"Double tj.nr: {len(double_tjnr)}")


def extract_match(text: str, search: str):
    """Function to extract"""
    match = re.search(search, text)
    if match:
        return match.group(1)
    return None


# Function to create a box with information and return as a PDF
def create_info_box(row):
    """Function to create info box in pdfs"""
    # Setup canvas
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont("Helvetica-Bold", 10)  # Set font size to 8
    left, lo, space = 70, 70, 15

    # Print text to box
    can.drawString(left, (lo + space * 5), "Digital Post afsendelses information")
    can.setFont("Helvetica", 8)  # Set font size to 8
    deliver_text = (
        f"Leveret: {row['Tidspunkt'].strftime("%Y-%m-%d %T")}"
        if row["Status fra Digital Post"] == "AVAILABLE_TO_RECIPIENT"
        else f"Afsendelse ikke leveret. Sidste log: {row['Tidspunkt'].strftime("%Y-%m-%d %T")}"
    )
    can.drawString(left, (lo + space * 4), deliver_text)
    can.drawString(left, (lo + space * 3), f"UUID Digital Post: {row['Digital Post ID']}")
    can.drawString(left, (lo + space * 2), f"Status Digital Post: {row['Status fra Digital Post']}")
    can.drawString(left, (lo + space * 1), f"JobID OneTooX: {row['Job ID']}")
    can.drawString(left, (lo + space * 0), f"Status OneTooX: {row['OneTooX Status']}")

    # Draw the box around the text
    can.rect(left - 10, lo - 10, 300, 6 * space + 10)  # (x, y, width, height)

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def add_box_to_page(page: PageObject, box_pdf):
    """Function to add the box to the pdfs"""
    page.merge_page(box_pdf.pages[0])
    return page


if __name__ == '__main__':
    os.system('cls')
    parser = argparse.ArgumentParser(description='Set path and whether to add log.')
    parser.add_argument('-p', '--Path', required=True, help='Path with collected pdf and (optional) log file.')
    parser.add_argument('--add-log', required=True, type=int, help='Whether to add info box with Digital Post log (0=No, 1=Yes). Requires log file to be prepared.')
    args = parser.parse_args()
    main(root_path=args.Path, add_log=args.add_log)
