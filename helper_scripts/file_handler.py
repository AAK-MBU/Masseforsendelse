import os
import csv

from pathlib import Path

import pandas as pd


class FileHandler:
    """
    A class to read data from Excel files with .xlsx format located in a specified directory.

    Attributes:
    -----------
    directory : str
        The directory where Excel files are stored.

    Methods:
    --------
    get_cpr_values(sheet_name: str, filename: str) -> List[str]:
        Reads the 'CPR' column from the given sheet in the specified file,
        ensuring values are stored as strings with preserved leading zeros, and returns them sorted.
    """
    def __init__(self, directory: str):
        """
        Initializes the ExcelHandler with the directory containing Excel files.

        Parameters:
        -----------
        directory : str
            The directory path where Excel files are stored.
        """
        if not os.path.isdir(directory):
            raise ValueError(f"{directory} is not a valid directory.")
        self.directory = directory

    def _get_file_path(self, filename: str) -> str:
        """
        Helper method to construct the full file path from the directory and filename.

        Parameters:
        -----------
        filename : str
            The name of the Excel file.

        Returns:
        --------
        str
            The full path to the Excel file.
        """
        return os.path.join(self.directory, filename)

    def load_or_create_csv_with_headers(self, filename: str, headers: list[str]) -> Path:
        """
        Ensures a CSV file exists in the handler's directory with the specified headers.
        If the file doesn't exist or is empty, it creates it with the given headers.

        Parameters:
            filename (str): The name of the CSV file (e.g., 'test.csv').
            headers (list[str]): The list of headers to write if creating the file.

        Returns:
            Path: The full path to the CSV file.
        """

        csv_path = Path(self.directory) / filename

        if not csv_path.exists() or csv_path.stat().st_size == 0:
            with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                writer.writerow(headers)

        return csv_path

    def build_cpr_mapping(self, filename: str, sheet_name: str) -> dict:
        """
        Reads each row in an Excel file (identified by 'filename' and 'sheet_name') and
        returns a dictionary of the form:

            {
                "some_cpr": {
                    "tjenestenummer": ...,
                    "navn": ...,
                    "stilling": ...
                },
                "another_cpr": {
                    "tjenestenummer": ...,
                    "navn": ...,
                    "stilling": ...
                },
                ...
            }

        It assumes the Excel has columns:
            - "Tjenestenummer"
            - "CPR"
            - "Navn"
            - "Stilling"

        and that "CPR" is used as the key in the returned dictionary.

        The DataFrame is first sorted by the numeric value of the "CPR" column (smallest first).
        """

        file_path = self._get_file_path(filename)

        # Read the Excel file with converters to ensure values are read as strings
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            converters={
                'CPR': str,
                'Tjenestenummer': str,
                'Navn': str,
                'Stilling': str
            }
        )

        # Ensure required columns exist
        required_cols = ['CPR', 'Tjenestenummer', 'Navn', 'Stilling']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in the sheet.")

        # Sort the DataFrame, in ascending order, by the numeric value of the CPR column - this assumes that CPR values are numeric even if stored as strings.
        df.sort_values(by='CPR', key=lambda col: col.astype(int), inplace=True)

        # Build the dictionary, preserving the sorted order.
        cpr_dict = {}
        for _, row in df.iterrows():
            cpr_value = row['CPR']

            # Skip rows with missing CPR value
            if pd.isna(cpr_value):
                continue

            # Remove any accidental whitespace
            cpr_value = cpr_value.strip()

            cpr_dict[cpr_value] = {
                "tjenestenummer": row['Tjenestenummer'] if not pd.isna(row['Tjenestenummer']) else "",
                "navn": row['Navn'] if not pd.isna(row['Navn']) else "",
                "stilling": row['Stilling'] if not pd.isna(row['Stilling']) else ""
            }

        return cpr_dict

    def cpr_exists_in_csv(self, output_filename: str, cpr: str) -> bool:
        """
        Checks if a given CPR number exists in the CSV file.

        Parameters:
            output_filename (str): The name of the CSV file (e.g., 'test.csv').
            cpr (str): The CPR number to check.

        Returns:
            bool: True if the CPR number exists, False otherwise.
        """

        output_file_path = os.path.join(self.directory, output_filename)

        if not os.path.exists(output_file_path) or os.path.getsize(output_file_path) == 0:
            return False

        # Ensure the "CPR Nummer" column is read as string
        df = pd.read_csv(output_file_path, dtype={"cpr": str})

        if "cpr" not in df.columns:
            return False

        return cpr in df["cpr"].values

    def append_cpr_case_mapping_csv(self, mapping: list, output_filename: str) -> None:
        """
        Appends a list of dictionaries mapping CPR numbers to Salary Case IDs into a CSV file.
        If the file does not exist or is empty, it writes the headers 'CPR Nummer' and 'Salary Case ID'
        at the top of the file.

        Parameters:
            mapping (list of dict): A list where each dictionary contains one key-value pair {cpr_nummer: salary_case_id}.
            output_filename (str): The name of the CSV file to append to (e.g., 'cpr_mapping.csv').
        """

        output_file_path = os.path.join(self.directory, output_filename)

        # Check if the file doesn't exist or is empty to decide if we need to write headers.
        write_header = not os.path.exists(output_file_path) or os.path.getsize(output_file_path) == 0

        with open(output_file_path, mode='a', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)

            if write_header:
                writer.writerow(["CPR Nummer", "Salary Case ID"])

            # Append each mapping entry as a new row.
            for entry in mapping:
                for cpr, case_id in entry.items():
                    writer.writerow([cpr, case_id])

    def get_cpr_csv_mapping(self, filename: str) -> dict:
        """
        Reads each row in a CSV file (identified by 'filename') and returns a dictionary mapping:
            Key: CPR Nummer
            Value: Salary Case ID
        """

        file_path = self._get_file_path(filename)

        # Read the CSV file with converters to ensure values are read as strings
        df = pd.read_csv(
            file_path,
            converters={
                'CPR Nummer': str,
                'Salary Case ID': str
            }
        )

        # Ensure required columns exist
        required_cols = ['CPR Nummer', 'Salary Case ID']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column '{col}' in the CSV file.")

        # Optionally: sort the DataFrame by the numeric value of the CPR Nummer column
        df.sort_values(by='CPR Nummer', key=lambda col: col.astype(int), inplace=True)

        cpr_mapping = {}

        for _, row in df.iterrows():
            cpr_value = row['CPR Nummer']

            if pd.isna(cpr_value):
                continue  # Skip rows with missing CPR Nummer

            cpr_value = cpr_value.strip()  # Remove accidental whitespace

            # Get Salary Case ID, using an empty string if it's missing
            salary_case_id = row['Salary Case ID']
            if pd.isna(salary_case_id):
                salary_case_id = ""
            else:
                salary_case_id = salary_case_id.strip()

            cpr_mapping[cpr_value] = salary_case_id

        return cpr_mapping
