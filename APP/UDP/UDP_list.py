import socket

# UDP-Socket recive
IPAddr = "0.0.0.0"
UDP_PORT = 27299

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Set timeout of 0.1 seconds
sock.settimeout(0.1)

try:
    # Bind the socket once, outside the loop
    sock.bind((IPAddr, UDP_PORT))
    print(f"Listening for UDP packets on {IPAddr}:{UDP_PORT}")
except Exception as e:
    print(f"Fehler beim Binden: {e}")
    exit()

while True:
    try:
        # Receive data from the socket
        data, addr = sock.recvfrom(1024)
        print(f"Von {addr} empfangen: {data.decode('utf-8').strip()}")
        break
    except socket.timeout:
        print("Timeout – kein Paket empfangen.")
    except Exception as e:
        print(f"Anderer Fehler: {e}")
