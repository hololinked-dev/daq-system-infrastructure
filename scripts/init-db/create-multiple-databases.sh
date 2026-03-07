#!/bin/bash

set -e
set -u

# https://github.com/mrts/docker-postgresql-multiple-databases

# MIT License

# Copyright (c) 2017 Mart Sõmermaa

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

function create_user_and_database() {
	local database=$1
	local username=$2
	local password=$3
	echo "Creating user and database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE USER $username WITH ENCRYPTED PASSWORD '$password';
	    CREATE DATABASE $database WITH OWNER $username;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $username;
		GRANT USAGE, CREATE ON SCHEMA public TO $username;
		EOSQL
	echo "User and database '$database' created"
}

if [ -n "$POSTGRES_DATABASES" ]; then
	echo "Multiple database creation requested: $POSTGRES_DATABASES"
	IFS=',' read -ra dbs <<< "$POSTGRES_DATABASES"
	IFS=',' read -ra users <<< "$POSTGRES_DATABASE_USERNAMES"
	IFS=',' read -ra pwds <<< "$POSTGRES_DATABASE_PASSWORDS"
	for i in "${!dbs[@]}"; do
		create_user_and_database "${dbs[$i]}" "${users[$i]}" "${pwds[$i]}"
	done
	echo "Multiple databases created"
fi

