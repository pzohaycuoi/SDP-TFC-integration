import git
import os


def git_clone(repo_url, folder_path):
    """
    Use GitPython to clone repository,
    Get the git directory so get_tf_var function can find all available variables
    :param repo_url: Terraform code repository url
    :param folder_path: folder path to contain the repository
    :return: repository directory path
    """
    try:
        repo = git.Repo.clone(repo_url, folder_path)
    except AssertionError as err:
        raise SystemExit(err)

    return repo.git_dir


def find_all(name, path):
    """
    Find file with provided name in folder path
    Use this to find all variables file in repository folder
    :param name: file name to find
    :param path: folder path to find file
    :return: list of file path
    """
    result = []
    for root, dirs, files in os.walk(path):
        if name in files:
            result.append(os.path.join(root, name))
    return result


def get_tf_var(filepath: str):
    """
    Get list of terraform variable from a file
    TODO: add function to get type of variable
    :param filepath: file path of the variables.tf file
    :return: list of variable name
    """
    pattern = "variable"
    matching_lines = [line for line in open(filepath).readlines() if pattern in line]
    var_list = []
    replace_list = [" ", '"', "{", "variable"]
    for line in matching_lines:
        for char in replace_list:
            line = line.replace(char, '')

        var_list.append(line)

    return var_list
