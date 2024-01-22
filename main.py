import cv2, numpy as np, sys, traceback

from db_connect import db_connect
from datetime import datetime
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget
from pyzbar.pyzbar import ZBarSymbol, decode
from posPrinter import QRCodePrinter

from ui import Ui_MainWindow
from cameraDetect import CameraDetect
from customMsgBox import CustomMsgBox
from topLinkIntranet import TopLinkIntranet
from usbDeviceCheck import UsbDeviceCheck


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 離線核銷會員紀錄
        self.offlineCheckedMember = []
        # 核銷選擇紀錄
        self.firstOfflineSelection = True
        # 已核銷的離線資料
        self.offlineCheckInRow = 0
        # 待核銷的離線資料
        self.offlineCheckinData = {}
        # 前張QRcode
        self.previousBarcodeData = ''
        # 選擇綁定裝置
        self.selectedDevice = ''
        # 裝置綁定的活動
        self.bindTicket = ''
        # 核銷機制
        self.offlineValue = None
        # 會員電話綁No
        self.getMemberPhoneBindMemberNo = None

        # GUI 介面設定
        self.ui = Ui_MainWindow()
        self.ui.guiSetting(self)

        # 自訂錯誤訊息框
        self.customMsgBox = CustomMsgBox(self)

        # 資料庫連線
        self.db = db_connect(self)
        self.db.connect()

        # 相機裝置檢測
        self.cameraDetect = CameraDetect(self)
        self.cameraDetect.cameraInit()

        # USB設備連線檢查
        self.usbDeviceCheck = UsbDeviceCheck(self)
        self.usbDeviceCheck.checkUsbLink()

        # 讀取綁定裝置資料
        self.deviceInit()

        # 核銷機制異動觸發事件
        self.ui.offlineCombobox.currentIndexChanged.connect(self.offlineChanged)
        self.ui.inputButton.clicked.connect(self.onInputButtonClicked)

        # 定時器
        self.timerInsertCheckinData = QTimer(self)
        self.timerInsertCheckinData.timeout.connect(self.insertCheckinData)

        # toplink Intranet response
        self.intranetTest = TopLinkIntranet(self)

    def offlineChanged(self, index):
        selectedOfflineOption = self.ui.offlineCombobox.itemData(index)
        
        if not self.firstOfflineSelection and selectedOfflineOption != self.offlineValue:
            self.customMsgBox.show("Warning", "已異動離線機制, 程式將關閉!")
            sys.exit()
        self.firstOfflineSelection = False

    def printerPapperCheck(self):
        # 檢查熱感應列印機紙張
        try:
            status = self.printer.checkPrinterPaper()

            if status == 2:
                return True
            elif status == 1:
                self.customMsgBox.show("Warning", "紙張即將用盡, 請補充紙張!")
            elif status == 0:
                self.customMsgBox.show("Warning", "紙張已用盡, 請補充紙張!")
            sys.exit()
        except Exception as e:
            print(f"An exception occurred: {e}")
            traceback_str = traceback.format_exc()
            print(traceback_str)
            print(e)

    def deviceInit(self):
        self.devices = self.db.getDevices()
        self.devices = {device['id']: device for device in self.devices}

        self.printer = QRCodePrinter(self.usbDeviceCheck.usbDviceResult.device)
        self.printerPapperCheck()

        for deviceID, deviceInfo in self.devices.items():
            self.ui.deviceCombobox.addItem(deviceInfo['name'], deviceID)

        # 設備選單異動觸發事件
        self.ui.deviceCombobox.currentIndexChanged.connect(self.deviceChanged)

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
        self.ui.cameraLabel.setPixmap(rounded_pixmap)

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
                    self.ui.cameraLabel.setPixmap(rounded_pixmap)

                # 檢查是否為新的 QR 碼
                if barcodeData != self.previousBarcodeData:
                    self.previousBarcodeData = barcodeData  # 更新先前檢測到的 QR 碼資料
                    self.scan_counter = 0  # 重置
                    return barcodeData
                else:
                    self.scan_counter += 1
                    if self.scan_counter >= 100:
                        self.scan_counter = 0  # 重置
                        return barcodeData

        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e}")
            print(traceback_str)
            print(e)

    def deviceChanged(self, index):
        # deivce異動檢測
        try:
            selectedDeviceID = self.ui.deviceCombobox.itemData(index)
            self.selectedDevice = self.devices.get(selectedDeviceID)

            if selectedDeviceID != -1:
                deviceName = self.ui.deviceCombobox.currentText()
                self.offlineValue = self.ui.offlineCombobox.currentData()

                # 檢查裝置是否綁定活動
                self.bindTicket = self.devices.get(selectedDeviceID)['ticket_id']
                if self.bindTicket == '':
                    self.customMsgBox.show("Error", f"Device Name: 『{deviceName}』\n\n\n 目前未綁定活動資料。\n\n\n請先綁定活動資料再使用。")

                    self.ui.deviceCombobox.setCurrentIndex(0) # device select init
                    self.ui.deviceNameLabel.clear()
                    self.ui.deviceNameLabel.setText("     **  請重新選擇裝置  **")
                    return
                else :
                    self.ui.inputLabel.show()
                    self.ui.inputButton.show()

                    # 會員bind會員no資料
                    self.getMemberPhoneBindMemberNo = self.db.getMemberPhoneBindMemberNo(self.bindTicket)

                    if self.offlineValue != 1:
                        # 線上核銷
                        offlineSelected = '線上核銷'
                    else :
                        offlineSelected = '離線核銷'
                        self.offlineInit({'selectedDeviceID':selectedDeviceID, 'deviceName': deviceName})

                self.customMsgBox.show("Information", f"核銷方式: {offlineSelected}\nDevice ID: {selectedDeviceID}\nDevice Name: {deviceName}")
                self.ui.deviceNameLabel.setText(f"     **  {deviceName}  **")
            else:
                self.ui.deviceNameLabel.clear()
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e}")
            print(traceback_str)
            print(e)
            self.customMsgBox.show("Error", f"An exception occurred: {e}")
            self.ui.deviceNameLabel.clear()

    def onlineReimburse(self, scanResult):
        # 線上核銷
        if self.bindTicket == '':
            self.customMsgBox.show("Error", "請先綁定活動資料再使用。")
            return
        
        queryData = {
            'no' : scanResult,
            'ticketID' : self.bindTicket
        }
        member = self.db.getMemberTicketSignData(queryData)
        if not member:
            self.customMsgBox.show("Error", "查無此QRcode資料。")
            return

        # GUI 會員欄位顯示
        self.ui.memberLabel.setText("會員")
        self.ui.memberNameLabel.setText(member['name'])

        uniqueTicketIDs = set()
        checkedDatas = []

        for res in member['ticketData']:
            ticketID = res.get('ticket_id')
            ticketSignID = res.get('id')

            checkinRes = self.memberCheckIn(ticketSignID)
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
                rePrintData = {
                    'ticketID': ticketID,
                    'member': member,
                }
                checkedDatas.append(rePrintData)
                ticketID = '' # 清空票券

        if checkedDatas:
            self.customMsgBox.show("Warning", f"會員 : {member['name']} - 已核銷入場，是否需要重印票券?", checkedDatas)

        # # 取得活動票券圖檔，目前採活動banner
        if ticketID != '':
            imageUrls = self.onlinReformImageData(ticketID)
            if imageUrls:
                if (self.printerPapperCheck()):
                    self.printer.printTickets('online', member, imageUrls) # 列印票券
                print(imageUrls)

    def offlineReimburse(self, scanResult):
        # 離線核銷
        if self.bindTicket == '':
            self.customMsgBox.show("Error", "請先綁定活動資料再使用。")
            return

        memberList = self.members.get(scanResult, [])

        if len(memberList) != 0:
            imageUrls = None
            ticketID = set()
            if memberList['member_id'] in self.offlineCheckedMember:
                self.customMsgBox.show("Warning", f"會員 : {memberList['name']} - 已核銷入場，是否需要重印票券?", memberList)
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
            self.customMsgBox.show("Warning", "查無該會員資料!")

    def onlinReformImageData(self, ticketID):
        # 取得併重整圖檔資料
        imageData = self.db.getTicketBannerByID(ticketID)
        targetUrl = "https://dykt84bvm7etr.cloudfront.net/uploadfiles/"

        if imageData:
            urls = [f"{targetUrl}{data['exhibit_id']}/{data['image_pos']}" for data in imageData]        
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
            if data.get('image_pos') != '':
                pilImage = self.printer.downloadImages(f"{targetUrl}{data['exhibit_id']}/{data['image_pos']}")   
                data['pilImage'] = pilImage

        return imageData

    def insertCheckinData(self):
        # 定時插入核銷資料
        try:
            self.intranetTest.testLink()
            if not self.intranetTest.getHtmlLinkStatus:
                self.customMsgBox.show("Warning", "連線錯誤!")
            else :
                if self.offlineCheckinData and self.offlineCheckinData['ticketSignID'] != []: 
                    for ticketSignID in self.offlineCheckinData['ticketSignID']:
                        # 活動核銷
                        checkinRes = self.memberCheckIn(ticketSignID)

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
                            # print(f"remove - {ticketSignID}")
                            self.offlineCheckinData['ticketSignID'].remove(ticketSignID)
                    
                    # 顯示更新筆數與最後更新時間
                    self.ui.offlineTitleInfoLabel.setText("離線核銷")
                    self.ui.offlineInfoLabel.setText(f"已累計核銷筆數 『{self.offlineCheckInRow}』\n最後核銷時間 『{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}』")
                self.initMember()
        except Exception as e:
            self.customMsgBox.show("Warning", e)
            return False

    def initMember(self):
        # 取得會員資料及活動Banner圖檔
        try:
            self.db.disconnect()
            self.db.connect()
            self.members = self.db.getMemberSignTicketByTicketID(self.bindTicket)
            self.offlineCheckedMember = self.db.getMemberCheckIn(self.bindTicket)
        except Exception as e:
            self.customMsgBox.show("Warning", e)
            return False

    def memberCheckIn(self,ticketSignID):
        # 會員核銷
        try:
            self.db.disconnect()
            self.db.connect()
            checkinRes = self.db.memberCheckIn(ticketSignID)
            return checkinRes
        except Exception as e:
            self.customMsgBox.show("Warning", e)
            return False

    def offlineInit(self, data):
        # 離線核銷資料初始化
        try:
            self.db.disconnect()
            self.db.connect()

            # 報名會員資料
            self.members = self.db.getMemberSignTicketByTicketID(self.bindTicket)
            # 活動圖檔資料
            self.ticketBanner = self.offlineGetImage(self.bindTicket)
            # 會員登記入場資料
            self.offlineCheckedMember = self.db.getMemberCheckIn(self.bindTicket)

            # 離線核銷資料
            self.offlineCheckinData['deviceID'] = self.devices.get(data['selectedDeviceID'])['id']
            self.offlineCheckinData['deviceName'] = data['deviceName']
            self.offlineCheckinData['comment'] = '票機離線核銷'
            self.offlineCheckinData['ticketSignID'] = []

            self.intranetTest.testLink()

            # 定時器, 寫入核銷更新
            if not self.timerInsertCheckinData.isActive():
                self.timerInsertCheckinData.start(5 * 1000)
        except Exception as e:
            self.customMsgBox.show("Warning", e)
            return False

    def onInputButtonClicked(self):
        # 判斷核銷方式
        phone_number = self.ui.inputLabel.text()
        memberNo = self.getMemberPhoneBindMemberNo.get(phone_number)

        if not memberNo:
            self.customMsgBox.show("Error", "查無此號碼資料。")
            return

        if self.offlineValue:
            self.offlineReimburse(memberNo)
        else:
            self.onlineReimburse(memberNo)