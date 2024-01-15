import cv2
import numpy as np
import serial.tools.list_ports, sys, traceback, requests

from db_connect import db_connect
from datetime import datetime
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QSize, Qt
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath, QFont
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QFormLayout, QGraphicsScene, QGraphicsView, QMessageBox, QPushButton, QLineEdit, QDialog
from pyzbar.pyzbar import ZBarSymbol, decode
from printqrcode import QRCodePrinter
from pygrabber.dshow_graph import FilterGraph


class CameraThread(QThread):
    frameSignal = pyqtSignal(np.ndarray)

    def __init__(self, selectedCamera):
        super().__init__()
        self.selectedCamera = selectedCamera
        self.cap = None

    def releaseCamera(self):
        if self.cap:
            self.cap.release()
            print("Camera released")

    def run(self):
        # 鏡頭選擇
        try :
            self.cap = cv2.VideoCapture(self.selectedCamera, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                raise Exception("Failed to open the second camera.")

            while True:
                ret, frame = self.cap.read()
                if not ret:
                    print("無法接收畫面。正在退出...")
                    break

                self.frameSignal.emit(frame)
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e}")
            print(traceback_str)
        finally:
            self.releaseCamera()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 鏡頭
        self.selectedCamera = 0
        # 離線核銷會員紀錄
        self.offlineCheckedMember = []
        # 核銷選擇紀錄
        self.firstOfflineSelection = True
        # 已核銷的離線資料
        self.offlineCheckInRow = 0
        # 待核銷的離線資料
        self.offlineCheckinData = {}
        # 檢測QRcode
        self.previousBarcodeData = ''
        # 選擇綁定裝置
        self.selectedDevice = ''
        # 裝置綁定的活動
        self.bindTicket = ''
        # 核銷機制
        self.offlineValue = None

        # 資料庫連線
        self.db = db_connect(host='13.112.88.211', user='readonly_test', password='2WSX^yhn9ol>', database='alpha_user')
        self.db.connect()

        # GUI 介面設定
        self.guiSetting()

        # 相機檢測
        self.cameraInit()

        # USB設備連線檢查
        self.checkUsbLink()

        # 讀取綁定裝置資料
        self.deviceInit()

        # 核銷機制異動觸發事件
        self.offlineCombobox.currentIndexChanged.connect(self.offlineChanged)

        # 相機線程
        self.cameraThread = CameraThread(self.selectedCamera)
        self.cameraThread.frameSignal.connect(self.updateCameraView)

        # 定時器
        self.timerInsertCheckinData = QTimer(self)
        self.timerInsertCheckinData.timeout.connect(self.insertCheckinData)
        
        self.timerInitMember = QTimer(self)
        self.timerInitMember.timeout.connect(self.initMember)


    def cameraInit(self):
        avalibaleCamera = self.getAvailableCamera()
        if avalibaleCamera and avalibaleCamera != []:
            index = 0
            for camera in avalibaleCamera:
                self.cameraCombobox.addItem(f"鏡頭 - {camera} - {index}", index)
                index += 1
        else :
            self.customMsgBox("Warning", "無法取得相機, 程式將關閉!")
            sys.exit()
        # 核銷機制異動觸發事件
        self.cameraCombobox.currentIndexChanged.connect(self.cameraChanged)

    def cameraChanged(self, index):
        try:
            selectedCameraOption = self.cameraCombobox.itemData(index)
            if index == 0:
                self.customMsgBox("Warning", "請選擇相機")
            else:    
                if selectedCameraOption != self.selectedCamera or self.selectedCamera == 0:
                    self.customMsgBox("Warning", f"已選擇 鏡頭-{self.cameraDevices[selectedCameraOption]}!")
                    self.selectedCamera = selectedCameraOption
            # print(f"index - {self.selectedCamera}")
            # 相機線程
            if self.cameraThread and self.cameraThread.isRunning():
                self.cameraThread.frameSignal.disconnect()
                self.cameraThread.releaseCamera()
                self.cameraThread.quit()
                self.cameraThread.wait()

            self.cameraThread = CameraThread(self.selectedCamera)
            self.cameraThread.frameSignal.connect(self.updateCameraView)
            self.cameraThread.start()
        except Exception as e:
            print(f"An exception occurred: {e}")
            traceback_str = traceback.format_exc()
            print(traceback_str)
            print(e)    

    def offlineChanged(self, index):
        selectedOfflineOption = self.offlineCombobox.itemData(index)
        
        if not self.firstOfflineSelection and selectedOfflineOption != self.offlineValue:
            self.customMsgBox("Warning", "已異動離線機制, 程式將關閉!")
            sys.exit()
        self.firstOfflineSelection = False

    def printerPapperCheck(self):
        # 檢查熱感應列印機紙張
        status = self.printer.checkPrinterPaper()

        if status == 2:
            return True
        elif status == 1:
            self.customMsgBox("Warning", "紙張即將用盡, 請補充紙張!")
        elif status == 0:
            self.customMsgBox("Warning", "紙張已用盡, 請補充紙張!")
        sys.exit()

    def deviceInit(self):
        self.devices = self.db.getDevices()
        self.devices = {device['id']: device for device in self.devices}

        self.printer = QRCodePrinter(self.usbDviceResult.device)
        self.printerPapperCheck()

        for deviceID, deviceInfo in self.devices.items():
            self.deviceCombobox.addItem(deviceInfo['name'], deviceID)

        # 設備選單異動觸發事件
        self.deviceCombobox.currentIndexChanged.connect(self.deviceChanged)

    def guiSetting(self):
        self.QMessageStyle = """
            background-color: #504945;
            color: #ebdbb2;
            font-family: 'GenSenRounded JP';
            font-size: 20px;
            font-weight: 500;
        """

        # 字型
        self.labelTitleFont = QFont('GenSenRounded JP', 18)
        self.labelFont = QFont('GenSenRounded JP', 14)

        # 左半部
        # 相機嵌入框畫面
        self.cameraLabel = QLabel("")
        self.cameraLabel.setStyleSheet("border: 2px dashed #fb4934; border-radius: 10px;")

        # 右半部
        # 離線核銷更新資訊
        self.offlineTitleInfoLabel = QLabel("")
        self.offlineInfoLabel = QLabel("")
        self.offlineTitleInfoLabel.setFont(self.labelTitleFont)
        self.offlineInfoLabel.setFont(self.labelTitleFont)
        self.offlineTitleInfoLabel.setStyleSheet("color: #d79921;font-size: 18px;")
        self.offlineInfoLabel.setStyleSheet("color: #d79921;font-size: 18px;")

        # 鏡頭選擇
        self.cameraTitleLable = QLabel("鏡頭")
        self.cameraInfoLabel = QLabel("")
        self.cameraCombobox = QComboBox()
        self.cameraCombobox.addItem("請選擇鏡頭", -1)
        self.cameraTitleLable.setFont(self.labelTitleFont)
        self.cameraInfoLabel.setFont(self.labelFont)
        self.cameraCombobox.setFont(self.labelFont)

        # 是否離線核銷
        self.offlineLabel = QLabel("核銷方式")
        self.offlineCombobox = QComboBox()
        self.offlineCombobox.addItem("請選擇是否離線核銷")
        self.offlineCombobox.addItem("Yes", 1)
        self.offlineCombobox.addItem("No", 0)
        self.offlineLabel.setFont(self.labelTitleFont)
        self.offlineCombobox.setFont(self.labelFont)

        # 設備選單
        self.deviceTitleLabel = QLabel("裝置綁定")
        self.deviceNameLabel = QLabel("")
        self.deviceCombobox = QComboBox()
        self.deviceCombobox.addItem("請選擇掃描裝置", -1)

        self.deviceTitleLabel.setFont(self.labelTitleFont)
        self.deviceNameLabel.setFont(self.labelFont)
        self.deviceNameLabel.setStyleSheet("color: #fb4934;font-size: 22px")
        self.deviceCombobox.setFont(self.labelFont)

        # 會員 & 活動資訊
        self.memberLabel = QLabel("")
        self.memberNameLabel = QLabel("")
        self.memberLabel.setFont(self.labelTitleFont)
        self.memberNameLabel.setFont(self.labelFont)

        # Layout
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.cameraLabel)
        rightLayout = QFormLayout()

        rightLayout.addRow(self.offlineTitleInfoLabel, self.offlineInfoLabel)

        # 鏡頭
        rightLayout.addRow(self.cameraTitleLable, self.cameraInfoLabel)
        rightLayout.addRow(self.cameraCombobox)
        rightLayout.addRow(QLabel(""), QLabel("")) # 排版

        # 離線核銷更新資訊
        rightLayout.addRow(self.offlineLabel, self.offlineCombobox)
        rightLayout.addRow(self.offlineCombobox)
        rightLayout.addRow(QLabel(""), QLabel("")) # 排版

        # 裝置綁定
        rightLayout.addRow(self.deviceTitleLabel, self.deviceNameLabel)
        rightLayout.addRow(self.deviceCombobox)
        rightLayout.addRow(QLabel(""), QLabel("")) # 排版

        # 會員 & 活動資訊
        rightLayout.addRow(self.memberLabel, self.memberNameLabel)

        mainLayout = QHBoxLayout(self)
        mainLayout.addLayout(leftLayout, 3)
        mainLayout.addLayout(rightLayout, 1)

        # 設置樣式
        self.setStyleSheet("""
            background-color: #504945;
            color: #ebdbb2;
        """)

        self.setWindowTitle("QR Code Scanner")
        # 起始座標大小
        self.setGeometry(100, 100, 1220, 500)
        
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumSize(QSize(640, 480))
        self.image_item = self.scene.addPixmap(QPixmap())

    def createRoundedPixmap(self, pixmap):
        # 圓角畫面
        if pixmap.isNull():
            return QPixmap()

        rounded_pixmap = QPixmap(pixmap.size())
        rounded_pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded_pixmap)
        path = QPainterPath()
        path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 10, 10)
        painter.setClipPath(path)
        painter.drawPixmap(0, 0, pixmap)

        return rounded_pixmap
    
    def updateCameraView(self,frame):
        # 掃描，並執行資料驗證。 相機畫面顯示
        frame = cv2.resize(frame, (640, 480))
        height, width, channel = frame.shape
        bytesPerLine = channel * width
        qImage = QImage(frame.data, width, height, bytesPerLine, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(qImage)
        rounded_pixmap = self.createRoundedPixmap(pixmap)
        self.cameraLabel.setPixmap(rounded_pixmap)

        scanResult = self.decoder(frame)
        if scanResult:
            if self.offlineValue != 1: 
                self.onlineReimburse(scanResult)  # 線上核銷
            else :
                self.offlineReimburse(scanResult) # 離線核銷

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
                    cv2.polylines(image, [pts], True, (0, 255, 0), 2)
                    barcodeData = obj.data.decode("utf-8")
                    barcodeType = obj.type
                    string = "Data: " + str(barcodeData) + " Type: " + str(barcodeType)

                    cv2.putText(image, string, (x,y), cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255), 2)

                    # 更新cv2繪製圖檔
                    height, width, channel = image.shape
                    bytesPerLine = channel * width
                    qImage = QImage(image.data, width, height, bytesPerLine, QImage.Format.Format_RGB888).rgbSwapped()
                    pixmap = QPixmap.fromImage(qImage)
                    rounded_pixmap = self.createRoundedPixmap(pixmap)
                    self.cameraLabel.setPixmap(rounded_pixmap)

                # 檢查是否為新的 QR 碼
                if barcodeData != self.previousBarcodeData:
                    self.previousBarcodeData = barcodeData  # 更新先前檢測到的 QR 碼資料
                    return barcodeData

        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e}")
            print(traceback_str)
            print(e)

    def deviceChanged(self, index):
        # deivce異動檢測
        try:
            selectedDeviceID = self.deviceCombobox.itemData(index)
            self.selectedDevice = self.devices.get(selectedDeviceID)

            if selectedDeviceID != -1:
                deviceName = self.deviceCombobox.currentText()
                self.offlineValue = self.offlineCombobox.currentData()

                if self.offlineValue != 1:
                    # 線上核銷
                    self.bindTicket = self.devices.get(selectedDeviceID)['ticket_id']

                    offlineSelected = '線上核銷'
                else :
                    offlineSelected = '離線核銷'

                    self.bindTicket = self.devices.get(selectedDeviceID)['ticket_id']

                    self.members = self.db.getMemberSignTicketByTicketID(self.bindTicket)
                    self.ticketBanner = self.offlineGetImage(self.bindTicket)
                    self.offlineCheckedMember = self.db.getMemberCheckIn(self.bindTicket)
                    self.offlineCheckinData['deviceID'] = self.devices.get(selectedDeviceID)['id']
                    self.offlineCheckinData['deviceName'] = deviceName
                    self.offlineCheckinData['comment'] = '票機離線核銷'
                    self.offlineCheckinData['ticketSignID'] = []

                    # 定時器
                    # 寫入核銷更新
                    if not self.timerInsertCheckinData.isActive():
                        self.timerInsertCheckinData.start(15 * 1000)
                    if not self.timerInitMember.isActive():
                        self.timerInitMember.start(14 * 1000)


                self.customMsgBox("Information", f"核銷方式: {offlineSelected}\nDevice ID: {selectedDeviceID}\nDevice Name: {deviceName}\n\n\nPLEASE WAIT CAMERA OPEN.")
                self.deviceNameLabel.setText(f"     **  {deviceName}  **")
                # 啟動相機線程
                self.cameraThread.start()
            else:
                self.deviceNameLabel.clear()
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e}")
            print(traceback_str)
            print(e)
            self.customMsgBox("Error", f"An exception occurred: {e}")
            self.deviceNameLabel.clear()

    def checkUsbLink(self):
        # USB設備連線檢查(WP-720 setting)
        target_vid = 0x22A0
        target_pid = 0x000A
        self.usbDviceResult = self.checkUsbDevice(target_vid, target_pid)

        if self.usbDviceResult:
            self.customMsgBox("Information", "WP-720 已連接!")
        else:
            self.customMsgBox("Warning", "WP-720 未連接，請先連接設備!")
            sys.exit()

    def checkUsbDevice(self, vid, pid):
        target_hwid = f"VID:PID={vid:04X}:{pid:04X}"
        for port in serial.tools.list_ports.comports():
            if target_hwid in port.hwid:
                return port
        return False

    def onlineReimburse(self, scanResult):
        member = self.db.getMember(scanResult)
        if member:
            # GUI 會員欄位顯示
            self.memberLabel.setText("會員")
            self.memberNameLabel.setText(member['name'])

            if self.bindTicket != '':
                # 根據member&device綁定的ticket_id 檢查 new_ticket_sign是否有會員報名的活動
                ticketSignCheckResult = self.db.getMemberTickets(member['id'], self.bindTicket)

                # 根據檢查結果來取得活動banner圖檔並印出, 並將核銷new_ticket_sign資料進入new_ticket_checkin
                if ticketSignCheckResult:
                    uniqueTicketIDs = set()
                    checkedDatas = []
                    for res in ticketSignCheckResult:
                        ticketID = res.get('ticket_id')
                        ticketSignID = res.get('id')

                        checkinRes = self.db.checkMemberCheckIn(ticketSignID) # 核銷紀錄查詢

                        if not checkinRes:
                            insertFields = {
                                'type':0,
                                'deviceId': self.selectedDevice.get('id'),
                                'ticketSignId': ticketSignID,
                                'gateNo': self.selectedDevice.get('name'),
                                'comment': '票機線上核銷'
                            }
                            self.db.insertMemberCheckIn(insertFields)

                            if ticketID is not None:
                                uniqueTicketIDs.add(ticketID)
                                ticketID = ','.join(map(str, uniqueTicketIDs))
                        else:
                            rePrintData = {}
                            rePrintData['ticketID'] = ticketID
                            rePrintData['member'] = member
                            checkedDatas.append(rePrintData)
                            ticketID = '' # 清空票券

                    if checkedDatas:
                        # print(checkedDatas)
                        self.customMsgBox("Warning", f"會員 : {member['name']} - 已核銷入場，是否需要重印票券?", checkedDatas)

                    # 取得活動票券圖檔，目前採活動banner
                    if ticketID != '':
                        imageUrls = self.onlinReformImageData(ticketID)
                        if imageUrls:
                            if (self.printerPapperCheck()):
                                self.printer.printTickets('online', member, imageUrls) # 列印票券
                                print(imageUrls)
                else:
                    self.customMsgBox("Warning", "查無該會員資料!")
            else:
                self.customMsgBox("Warning", "查無該會員資料!")

    def offlineReimburse(self, scanResult):
        # 離線核銷，根據綁定裝置&離線核銷先取得會員名單來進行驗證
        memberList = self.members.get(scanResult, [])

        if len(memberList) != 0:
            imageUrls = None
            ticketID = set()
            if memberList['member_id'] in self.offlineCheckedMember:
                self.customMsgBox("Warning", f"會員 : {memberList['name']} - 已核銷入場，是否需要重印票券?", memberList)
            else:
                self.offlineCheckedMember.append(memberList['member_id'])
                for tsID in memberList['ticket_id']: # 每個活動組合
                    for key, value in tsID.items():
                        if value['ticket_sign_id'] not in self.offlineCheckinData['ticketSignID']:
                            self.offlineCheckinData['ticketSignID'].append(value['ticket_sign_id'])
                            ticketID.add(key)
                imageUrls = self.offlineReformImageData(ticketID)

            if imageUrls:
                if (self.printerPapperCheck()):
                    self.printer.printTickets('offline', memberList, imageUrls) # 列印票券
                    print(imageUrls)
        else:
            self.customMsgBox("Warning", "查無該會員資料!")

    def onlinReformImageData(self, ticketID):
        # 取得併重整圖檔資料
        imageData = self.db.getTicketBannerByID(ticketID)
        targetUrl = "https://dykt84bvm7etr.cloudfront.net/uploadfiles/"

        if imageData:
            urls = [f"{targetUrl}{data['exhibit_id']}/{data['image']}" for data in imageData]        
            return urls
        return False
    
    def offlineReformImageData(self, ticketID):
        # 離線活動Banner圖檔重整
        matchingData = []
        for info in self.ticketBanner:
            if info['id'] in ticketID:
                matchingData.append(info['pilImage'])
        return matchingData 

    def offlineGetImage(self, ticketID):
        # 離線活動圖檔下載
        imageData = self.db.getTicketBannerByID(ticketID)
        targetUrl = "https://dykt84bvm7etr.cloudfront.net/uploadfiles/"

        for data in imageData:
            if data.get('image') != '':
                pilImage = self.printer.downloadImages(f"{targetUrl}{data['exhibit_id']}/{data['image']}")   
                data['pilImage'] = pilImage

        return imageData
    
    def customMsgBox(self, title, text, checkedDatas = []):    
        # 自定義message box
        msgBox = QMessageBox()
        msgBox.setStyleSheet(self.QMessageStyle)
        icon_name = title.capitalize() 
        icon = getattr(QMessageBox.Icon, icon_name, QMessageBox.Icon.Information)
        msgBox.setIcon(icon)
        msgBox.setWindowTitle(f"{title}")

        # 重印詢問
        if len(checkedDatas) != 0:
            msgBox.setText(f"\n\n{text}\n\n\n\n是否重印票券\n\n")
            rePrintBtn = QPushButton("重印")
            rePrintCancleBtn = QPushButton("取消")
            msgBox.addButton(rePrintBtn, QMessageBox.ButtonRole.YesRole)
            msgBox.addButton(rePrintCancleBtn, QMessageBox.ButtonRole.NoRole)

            # 重印詢問, click觸發
            rePrintBtn.clicked.connect(lambda:self.reprintCheck(checkedDatas))
            

        msgBox.setText(f"\n\n{text}\n\n")
        msgBox.exec()

    def insertCheckinData(self):
        # 定時插入核銷資料

        # 確認連線是否正常
        if self.testLink():
            if self.offlineCheckinData and self.offlineCheckinData['ticketSignID'] != []: 
                for ticketSignID in self.offlineCheckinData['ticketSignID']:
                    # 活動核銷
                    checkinRes = self.db.checkMemberCheckIn(ticketSignID)

                    if not checkinRes:
                        insertFields = {
                            'type':0,
                            'deviceId': self.selectedDevice.get('id'),
                            'ticketSignId': ticketSignID,
                            'gateNo': self.selectedDevice.get('name'),
                            'comment': '票機離線核銷'
                        }
                        self.offlineCheckInRow += int(self.db.insertMemberCheckIn(insertFields))
                    else :
                        print(f"remove - {ticketSignID}")
                        self.offlineCheckinData['ticketSignID'].remove(ticketSignID)
                
                # 顯示更新筆數與最後更新時間
                self.offlineTitleInfoLabel.setText("離線核銷")
                self.offlineInfoLabel.setText(f"已累計核銷筆數 『{self.offlineCheckInRow}』\n最後核銷時間 『{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}』")

    def initMember(self):
        # 取得會員資料及活動Banner圖檔
        if self.testLink():
            self.members = self.db.getMemberSignTicketByTicketID(self.bindTicket)
            self.offlineCheckedMember = self.db.getMemberCheckIn(self.bindTicket)
        else:
            self.customMsgBox("Warning", "目前無連接網路，無法同步會員資料!")

    def testLink(self):
        # 測試裝置連線
        try:
            url = f"https://api.top-link.com.tw/device/Connect/test?device={self.selectedDevice.get('key', 0)}"
            response = requests.get(url)

            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            self.customMsgBox("Warning", e)
            return False

    def getAvailableCamera(self):
        # 取得可用攝影機列表，並且顯示在畫面上，並且可以選擇攝影機連線進行核銷活動
        try :
            availableCameras = []
            index = 0

            graph = FilterGraph()
            self.cameraDevices = graph.get_input_devices()

            while index < len(self.cameraDevices):
                cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
                if not cap.isOpened():
                    break
                cap.release()
                availableCameras.append(self.cameraDevices[index])
                index += 1

            return availableCameras

        except Exception as e:
            print(f"An exception occurred: {e}")
            return False

    def toggle_password(self):
        # 切換設備碼明暗碼
        current_mode = self.deviceKeyInput.echoMode()
        if current_mode == QLineEdit.EchoMode.Normal:
            new_mode = QLineEdit.EchoMode.Password
        else:
            new_mode = QLineEdit.EchoMode.Normal

        self.deviceKeyInput.setEchoMode(new_mode)

    def reprintCheck(self, checkedDatas):
        # 設備碼核對確認窗框
        self.deviceKeyInput = QLineEdit()
        self.deviceKeyInput.resize(400,20)
        self.deviceKeyInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.deviceKeyInput.setPlaceholderText("請輸入設備碼")

        toggle_button = QPushButton('Toggle Password', self)
        toggle_button.clicked.connect(self.toggle_password)

        dialog = QDialog()
        dialog.setWindowTitle('設備碼驗證')
        dialog.resize(600,300)
        dialog.setStyleSheet(self.QMessageStyle)

        # 創建一個 QVBoxLayout 佈局
        layout = QVBoxLayout(dialog)
        layout.addWidget(self.deviceKeyInput)
        layout.addWidget(toggle_button)

        okBtn = QPushButton("確定", dialog)
        okBtn.clicked.connect(dialog.accept)
        layout.addWidget(okBtn)

        cancelBtn = QPushButton("取消", dialog)
        cancelBtn.clicked.connect(dialog.reject)
        layout.addWidget(cancelBtn)

        # click觸發事件
        dialog.accepted.connect(lambda:self.acceptDialog(checkedDatas))
        dialog.rejected.connect(self.rejectDialog)
        dialog.exec()        

    def acceptDialog(self, checkedDatas):
        deviceKey = self.deviceKeyInput.text()

        if (deviceKey == self.selectedDevice.get('key')):
            if len(checkedDatas) != 0:
                if 'member_id' in checkedDatas:
                    # 離線
                    checkTicketID = checkedDatas.get('ticket_id', [])
                    if checkTicketID:
                        ticketIDs = [list(ticket.keys())[0] for ticket in checkTicketID]
                    imageUrls = self.offlineReformImageData(ticketIDs)
                    if imageUrls:
                        if (self.printerPapperCheck()):
                            self.printer.printTickets('offline', checkedDatas, imageUrls) # 列印票券
                            print(imageUrls)
                else :
                    # 線上
                    ticketIDs = [data['ticketID'] for data in checkedDatas]
                    sTicketIDs = ','.join(map(str, ticketIDs))
                    imageUrls = self.onlinReformImageData(sTicketIDs)

                    if imageUrls:
                        if (self.printerPapperCheck()):
                            self.printer.printTickets('online', False, imageUrls) # 列印票券
                            print(imageUrls)
        else:
            self.customMsgBox("Warning", "設備碼錯誤!")

    def rejectDialog(self):
        # 取消設備碼輸入
        print("Rejected")

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()

