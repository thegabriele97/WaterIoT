# WaterIoT
Project developed for the Programming for IoT course - IoT system for field watering 

## Requirements
First is necessary to install docker and docker-compose. Clone the repository with ```git clone https://github.com/thegabriele97/WaterIoT```.

To create a new service go into the ```src``` folder. Here you will find a Makefile, in which there are all useful commands needed to add a service and build the project. 

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


### Build

To build the project run the command:

```
make
```

