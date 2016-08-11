# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, "packages")

import sys
import os
import json
import time
import requests
import magic
import zipfile

# SQL
from elixir import *
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine, UniqueConstraint
from sqlalchemy.schema import ThreadLocalMetaData


# --------------------
# IronWorker Settings
# --------------------

# # Get Payload
# payload_file = None
# payload = None
# env_payload_file = os.getenv("PAYLOAD_FILE")
#
# # Gets payload from enviroment variable
# if env_payload_file is not None:
#     with open(env_payload_file, "r") as f:
#         payload = json.loads(f.read())
#
# # Gets payload from passed arguments
# else:
#     for i in range(len(sys.argv)):
#         if sys.argv[i] == "-payload" and (i + 1) < len(sys.argv):
#             payload_file = sys.argv[i + 1]
#             with open(payload_file, "r") as f:
#                 payload = json.loads(f.read())
#             break


# Get Config
config_file = None
config = {}
env_config_file = os.getenv("CONFIG_FILE")

# Gets config from enviroment variable
if env_config_file is not None:
    with open(env_config_file, 'r') as f:
        config = json.loads(f.read())
# END


def get_env(key, else_val=None):
    """ Get enviroment variable if not then get value from config.json and payload.json """
    if os.getenv(key):
        return os.getenv(key)
    elif config.get(key):
        return config.get(key)
    else:
        return else_val

DOWNLOAD_FOLDER = '/worker/downloads'


# --------------------
# Setup DB connection
# --------------------
# UPC Engine
upc_engine_connection = '{engine}://{username}:{password}@{host}/{name}?charset=utf8&local_infile=1'.format(
    engine='mysql',
    username=get_env('MYSQL_USER'),
    password=get_env('MYSQL_PASSWORD'),
    host=get_env('MYSQL_HOST'),
    name='upc_engine',
    port='3306',
)


upc_engine_engine = create_engine(upc_engine_connection, echo=False)
upc_engine_session = scoped_session(
    sessionmaker(autoflush=True, bind=upc_engine_engine))
upc_engine_metadata = ThreadLocalMetaData()
upc_engine_metadata.bind = upc_engine_engine
# End


# --------
# Helpers
# --------
def download(url):
    ts = time.time()
    response = {}

    # Verify if download folder exists, if not then create folder
    if not os.path.exists(DOWNLOAD_FOLDER):
        os.makedirs(DOWNLOAD_FOLDER)

    file_name = DOWNLOAD_FOLDER + '/' + 'geolite-city-csv-{timestamp}.zip'\
        .format(timestamp=int(ts))

    r = requests.get(url, stream=True, verify=False)

    if r.status_code < 400:  # if not r.raise_for_status():
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

        file_type = magic.from_file(file_name)

        # Check if ZIP file is valid, if not then retry with a decoded URL
        if 'Zip archive data' in file_type:
            response['file_name'] = file_name

    return response
# End


def sync():
    # ---------------
    # Download Files
    # ---------------
    response = download("http://geolite.maxmind.com/download/geoip/database/GeoLite2-City-CSV.zip")  # TODO: Parse URL from config.json

    if response.get("file_name"):
        city_blocks_file_path = DOWNLOAD_FOLDER
        city_locations_file_path = DOWNLOAD_FOLDER

        with zipfile.ZipFile(response.get("file_name"), 'r') as zip_ref:
            zip_ref.extractall(DOWNLOAD_FOLDER)
            for name in zip_ref.namelist():
                if "GeoLite2-City-Blocks-IPv4.csv" in name:
                    city_blocks_file_path += "/"+name

                if "GeoLite2-City-Locations-en.csv" in name:
                    city_locations_file_path += "/"+name

    # --------------
    # Create tables
    # --------------
    with open("schemas/geo_ip_blocks.sql") as f:
        upc_engine_session.execute(f.read())
        upc_engine_session.commit()

    with open("schemas/geo_ip_locations.sql") as f:
        upc_engine_session.execute(f.read())
        upc_engine_session.commit()
    # End

    # -------------------
    # Populate DB tables
    # -------------------
    if city_blocks_file_path:
        load_city_blocks_sql = """\
        TRUNCATE geo_ip_blocks;

        LOAD DATA LOCAL INFILE '{file_absolute_path}' INTO TABLE geo_ip_blocks COLUMNS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' IGNORE 1 LINES (
        @network,
        geoname_id,
        registered_country_geoname_id,
        represented_country_geoname_id,
        is_anonymous_proxy,
        is_satellite_provider,
        postal_code,
        latitude,
        longitude,
        accuracy_radius) SET
        ip_from = INET_ATON(SUBSTRING(@network, 1, LOCATE('/', @network) - 1)),
        ip_to = (INET_ATON(SUBSTRING(@network, 1, LOCATE('/', @network) - 1)) + (pow(2, (32-CONVERT(SUBSTRING(@network, LOCATE('/', @network) + 1), UNSIGNED INTEGER)))-1));
        """.format(file_absolute_path=city_blocks_file_path)

        # Execute query and commit
        upc_engine_session.execute(load_city_blocks_sql)
        upc_engine_session.commit()

    if city_locations_file_path:
        load_city_locations_sql = """\
        TRUNCATE geo_ip_locations;

        LOAD DATA LOCAL INFILE '{file_absolute_path}' INTO TABLE geo_ip_locations COLUMNS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' IGNORE 1 LINES (
        geoname_id,
        locale_code,
        continent_code,
        continent_name,
        country_iso_code,
        country_name,
        subdivision_1_iso_code,
        subdivision_1_name,
        subdivision_2_iso_code,
        subdivision_2_name,
        city_name,
        metro_code,
        time_zone);
        """.format(file_absolute_path=city_locations_file_path)

        # Execute query and commit
        upc_engine_session.execute(load_city_locations_sql)
        upc_engine_session.commit()
    # End


    # ---------------
    # Create Indexes
    # ---------------
    try:
        upc_engine_session.execute("""\
        ALTER TABLE `geo_ip_blocks` ADD PRIMARY KEY `ip_to` (`ip_to`);
        ALTER TABLE `geo_ip_locations` ADD PRIMARY KEY `geoname_id` (`geoname_id`);
        """)
        upc_engine_session.commit()
    except Exception as err:
        print err

    # -----------------
    # Creates Function
    # -----------------
    # TODO: FIX SQL syntax on CREATE FUNCTION statement.
    # try:
    #     upc_engine_engine.execute("""DROP FUNCTION IF EXISTS `IP2Location`;""")
    #     upc_engine_session.commit()
    # except Exception as err:
    #     print err
    #
    # upc_engine_engine.execute("""\
    # DELIMITER $$
    #
    # CREATE FUNCTION `IP2Location`(`ip` varchar(50))
    #     RETURNS int(11)
    #     LANGUAGE SQL
    #     DETERMINISTIC
    #     CONTAINS SQL
    #     SQL SECURITY DEFINER
    #     COMMENT ''
    # BEGIN
    #
    # DECLARE loc_id INT;
    #
    # SELECT geoname_id INTO loc_id FROM geo_ip_blocks WHERE ip_to >= INET_ATON(TRIM(ip)) ORDER BY ip_to LIMIT 1;
    #
    # RETURN IFNULL(loc_id, 0);
    #
    # END $$
    # """)
    # upc_engine_session.commit()

if __name__ == "__main__":
    # Main function
    sync()
