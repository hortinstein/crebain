This file contains instructions on what I am trying to accomplish to setup a testable database component for crebain

# Structure outline
- The database should be created using the latest version of pocketbase in docker
- The database should be initialized with a username set from environmental variables and should be initialized so it's not prompted via web API in the dockerfile or docker compose.  It should not use go, but should keep it to a simple shell script
```
POCKETBASE_ADMIN_EMAIL=test@pocket.co
POCKETBASE_ADMIN_PASSWORD=fuckthiswebshit
```
See the following for how to use upsert to set this up: https://github.com/pocketbase/pocketbase/discussions/5814