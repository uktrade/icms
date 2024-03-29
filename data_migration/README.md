# ICMS - Data Migration

## Environment Variables

The following environment variables must be set for the migration script to run
`ALLOW_DATA_MIGRATION` - True
`APP_ENV` - "Production"

For connection to the V1 replcica
`ICMS_V1_REPLICA_USER`, `ICMS_V1_REPLICA_PASSWORD`, `ICMS_V1_REPLICA_DSN`

## Scripts

The following three scripts are used to run the data migration.

```
python manage.py export_from_v1  # extracts the data from v1 into the data_migration models
python manage.py extract_v1_xml  # parses the data out of the xml fields in the data_migration models
python manage.py import_v1_data  # migrates the data from the data_migration models into the web models
python manage.py create_icms_groups  # creates the groups for assigning permissions
python manage.py post_migration  # post migration tasks of setting user and organisation permissions
```

The scripts run in the each data type in a set order to maintain data intgrety when creating the models. The order of the data types are listed below

1. user
2. reference
3. file
4. import_application

The commands can be run with flags to skip parts of the export where relevant
* `--batchsize` to modify the size of the batches when running the migration (default 1000)
* `--skip_ref` to skip migrating reference data
* `--skip_ia` to skip migrating import application data
* `--skip_user` to skip migrating user data
* `--skip_file` to skip migrating file data
* `--skip_task` to skip the creation of tasks (import_v1_data only)

The migration scripts can also be restarted from a specific point using the `--start` parameter in the format `--start=<data_type>.<index>`
e.g. `python manage.py export_from_v1 --start=ia.2`  will start the export from point 2 of the import_application data type

The following data_types are valid in the `--start` parameter
*  `r`, `ref` or `reference` for the reference data type
* `f` or `file` for the file data type
* `ia` or `import_application` for the import_application data type

## File Import

The following script is used to pull the file data from V1 and export into S3

```
python manage.py import_v1_files_to_s3
```
The command can be run with options
* `--batchsize` to modify the size of the batches when running the migration (default: 500)
* `--run-data-batchsize` to modify the size of the batches when periodically saving the run data to s3 (default: 100)
* `--limit` to limit the database queries to only return a set number of rows (default: None)
* `--ignore-last-run` to ignore the data in the last run json file (if present) in s3 (default: False)
* `--queries` to specify which queries to run (default: All available queries)
* `--count-only` to retrieve just the total count (and file size) of the number of files that be processed per query (default: False)

Some of the queries are smaller than others, so it is recommended the script is run as follows
```
python manage.py import_v1_files_to_s3 --queries small
python manage.py import_v1_files_to_s3 --queries sil_application_files
python manage.py import_v1_files_to_s3 --queries sps_application_files
python manage.py import_v1_files_to_s3 --queries sps_docs --limit 11000 (Run 8 times)
python manage.py import_v1_files_to_s3
```



## Deployment

Before new versions of the data migration are deployed, the database should be wiped and rolled back ready to deploy the latest version

```
python manage.py flush
python manage.py migrate data_migration zero
python manage.py migrate web zero
```