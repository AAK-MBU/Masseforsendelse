"""
THIS IS A TEST SCRIPT
"""

import re

import sys

from pathlib import Path

from helper_scripts.file_handler import FileHandler

from mbu_dev_shared_components.getorganized.objects import CaseDataJson

from helper_scripts.case_handler import CaseHandler

from helper_scripts.document_handler import DocumentHandler

from helper_scripts import helper_functions


LINE_BREAK = "\n\n\n------------------------------------------------------------------------------------------------------------------\n\n\n"


class DatabaseError(Exception):
    """Custom exception for database related errors."""


class RequestError(Exception):
    """Custom exception for request related errors."""


def run_validation(
    file_handler: FileHandler,
    case_handler: CaseHandler,
    case_data_handler: CaseDataJson,
    document_handler: DocumentHandler,
    employee_list_filename: str,
    employee_list_sheet_name: str,
    case_type: str,
    case_title: str,
    files_to_journalize_path: str = "",
):
    """
    main func
    """

    employee_ssn_to_case_id_mapping = file_handler.load_or_create_csv_with_headers(filename="case_ids.csv", headers=["cpr", "case_id"])

    validation_csv = file_handler.load_or_create_csv_with_headers(filename="validation.csv", headers=["cpr", "error_message"])

    already_journalized_csv = file_handler.load_or_create_csv_with_headers(filename="journalized_docs.csv", headers=["CPR Nummer", "Journalized Doc ID"])
    already_journalized_mapping = helper_functions.build_already_journalized_mapping(csv_filepath=already_journalized_csv)

    # Build a mapping of CPR numbers to employee data from the Excel file
    cpr_dict_from_excel_file = file_handler.build_cpr_mapping(filename=employee_list_filename, sheet_name=employee_list_sheet_name)

    case_id_csv_to_dict = helper_functions.build_ssn_to_caseid_mapping(employee_ssn_to_case_id_mapping)

    # The cpr dictionary should look like this:
    """
    cpr_dicts = {
        "cpr_1": {
            "tjenestenummer": "12345",
            "navn": "Bob Testperson",
            "stilling": "Employee Type 1"
        },
        "cpr_2": {
            "tjenestenummer": "67890",
            "navn": "Helle Testperson",
            "stilling": "Employee Type 2"
        },
        ...
    }

    If the intended use is not to upload an Excel file, but instead to run it on a 1-by-1/case-by-case basis, you can just manually create the dictionary as above, and pass it to the cpr_dicts variable
    """

    print(f"Total CPR count:{len(cpr_dict_from_excel_file)}\n")

    all_journalized_docs = helper_functions.get_all_journalized_documents(
        document_handler=document_handler,
        journalized_filename="Meddelelse om løn 2025.07.01",
    )

    print(f"Total journalized documents found: {len(all_journalized_docs)}\n")

    print(all_journalized_docs[0])

    for doc in all_journalized_docs:
        doc_id = doc.get("DocId")

        case_id = doc.get("caseid")

























    # pdf_files = {}
    # folder = Path(files_to_journalize_path)
    # for f in folder.glob('*.pdf'):
    #     ssn = f.stem.split('_med_log')[0]
    #     pdf_files[ssn] = f  # store the Path object

    # # Iterate through each CPR number and its associated data in the dictionary
    # for i, (cpr, data) in enumerate(cpr_dict_from_excel_file.items()):
    #     # if i > 650:
    #     #     continue

    #     if cpr not in pdf_files:
    #         continue

    #     error_message = ""

    #     employee_folder_id = case_id_csv_to_dict[cpr].rsplit('-', 1)[0]
    #     salary_case_id = case_id_csv_to_dict[cpr]
    #     employment_code = data.get("tjenestenummer")
    #     employment_type = data.get("stilling")
    #     pdf_filename = pdf_files[cpr].name  # get just the filename

    #     employee_dictionary = {
    #         "cpr": cpr,
    #         "employee_folder_id": employee_folder_id,
    #         "salary_case_id": salary_case_id,
    #         "employment_code": employment_code,
    #         "employment_type": employment_type,
    #         "pdf_filename": pdf_filename,
    #     }

    #     print(employee_dictionary)

    #     is_already_journalized = helper_functions.look_for_already_journalized_file(
    #         document_handler=document_handler,
    #         employees_salary_case_id=employee_dictionary["salary_case_id"],
    #         filename_to_match="2025.03.28 Meddelelse om løn 2025.07.01"
    #     )

    #     if is_already_journalized:
    #         print("\nThis employee has a successfully journalized document\n")

    #     else:
    #         error_message = "This employee does NOT have a successfully journalized document !!!"

    #         print(f"\n{error_message}\n")

    #         mapping_entry = {cpr: error_message}

    #         file_handler.append_cpr_case_mapping_csv(mapping=[mapping_entry], output_filename="validation.csv")

    #     print(LINE_BREAK)

    #     continue

    return "Success"


def extract_digits(value: str) -> str:
    """
    test func
    """

    return ''.join(re.findall(r'\d+', value))
