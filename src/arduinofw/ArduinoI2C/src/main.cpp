#include <Arduino.h>
#include <Wire.h>

void onRecv(int ln) {

  while(Wire.available()) {
    char readWire= Wire.read();
    if (readWire == 0x0) {
      PORTB &= ~(1 << 5); //xxx0xxxx
      PORTB |= (Wire.read() & 0x1) << 5; 
    }
  }

}
void onReq(){
  int readValue = analogRead(A1); //read the analog value from A1 and transform it in a value of 10 bit
  Serial.println(readValue);
  Wire.write((uint8_t*)&readValue, 2); // respond with message of 10 bit

}
void setup() {
  //needed for the control of the I/O, 1 for output 0 for input 8 bit
  DDRB |= (1 << 5)|(1 << 6);
  //00110000 5 AND 6 AS OUTPUT
  Serial.begin(9600);
  Wire.begin(0x8); //slave indirizzo 8
  Wire.onReceive(onRecv);
  Wire.onRequest(onReq);
}

void loop() {
  
}