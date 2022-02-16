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
        gcs_uri: str,
        exported_dataset: Output[Dataset]
) -> None:

    from google.cloud import bigquery
    import logging

    bq_project_id, bq_dataset_id, bq_table_id = bq_uri.split('.')

    dataset_ref = bigquery.DatasetReference(bq_project_id, bq_dataset_id)
    table_ref = dataset_ref.table(bq_table_id)

    exported_dataset.uri = gcs_uri

    destination_uris = ["{}/{}".format(exported_dataset.uri, "data_*.csv")]

    client = bigquery.Client(project=bq_project_id)
    print(type(client))
    extract_job = client.extract_table(
        table_ref,
        destination_uris,
        # Location must match that of the source table.
        # location="europe-west4",
    )  # API request
    print(extract_job)
    print(extract_job.result())  # Waits for job to complete.

    # TODO: Check that job did not error

    logging.info(
        "Exported {}:{}.{} to {}".format(
            bq_project_id,
            bq_dataset_id,
            bq_table_id,
            exported_dataset.uri)
    )
    return None