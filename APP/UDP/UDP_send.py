import socket
import time

def send_data():
    # Ziel-IP-Adresse und Port (muss mit dem Listener übereinstimmen)
    UDP_IP = "127.0.0.1"
    UDP_PORT = 27299

    # Die Nachricht, die gesendet werden soll (z.B. eine Liste von Zahlen)
    message = "janein"

    # UDP-Socket erstellen
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        while True:
            # Nachricht codieren und senden
            sock.sendto(message.encode("utf-8"), (UDP_IP, UDP_PORT))
            print(f"Gesendet: {message}")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Senden abgebrochen.")
    finally:
        sock.close()

if __name__ == "__main__":
    send_data()
