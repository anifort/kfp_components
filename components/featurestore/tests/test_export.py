from components.featurestore import export


bigquery_location = 'EU'
bigquery_project_id = "myfirstproject-226013"
bigquery_read_instances_staging_table = "myfirstproject-226013.telco.tmptable-v22"
bigquery_features_export_table_uri="myfirstproject-226013.telco.featurestable-v22"
bigquery_read_instances_query= """
        SELECT customerID as customer, "Sony - CMD J5" as phone, TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)  as timestamp, Churn as label
            FROM `myfirstproject-226013.telco.churn` WHERE 1=1
        """

feature_store_location = 'europe-west4'
feature_store_project_id = 'myfirstproject-226013'
feature_store_name = 'telco'



my_features  = {'customer': ["tenure", "monthly_charges", "internet_service"],
                'phone': ["model", "approx_price_euro"]}



def test_pipeline_using_component_e2e():

    from google.cloud.aiplatform.pipeline_jobs import PipelineJob
    from kfp.v2 import compiler, dsl
    from kfp.v2.dsl import Dataset, Input, component
    import inspect

    @component()
    def print_uri(arti: Input[Dataset]):
        print(vars(arti))
        print(arti.uri)



    pipeline_bucket = "gs://myfirstproject-226013/test-pipeline"
    @dsl.pipeline(
        name='test-feature-store-comp',
        description='testing pipeline for feature store component',
        pipeline_root=pipeline_bucket
    )
    def pipeline(
            bigquery_project_id: str,
            bigquery_location: str,
            bigquery_read_instances_staging_table: str, # includes project.dataset.table without bq://
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
            bigquery_read_instances_staging_table, # includes project.dataset.table without bq://
            bigquery_read_instances_query,
            feature_store_location,
            feature_store_name,
            feature_store_project_id,
            bigquery_features_export_table_uri, # includes project.dataset.table without bq://
            features_dict,
            timeout
        )
        printer_op = print_uri(arti = export_features_from_bq_search_op.outputs["features_table"])

    pipeline_path = './artefacts/{}.json'.format(inspect.currentframe().f_code.co_name)

    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_path)

    pl = PipelineJob(display_name= "fs-comp-test",
                     template_path= pipeline_path,
                     location=feature_store_location,
                     enable_caching=False,
                     parameter_values={
                         'bigquery_project_id': bigquery_project_id,
                         'bigquery_location': bigquery_location,
                         'bigquery_read_instances_staging_table': bigquery_read_instances_staging_table, # includes project.dataset.table without bq://
                         'bigquery_read_instances_query': bigquery_read_instances_query,
                         'feature_store_location': feature_store_location,
                         'feature_store_name': feature_store_name,
                         'feature_store_project_id': feature_store_project_id,
                         'bigquery_features_export_table_uri': bigquery_features_export_table_uri, # includes project.dataset.table without bq://
                         'features_dict': my_features,
                         'timeout': 600})

    print(pl.run(sync=True,
                 #service_account=""
                 ))