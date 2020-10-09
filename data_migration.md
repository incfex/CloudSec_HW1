# Migrating Data

## Plan

1. Login to the first user.
2. Query all the events have their ancestor being ROOT.
3. For each event queried, put it back into database with ancestor being the user.
4. Delete the events that ancestors are ROOT from the database.


## Execution

1. An link '/migrate' is created to process the migration, code in `main.py`.
2. In production env, go to `address/migrate`, login using the first user.
3. After server finished migration, go to index and check the events.
4. Login to another user, and check that old events are not showing up.
5. All clear.


# Write-Up

## A user desires to change their username
In the database, instead of using username as identity of user, use randomly generated UUID as the identity of user. Thus, change username is easily achieved by updating a field in database. Recall previous tokens. No data migration required.

## A user desires to change their password
Same as above, change the password hash field in database. Recall previous token. No data migration required.

## A user desires to delete their account and all associated data
Same as above. Only keep UUID of the user in the database in case of duplication. Delete all other fields including username, password, events. Recall previous tokens. No data migration required.

## A user loses their password
This will need additional information from user when registering, e.g. email address and security question. With email address, and security question stored in database encrypted; security question answer stored in database encrypted and stretched. User can only reset their password through email. Recall previous tokens. No data migration required.

## A user has their password stolen and used by someone else
Users can go through previous mentioned `forgot password` procedure to reset their password, since security question and answer cannot be get through website. Recall previous tokens. No data migration required.


## Learnt
How to login page works.

## Surprise
Need to stretch the password before storing it.

## Seems easy
Storing data and query them from the database.

## Actually easy
Stretch password, since there are libraries to use.