# Nuclei

built using Fastapi and flutter and respective extensions. 

Nuclei is a web application that allows you to upload and manage your own compressed media to increase media availability and accessibility.

Nuclei Daemon Moderans for Linux
Nuclei Daemon Moderans for Linux is an open source software that securely stores your media files using IPFS (InterPlanetary File System) with compression applied to decrease the size of the media files. It provides temporary access to the files to increase the security of the media.

Mission
The mission of Nuclei is to provide a secure and efficient way to store and access media files. By leveraging the power of IPFS and compression techniques, Nuclei aims to provide a solution that not only reduces the size of the files but also ensures the files are stored securely.

Problems solved by Nuclei
Security: Nuclei provides a secure way to store media files by using IPFS. The files are encrypted and can only be accessed by users with the appropriate permissions.
Efficiency: By applying compression techniques, Nuclei reduces the size of media files, making it faster and more efficient to store and access them.
Accessibility: Nuclei provides temporary access to media files, making it more secure by limiting the time a file is accessible.
How to run
Nuclei can be run using Docker Compose. Here are the steps to get started:

Clone the repository:
bash
Copy code
git clone https://github.com/Nuclei-Media/daemon-moderans-linux.git
Change into the cloned directory:
bash
Copy code
cd daemon-moderans-linux
Copy the .env.example file to .env:
bash
Copy code
cp .env.example .env
Modify the .env file to set your IPFS and Redis credentials:
```


