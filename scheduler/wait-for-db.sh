#!/bin/sh

echo "Waiting for MySQL to be ready at host '$1' with user '$MYSQL_USER'..."

while ! mysqladmin ping -h"$1" --silent --connect-timeout=2 --user="$MYSQL_USER" --password="$MYSQL_PASSWORD"; do
  echo "MySQL is not ready yet..."
  sleep 2
done

echo "MySQL is ready - launching app"
exec "${@:2}"

