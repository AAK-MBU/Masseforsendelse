"""
THIS IS A TEST SCRIPT
"""

import csv

from io import BytesIO

from pathlib import Path

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from handle_journalization import journalize_process as jp

from helper_scripts import helper_functions

from helper_scripts.file_handler import FileHandler
from helper_scripts.document_handler import DocumentHandler

LINE_BREAK = "\n\n\n-------------------------------------------------------------------------------------------------------------------------\n\n\n"


def handle_journalization(
    orchestrator_connection: OrchestratorConnection,
    file_handler: FileHandler,
    document_handler: DocumentHandler,
    masseforsendelse_folder_path: str = "",
    files_to_journalize_path: str = "",
    journalized_filename: str = "",
    document_category: str = "",
) -> None:

    """
    main function for the script
    """

    cpr_mapping = file_handler.get_cpr_csv_mapping("case_ids.csv")

    csv_with_already_journalized, csv_path = helper_functions.load_or_create_journal_log(f"{masseforsendelse_folder_path}journalized_docs.csv")

    pdf_files = {}
    folder = Path(files_to_journalize_path)
    for f in folder.glob('*.pdf'):
        ssn = f.stem.split('_med_log')[0]
        pdf_files[ssn] = f.read_bytes()

    for i, (key, value) in enumerate(cpr_mapping.items()):
        ssn = key
        employees_salary_case_id = value

        print(f"ssn: {ssn} - case_id for employees salary_case_folder: {employees_salary_case_id}\n")

        is_already_journalized = False

        if value == "SPECIAL CASE - CHECK CPRS_TO_IGNORE":
            print("skipping special case !!!")

        elif key not in pdf_files:
            print(f"{key} not in pdf_files - skipping !!!")

        elif ssn in csv_with_already_journalized:
            print(f"skipping {ssn} - already journalized")

        else:
            is_already_journalized = helper_functions.look_for_already_journalized_file(
                document_handler=document_handler,
                employees_salary_case_id=employees_salary_case_id,
                filename_to_match=journalized_filename
            )

            print(f"is_already_journalized: {is_already_journalized}")

            if is_already_journalized:
                print(f"skipping {ssn} after check - already journalized")

            else:
                print("Employee does not have existing journalized file - running upload and journalization process")

                # upload = False
                upload = True

                if upload:
                    salary_document_to_journalize_as_byte_stream = BytesIO(pdf_files.get(ssn))

                    filename_with_extension = f"{journalized_filename}.pdf"
                    filename_without_extension = journalized_filename

                    print(f"filename_with_extension: {filename_with_extension}")
                    print(f"filename_without_extension: {filename_without_extension}\n")

                    journalized_file_doc_id, status_message = jp.journalize_file(
                        document_category=document_category,
                        document_handler=document_handler,
                        case_id=employees_salary_case_id,
                        filename_with_extension=filename_with_extension,
                        filename_without_extension=filename_without_extension,
                        salary_document_to_journalize_as_byte_stream=salary_document_to_journalize_as_byte_stream,
                        orchestrator_connection=orchestrator_connection
                    )

                    if status_message != "Success":
                        print("An error occurred")

                        break

                    print(f"\nFinal journalized file doc id: {journalized_file_doc_id}")

                    with open(csv_path, mode="a", newline="", encoding="utf-8") as log_f:
                        writer = csv.writer(log_f)

                        # write a new row: [CPR, DocID]
                        writer.writerow([ssn, journalized_file_doc_id])

        print(LINE_BREAK)

    return "Process done!"
