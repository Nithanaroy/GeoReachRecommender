#Recommendation System for a Social-Spatial Graph
The aim of the project is to use a graph which has both social (people and their relations) 
and spatial (businesses with their locations) nodes and provide recommendations given a social node (a person) 
and a spatial query (a region of interest). That is, recommend restaurants for PersonA in Arizona State University.

##Specifics about this project
We use data from Yelp to create our socio-spatial graph. To perform spatial queries we use MongDB and 
Neo4J for social graph queries. Our social graph consists of users from Yelp and spatial graph consists of
businesses on Yelp. 

- There is an edge between a user node and a business node if the user added a review for that business.
- There is an edge between two user nodes if they are friends on Yelp
- There is never an edge between two businesses. They are only connected via users.

##Set Up
- Clone/Fork-Clone the repo
- Download Yelp Challenge Dataset (https://www.yelp.com/dataset_challenge)
- Import data into MongoDB and Neo4J
- Start Python Flask server
- Perform Queries!

###Import data into MongoDB and Neo4J
The data from yelp dataset has to be modified to create spatial indices in MongoDB. Use the script in
data_cleansing folder, fix_business.py to generate a json array. Made necessary changes when calling the `main()` function 
in the file. Then use `mongoimport` command to import this data into MongoDB.

`mongoimport --db yelpdata --collection business --jsonArray --file out.json`

Here I am using `yelpdata` as the database, `business` as the collection and connecting to default MongoDB server.
Now we create a `2D` index on the `loc` attribute in the `business` collection.

`db.business.createIndex({"loc":"2d"})`

Let us check if everything works by issuing a box query on `business` collection to find all businesses in Arizona State University.

`db.business.find({
    loc: { $geoWithin: { $box:  [ [ -111.9504, 33.4072 ], [ -111.8988, 33.4360 ] ] } }
})`