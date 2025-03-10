import socket
import struct
from influxdb_client import InfluxDBClient, Point, WritePrecision
from proto import communication_pb2  # Protobuf data structure

# Multicast settings
MULTICAST_GROUP = '224.0.0.1'
RECEIVE_PORT = 19900

# database settings (InfluxDB)
influx_url = "https://us-east-1-1.aws.cloud2.influxdata.com"
influx_token = "0wm-XUgGS_MHJ8wBQ5kzW56YiwMlk_IHD5UF9uqEUkBac5tyBQcfAxasVxSL8bOUfYP67T0ioN87ehJaaUmqnA=="
influx_org = "CIn"
influx_bucket = "RobotsTelemetry_db"

# Initializing the InfluxDB client
client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
write_api = client.write_api()

# Configuring a UDP socket to receive multicast
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(('', RECEIVE_PORT))

mreq = struct.pack("4sl", socket.inet_aton(MULTICAST_GROUP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    try:
        # Receiving the UDP message
        data, _ = sock.recvfrom(1024)

        # decoding the message using protobuf
        feedback = communication_pb2.Feedback()
        feedback.ParseFromString(data)

        print(f"ID: {feedback.id}")
        print(f"Battery: {feedback.battery}V | KickLoad: {feedback.kickLoad}")
        print(f"Velocity: M1:{feedback.velocity.m1}, M2:{feedback.velocity.m2}, M3:{feedback.velocity.m3}, M4:{feedback.velocity.m4}")
        print(f"Current: M1:{feedback.current.m1}, M2:{feedback.current.m2}, M3:{feedback.current.m3}, M4:{feedback.current.m4}")
        print(f"Timestamp: {feedback.timestamp}")

        point = (
            Point("robot_feedback")
            .tag("robot_id", feedback.id)
            .field("battery", feedback.battery)
            .field("kickLoad", feedback.kickLoad)
            .field("irBall", feedback.irBall)
            .field("velocity_m1", feedback.velocity.m1)
            .field("velocity_m2", feedback.velocity.m2)
            .field("velocity_m3", feedback.velocity.m3)
            .field("velocity_m4", feedback.velocity.m4)
            .field("current_m1", feedback.current.m1)
            .field("current_m2", feedback.current.m2)
            .field("current_m3", feedback.current.m3)
            .field("current_m4", feedback.current.m4)
            .time(feedback.timestamp, WritePrecision.MS)
        )
        
        # Writing the point on InfluxDB
        write_api.write(bucket=influx_bucket, org=influx_org, record=point)

        print("Data successfully sent to InfluxDB!")

    except KeyboardInterrupt:
        print("\nClosing data_transfer.py...")
        break

client.close()
sock.close()