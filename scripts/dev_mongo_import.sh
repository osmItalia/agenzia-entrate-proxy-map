#!/bin/bash

# Imports in data in innit_item.json in a MongoDB database called reportmap.
# To be used on the local machine
mongoimport -d reportmap -c reportmap --type json --file $OPENSHIFT_REPO_DIR/init_items.json  -h $OPENSHIFT_MONGODB_DB_HOST
