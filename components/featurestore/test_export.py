from components.featurestore import export
bigquery_location = 'EU'
bigquery_project_id = "myfirstproject-226013"
bigquery_read_instances_staging_table = "myfirstproject-226013.telco.tmp-table-v5"
bigquery_read_instances_query= """
        SELECT customerID as customer,TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)  as timestamp, Churn as label
            FROM `myfirstproject-226013.telco.churn` WHERE 1=1
        """



fs_location = 'europe-west4'
fs_project = 'myfirstproject-226013'
ffeaturestore_name = 'telco'


bq_export_table_uri="myfirstproject-226013.telco.features-table-v5"

my_features  = {'customer': ["tenure", "monthly_charges", "internet_service"]}


def test_export_to_staging():
    export.export_to_staging(
        bigquery_project_id,
        bigquery_location,
        bigquery_read_instances_staging_table,
        bigquery_read_instances_query,
        timeout=600)
    assert True


def test_validate_staging_against_featurestore():
    assert True


def test_export_features_to_bq():
    assert True


def test_export_features_from_bq_search():
    assert True

export.export_to_staging(
    bigquery_project_id,
    bigquery_location,
    bigquery_read_instances_staging_table,
    bigquery_read_instances_query,
    timeout=600)