#  🔍 IPA scout

> ⚠️ Incubation Project: This project is an incubation project; as such, we DON’T recommend using it in any critical use case. This project is in active development and a work in progress. 

Scout automatically analyses new project documents w.r.t to IPA guidance and gate workbooks, flagging potential problems as soon as possible. This tool improves and expedites the work of assurance review teams.

There is a pipeline that ingests project documents, criteria, then uses an LLM to evaluate projects against the criteria. The project data, criteria and evaluation results are saved in a database. There is then an app that allows users to explore this data and identify potential issues with projects.

At present this code only runs locally.

For more detailed documentation, see the `docs` folder. There are also example scripts in `scripts`.


# Installing the project locally

Note that you will need Docker and Python installed on your laptop.

Clone the repo.
```
git clone git@github.com:i-dot-ai/scout.git
cd scout
```
Make sure you have [poetry installed](https://python-poetry.org/docs/) for dependency management.

Install packages: 
```
poetry install --with dev
```

Set up pre-commit for linting, checking for secrets etc:
```
pre-commit install
```

Install `nltk` data:
```
poetry run python -c "import nltk; nltk.download('punkt_tab');nltk.download('averaged_perceptron_tagger_eng');nltk.download('averaged_perceptron_tagger_eng')"
```

Copy the `.env` file and add your environment variables e.g. API keys:
```
cp .env.example .env
```

You may need to install `poppler` (this is a reqirement for the `pdf2image` Python library): 
```
brew install poppler
```
(assuming you are using a Mac with Homebrew).

Run using:
```
docker compose build
docker compose up
```

You will also need to run migrations (more detail on database below):
```
poetry run alembic upgrade head
```
or 
```
make alembic-upgrade
```
(depends how you set-up alembic).

In your browser see the app at: 
```
http://localhost:3000
```

There won't be any data in the app yet - you will have to run the pipeline to analyse project data and populate the database. 

You can manually reset your database using `make reset-local-db` (when you have your database running). For this to work, you will need postgres installed locally (with a Mac: `brew install postgres` or `brew install postgres@13` or whichever version you want).


# Running the analysis pipeline

The pipeline to evaluate projects runs outside the app.

Make a `.data` directory in the root of the project: 
```
mkdir .data
cd .data
```
Don't commit this to git, it is in the `.gitignore`.

This is where you will create folders with your project documents, and folders for your criteria.

There is an example script in `scripts/analyse_project.py` - follow the instructions below to run the pipeline.

You may wish to use the example data in the `example_data` folder - this contains example project data, full criteria extracted from IPA stage gate workbooks, and some example criteria for testing.

1. Save your project data in a folder within `.data` - the name of the folder is the project name (e.g. `example_project`).
2. Save the criteria CSVs in `.data` (e.g. in a folder called `criteria`).
3. Make sure Python packages are installed: `poetry install`.
4. Make sure your database, minio and libreoffice services are running: `docker compose up db minio libreoffice`.
5. In the script, change your `project_directory_name`, `gate_review`, and `llm` to reflect your project (if you are using the example data, you won't need to change anything).
6. Run the script (outside Docker): `poetry run python scripts/analyse_project.py` (this takes a few minutes with the example data).
7. View your results in the frontend - run the app in Docker `docker compose up` and go to http://localhost:3000.

More detailed documentation can be found in `docs/analyse_projects.md`.


# Database

Scout uses a persistent data store using PostgreSQL, running in a Docker container locally (called `db`).

Models for the database are kept in `scout/utils/storage/postgres_models.py`.

Pydantic models for the database interaction are kept in `scout/DataIngest/models/schemas.py`.

A function interface for interacting with the database is kept in `scout/utils/storage/postgres_interface.py`.

We use SQLAlchemy for database connections, and alembic for tracking migrations. The `alembic.ini` file at the root of the project handles alembic configuration and the connection string to the db to action against.

When adding new models, import each model into `alembic/env.py` so that alembic reads it into the config.

Run `make alembic-revision` to generate a new migration, and `make alembic-upgrade` to run the upgrade to apply the new migration.


## Data analysis modules

Distinct modules for data analysis should have their own folders in the scout package. Where possible each module should use models from the data ingest module. All other models should be placed in a `models.py` file for the module.

Each module should have a corresponding script in the `scripts` folder that runs a pipeline that uses that module.


# Troubleshooting

## Docker issues
If you have issues on `docker compose build` with permissions, for example:
```
Error response from daemon: error while creating mount source path '/Users/<username>/scout/data/objectstore'
```

You can update the permissions using:
```
chmod 755 /Users/<username>/scout/libreoffice_service/config
```

## `make reset-local-db`

This command resets your local database (make sure you have it running in Docker: `docker compose up db`).

Make sure you have psql installed through brew `brew install postgresql`. 

The local postgresql service needs to be stopped before running this `make` command: `brew services stop postgresql`.

If the db/tables can't be found, check that you've run `poetry run alembic upgrade head` (or `make alembic-upgrade`) and that the `db` container is running.


# Tests

**Note** these tests will generate data in your local database and Minio (local S3), and will generate a vector store in your example data folder.

These tests use the example data in `example_data` folder - if you run the pipeline normally, you should be saving data in `.data`.

Future improvements would use a separate test database and file storage.

`test_CreateDBPipeline.py` and `test_LLMFlag.py` serve as integration tests and run the pipelines to ingest project data and populate the database, and the to evaluate the projects against the criteria (LLM flag).

These tests may take a while to run (~5-10 mins).

The other test files contain unit tests.

## Running the tests

1. Ensure your local `.env` contains `LIBREOFFICE_URL`, API keys etc. (see the `.env.example` for what needs to be included).
2. Run the database, Minio and Libreoffice `docker compose up db minio libreoffice`
3. Run the tests using pytest. The tests require the DB to be empty for the tests to pass. These can be run from the root folder using the flag `--reset-db` to reset the DB before running the tests. The flag accepts `postgres`, `vector_store` and `all` as arguments with `all` being recommended. The `-v` flag is for verbose output. Note that the integration tests may take a while (~10 minutes).
4. Example usage: 
- `poetry run pytest tests/test_CreateDBPipeline.py --reset-db all -v`, 
- `poetry run pytest tests/test_LLMFlag.py --reset-db all -v`. 
- `poetry run pytest tests/test_file_update.py` (can be run without resetting DB)
- `poetry run pytest tests/test_create_db.py` (can be run without resetting DB)

The tests should be run from the root folder.

You can reset your local database after running tests with `make reset-local-db`.

Changing the document count or contents will cause the tests to fail.

