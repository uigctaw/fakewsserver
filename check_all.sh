#!/bin/bash

set -e

poetry run pytest
poetry run bandit --quiet -r fakewsserver
poetry run flake8
poetry run mypy --show-error-codes fakewsserver
aspell check README.md
