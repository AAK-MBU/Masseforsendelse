"""
This module handles the journalization process for case management.
It contains functionality to upload and journalize documents, and manage case data.
"""
import time

from typing import Optional

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from helper_scripts.document_handler import DocumentHandler


class DatabaseError(Exception):
    """Custom exception for database related errors."""


class RequestError(Exception):
    """Custom exception for request related errors."""


def log_and_raise_error(orchestrator_connection: OrchestratorConnection, error_message: str, exception: Exception) -> None:
    """
    Log an error and raise the specified exception.

    Args:
        orchestrator_connection (OrchestratorConnection): Connection object to log errors.
        error_message (str): The error message to log.
        exception (Exception): The exception to raise.

    Raises:
        exception: The passed-in exception is raised after logging the error.
    """

    orchestrator_connection.log_error(error_message)

    raise exception


def journalize_file(
    document_category: str,
    document_handler: DocumentHandler,
    case_id: str,
    filename_with_extension: str,
    filename_without_extension: str,
    salary_document_to_journalize_as_byte_stream,
    orchestrator_connection: OrchestratorConnection
):
    """Journalize associated files in the 'Document' folder under the citizen case."""

    def call_journalization(journalize_and_finalize: bool = False) -> Optional[str]:
        # Logic that actually calls all the functions
        print("ABOUT TO CALL JOURNALIZATION FUNCTIONS ... \n")
        try:
            orchestrator_connection.log_trace("Uploading document(s) to the case.")
            print("Uploading document(s) to the case.")

            document_id = process_documents()

            print(f"Document ID: {document_id}")

            document_ids = []
            document_ids.append(document_id)

            journalize_and_finalize = False
            # journalize_and_finalize = True

            if journalize_and_finalize:
                orchestrator_connection.log_trace("Journalizing documents in the case.")
                print("Journalizing documents in the case.")
                handle_journalization(document_ids)

                orchestrator_connection.log_trace("Finalizing document(s) in the case.")
                print("Finalizing document(s) in the case.")
                handle_finalization(document_ids)

            status_message = "Success"

            return document_id, status_message

        except (DatabaseError, RequestError) as e:
            print(f"An error occurred: {e}")

            status_message = "Error"

            return "Journalization process was unsuccessfull", status_message

        except Exception as e:
            print(f"An unexpected error occurred during file journalization: {e}")

            status_message = "Error"

            return "Journalization process was unsuccessfull", status_message

    def process_documents():
        """N/A"""

        received_date = time.strftime("%Y-%m-%d")

        doc_id = upload_single_document(received_date, document_category)

        return doc_id

    def upload_single_document(received_date, document_category, wait_sec=5):
        """N/A"""

        file_bytes = salary_document_to_journalize_as_byte_stream

        upload_status = "failed"

        upload_attempts = 0

        file_bytes.seek(0)
        data_in_bytes = list(file_bytes.read())

        while upload_status == "failed" and upload_attempts < 1:
            document_data = document_handler.create_document_metadata(
                case_id=case_id,
                filename=filename_with_extension,
                data_in_bytes=data_in_bytes,
                overwrite="true",  # Determines if the document should be overwritten if it already exists - based on the filename!
                document_date=received_date,
                document_title=filename_without_extension,
                document_receiver="",
                document_category=document_category
            )

            response = document_handler.upload_document(document_data, '/_goapi/Documents/AddToCase')

            print(f"response: {response}")
            print(f"response.ok: {response.ok}")
            print(f"response.status_code: {response.status_code}")
            print(f"response.text: {response.text}")
            print(f"response.json(): {response.json()}\n")

            upload_attempts += 1

            if response.ok:
                upload_status = "succeeded"

            else:
                time.sleep(wait_sec)

        attempts_string = f"{upload_attempts} attempt"

        attempts_string += "s" if upload_attempts > 1 else ""

        orchestrator_connection.log_trace(f"Uploading {filename_with_extension} {upload_status} after {attempts_string}")

        if not response.ok:
            log_and_raise_error(orchestrator_connection, "An error occurred when uploading the document.", RequestError("Request response failed."))

        document_id = response.json()["DocId"]

        orchestrator_connection.log_trace(f"Document uploaded with ID: {document_id}\n")

        return document_id

    def handle_journalization(document_ids):
        orchestrator_connection.log_trace("Journalizing document.")
        print("Journalizing document.")
        response = document_handler.journalize_document(document_ids, '/_goapi/Documents/MarkMultipleAsCaseRecord/ByDocumentId')

        if not response.ok:
            log_and_raise_error(orchestrator_connection, "An error occurred while journalizing the document.", RequestError("Request response failed."))

        orchestrator_connection.log_trace("Document was journalized.")
        print("Document was journalized.\n")

    def handle_finalization(document_ids):
        orchestrator_connection.log_trace("Finalizing document.")
        print("Finalizing document.")
        response = document_handler.finalize_document(document_ids, '/_goapi/Documents/FinalizeMultiple/ByDocumentId')

        if not response.ok:
            log_and_raise_error(orchestrator_connection, "An error occurred while finalizing the document.", RequestError("Request response failed."))

        orchestrator_connection.log_trace("Document was finalized.")
        print("Document was finalized.\n")

    doc_id = call_journalization()

    orchestrator_connection.log_trace("Document journalization process completed.")
    print("Document journalization process completed.")

    return doc_id
