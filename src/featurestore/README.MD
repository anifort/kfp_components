# Features Export from Vertex Feature Store using BQ Search

This component allows you to export features from your vertex feature store based on a BQ table.

The process for exporting features is as follows:
* Create a BigQuerySource Table in BQ that contains the following information:
  * **Entity Columns:** Columns that their names match to entity types in feature store. The values of each column will be the entiy type IDs 
  * **Timestamp Column:** A column called **timestamp** of type **Timestamp**. As feature store supports point in time lookups, this column refers to the time the entity types features map to
  * **Pass Through Columns:** Columns that contain pass through values. This columns will not be processed by the features store and they will simply appear in the output table with the exported features
* Submit the BigQuerySource Table to a Batch Feature Values export job. The results will be exported at a destination table

### ! This component automates the above process ! 
The component allows you to submit a search query for an export job. It runs necessary validations and the end result is
the creation of a table with the requested features. This table can then be used for other down stream processes such as model training.


---

## The component has the following parameters



### BigQuery Parameters

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
schema. First columns before timestamp are entity type columns. The name of the entity type returned by the query should match your feature store entity name (i.e must be identical). Then you have a timestamp 
column followed by any column you want to pass through (pass through columns are ignored by feature store but appear on the export table) to the output table, such us a "label" column

example:
```SQL
SELECT p.customerID as customer, 
      p.phoneID as phone, 
      CURRENT_TIMESTAMP() as timestamp, 
      c.churn as label
            FROM `my_project.telco.phone` as p
             LEFT JOIN `my_project.telco.churn` as c ON p.customerID = c.customerID  
             WHERE p.screen_size>3
```

| customer | phone    |  timestamp | label    | 
|----------|----------|---|----------|
| id_1     | pixel 6  | 2022-02-10 23:18:21.935081 UTC  | churn    |
| id_2     | pixel 3  | 2022-02-10 23:18:21.935081 UTC  | no churn |
| id_3     | iphone 5 | 2022-02-10 23:18:21.935081 UTC  | churn    |

The above table is what will be submited to feature store for exporint features.
Therefore customer and phone should exists as entity types in the feature store


### Feature Store Parameters

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
example:
```python
{
  "customer": ["tenure", "monthly_charges", "internet_service"],
  "phone": ["battery_life","screen_size"]
}
```

#### timeout (int)
timeout for BQ opperations and feature store export job

---

## Example output

For the bigquery_read_instances_query and features_dict examples provided above, the output will look like the following table


| label    | timestamp                  | entity_type_customer | tenure | monthly_charges | internet_service | entity_type_phone | battery_life | screen_size | 
|----------|----------------------------|----------------------|--------|-----------------|------------------|-------------------|--------------|-------------|
| churn    | 2022-02-10 23:18:21.935081 UTC | id_1                 | 12     | 20.00           | yes              | pixel 6           | 48           | 6.4         |
| no churn | 2022-02-10 23:18:21.935081 UTC | id_2                 | 6      | 25.78           | yes              | pixel 3           | 36           | 5.5         |
| churn    | 2022-02-10 23:18:21.935081 UTC | id_3                 | 9      | 17.32           | no               | iphone 4          | 45           | 4           |
