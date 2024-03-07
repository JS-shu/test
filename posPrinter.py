import io
import requests

from escpos.printer import Serial
from PIL import Image
from PyQt6.QtCore import QThread, pyqtSignal


class PrintThread(QThread):
    finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

    def run(self):
        self.parent.printer.printTickets('offline', self.member, self.outPutData)
        self.printType = None
        self.member = None
        self.outPutData = []
        self.finished.emit()


class QRCodePrinter:
    def __init__(self, port):
        self.ser = Serial(port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1.00, dsrdtr=True)

    def checkPrinterPaper(self):
        status = self.ser.paper_status()
        return status

    def printTickets(self, mode, member=False, datas=[]):
        for data in datas:
            if member :
                self.printMember(member)
            if mode == 'online':
                self.printQrCodeOnline(data)
            else:
                self.printQrCodeOffline(data)

    def printMember(self, member):
        self.ser.set_with_default(align="left", font='a', width=1, height=1, custom_size=1)
        self.ser._raw(f"會員: {member['name']}\n\n".encode('big5'))

    def printQrCodeOnline(self, url):
        # 下載 QR 碼圖片
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        response = requests.get(url, headers=headers)

        # 檢查是否成功取得圖片
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))

            # 最長長度設置
            paper_width = 255

            # 計算縮放比例
            scale_factor = min(paper_width / img.height, 1.0)

            # 調整圖片大小以保持原始寬高比例，並確保寬度不超過80mm
            new_img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.LANCZOS)

            # 設定打印機參數（可以根據需要進行調整）
            self.ser.image(new_img)
            self.ser.cut(mode='PART')

        else:
            print(f"Failed to fetch image. Status code: {response.status_code}")

    def downloadImages(self, url):
        # 下載 QR 碼圖片
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        response = requests.get(url, headers=headers)

        # 檢查是否成功取得圖片
        if response.status_code == 200:
            img = Image.open(io.BytesIO(response.content))

            # 最長長度設置
            paper_width = 255
            # 計算縮放比例
            scale_factor = min(paper_width / img.height, 1.0)
            # 調整圖片大小以保持原始寬高比例，並確保寬度不超過80mm
            new_img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.LANCZOS)

            return new_img

    def printQrCodeOffline(self, data):
        try:
            for d in data:
                if d['image'] != '':
                    self.ser.image(d['image'], center=True)
                self.ser.set_with_default(align="center",width=d['fontSize'], height=d['fontSize'], custom_size=d['fontSize'])
                if d['text'] != '':
                    self.ser._raw('\n'.encode('big5'))
                    self.ser._raw(f"{d['text']}\n".encode('big5'))

                self.ser.cut(mode='PART')
        except Exception as e:
            print(f"An exception occurred: {e}")
            return False
