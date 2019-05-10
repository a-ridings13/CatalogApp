# Catalog Application Project

This is a python and flask web application to allow users to create items within categories and save them to an SQLite database, and also they can view other users Items that have been added. 


### Design of code:
This application utilizes the flask framework and Googles oauth2 API to allow 3rd party sign in for this application.

### How to execute:
   * First you will need to clone this repo to your local vagrant directory.
   
   Open a terminal and cd to your /vagrant directory and run the command:

    vagrant ssh
    
   Your terminal will now look like the following:

    vagrant@vagrant:$
   
   Next, cd into the /vagrant directory on vagrant box terminal.
   
    vagrant@vagrant:$ cd /vagrant
    
   Next you will need to cd into the CatalogApp directory on your vagrant machine
   
    vagrant@vagrant:/vagrant$ cd CatalogApp/

   After you have changed into this application directory you will need to create and populate the SQLite database via the following commands:
   
    vagrant@vagrant:/vagrant$ python database.py

   and:

    vagrant@vagrant:/vagrant$ python dummy.py
       
   After you have changed into this application directory you can launch this application via the following command:
   
    vagrant@vagrant:/vagrant$ python app.py
    
### Results:
    This will launch the application on your vagrant machine which you should be able to access via http://localhost:8000 or 0.0.0.0:8000

    From here you will be able to browse around the application's categories and view items that are in the database. You will also be able to login to the application using your google account. **Please note:** To login using the google sign in you will need to be at the following URL: http://localhost:8000/login

    After you have logged in successfully you will be able to create, update, and delete items of your own.
