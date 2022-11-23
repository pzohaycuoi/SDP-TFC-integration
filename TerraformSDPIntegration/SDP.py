import json


def convert_json(file_path: str):
    """
    Convert data in file to JSON.
    ON SDP ticket creation, SDP will create a temporary file contains all fields in the ticket (for 60 seconds)
    We will need get data of the file, so we can use later
    :param file_path: string, file path of the file
    :return: dict, data inside the file of file_path convert to JSON
    """
    with open(file_path) as data_file:
        data = data_file.read()
        data.replace('&quot;', '"')
        data_json = json.loads(data)

    return data_json


# def custom_fields(json_data: dict, var_list: list):
#     """
#     Get value from SDP custom_fields, use to construct API payload.
#     :param json_data: dict, JSON format, SDP information has been parsed
#     :param var_list: list, list of Terraform variables = as fields in the ticket
#     variable name must be same as the ticket field name
#     :return: dict, variable name with its value in key-pair form
#     """
#     field_and_value = {}
#     for i in var_list:
#         k = i
#         v = ""
#         for label in json_data["INPUT_DATA"]["entity_data"]["custom_fields"]:
#             if label["label"] == k:
#                 v = label["value"]
#
#         field_and_value.update({k: v})
#
#     return field_and_value


def get_field(json_data: dict):
    """
    Get value from SDP custom_fields, use to construct API payload.
    :param json_data: dict, JSON format, SDP information has been parsed
    variable name must be same as the ticket field name
    :return: dict, variable name with its value in key-pair form
    """
    field_and_value = {}
    for field in json_data["INPUT_DATA"]["entity_data"]["custom_fields"]:
        k = field["label"]
        v = field["value"]
        field_and_value.update({k: v})

    return field_and_value

