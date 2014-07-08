#!/bin/bash

# Imports in data in innit_item.json in a MongoDB database called reportmap.
# To be used on the remote machine on OpenShift via SSH
mongoimport -d reportmap -c reportmap --type json --file $OPENSHIFT_REPO_DIR/init_items.json  -h $OPENSHIFT_MONGODB_DB_HOST  -u $OPENSHIFT_MONGODB_DB_USERNAME -p $OPENSHIFT_MONGODB_DB_PASSWORD

# To login in MongoDB on the remote machine do:
# mongo $OPENSHIFT_MONGODB_DB_HOST:$OPENSHIFT_MONGODB_DB_PORT/$OPENSHIFT_APP_NAME -u $OPENSHIFT_MONGODB_DB_USERNAME -p $OPENSHIFT_MONGODB_DB_PASSWORD 
