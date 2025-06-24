"""
THIS IS A TEST SCRIPT
"""

from mbu_dev_shared_components.getorganized.objects import CaseDataJson

from helper_scripts.case_handler import CaseHandler

from helper_scripts.file_handler import FileHandler

from helper_scripts import helper_functions


LINE_BREAK = "\n\n\n------------------------------------------------------------------------------------------------------------------\n\n\n"


class DatabaseError(Exception):
    """Custom exception for database related errors."""


class RequestError(Exception):
    """Custom exception for request related errors."""


def identify_employee_folders(
    file_handler: FileHandler,
    case_handler: CaseHandler,
    case_data_handler: CaseDataJson,
    employee_list_filename: str,
    employee_list_sheet_name: str,
    case_type: str,
    case_title: str,
):
    """
    main func
    """

    employee_case_ids_csv_file = file_handler.load_or_create_csv_with_headers(filename="employee_case_ids.csv", headers=["cpr", "case_id"])

    # Build a mapping of CPR numbers to employee data from the Excel file
    cpr_dicts = file_handler.build_cpr_mapping(filename=employee_list_filename, sheet_name=employee_list_sheet_name)

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

    print(f"Total CPR count:{len(cpr_dicts)}\n")

    # Iterate through each CPR number and its associated data in the dictionary
    for i, (cpr, data) in enumerate(cpr_dicts.items()):
        # Initialize the salary_case_id variable to None for each iteration, so we can freely manipulate it later
        salary_case_id = None

        employment_code = data.get("tjenestenummer")

        if file_handler.cpr_exists_in_csv(output_filename="employee_case_ids.csv", cpr=cpr):
            print(f"CPR {cpr} already exists. Skipping...\n")

            print(LINE_BREAK)

            continue

        # Retrieve the employee's name and ID from the case handler using the CPR number
        person_full_name, person_go_id = helper_functions.contact_lookup(case_handler=case_handler, ssn=cpr)
        print(f"iterative_number: {i + 1}\nname: {person_full_name}\nperson_go_id: {person_go_id}\ncpr: {cpr}\nemployment code: {data.get('tjenestenummer')}\n")

        # This dictionary contains the properties we want to use, when searching for the case folder
        properties_for_case_search = {
            "ows_Title": case_title
        }

        # Attempt 1: Check case folder with initial parameters
        # In the 1st attempt, we include the name in the search, as we want to find the case folder for this specific person, and we also include the case_title as a field property to narrow down the search
        print("Attempt 1")
        salary_case_info = helper_functions.check_case_folder(
            case_data_handler=case_data_handler,
            case_handler=case_handler,
            case_type=case_type,
            person_full_name=person_full_name,
            person_go_id=person_go_id,
            ssn=cpr,
            include_name=True,
            returned_cases_number="25",
            field_properties=properties_for_case_search
        )

        print(f"salary_case_info:\n{salary_case_info}")

        if salary_case_info:
            salary_case_id = get_correct_case_id(
                case_handler=case_handler,
                salary_case_info=salary_case_info,
                employment_code=employment_code
            )

        if not salary_case_id:
            # In some cases, the search might return no case folder at all - therefore we expand the search by removing the name from the search, whils keeping the ssn, the go_id, and with with the case_title as a field property
            print("\nAttempt 2")

            salary_case_info_without_name = helper_functions.check_case_folder(
                case_data_handler=case_data_handler,
                case_handler=case_handler,
                case_type=case_type,
                person_full_name=person_full_name,
                person_go_id=person_go_id,
                ssn=cpr,
                include_name=False,
                returned_cases_number="25",
                field_properties=properties_for_case_search
            )
            print(f"salary_case_info_without_name:\n{salary_case_info_without_name}")

            if salary_case_info_without_name:
                salary_case_id = get_correct_case_id(
                    case_handler=case_handler,
                    salary_case_info=salary_case_info_without_name,
                    employment_code=employment_code
                )

            # Worst case scenario, the search returns no case folder at all - therefore we expand the search by removing the case_title from the search, and only keeping the name, go_id and ssn in the search
            # This will now return all active employee cases for the person, regardless of the case_title
            if not salary_case_id:
                print("\nAttempt 3")

                all_cases_info = helper_functions.check_case_folder(
                    case_data_handler=case_data_handler,
                    case_handler=case_handler,
                    case_type=case_type,
                    person_full_name=person_full_name,
                    person_go_id=person_go_id,
                    ssn=cpr,
                    include_name=True,
                    returned_cases_number="25",
                    field_properties=None
                )

                if all_cases_info:
                    print(f"\nall_cases_info:\n{all_cases_info}\n")

                    salary_case_id = helper_functions.get_case_id_through_metadata(
                        case_handler=case_handler,
                        all_cases_info=all_cases_info,
                        case_title=case_title,
                        employment_code=employment_code
                    )

                else:
                    salary_case_id = None

        if salary_case_id:
            mapping_entry = {cpr: salary_case_id}

        else:
            mapping_entry = {cpr: "CPR NOT PROPERLY HANDLED - Please investigate this SSN"}

        file_handler.append_cpr_case_mapping_csv(mapping=[mapping_entry], output_filename="employee_case_ids.csv")

        print(f"\nFinal Salary CPR to Case ID mapping: {mapping_entry}\n")

        print(LINE_BREAK)

    # return employee_ssn_to_case_id_mapping
    return employee_case_ids_csv_file


def get_correct_case_id(case_handler: CaseHandler, salary_case_info: list, employment_code: str) -> str:
    """
    This function retrieves the correct case ID from the salary_case_info list based on the employment code.
    """

    employment_code_with_xa = f"XA{employment_code}"

    for case in salary_case_info:
        case_id = case.get('CaseID')

        employee_folder_id = case.get('RelativeUrl').split("/")[-1]

        if case_id == employee_folder_id:
            continue

        response = case_handler.get_case_metadata(endpoint_path=f'/_goapi/Cases/Metadata/{employee_folder_id}')

        # We parse the metadata string returned from the API, using the parse_metadata function
        formatted_case_metadata = helper_functions.parse_metadata(metadata_str=response.json().get("Metadata"))

        if formatted_case_metadata.get("ows_EmploymentCode") in (employment_code, employment_code_with_xa):
            salary_case_id = case_id

            return salary_case_id

    # If no matching case is found, return None
    return None
