virtualenv venv-pytest
source venv-pytest/bin/activate
pip install -r requirements.txt
python -m pytest -m "not inte" --cov=components --cov-config=./coverage.ini \
--cov-report=term-missing --cov-fail-under=60 -s -v -c custom_pytest.ini
rtrn_code=$?
coverage erase
deactivate
rm -rf venv-pytest
exit $rtrn_code