# WaterIoT
Project developed for the Programming for IoT course - IoT system for field watering 

Promo video: insert the link to the youtube video 

Demo video: insert the link to the youtube video
## Brief Description
The platform provides an end-users with the detail of the measurement of soil humidity and air temperature in order to check the plants and provide a remote control of the irrigator (or drip irrigation). All the interface communicates via MQTT and REST. 
Summarising, the main features it offers are:
- Remote control of irrigator (if there is one)
- Control of the humidity of the terrain
- Control of the air temperature and humidity
- End-user platform for plants healthy
- Fully docker-based with all services communicating via REST and MQTT
- Dashboards to monitor the system components


## Complete Description

The proposed IoT platform for Smart Watering follows the microservices designing pattern. It also exploits two communication paradigms: 

- publish/subscribe with MQTT protocol.
- request/response based on HTTP REST Web Services.

In this context, 14 actors have been identified and introduced in the following:

1) The Message Broker provides an asynchronous communication based on MQTT protocol.
2) The S&D Catalog acts both as a service and as a device registry system for all the actors in the system. It provides information about end-point (like REST Web Services and MQTT topics), how to access them and info about their availability (online or offline). Each actor, during its operation, should retrieve such information before using an end-point in order to be sure that the service is online and the actor is using the most updated info on how to use it.
3) The Device Config provides an HTTP Rest interface in order to set up and retrieve various configurations of the system. Moreover, it uses MQTT too in order to publish on a specific topic a new change in the configuration. The configuration stored here are, for example, the delay between a publish and another for sensors or possible thresholds for the Water Control.
4) The Water Control is the main service that performs statistics and computation over data. It’s a control strategy that manages the health of plants based on the air temperature, soil humidity and current weather. The service performs continuous evaluation about environmental conditions: by receiving periodical data from the sensors via MQTT and according with other information from other services (like Open Weather Adaptor and Device Config) provides user suggestions on actions that can be executed in order to improve the overall conditions of the soil.
5) The Thingspeak Adaptor is an MQTT subscriber that receives environmental measurements and uploads them on Thingspeak through REST Web Services.
6) Thingspeak is a third-party software (https://thingspeak.com/) that provides REST Web Services. It is an open-data platform for the Internet of Things to store, post-process and visualize data (through plots).
7) The Raspberry Pi Connector is a Device Connector that integrates into the platform raspberry pi boards. Each raspberry is equipped with temperature and humidity sensors to provide environmental information about the status of a terrain. It provides both Rest web services and an MQTT topic in order to retrieve environmental information (i.e. temperature and humidity). The rate at which information is published with MQTT is based on a value per minute that the user can configure via the Device Config service. 
8) The Arduino Pi Connector is a Device Connector that integrates into the platform Arduino boards. Each Arduino is equipped with an actuator to switch on and switch off the watering system. It provides Rest Web Services to retrieve and change the status of the watering system (on/off). It also works as an MQTT subscriber to receive actuation commands from the Device Config.
9) Open Weather Adaptor provides an HTTP REST interface in order to retrieve information from Open Weather.
10) Open Weather is a third-party software (https://openweathermap.org) that provides REST Web Services. It is an open-data platform for retrieving pieces of information about the current weather. 
11) Node-Red is a dashboard (https://nodered.org/) to retrieve data from IoT devices and visualize them exploiting the REST Web Services provided by Raspberry Pi and Arduino Connectors. It also exploits the Thinkspeak and the Open Weather Web Services to import plots about weather and environmental measurements.
12) Uptime-kuma (https://github.com/louislam/uptime-kuma) is a self-hosted monitoring tool used to monitor docker-container.
13) Telegram is a third-party software to integrate the proposed infrastructure into Telegram platform, which is a cloud-based instant messaging infrastructure. 
14) Telegram Manager provides an HTTP REST API in order to interface from the system and with the system with elegram. It retrieves measurements from IoT devices exploiting the REST Web Services provided by Raspberry Pi and Arduino Connectors. It also allows users to send actuation commands to IoT devices or to configure the system, again exploiting REST.

## Modify the Code

### Docker and Docker Compose
First is necessary to install [docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/). 

### Clone the repository

Now you can clone the repository with 

```sh
git clone https://github.com/thegabriele97WaterIoT
```

### Nodered install
We can install nodered and its library only with version > 12. This is done with the command:

```sh
sudo apt install build-essential libssl-dev
```

We take the NVM installation script from git:

```sh
curl -sL https://raw.githubusercontent.com/creationix/nvm/v0.33.2/install.sh -o install_nvm.sh
```

Start the script:

```sh
bash install_nvm.sh
```

Restart the terminal

```sh
source .bashrc
```

Install the version 12.22.10:

```sh
nvm install v12.22.10
```

With the following command you can verify the installed node version:

```sh
node -v
```

Now you can start node-red:

```sh
node-red
```

Remember to install the lib node-red-contrib-python3-function
and node-red-dashboard using the following command:

```sh
npm install node-red-dashboard
```

```sh
npm install node-red-contrib-python3-function
```

### Creating a new service
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

Then you need to add you service to the docker-compose file. Open the file ```docker-compose.yml``` inside the ```src``` folder and add your service, following the syntax of the others. Remember to change the port and assign a new one. The same port must be written in the ```setting.json``` file inside the directory of your new service. 

If you are adding a device, remember to pass through the necessary devices. 

### Adding a environment file

This is a very important step, since inside this file you will store you API keys for the service to work. This file must be called ```loadenv.sh``` and must be inside the ```src``` folder. Copy this line inside the file

```sh
export ONRASPBERRY=0
m=$(cat /sys/firmware/devicetree/base/model 2> /dev/null)
if echo $m | grep -ic "raspberry pi" > /dev/null ; then
    export ONRASPBERRY=1
fi
```

Then, after these few lines, you can add all your API keys. The format must be:

```sh
export OPENWETHERMAPAPIKEY=your_api_key
export TELEGRAMAPAPIKEY=your_api_key
...
```


### Build

To build the project, from the ```src``` directory run these commands:

```sh
source loadenv.sh
```

```sh
make
```

After that the services will be up and running. You can check the status by giving the command:

```sh
docker-compose ps
```

To check the logs of all containers use the command:

```sh
docker-compose logs
```

To check the logs of a specific container use the command:

```sh
docker-compose logs container_name
```

To follow the logs simply add ```-f``` paramenter to the previous command. 

