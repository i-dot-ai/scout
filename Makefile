-include .env
export

# Setting up your python environment - 3.12.2
PYTHON_VERSION=3.12.2
PYTHON = poetry run python

install: ## Install all dependencies including dev packages
	poetry install --with dev
	poetry run pre-commit install
	

setup: install ## Complete setup including pre-commit hooks and NLTK data
	$(PYTHON) -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')"
	brew install poppler
	test -f .env || cp .env.example .env
	@echo "Don't forget to update your .env file with your API keys!"
	

alembic-upgrade:
	poetry run alembic upgrade head

alembic-revision:
	poetry run alembic revision --autogenerate

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

