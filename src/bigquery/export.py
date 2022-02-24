from kfp.v2.dsl import (
    component,
    Output,
    Dataset
)

@component(
    packages_to_install=["google-cloud-bigquery==2.24.1"]
)
def bq_export(
        bq_uri: str,
        project: str,
        location: str, # location of extract job - must match location of dataset
        gcs_uri: str,
        exported_dataset: Output[Dataset]
) -> None:

    from google.cloud import bigquery
    import logging

    if gcs_uri.endswith('/'):
        gcs_uri = gcs_uri[:-1]

    if bq_uri.startswith('bq://'):
        bq_uri = bq_uri[5:]

    bq_project_id, bq_dataset_id, bq_table_id = bq_uri.split('.')

    dataset_ref = bigquery.DatasetReference(bq_project_id, bq_dataset_id)
    table_ref = dataset_ref.table(bq_table_id)

    exported_dataset.uri = gcs_uri

    destination_uris = ["{}/{}".format(exported_dataset.uri, "data2_*.csv")]

    client = bigquery.Client(project=bq_project_id)

    extract_job = client.extract_table(
        source= table_ref,
        destination_uris=destination_uris,
        project=project,
        location=location
    )  # API request

    extract_job.result()  # Waits for job to complete.

    # TODO: Check that job did not error

    logging.info(
        "Exported {}:{}.{} to {}".format(
            bq_project_id,
            bq_dataset_id,
            bq_table_id,
            exported_dataset.uri)
    )
    return None