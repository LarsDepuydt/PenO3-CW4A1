# Networking protocols/methods to send images/video stream between Raspberry Pi's and another device

To research:
* Socket
* XMODEM / YMODEM / ZMODEM
* ImageZMQ
* MQTT
* RabbitMQ
* AMQP
* ROS
* ZEROMQ

## ImageZMQ:
'imageZMQ is a set of Python classes that transport OpenCV images from one computer to another using PyZMQ messaging' [1]

## PyZMQ
'This package contains Python bindings for ØMQ' [2]

## ØMQ
'ZeroMQ (also known as ØMQ, 0MQ, or zmq) looks like an embeddable networking library but acts like a concurrency framework. 
It gives you sockets that carry atomic messages across various transports like in-process, inter-process, TCP, and multicast.' [3]


PyZMQ with ImageZMQ seems to check all the boxes for what we need in a networking libary.
* Fast, to enable a low-latency real-time video mode and high bandwith image/video transfer
* Seemless integration with Python



References:

https://github.com/prakhar308/message-queues-in-python [1]
https://pypi.org/project/pyzmq/ [2]
https://github.com/jeffbass/imagezmq [3]


