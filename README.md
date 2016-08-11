# geolocation-dbsync-worker
ironWorker which downloads GeoLite2 City in its CSV Format from MaxMind and populate a mySQL database with the CSV file content.

#### Requirements
- [Docker Platform](https://docs.docker.com/engine/installation/#installation)
- [Iron.io CLI](http://dev.iron.io/worker/cli/)

#### Installation
```shell
bash deploy.sh --build-docker
```

#### Testing locally
Create a config.local.json file containing your DB credentials
```shell
bash deploy.sh --local
```

#### Deploy to Iron.io
1- Setup Iron.io credentials([more info.](http://dev.iron.io/worker/reference/configuration/)).
```shell
IRON_TOKEN=MY_TOKEN
IRON_PROJECT_ID=MY_PROJECT_ID
```
2- Run deployment script.
```shell
bash deploy.sh
```

#### Sample config.json and config.local.json
```json
{
  "MYSQL_USER": "<db_user>",
  "MYSQL_PASSWORD": "<db_password>",
  "MYSQL_HOST": "<db_host>",
  "MYSQL_NAME": "<db_name>",
  "MYSQL_PORT": "3306"
}
```
