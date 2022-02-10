from kfp.v2.dsl import (
    component
)

def export_to_staging(
        bigquery_project_id: str,
        bigquery_location: str,
        bigquery_read_instances_staging_table: str, # includes project.dataset.table without bq://
        bigquery_read_instances_query: str,
        timeout: int):

    import logging
    from google.cloud import bigquery

    client = bigquery.Client(project=bigquery_project_id, location=bigquery_location)

    overwrite_table = False
    job_config = bigquery.QueryJobConfig(
        write_disposition = bigquery.job.WriteDisposition.WRITE_TRUNCATE if overwrite_table else bigquery.job.WriteDisposition.WRITE_EMPTY,
        destination = bigquery_read_instances_staging_table)

    try:
        query_job = client.query(query = bigquery_read_instances_query,
                                 job_config = job_config)
        query_job.result(timeout=timeout)
        #if .total_rows == 0:
        #    raise Exception("Query return no rows".format(bigquery_read_instances_staging_table))

        if query_job.errors:
            raise Exception(query_job.errors)
    except Exception as e:
        raise e

    table_dataset_metadata={}

    table = client.get_table(bigquery_read_instances_staging_table)  # Make an API request.
    table_dataset_path = "bq://{}".format(bigquery_read_instances_staging_table)
    table_dataset_metadata['table_name'] = bigquery_read_instances_staging_table



    if table.num_rows==0:
        raise Exception("BQ table {} has no rows. Ensure that your query returns results: {}".format(bigquery_read_instances_staging_table, bigquery_read_instances_query))

    from collections import OrderedDict # in case dict is not created using python>=3.6
    schema = OrderedDict((i.name,i.field_type) for i in table.schema)
    entity_type_cols = []
    pass_through_cols = []
    found_timestamp=False
    for key, value in schema.items():
        if key=='timestamp':
            found_timestamp=True
            if value!="TIMESTAMP":
                raise ValueError("timestamp column must be of type TIMESTAMP")
        else:
            if found_timestamp==False:
                entity_type_cols.append(key)
            else:
                pass_through_cols.append(key)

    if found_timestamp==False: # means timestamp column was not found so this remained False
        raise ValueError("timestamp column missing from BQ table. It is required for feature store data retrieval")

    return entity_type_cols, pass_through_cols



def validate_staging_against_featurestore(
        feature_store_location: str,
        feature_store_name: str,
        feature_store_project_id: str,
        features_dict: dict,
        entity_type_cols: list,
        query: str):

    from google.cloud.aiplatform_v1beta1 import FeaturestoreServiceClient
    fs_path= 'projects/{fs_project}/locations/{fs_location}/featurestores/{fs_name}'.format(fs_project=feature_store_project_id,
                                                                                            fs_location=feature_store_location,
                                                                                            fs_name=feature_store_name)


    API_ENDPOINT = "{}-aiplatform.googleapis.com".format(feature_store_location)

    admin_client = FeaturestoreServiceClient(
        client_options={"api_endpoint": API_ENDPOINT})

    fs_entities = admin_client.list_entity_types(parent=fs_path).entity_types

    fs_entities = [i.name.split('/')[-1] for i in fs_entities]

    if len(set(entity_type_cols).difference(fs_entities))>0:
        raise ValueError("Table column(s) {} before timestamp column do not match entities in feature store {} ".format(entity_type_cols, fs_entities))


    entities_diff = set(features_dict.keys()).difference(entity_type_cols)
    if len(entities_diff)>0:
        raise LookupError("\n Entities {} must exist in filtering query columns: {} ".format(entities_diff, query))

    error_buffer = ""
    for k,v in features_dict.items():
        fs_features = admin_client.list_features(parent=fs_path+"/entityTypes/{}".format(k)).features
        fs_features = [i.name.split('/')[-1] for i in fs_features]

        missing_features = set(v).difference(fs_features)
        if len(missing_features)>0:
            error_buffer += "\n Features requested for entity [{}] do not exist: {}".format(k, missing_features)

    if error_buffer!="":
        raise LookupError(error_buffer)

    return fs_path

