import cv2
import numpy as np
import serial.tools.list_ports
import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPalette, QColor, QPixmap, QImage
from db_connect import db_connect
from PyQt6.QtCore import QThread, pyqtSignal, QSize
from pyzbar.pyzbar import ZBarSymbol, decode
from PyQt6.QtWidgets import QMessageBox
from printqrcode import QRCodePrinter


class CameraThread(QThread):
    frameSignal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

    def run(self):
        # 鏡頭選擇
        cap = cv2.VideoCapture(1)
        while True:
            ret, frame = cap.read()
            if not ret:
                print("無法接收畫面。正在退出...")
                break

            self.frameSignal.emit(frame)
        cap.release()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 檢測QRcode
        self.previousBarcodeData = ''

        # 資料庫連線物件
        self.db = db_connect(host='13.112.88.211', user='readonly_test', password='2WSX^yhn9ol>', database='alpha_user')
        self.db.connect()

        # 左半部
        # 相機嵌入框畫面
        self.cameraLabel = QLabel("")
        self.cameraLabel.setStyleSheet("border: 2px dotted gray;")

        # 右半部
        # 是否離線核銷
        self.offlineLabel = QLabel("核銷方式:")
        self.offlineCombobox = QComboBox()
        self.offlineCombobox.addItem("請選擇是否離線核銷")
        self.offlineCombobox.addItem("Yes", 1)
        self.offlineCombobox.addItem("No", 0)

        # 設備選單
        self.deviceLabel = QLabel("裝置綁定:")
        self.deviceNameLabel = QLabel("")
        self.deviceCombobox = QComboBox()
        self.deviceCombobox.addItem("請選擇掃描裝置", -1)

        # 會員 & 活動資訊
        self.memberLabel = QLabel("Member:")
        self.memberNameLabel = QLabel("")
        # self.activityLabel = QLabel("Activity:")
        # self.activityCombobox = QComboBox()
        # self.activityCombobox.addItem("Please scan member first")
        # self.activityCombobox.setEnabled(False)

        self.printButton = QPushButton("Print")
        self.printButton.setEnabled(False)  # 初始狀態設為不可用

        # Layout
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.cameraLabel)

        rightLayout = QFormLayout()
        rightLayout.addRow(self.offlineLabel, self.offlineCombobox)
        rightLayout.addRow(self.offlineCombobox)
        rightLayout.addRow(self.deviceLabel, self.deviceNameLabel)
        rightLayout.addRow(self.deviceCombobox)
        
        # 排版用間隔
        # rightLayout.addRow(QLabel(""))
        # rightLayout.addRow(QLabel(""))
        # rightLayout.addRow(QLabel(""))
        # rightLayout.addRow(QLabel(""))

        # 會員 & 活動資訊
        rightLayout.addRow(self.memberLabel, self.memberNameLabel)

        # 目前採自動列印
        # rightLayout.addRow(self.activityLabel, self.activityCombobox)
        # rightLayout.addRow(self.printButton)

        mainLayout = QHBoxLayout(self)
        mainLayout.addLayout(leftLayout, 3)
        mainLayout.addLayout(rightLayout, 1)

        # 設置樣式
        self.setStyles()
        self.setStyleSheet("""
            QWidget {
                background-color: #282828;
            }
            QLabel {
                color: #D7D7C6;
            }
        """)

        self.setWindowTitle("QR Code Scanner")
        self.setGeometry(100, 100, 1030, 500)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumSize(QSize(640, 480))
        self.image_item = self.scene.addPixmap(QPixmap())

        # 啟動相機線程
        self.cameraThread = CameraThread()
        self.cameraThread.frameSignal.connect(self.
        updateCameraView)

        self.checkUsbLink()

        # 讀取綁定裝置資料
        self.devices = self.db.getDevices()
        self.devices = {device['id']: device for device in self.devices}

        self.printer = QRCodePrinter(self.usbDviceResult.device)
        # 選擇綁定裝置
        self.selectedDevice = ''
        # 裝置綁定的活動
        self.bindTicket = ''

        for deviceID, deviceInfo in self.devices.items():
            self.deviceCombobox.addItem(deviceInfo['name'], deviceID)

        # 設備選單異動觸發事件
        self.deviceCombobox.currentIndexChanged.connect(self.deviceChanged)

    def updateCameraView(self,frame):

        result = self.decoder(frame)
        if result:
            member = self.db.getMember(result)
            if member:
                self.memberNameLabel.setText(member['name'])

                if self.bindTicket != '':
                    # 根據member&device綁定的ticket_id 檢查 new_ticket_sign是否有會員報名的活動
                    ticketCheckResult = self.db.getMemberTickets(member['id'], self.bindTicket)

                    # 如果有報名活動異動報名狀態 new_ticket_checkin insert


                    # 根據檢查結果來取得活動banner圖檔並應出
                    if ticketCheckResult:
                        uniqueTicketIDs = set()

                        for res in ticketCheckResult:
                            ticket_id = res.get('ticket_id')
                            if ticket_id is not None:
                                uniqueTicketIDs.add(ticket_id)

                                ticketID = ','.join(map(str, uniqueTicketIDs))

                    # 取得圖檔
                    if ticketID != '':
                        imageData = self.db.getTicketBanner(ticketID)

                        # 整理 imageData 
                        if imageData:
                            imageUrls = [f"https://dykt84bvm7etr.cloudfront.net/uploadfiles/{item['exhibit_id']}/{item['image']}" for item in imageData]

                            # 列印票券
                            self.printer.printTickets(member, imageUrls)
                else:
                    print("No ticket found!")

            # members_with_qr = [member for member in self.members if member['qr_code'] == result]
            # print(members_with_qr)


        # 在相機標籤中顯示畫面
        frame = cv2.resize(frame, (640, 480))
        height, width, channel = frame.shape
        bytesPerLine = channel * width
        qImage = QImage(frame.data, width, height, bytesPerLine, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImage)
        self.cameraLabel.setPixmap(pixmap)

        
    def decoder(self, image):
        try:
            grayImg = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            barcode = decode(grayImg, symbols=[ZBarSymbol.QRCODE])

            if barcode:
                for obj in barcode:
                    points = obj.polygon
                    (x,y,w,h) = obj.rect
                    pts = np.array(points, np.int32)
                    pts = pts.reshape((-1, 1, 2))
                    cv2.polylines(image, [pts], True, (0, 255, 0), 3)

                    barcodeData = obj.data.decode("utf-8")
                    barcodeType = obj.type
                    string = "Data: " + str(barcodeData) + " Type: " + str(barcodeType)
                    
                    cv2.putText(image, string, (x,y), cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255), 2)
                # 檢查是否為新的 QR 碼
                if barcodeData != self.previousBarcodeData:
                    self.previousBarcodeData = barcodeData  # 更新先前檢測到的 QR 碼資料
                    return barcodeData

        except Exception as e:
            print(e)

    def setStyles(self):
        # 設定暗色系 Gruvbox 顏色主題
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(40, 40, 40))  # 背景色
        palette.setColor(QPalette.ColorRole.WindowText, QColor(235, 219, 178))  # 前景色
        palette.setColor(QPalette.ColorRole.Button, QColor(94, 60, 59))  # 按鈕背景色
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(235, 219, 178))  # 按鈕前景色
        self.setPalette(palette)

    def deviceChanged(self, index):
        deviceId = self.deviceCombobox.itemData(index)
        if deviceId != -1:
            deviceName = self.deviceCombobox.currentText()

            offlineValue = self.offlineCombobox.currentData()

            # 顯示對話框
            msgBox = QMessageBox()
            msgBox.setIcon(QMessageBox.Icon.Information)
            msgBox.setWindowTitle("Device Information")

            if offlineValue == 1:
                offlineSelected = '離線核銷'
            else :
                offlineSelected = '線上核銷'

            msgBox.setText(f"核銷方式: {offlineSelected}\nDevice ID: {deviceId}\nDevice Name: {deviceName}\n\nPLEASE WAIT CAMERA OPEN.")
            msgBox.exec()

            self.selectedDevice = deviceId
            self.bindTicket = self.devices.get(deviceId)['ticket_id']
            '''
            # 離線版本, 取得deivce_id後直接撈會員資料
            ticketBindDevicesID = self.devices.get(deviceId)['ticket_id']

            # 取得會員數據
            self.members = self.db.getMembersByTicketID(ticketBindDevicesID)

            '''
            self.deviceNameLabel.setText(f"{deviceName}")
            # 啟動相機線程
            self.cameraThread.start()
        else:
            self.deviceNameLabel.clear()

        self.printButton.setEnabled(deviceId != -1)  # 如果有選擇設備，啟用列印按鈕


    # USB設備連線檢查
    def checkUsbLink(self):
        target_vid = 0x22A0
        target_pid = 0x000A

        self.usbDviceResult = self.checkUsbDevice(target_vid, target_pid)
        if self.usbDviceResult:
            QMessageBox.information(self, "info", "WP-720 已連接")
        else:
            QMessageBox.critical(self, "Error", "WP-720 未連接，請先連接設備!")
            sys.exit()

    def checkUsbDevice(self, vid, pid):
        target_hwid = f"VID:PID={vid:04X}:{pid:04X}"
        
        for port in serial.tools.list_ports.comports():
            if target_hwid in port.hwid:
                return port
        return False

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

