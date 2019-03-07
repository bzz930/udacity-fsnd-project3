# Linux Server Deployment Project

## Project Info
This is the last project of Udacity's Full Stack Web Developer Nanodegree.
The project aims to deploy the web application created in the previous project on
a real server.

To view the project, go to the IP address (or URL) provided below:

IP address: 54.212.201.124

URL: www.morejuno.com

SSH Port: 2200

## Major Configurations
**1 - Create a super user "grader" and give it key-based authentication**

Commands used:

`sudo adduser grader` - create a user (set default password to "grader")

`sudo usermod -aG sudo grader`- add grader to the sudo group which makes grader a super user

`ssh-keygen` - generate a key pair (make sure you perform this step on your local machine, not on the server)

`cat /c/Users/BZZ/.ssh/grader.pub` - read the content of the key (paste it somewhere for later use)

`cd /home/grader`
`sudo mkdir .ssh` - reate a .ssh directory under "grader"

`sudo touch .ssh/authorized_keys` - create a file called "authorized_keys" inside .ssh

`sudo nano .ssh/authorized_keys` - open the file with nano editor and paste the key in here

`sudo chmod 700 .ssh`, `sudo chmod 644 .ssh/authorized_keys` - set up permissions for the key file and the .ssh directory

`sudo nano /etc/ssh/sshd_config` and then change `PasswordAuthentication` to `No` - force key-based authentication for all users

`sudo service ssh restart` restart the sshd service

**2 - Install and configure Apache**

`sudo apt-get install apache2` - install Apache

`sudo apt-get install libapache2-mod-wsgi` - install mod-wsgi

`sudo nano /etc/apache2/sites-enabled/000-default.conf` - add `WSGIScriptAlias / /var/www/html/myapp.wsgi` right before `</VirtualHost>`

`sudo apache2ctl restart` - restart Apache

**3 - Install and configure PostgreSQL**

`sudo apt-get install postgresql` - install PostgreSQL

`sudo su - postgres` - log in as user "postgres"

`psgl` - get into PostgreSQL shell

At the PostgreSQL shell prompt:

`CREATE DATABASE catalog;` - create a database called "catalog"

`CREATE USER catalog;` - create a user named "catalog"

`ALTER ROLE catalog WITH PASSWORD 'password';` - set a password for user catalog

`GRANT ALL PRIVILEGES ON DATABASE catalog TO catalog;`- give database permission to user catalog

`\q` - quit PostgreSQL shell

`exit` - exit PostgreSQL

**4 - Install Git and clone project to server**

`sudo apt-get install git` - install Git

`cd/var/www` - cd into www directory

`sudo mkdir FlaskApp` - create a directory for the web application

`sudo git clone https://github.com/bzz930/udacity-fsnd-project3.git` - this will create a directory named "udacity-fsnd-project3" inside the "FlaskApp" directory

`sudo mv ./udacity-fsnd-project3 ./FlaskApp` - rename the directory to "FlaskApp"

`cd FlaskApp`

`sudo mv app.py __init__.py` - rename the app file so this can be executed by Python2

Edit `__init__.py` and `db_setup.py` so the database links to the PostgreSQL database just created:

Change `engine = create_engine('sqlite:///catalog.db') to engine = create_engine('postgresql://catalog:password@localhost/catalog')`

 **5 - Install pip and dependencies for the app**

 `sudo apt-get install python-pip`

 `sudo pip install -r requirements.txt`


 **6 - Initialize database and run the app**

`sudo python db_setup.py`

`sudo python db_init.py`

Now go to [54.212.201.124](54.212.201.124) and the project should be deployed and running

**7 - Configure UFW**

`sudo ufw status` - current status should be inactive

`sudo ufw default deny incoming`

`sudo ufw default deny outgoing`

`sudo ufw allow ssh`

`sudo ufw allow 2200/tcp`

`sudo ufw allow www`

`sudo ufw allow 123/udp`

`sudo ufw enable`

**8 - Change timezone to UTC**

`sudo dpkg-reconfigure tzdata` -
select "none of the above" and then select 33 UTC

## Resources

[Deploying a Flask App with Heroku](https://www.youtube.com/watch?v=5UNAy4GzQ5E)

[SSH: How to access a remote server and edit files](https://www.youtube.com/watch?v=HcwK8IWc-a8)

[Intro to TMux](https://www.youtube.com/watch?v=hZ0cUWWixqU)
