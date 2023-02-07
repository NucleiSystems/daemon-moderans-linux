# ideas

## todays-goals

- [ ] internal p2p ecosystem for servers and clients

  - [ ] additional option for a house to be the storage medium for ipfs
  - [ ] use the apps to create a p2p network
  - [ ] Generate a key pair for each user along with keys

- [ ] index a directory of files

  - [ ] scan through a given directory and use the walking algorithm to index the files
  - [ ] u

    se the routes to dispatch the files where they belong

  - [ ] use a singular uuid to attach to files and thier folder
  - [ ] use a date, folder and uuid to create a unique identifier for each file
    - [ ] using the identifier, create a status of the folder to track the files and sync if the directory has been modified. This will be used to determine if the files need to be synced.

- [ ] add a syncing mechanism to the index

  - [ ] the directory is watched, if there are state inconsistancies
  - [ ] the targeted directories will be checked for changes and the cloud will ask for change management
  - [ ] upon change, the database will be updated and the files will be replaced
  - [ ] but the files which are deleted wont be synced and be persistant on the cloud

- [ ] add a drag and drop system for the uploads
- [ ] add a internal-virtual filesystem

  - [ ] the root of the filesystem begin in .
  - [ ] sub-directories are childs to root parent

- [ ] figure out storage format for virtual filesytem
- [ ] add request pgp signatures for files
- [ ] add firestore in flutter
- [ ] figure out auth for the frontend
- [ ] clean up exception hell in assemble_records.py
