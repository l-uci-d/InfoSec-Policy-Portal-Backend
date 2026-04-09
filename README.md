# InfoSec Backend Setup

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

## Add Users:
```shell
cd InfoSecBackend
python manage.py migrate
python manage.py create_users
```

## Run Server:
```shell
cd InfoSecBackend
python manage.py runserver
```
<br>
<hr>


## After this set up, you can use these credentials in Frontend App:
<li> 

### <u> Admin</u> <br>
<b>Email </b>: admin1@gmail.com <br>
<b>Password </b>: password123
<br><br>
<b>Email </b>: admin2@gmail.com <br>
<b>Password </b>: password123
<br><br>

<li> 

### <u> Employee/Staff</u> <br>
<b>Email </b>: staff1@gmail.com <br>
<b>Password </b>: password123
<br><br>
<b>Email </b>: staff2@gmail.com <br>
<b>Password </b>: password123
<br><br>
<b>Email </b>: staff3@gmail.com <br>
<b>Password </b>: password123
<br><br>