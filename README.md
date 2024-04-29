# SociaLens alpha version 1.3
## GOAL: Get to SociaLens aplha version 2.0

---
### SETUP to run the initial commit
- install Flask, Pandas
- to run the application:
-   cd into the application root folder where app.py is.
-   run the application with:
``` python3 app.py ```

### PYTHON 3.9 Please
- upgrade your python version to 3.9 please
- this will change certain things
``` python3 app.py ```
instead of 
``` python app.py ```

``` pip3 install Flask ```
instead of 
``` pip install Flask ```
- newer versions make us more pythonic

---
### USING SociaLens version 1.3
- You start off in index.html
- Click on data upload -> upload a xlsx file ("Jan-Cleaned.xlsx")
- upload a pdf file -> observe the failure message
- after uploading a file -> a list of uploaded files appears in the window
- click on Explore Data in the nav bar
- select the data set then click Explore -> you will be able to explore the raw data
- click on Descriptive Statistics in the nav bar
- select the data set -> you will be able to scroll through lists of calculated descriptive statistics
---
### TROUBLESHOOTING
- if you get an error connecting to the Flask application in chrome, flush the socket pool
- chrome://net-internals/#sockets
- if on arc -> arc://net-internals/#sockets
- click on Flush Socket Pools
- reload the application