def export_features_to_bq(
        feature_store_location: str,
        feature_store_name: str,
        feature_store_project_id: str,
        bigquery_read_instances_staging_table: str,
        bigquery_features_export_table_uri: str,
        pass_through_cols: list,
        features_dict: dict,
        timeout: int):

    fs_path= 'projects/{fs_project}/locations/{fs_location}/featurestores/{fs_name}'.format(fs_project=feature_store_project_id,
                                                                                            fs_location=feature_store_location,
                                                                                            fs_name=feature_store_name)


    from google.cloud.aiplatform_v1beta1 import FeaturestoreServiceClient

    from google.cloud.aiplatform_v1beta1.types import (featurestore_service as featurestore_service_pb2,
                                                       feature_selector as feature_selector_pb2,
                                                       BigQuerySource, BigQueryDestination)

    entity_type_specs_arr=[]

    # Select features to read
    for ent_type, features_arr in features_dict.items():
        entity_type_specs_arr.append(
            featurestore_service_pb2.BatchReadFeatureValuesRequest.EntityTypeSpec(
                # read feature values of features subscriber_type and duration_minutes from "bikes"
                entity_type_id= ent_type,
                feature_selector= feature_selector_pb2.FeatureSelector(
                    id_matcher=feature_selector_pb2.IdMatcher(
                        ids=features_arr))
            )
        )

    # Select columns to pass through
    pass_through_fields_arr = []
    for ptc in pass_through_cols:
        pass_through_fields_arr.append(
            featurestore_service_pb2.BatchReadFeatureValuesRequest.PassThroughField(
                # read feature values of features subscriber_type and duration_minutes from "bikes"
                field_name=ptc
            )
        )

    batch_serving_request = featurestore_service_pb2.BatchReadFeatureValuesRequest(
        featurestore=fs_path,
        bigquery_read_instances=BigQuerySource(input_uri = "bq://{}".format(bigquery_read_instances_staging_table)),
        #csv_read_instances=io_pb2.CsvSource(
        #    gcs_source=io_pb2.GcsSource(uris=[FEATURE_REQ_CSV_PATH])),

        # Output info
        destination=featurestore_service_pb2.FeatureValueDestination(
            bigquery_destination=BigQueryDestination(
                # output to BigQuery table
                output_uri='bq://{}'.format(bigquery_features_export_table_uri))),
        #destination=featurestore_service_pb2.FeatureValueDestination(
        #    tfrecord_destination=io_pb2.CsvDestination(
        #        gcs_destination=EXPORT_TF_PATH)),

        entity_type_specs=entity_type_specs_arr,
        pass_through_fields=pass_through_fields_arr

    )

    try:
        admin_client = FeaturestoreServiceClient(
            client_options={"api_endpoint": "{}-aiplatform.googleapis.com".format(feature_store_location)})
        print(admin_client.batch_read_feature_values(batch_serving_request).result(timeout=timeout))
    except Exception as ex:
        print(ex)



@component(#base_image=""
    packages_to_install=["google-cloud-bigquery==2.24.1"],
    output_component_file='export_features_from_bq_search.yaml'
)
def export_features_from_bq_search(
        bigquery_project_id: str,
        bigquery_location: str,
        bigquery_read_instances_staging_table: str, # includes project.dataset.table without bq://
        bigquery_read_instances_query: str,
        feature_store_location: str,
        feature_store_name: str,
        feature_store_project_id: str,
        bigquery_features_export_table_uri: str, # includes project.dataset.table without bq://
        features_dict: dict,
        timeout: int = 600

) -> None:

    entity_type_cols, pass_through_cols = export_to_staging(
        bigquery_project_id,
        bigquery_location,
        bigquery_read_instances_staging_table, # includes project.dataset.table without bq://
        bigquery_read_instances_query,
        timeout)

    validate_staging_against_featurestore(
        feature_store_location,
        feature_store_name,
        feature_store_project_id,
        features_dict,
        entity_type_cols,
        bigquery_read_instances_query
    )

    export_features_to_bq(
        feature_store_location,
        feature_store_name,
        feature_store_project_id,
        bigquery_read_instances_staging_table,
        bigquery_features_export_table_uri,
        pass_through_cols,
        features_dict,
        timeout
    )



