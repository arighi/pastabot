#!/usr/bin/env python3
#
# This server needs to run on the LEGO EV3 kit with ev3dev installed (Linux)

from socket import *
from ev3dev.auto import *
from time import sleep
import json

# Check if motors are connected properly
motors = [LargeMotor(address) for address in (OUTPUT_A, OUTPUT_D)]
assert all([m.connected for m in motors]), \
    "A large motor should be connected to port A"

# Motors speed
SPEED = 400

# Motor movement
STEP = 45

# Wait motors to get in the programmed position
def wait():
    while True:
        all_done = True
        for m in motors:
            if m.state != []:
                all_done = False
        if all_done:
            return

# Initialize motors
def init():
    for m in motors:
        m.run_to_abs_pos(speed_sp=SPEED, position_sp=0)
    wait()

# Do a single movement
def single_move():
    motors[0].run_to_abs_pos(speed_sp=SPEED, position_sp=STEP, stop_action="brake")
    motors[1].run_to_abs_pos(speed_sp=SPEED, position_sp=-STEP, stop_action="brake")
    wait()

    motors[0].run_to_abs_pos(speed_sp=SPEED, position_sp=-STEP, stop_action="brake")
    motors[1].run_to_abs_pos(speed_sp=SPEED, position_sp=STEP, stop_action="brake")
    wait()

# Move the robot
def move():
    init()
    for i in range(5):
        single_move()
    init()

# Say a message using espeak
def say(msg):
    Sound.speak(msg, espeak_opts="-a 200").wait()

def main():
    # Initialize motors
    for m in motors:
        m.reset()
        m.stop()

    # Create a TCP/IP socket
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

    # Bind the socket to the port
    server_address = ('0.0.0.0', 3636)
    sock.bind(server_address)

    print('server ready')
    while True:
        message, address = sock.recvfrom(4096)
        client_ip = address[0]
        print('%s: %s' %(client_ip, message))
        if message == b'HELLO':
            sock.sendto(b'ACK', address)
        elif message == b'MOVE':
            move()
        else:
            say(message.decode('utf-8'))

if __name__ == '__main__':
    main()
