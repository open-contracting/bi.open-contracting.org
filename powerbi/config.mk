# The host of the project's database.
DATABASE_HOST=localhost
# The name of the project's database.
DATABASE_NAME=cardinal
# The user to update to the project's database.
DATABASE_USER=cardinal
# The user to create the DATABASE_NAME and DATABASE_USER.
MAINTENANCE_DATABASE_USER=$(whoami)
# The database to which the DATABASE_USER_MAINTENANCE connects.
MAINTENANCE_DATABASE_NAME=postgres
# The host of the project's database, from within the Docker container.
DATABASE_HOST_DOCKER=host.docker.internal
# The project's working directory.
CARDINAL_WORKDIR=/home/cardinal
