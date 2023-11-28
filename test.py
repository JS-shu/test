import socket
import qrcode
import io
from PIL import Image

def test_conn(ip, port) :
    try:
        # qrdata = "2c648450b-15d0-3cfd-a0e6-72b875127179"
        qrdata = "Rg6Du6spoAWjDd1FA82XDQxOWhSi7AQRuWcAwjXJpwulJYRdqAWRfDoG"
        store_len = len(qrdata) + 3 # 
        store_pL = store_len % 256  # 40
        store_pH = store_len // 256 # 00

    
        # QR Code: Select the model
        modelQR = bytes([0x1D, 0x28, 0x6B, 0x04, 0x00, 0x31, 0x41, 0x32, 0x00])

        # QR Code: Set the size of module
        sizeQR = bytes([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x43, 0x8])

        # QR Code: Set error correction level to 15%
        errorQR = bytes([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x45, 0x31])

        # QR Code: Store the data in the symbol storage area
        storeQR = bytes([0x1D, 0x28, 0x6B, store_pL, store_pH, 0x31, 0x50, 0x30])
        

        # QR Code: Print the symbol data in the symbol storage area
        printQR = bytes([0x1D, 0x28, 0x6B, 0x03, 0x00, 0x31, 0x51, 0x30])
        print(storeQR.hex())

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((ip, port))
            sock.send(modelQR)
            sock.send(sizeQR)
            sock.send(errorQR)
            sock.send(storeQR)
            sock.send(qrdata.encode())
            sock.send(printQR)

            sock.send(b'\x1D\x56\x42\x00')
    except Exception as e:
        print("Error:", str(e))


ip = "10.168.168.87"
port = 9100

test_conn(ip, port)

# winpos 測試