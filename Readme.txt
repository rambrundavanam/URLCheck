Pre Project requirement:
A. tar -xf URLCheck.tar.gz
B. "pip install virtualenv", "cd URLCheck", "virtualenv env", "source env/bin/activate"  # to not conflict with other projects

1. This application assumes the postgres database is already running so, we need to install and run the docker image for that using

docker run --name basic-postgres --rm -e POSTGRES_USER=postgres
-e POSTGRES_PASSWORD=4y7sV96vA9wv46VR -e PGDATA=/var/lib/postgresql/data/pgdata -v /tmp:/var/lib/postgresql/data
-p 5432:5432 -it postgres:14.1-alpine

2. There is a urls.txt file which contains test data
3. cd into the project root - "cd URLCheck"
4. Run "docker-compose up --build" in project root where you see docker-compose.yml
5. The docker compose with get the application up and running but we need test data in the postgres db
6. Add test data into Postgres database by running "python3 db.py", it might take a couple of minutes since it synchronous
7. Open any browser and enter https://127.0.0.1:5000/urlinfo/1/{any_url_from urls.txt} or url in this format{name.com:portnumber/query}
8. If the URL exists in the cache, it is returned from Redis cache we setup in docker compose
9. If the URL doesn't exist in the cache it will query the Postgres DB and return it, also add it to cache
10. The response format is in json like below
{
  "DECISION": "SAFE", --> Where the URL is safe to access
  "HOSTNAME": "safe.com", --> Hostname entered in the URL
  "PORT": "30026", --> Portnumber entered in the URL
  "QUERY": "YWDopsuGmAdsasa", --> Query from the URL
  "REASON": "Safe since didnt match our criteria" --> "Reason why it was decided safe or notsafe"
}

11. The decision to mark a new safe/not safe for a URL that doesn't exist in Redis cache or Postgres DB is taken as below:

If the url hostname has "harmful", "malicious", "dangerous", portnumber in range(20000-24000) or querylength > 100 it is marked "NOT SAFE"
else it is marked "SAFE" for testing purposes

12. Each subsequent request after a url is returned from DB will be returned from cache for 10 minutes, then the cache is removed.





