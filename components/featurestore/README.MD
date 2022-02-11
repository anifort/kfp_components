# Feature Store Export from BQ Search

This component allows you to export features from your features store based on a BQ table.

The process for exporting features is as follows:
* Create a BigQuerySource Table in BQ that contain the following information
  * Columns that their names correspont to an entity type in feature store. The values of each column will be the entiy type IDs 
  * A column called **timestamp** of type **Timestamp**. As feature store supports point in time lookups, this column refers to the time the entity types features map to
  * Columns that contain pass through information. This will be ignored by the feature store export job but they will be included in the exported features table
* Submit the BigQuerySource Table to a Batch Feature Values export job for a destination table

## This component automates the above process easy
The component allows you to submit a search query for an export job. It runs necessary validations and the end result is
the creation of a table with the requested features

##The component has the following parameters

#### bigquery_project_id (str)
The project id that the BigQuery source table is at

#### bigquery_location (str)
The location that the BigQuery source table is at

#### bigquery_read_instances_staging_table (str)
Staging table uri without bq://
. This table is created based on the search query and the passed into feature store export job
example: project.dataset.table 

#### bigquery_read_instances_query (str)
The query that connets entity type ids for export.
This query is flexible and the user can use it an any way for joins an filtering, as long as it matches the following
schema. First columns before timestamp are entity type columns that match your feature store. Then you have a timestamp 
column followed by any column you want to pass through variables, such us a label column\

example:
```SQL
SELECT p.customerID as customer, 
      p.phoneID as phone, 
      CURRENT_TIMESTAMP() as timestamp, 
      c.churn as label
            FROM `my_project.telco.phone` as p
             LEFT JOIN `my_project.telco.churn` as p ON p.customerID = c.customerID  
             WHERE p.screen_size>3
```

| customer | phone    |  timestamp | label    | 
|----------|----------|---|----------|
| 1        | pixel 6  | 2022-02-10 23:18:21.935081 UTC  | churn    |
| 2        | pixel 3  | 2022-02-10 23:18:21.935081 UTC  | no churn |
| 3        | iphone 5 | 2022-02-10 23:18:21.935081 UTC  | churn    |

The above table is what will be submited to feature store for exporint features.
Therefore customer and phone should exists as entity types in the feature store

#### feature_store_location (str)
region of your feature store.\
example: europe-west4

#### feature_store_name (str)
the name of your feature store

#### feature_store_project_id (str)
The project in which your feature store is set up

#### bigquery_features_export_table_uri (str)
Export table uri. This is where your features will exported to. The uri should not include bq://\
example: project.dataset.table

#### features_dict (dict)
Dictionary that contains the features you would like to retrieve for each entity type
Keys in the dictionary is entity types
Values is a list of features
\
example: \
```python
{
  "customer": ["tenure", "monthly_charges", "internet_service"]
  "phone": ["battery_life","screen_size"]
}
```

#### timeout (int)
timeout for BQ opperations and feature store export job

## Example output


| label    | timestamp                  | entity_type_customer | tenure | monthly_charges | internet_service | entity_type_phone | battery_life | screen_size | 
|----------|----------------------------|-----------------|--------|-----------------|------------------|-------------------|--------------|-------------|
| churn    | 2022-02-10 23:18:21.935081 UTC | 1           | 12     | 20.00           | yes              | pixel 6           | 48           | 6.4         |
| no churn | 2022-02-10 23:18:21.935081 UTC | 2           | 6      | 25.78           | yes              | pixel 3           | 36           | 5.5         |
| churn    | 2022-02-10 23:18:21.935081 UTC | 3           | 9      | 17.32           | no               | iphone 4          | 45           | 4           |
