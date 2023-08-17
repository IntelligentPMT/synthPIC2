# Docker

## Rebuild

If `docker/Pipfile` changed:
1. `docker compose run app`
2. `cd docker`
3. `pipenv lock`
4. `exit`

`docker compose build`
