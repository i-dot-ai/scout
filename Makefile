-include .env
export

# Setting up your python environment - 3.12.2
PYTHON_VERSION=3.12.2

test:
	poetry install --with dev && poetry run python -m pytest tests --cov=backend -v --cov-report=term-missing --cov-fail-under=0

alembic-upgrade:
	alembic upgrade head

alembic-revision:
	alembic revision --autogenerate

# Resetting system to make testing easier --------------
# Make sure you have psql installed through brew `brew install postgresql`
# If the db/tables can't be found, check that you've run `alembic upgrade head` and that the `db` container is running
# The local postgresql service needs to be stopped before running this: `brew services stop postgresql`
reset-local-db:
	psql postgresql://postgres:insecure@localhost:5432/ipa-scout -f reset_db.sql  # pragma: allowlist secret


delete-local-vectorstore:
	@if [ -z "$(PROJECT_NAME)" ]; then \
		echo "Error: PROJECT_NAME is not set"; \
		exit 1; \
	else \
		if [ -d ".data/$(PROJECT_NAME)/VectorStore" ]; then \
			rm -rf ".data/$(PROJECT_NAME)/VectorStore"; \
			echo "Deleted folder: .data/$(PROJECT_NAME)/VectorStore"; \
		else \
			echo "Folder .data/$(PROJECT_NAME)/VectorStore does not exist"; \
		fi \
	fi

