import io
from PIL import Image
from escpos.printer import Serial
import requests


class QRCodePrinter:
    def __init__(self, port):
        self.ser = Serial(port, baudrate=9600, bytesize=8, parity='N', stopbits=1, timeout=1.00, dsrdtr=True)

    def checkPrinterPaper(self):
        status = self.ser.paper_status()
        return status

    def printTickets(self, mode, member=False, urls=[]):
        if member :
            self.printMember(member)
        for url in urls:
            if mode == 'online':
                self.printQrCodeOnline(url)
            else:
                self.printQrCodeOffline(url)

    def printMember(self, member):
        self.ser._raw(f"會員: {member['name']}\n".encode('big5'))

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

    def printQrCodeOffline(self, image):
        self.ser.image(image)
        self.ser.cut(mode='PART')

# if __name__ == "__main__":
    # pass
