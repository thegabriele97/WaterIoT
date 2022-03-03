# WaterIoT
Project developed for the Programming for IoT course - IoT system for field watering 

## Requirements
First is necessary to install docker and docker-compose. Clone the repository with ```git clone https://github.com/thegabriele97/WaterIoT```.

To create a new service go into the ```src``` folder. Here you will find a Makefile, in which there are all useful commands needed to add a service and build the project. 

Nodered install
We can install nodered and its library only with version>12 so after
```sudo apt install build-essential libssl-dev```
We take the NVM installation script from git
```curl -sL https://raw.githubusercontent.com/creationix/nvm/v0.33.2/install.sh -o install_nvm.sh```
Start the script
```bash install_nvm.sh```
Restart the terminal
```source .bashrc```
Install the version 12.22.10
```nvm install v12.22.10```
If you want to verify it
```node -v```
start node-red
```node-red```
Remember to install the lib node-red-contrib-python3-function
and node-red-dashboard
### Add a new service

To add a new service use the command:

```sh
make create_service NAME=name_of_your_service
```

After that run the command: 

```sh
make genreq
```

To modify your new service go into ```src/services/name_of_your_service``` and open the file ```app.py```.

Then you need to add you service to the docker-compose file. Open the file ```docker-compose.yml``` inside the ```src``` folder and add your service, following the syntax of the others. Remember to change the port and assign a new one. 

### Build

To build the project run the command:

```
make
```

After that the services will be up and running. You can check the status by giving the command:

```
docker-compose ps
```

To check the logs use the command:

```
docker-compose logs
```

