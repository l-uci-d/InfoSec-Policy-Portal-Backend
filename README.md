# InfoSec Backend

make venv first using requirements.txt:

<br/>
Steps: 

```shell
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```


<br>
<br>

## Run Server:
```shell
cd InfoSecBackend
python manage.py runserver
```

<br>
<br>

<br>
<br>

# Recreate DB steps
<li> make sure to get 

`psql_infosec_db.sql`
on this repo 
<li>make sure to install psql or pgadmin

[download latest ver here](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)

the following steps will utilize psql, <b>the CLI</b>, instead of pgadmin 4
<br><br>

<li> wait for installation, and remember what you set as superuser password<br><br>
<li> add this to system variable paths (double check your version number): "C:\Program Files\PostgreSQL\18\bin" 
<br><br>
<li> open up a terminal and run this to make sure psql is installed and in PATH:

```shell
psql --version
```

<li> if there's no errors, you can now run this command on the dir with psql_infosec_db.sql:

```shell
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -v  -f .\psql_infosec_db.sql
```
<i> you will be prompted for the superuser password </i>

<li> to check if its successful, run this:
<br>

```shell
psql -h 127.0.0.1 -p 5432 -U postgres -d infosec_portal
```
(then superuser password again)
you should see this as the text cursor: <br>

`infosec_portal=#`

<br>then run:
```shell
\dt admin.*
```

<li> you can now run sql queries here (SELECT, CREATE, etc)


<br>
<br>

## After this set up, you can use these credentials in Frontend App:
<li> 

### <u> Admin</u> <br>
<b>Email </b>: juan@gmail.com <br>
<b>Password </b>: 123
<br><br>

<li> 

### <u> Employee/Staff</u> <br>
<b>Email </b>: employee@gmail.com <br>
<b>Password </b>: 123