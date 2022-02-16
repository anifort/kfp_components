from src.featurestore import export

import os
import pytest


bigquery_location = 'EU'
bigquery_project_id = "myfirstproject-226013"
bigquery_read_instances_staging_table_uri = "myfirstproject-226013.telco.tmp-tbl-"
bigquery_features_export_table_uri="myfirstproject-226013.telco.features-tbl-"
bigquery_read_instances_query= """
        SELECT customerID as customer, "Sony - CMD J5" as phone, TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)  as timestamp, Churn as label
            FROM `myfirstproject-226013.telco.churn` WHERE 1=1
        """

feature_store_location = 'europe-west4'
feature_store_project_id = 'myfirstproject-226013'
feature_store_name = 'telco'

pipeline_project = 'myfirstproject-226013'
pipeline_bucket = "gs://myfirstproject-226013/test-pipeline"
pipeline_location = 'europe-west4'

my_features  = {'customer': ["tenure", "monthly_charges", "internet_service"],
                'phone': ["model", "approx_price_euro"]}

''' 
@pytest.fixture(scope='module')
def db():
    print('*****SETUP*****')
    db = StudentData()
    db.connect('data.json')
    yield db
    print('******TEARDOWN******')
    db.close()
'''
@pytest.mark.unit
def test_unit():
    assert True


@pytest.mark.inte
#@pytest.mark.skipif('RUN_ENV' in os.environ and os.environ['RUN_ENV']=='test', reason="This is integration test and takes time -using only while developing")
def test_pipeline_using_component_e2e():

    from google.cloud.aiplatform.pipeline_jobs import PipelineJob
    from kfp.v2 import compiler, dsl
    from kfp.v2.dsl import Dataset, Input, component
    import inspect

    from datetime import datetime
    timestamp = str(int(datetime.now().timestamp()))


    pipeline_path = os.path.join(os.path.dirname(__file__), './artefacts/{}.json'.format(inspect.currentframe().f_code.co_name))

    @component()
    def print_uri(arti: Input[Dataset]):
        print(vars(arti))
        print(arti.uri)



    @dsl.pipeline(
        name='test-feature-store-comp',
        description='testing pipeline for feature store component'
    )
    def pipeline(
            bigquery_project_id: str,
            bigquery_location: str,
            bigquery_read_instances_staging_table_uri: str, # includes project.dataset.table without bq://
            bigquery_read_instances_query: str,
            feature_store_location: str,
            feature_store_name: str,
            feature_store_project_id: str,
            bigquery_features_export_table_uri: str, # includes project.dataset.table without bq://
            features_dict: dict,
            timeout: int
    ):


        export_features_from_bq_search_op = export.export_features_from_bq_search(
            bigquery_project_id,
            bigquery_location,
            bigquery_read_instances_staging_table_uri, # includes project.dataset.table without bq://
            bigquery_read_instances_query,
            feature_store_location,
            feature_store_name,
            feature_store_project_id,
            bigquery_features_export_table_uri, # includes project.dataset.table without bq://
            features_dict,
            timeout
        )
        printer_op = print_uri(arti = export_features_from_bq_search_op.outputs["features_table"])


    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_path)

    pl = PipelineJob(display_name= "fs-comp-test",
                     job_id= "fs-comp-test-"+timestamp,
                     template_path= pipeline_path,
                     pipeline_root= pipeline_bucket,
                     project=pipeline_project,
                     labels= {"env":"test"},
                     location=pipeline_location,
                     enable_caching=False,
                     parameter_values={
                         'bigquery_project_id': bigquery_project_id,
                         'bigquery_location': bigquery_location,
                         'bigquery_read_instances_staging_table_uri': bigquery_read_instances_staging_table_uri+timestamp, # includes project.dataset.table without bq://
                         'bigquery_read_instances_query': bigquery_read_instances_query,
                         'feature_store_location': feature_store_location,
                         'feature_store_name': feature_store_name,
                         'feature_store_project_id': feature_store_project_id,
                         'bigquery_features_export_table_uri': bigquery_features_export_table_uri+timestamp, # includes project.dataset.table without bq://
                         'features_dict': my_features,
                         'timeout': 600})

    print(pl.run(sync=True,
                 #service_account=""
                 ))