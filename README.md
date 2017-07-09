# Recommendation System for a Social-Spatial Graph
The aim of the project is to use a graph which has both social (people and their relations) 
and spatial (businesses with their locations) nodes and provide recommendations given a social node (a person) 
and a spatial query (a region of interest). That is, recommend restaurants for PersonA in Arizona State University.

## Specifics about this project
We use data from Yelp to create our socio-spatial graph. To perform spatial queries we use MongDB and 
Neo4J for social graph queries. Our social graph consists of users from Yelp and spatial graph consists of
businesses on Yelp. 

- There is an edge between a user node and a business node if the user added a review for that business.
- There is an edge between two user nodes if they are friends on Yelp
- There is never an edge between two businesses. They are only connected via users.

## Set Up
- Clone/Fork-Clone the repo
- Download Yelp Challenge Dataset (https://www.yelp.com/dataset_challenge)
- Import data into MongoDB and Neo4J
- Start Python Flask server
- Perform Queries!

Before we begin,

- Rename `secrets_template.py` to `secrets.py` and fill in your values. Otherwise the code
will not run. Remember to submit this file also to your hosting server (manually if required)
as this not included as part of your GIT repo
- Include the project in `PYTHONPATH` by `export PYTHONPATH=${PYTHONPATH}:/<YOUR_PATH>`

### Import data into MongoDB and Neo4J
#### Mongo Setup

**Import Businesses**

The data from yelp dataset has to be modified to create spatial indices in MongoDB. Use the script in
data_prep folder, fix_business.py to generate a json array. Make necessary changes when calling the `main()` function 
in the file. Then use `mongoimport` command to import this data into MongoDB.

`mongoimport --db yelpdata --collection business --jsonArray --file out.json`

Here I am using `yelpdata` as the database, `business` as the collection and connecting to default MongoDB server.
Now we create a `2D` index on the `loc` attribute in the `business` collection using Mongo Command Prompt.

`db.business.createIndex({"loc":"2d"})`

Let us check if everything works by issuing a box query on `business` collection to find all businesses in Arizona State University.

`db.business.find({
    loc: { $geoWithin: { $box:  [ [ -111.9504, 33.4072 ], [ -111.8988, 33.4360 ] ] } }
})`


#### Train and Test data
We will use reviews to test the accuracy of our system. Split the review.json file which has roughly 2 million
lines/reviews into train and test data. For this you can use the script train_test_split.py in the `data_prep` folder.

#### Neo4J Setup
Use the script `import_into_neo.py` to import users, businesses, relationships among users and 
relationships between users and businesses. Change chunk size (in the `insert()` method) from 200 
to any number based on your server & network power. Start with an empty database to avoid duplicates. 


### Start Flask Server

Obtain a Google Maps API key and set its value to an environment variable, `maps_api_key`. Install required node
modules by running `npm install` in the `static/` folder.


## Tech Stack

- Python Flask, Jinja2 for Backend
- MongoDB and Neo4J Databases 
- ECMA 2015 for front end
