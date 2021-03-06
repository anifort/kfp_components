from src.bigquery import export

import os
import pytest
from pytest_mock import MockerFixture
from unittest.mock import patch

bq_uri="myfirstproject-226013.telco.churn"
gcs_uri="gs://myfirstproject-226013/telco/churn"

pipeline_project = 'myfirstproject-226013'
pipeline_bucket = "gs://myfirstproject-226013/test-pipeline"
pipeline_location = 'europe-west4'

"""
@pytest.fixture
def et():
    return MockerFixture.patch("google.cloud.bigquery.Client.extract_table")
"""

@pytest.mark.unit
def test_bq_export_unit(mocker: MockerFixture):
    from kfp.v2.dsl import Dataset
    from google.cloud.bigquery import TableReference, DatasetReference
    from src.bigquery.export import bq_export
    from google.cloud.bigquery.job import ExtractJob


    ej = mocker.MagicMock(
        spec=ExtractJob,
        result=mocker.MagicMock(return_value=True)
    )

    mock_run = mocker.patch("google.cloud.bigquery.Client.extract_table", return_value=ej)

    bq_export.python_func(
        bq_uri=bq_uri,
        project=pipeline_project,
        location=pipeline_location,
        gcs_uri=gcs_uri,
        exported_dataset=Dataset(uri=bq_uri))

    bq_project_id, bq_dataset_id, bq_table_id = bq_uri.split('.')
    mock_run.assert_called_with(
        TableReference(DatasetReference(bq_project_id, bq_dataset_id), bq_table_id),
        [gcs_uri+'/data_*.csv'],
        'myfirstproject-226013',
        'europe-west4'
    )

@pytest.mark.inte
def test_bq_export_int(mocker: MockerFixture):
    from kfp.v2.dsl import Dataset

    dataset = mocker.Mock(spec=Dataset, uri = gcs_uri)
    export.bq_export.python_func(
        bq_uri,
        project=pipeline_project,
        location='EU',
        gcs_uri=gcs_uri,
        exported_dataset=Dataset(uri=bq_uri))


@pytest.mark.inte
#@pytest.mark.skipif('RUN_ENV' in os.environ and os.environ['RUN_ENV']=='test', reason="This is integration test and takes time -using only while developing")
def test_pipeline_using_component_e2e():

    from google.cloud.aiplatform.pipeline_jobs import PipelineJob
    from kfp.v2 import compiler, dsl
    import inspect

    from datetime import datetime
    timestamp = str(int(datetime.now().timestamp()))


    pipeline_path = os.path.join(os.path.dirname(__file__), './artefacts/{}.json'.format(inspect.currentframe().f_code.co_name))


    @dsl.pipeline(
        name='test-bq-export-comp',
        description='testing pipeline for exporting data from BQ to CSV'
    )
    def pipeline(
            bq_uri: str,
            project: str,
            location: str,
            gcs_uri: str
    ):


        export_features_from_bq_search_op = export.bq_export(
            bq_uri,
            project,
            location,
            gcs_uri
        )
        export_features_from_bq_search_op.set_display_name("export_data_bq")

    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_path)

    pl = PipelineJob(display_name= "bq-exp-test",
                     job_id= "bq-exp-test-"+timestamp,
                     template_path= pipeline_path,
                     pipeline_root= pipeline_bucket,
                     project=pipeline_project,
                     labels= {"env":"test"},
                     location=pipeline_location,
                     enable_caching=False,
                     parameter_values={
                         'bq_uri': bq_uri,
                         'project': pipeline_project,
                         'location': 'EU',
                         'gcs_uri': gcs_uri})

    print(pl.run(sync=True))