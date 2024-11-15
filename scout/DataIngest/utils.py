import datetime
from pathlib import Path


def get_project_directory(project_directory_name):
    # Project directory name is name of the folder where project
    # is saved (locally)
    return Path(".data") / project_directory_name


def get_vector_store_directory(project_directory_name):
    project_dir = get_project_directory(project_directory_name)
    return project_dir / Path("VectorStore")


def get_project_name_with_date_time(project_directory_name):
    name = project_directory_name + "-" + datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    return name


def sanitise_project_name(project_name: str) -> str:
    return project_name.replace(" ", "-")
