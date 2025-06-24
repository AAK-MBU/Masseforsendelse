""" the main function to run both the fetch and journalization processes """
import os
import sys
import json

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from mbu_dev_shared_components.getorganized.objects import CaseDataJson

from helper_scripts import helper_functions

from helper_scripts.file_handler import FileHandler

from helper_scripts.case_handler import CaseHandler

from helper_scripts.document_handler import DocumentHandler

from identify_employee_folders.main import identify_employee_folders

from handle_journalization.main import handle_journalization

LINE_BREAK = "\n\n\n------------------------------------------------------------------------------------------------------------------\n\n\n"

REQUIRED_VARIABLES = {
    "MASSEFORSENDELSE_FOLDER_PATH": "",  # This is the folder where you would have the Excel sheet of affected employees, and a subfolder with the files to be journalized
    "EMPLOYEE_LIST_FILENAME": "",  # This is the filename, for the Excel sheet with the list of affected employees
    "EMPLOYEE_LIST_SHEET_NAME": "",  # This is the name of the sheet in the Excel file with the list of affected employees
    "FILES_TO_JOURNALIZE_PATH": "",  # These are the (usually) PDF files that have been sent to the employees' digital post, and now need to be journalized
    "FINAL_JOURNALIZED_FILENAME": "",  # This is the desired filename of the journalized file, as in what the final document should be called in the system
    "DOCUMENT_CATEGORY": "",  # This is the document category, as in what type of document it is. This is usually "Udgående" for outgoing documents, but can be different depending on the type of document
    "CASE_TYPE": "",  # Is it a borger case or a personale case? Only relevant if this can vary, otherwise it is not needed
    "CASE_TITLE": "",  # This is the name of the case, as in what the case is called in the system. For example, this is "Ansættelse og lønaftaler" for salary cases, but can be different depending on the type of case
}


def main(
    orchestrator_connection: OrchestratorConnection,
    masseforsendelse_folder_path: str = "",
    employee_list_filename: str = "",
    employee_list_sheet_name: str = "",
    files_to_journalize_path: str = "",
    final_journalized_filename: str = "",
    document_category: str = "",
    case_type: str = "",
    case_title: str = "",
):
    """
    the main function to run everything
    """

    credentials = helper_functions.get_credentials_and_constants(orchestrator_connection)

    file_handler = FileHandler(directory=masseforsendelse_folder_path)

    case_handler = CaseHandler(
        api_endpoint=credentials['go_api_endpoint'],
        api_username=credentials['go_api_username'],
        api_password=credentials['go_api_password'],
    )

    case_data_handler = CaseDataJson()

    document_handler = DocumentHandler(
        credentials['go_api_endpoint'],
        credentials['go_api_username'],
        credentials['go_api_password'])

    case_ids_csv_file = identify_employee_folders(
        file_handler=file_handler,
        case_handler=case_handler,
        case_data_handler=case_data_handler,
        employee_list_filename=employee_list_filename,
        employee_list_sheet_name=employee_list_sheet_name,
        case_type=case_type,
        case_title=case_title,
    )

    journalized_docs = handle_journalization(
        orchestrator_connection=orchestrator_connection,
        file_handler=file_handler,
        document_handler=document_handler,
        csv_file=case_ids_csv_file,
        files_to_journalize_path=files_to_journalize_path,
        journalized_filename=final_journalized_filename,
        document_category=document_category,
    )

    print(f"Length of journalized_docs: {len(journalized_docs)}")

    return "Successfully ran masseforsendelse script"


if __name__ == "__main__":

    # !!! DELETE THIS !!!

    sys.argv = [
        "linear_framework.py",
        "DADJ - test af løn journalisering",
        os.getenv("ORCHESTRATOR_CONNECTION_STRING"),
        os.getenv("ORCHESTRATOR_ENCRYPTION_KEY"),
        json.dumps({
            "test_key": "test_value",
        })
    ]

    # !!! DELETE THIS !!!

    test_orchestrator_connection = OrchestratorConnection.create_connection_from_args()

    main(
        orchestrator_connection=test_orchestrator_connection,
        masseforsendelse_folder_path="C:/tmp/Masseforsendelse/",
        employee_list_filename="Masseforsendelse.xlsx",
        employee_list_sheet_name="Ansatte",
        files_to_journalize_path="C:/tmp/Masseforsendelse/udsendte_dokumenter",
        final_journalized_filename="2025.03.28 Meddelelse om løn 2025.07.01",
        document_category="Udgående",
        case_type="PER",
        case_title="Ansættelse og lønaftaler",
    )
