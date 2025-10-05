import csv
import io
import json
from pathlib import Path


def save_dict_to_json(data: list[dict], file_path: str) -> None:
    """
    Save a dictionary to a JSON file.

    Args:
    data (dict): The dictionary to be saved.
    file_path (str): The path to the file where the dictionary will be saved. If the file doesn't exist,
                     it will be created.

    Returns:
    None

    This function takes a dictionary and a file path as arguments, and saves the dictionary in JSON format to the specified file.
    It uses the 'json' module for JSON serialization and 'pathlib.Path' to handle file paths.
    """
    path = Path(file_path)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_json_to_dict(file_path: str) -> dict:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
    file_path (str): The path to the JSON file to be read.

    Returns:
    dict: The dictionary containing the data from the JSON file.

    This function takes a file path as an argument and reads the JSON file at that location, returning its contents as a dictionary.
    It uses the 'json' module for JSON deserialization and 'pathlib.Path' to handle file paths.
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def csv_string_to_json_list(csv_str: str) -> list[dict[str, str]]:
    """
    Converte uma string CSV para uma lista de dicionários (formato JSON).

    Args:
        csv_str (str): A string contendo dados em formato CSV (com cabeçalho).

    Returns:
        List[Dict[str, str]]: Lista de dicionários representando cada linha do CSV.
    """
    reader = csv.DictReader(io.StringIO(csv_str.strip()))
    return list(reader)
