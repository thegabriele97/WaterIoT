#include <Arduino.h>
#include <Wire.h>

void onRecv(int ln) {

	while(Wire.available()) {
		if (Wire.read() == 0x0) {
			PORTB &= ~(1 << 5);
			PORTB |= (Wire.read() & 0x1) << 5;
		}
	}

}

void setup() {
	DDRB |= (1 << 5);
	Wire.begin(0x8);
	Wire.onReceive(onRecv);
}

void loop() {
    
}