FROM nodered/node-red
  
RUN npm install node-red-dashboard
RUN npm install node-red-contrib-python3-function
RUN npm install node-red-node-markdown

COPY entrypoint.sh entrypoint.sh
COPY flows.json flows.json
  
# ENTRYPOINT [ "node-red", "-u", "." ]
ENTRYPOINT [ "bash", "entrypoint.sh" ]
