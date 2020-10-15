import os
import boto3
import botocore

# TODO: When we have multiple environments
MARIADB_ENVIRONMENT = 'production'
DB_RESTORE_ENVIRONMENT = 'test'
DB_RESTORE_SERVER = 'wheatley'
DATE = '2020-10-15'
# a bit of legacy to clean up here... presently 'live' is using portal4 / portalcdn for 'portal' and 'cdn'.
# We should look to standardise this for future ease of understanding.  I sense we don't actually need the 'CDN' backup
# as it is never bootstrapped, and only used for its assets(??)
APPLICATION_LIST = ['analytics', 'portal4', 'queuerunner', 'quickquote', 'risc', 'scorecards']
ANALYTICS_DB_LIST = ['pd_2020']
BUCKET_NAME = 'vendigital-backups'
s3 = boto3.resource('s3', region_name="eu-west-2")
ssm = boto3.client('ssm', region_name="eu-west-2")


def main():
    if os.getenv('ENVIRONMENT') == 'local':
        print('Local Environment...')
        mysql_user = 'root'
        mysql_pass = 'root'
    else:
        param = ssm.get_parameter(Name='/' + MARIADB_ENVIRONMENT + '/mariadb-columnstore/admin-user', WithDecryption=True)
        mysql_user = param['Parameter']['Value']
        param = ssm.get_parameter(Name='/' + MARIADB_ENVIRONMENT + '/mariadb-columnstore/admin-pass', WithDecryption=True)
        mysql_pass = param['Parameter']['Value']

    # Retrieve backup database files
    os.system("mkdir -p data")

    ## Restoration of 'core' Databases
    s3object_list = list()
    for application in APPLICATION_LIST:
        s3_object = DB_RESTORE_ENVIRONMENT + '/' + DATE + '/' + DB_RESTORE_SERVER + '/' + application + '/' + \
                    DB_RESTORE_ENVIRONMENT + '_' + DB_RESTORE_SERVER + '_' + application + '.sql.gz'
        local_object = './data/' + application + '.sql.gz'
        s3dict = dict(
            s3_upstream=s3_object,
            s3_local=local_object,
            database_name=application
        )
        s3object_list.append(s3dict)
    for s3object in s3object_list:
        try:
            s3.Bucket(BUCKET_NAME).download_file(s3object['s3_upstream'], s3object['s3_local'])
            print("Downloaded " + s3object['s3_upstream'] + " to: " + s3object['s3_local'])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("ERROR: The object " + s3object['s3_upstream'] + " does not exist.")
                # Removing reference from list as it does not exist to process
                s3object_list.remove(s3object)
            else:
                raise
    for s3object in s3object_list:
        mysql_command = "mysql -h 127.0.0.1 -u " + mysql_user + " -p" + mysql_pass + \
                        " -e \"CREATE DATABASE IF NOT EXISTS " + s3object['database_name'] + "\";"
        os.system(mysql_command)
        cmd = "gunzip < " + s3object['s3_local'] + " | mysql -h 127.0.0.1 -u " + mysql_user + " -p" + \
              mysql_pass + " " + s3object['database_name']
        os.system(cmd)

    # Restoration of Analytics databases
    s3_analytics_object_list = list()
    for analytics_db in ANALYTICS_DB_LIST:
        s3_object = DB_RESTORE_ENVIRONMENT + '/' + DATE + '/' + DB_RESTORE_SERVER + '/analytics/' +  DB_RESTORE_ENVIRONMENT + '_' + DB_RESTORE_SERVER + '_analytics_' + analytics_db + '.sql.gz'
        local_object = './data/' + analytics_db + '.sql.gz'
        analytics_db = "analytics_" + analytics_db
        s3dict = dict(
            s3_upstream=s3_object,
            s3_local=local_object,
            database_name=analytics_db
        )
        s3_analytics_object_list.append(s3dict)
    for s3object in s3_analytics_object_list:
        try:
            s3.Bucket(BUCKET_NAME).download_file(s3object['s3_upstream'], s3object['s3_local'])
            print("Downloaded " + s3object['s3_upstream'] + " to: " + s3object['s3_local'])
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
                print("ERROR: The object " + s3object['s3_upstream'] + " does not exist.")
                # Removing reference from list as it does not exist to process
                s3_analytics_object_list.remove(s3object)
            else:
                raise
    for s3object in s3_analytics_object_list:
        mysql_command = "mysql -h 127.0.0.1 -u " + mysql_user + " -p" + mysql_pass + \
                        " -e \"CREATE DATABASE IF NOT EXISTS " + s3object['database_name'] + "\";"
        os.system(mysql_command)
        cmd = "gunzip < " + s3object['s3_local'] + " | mysql -h 127.0.0.1 -u " + mysql_user + " -p" + \
              mysql_pass + " " + s3object['database_name']
        os.system(cmd)

    # Restoration of Wordpress Database
    # Same logic, but for one-off Wordpress database (to be adjusted when there is more than one wordpress environment)
    print("Now processing Wordpress DB")
    wp_sd_object = "live/" + DATE + "/gir/webstratlive/live_gir_webstratlive.sql.gz"
    wp_local_object = './data/webstratlive.sql.gz'
    wp_database_name = 'webstrat'
    try:
        s3.Bucket(BUCKET_NAME).download_file(wp_sd_object, wp_local_object)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("ERROR: The object " + wp_sd_object + " does not exist.")
            # Removing reference from list as it does not exist to process
        else:
            raise
    mysql_command = "mysql -h 127.0.0.1 -u " + mysql_user + " -p" + mysql_pass + \
                    " -e \"CREATE DATABASE IF NOT EXISTS " + wp_database_name + "\";"
    os.system(mysql_command)
    cmd = "gunzip < " + wp_local_object + " | mysql -h 127.0.0.1 -u " + mysql_user + " -p" + \
          mysql_pass + " " + wp_database_name
    os.system(cmd)


if __name__ == '__main__':
    main()
