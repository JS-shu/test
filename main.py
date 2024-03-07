import cv2, numpy as np, sys, traceback

from dbConnect import DbConnect
from datetime import datetime
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget
from pyzbar.pyzbar import ZBarSymbol, decode

from ui import Ui_MainWindow
from cameraDetect import CameraDetect
from customMsgBox import CustomMsgBox
from posPrinter import QRCodePrinter, PrintThread
from topLinkIntranet import TopLinkIntranet
from usbDeviceCheck import UsbDeviceCheck

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        # 預載圖檔
        self.ticketBanner = None
        # Y-m-d 格式日期
        self.todayDate = datetime.today().strftime('%Y-%m-%d')
        # 圖檔下載目標URL
        self.targetUrl = "https://dykt84bvm7etr.cloudfront.net/uploadfiles/"
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

        # 紙張列印線程
        self.printThread = PrintThread(self)

        # 自訂錯誤訊息框
        self.customMsgBox = CustomMsgBox(self)

        # 資料庫連線
        self.db = DbConnect(self)
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
        frame = cv2.resize(frame, (960, 600))
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

                    self.ui.telLabel.show()
                    self.ui.telInputLabel.show()
                    self.ui.cidLabel.show()
                    self.ui.cidInputLabel.show()
                    self.ui.inputButton.show()

                    # 會員bind會員no資料
                    self.getMemberPhoneBindMemberNo = self.db.getMemberPhoneBindMemberNo(self.bindTicket)

                    # 活動圖檔資料
                    self.ticketBanner = self.getTicketImage(self.bindTicket)
                    if self.offlineValue != 1:
                        # 線上核銷
                        offlineSelected = '線上核銷'
                    else :
                        offlineSelected = '離線核銷'
                        self.offlineInit({'selectedDeviceID':selectedDeviceID, 'deviceName': deviceName})

                self.customMsgBox.show("Information", f"核銷方式: {offlineSelected}\nDevice ID: {selectedDeviceID}\nDevice Name: {deviceName}")
                self.ui.deviceNameLabel.setText(f"     **  {deviceName}  **")

                self.ui.offlineLabel.hide()
                self.ui.offlineCombobox.hide()

                self.ui.deviceTitleLabel.hide()
                self.ui.deviceCombobox.hide()
                self.ui.deviceNameLabel.hide()

                self.ui.cameraTitleLable.hide()
                self.ui.cameraCombobox.hide()
            else:
                self.ui.deviceNameLabel.clear()
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e}")
            print(traceback_str)
            self.customMsgBox.show("Error", f"An exception occurred: {e}")
            self.ui.deviceNameLabel.clear()

    def onlineReimburse(self, scanResult):
        # 線上核銷
        if self.bindTicket == '':
            self.customMsgBox.show("Error", "請先綁定活動資料再使用。")
            return

        queryData = {
            'no': scanResult,
            'ticketID': self.bindTicket
        }
        member = self.db.getMemberTicketSignData(queryData)
        if not member:
            self.customMsgBox.show("Error", "查無此QRcode資料。")
            return

        # GUI 會員欄位顯示
        self.ui.memberLabel.setText("會員")
        self.ui.memberNameLabel.setText(member['name'])

        uniqueTicketIDs = []
        rePrintTicketIDs = []

        for res in member['ticketData']:
            ticketID = res.get('ticket_id')
            ticketSignID = res.get('id')
            checkinNum = res.get('checkin_num')
            checkinNumLimitDay = res.get('checkin_num_limit_day')
            params = {'ticketSignID': ticketSignID}

            if checkinNum == 1:
                checkinRes = self.memberCheckIn(params)
                if not checkinRes:
                    insertFields = {
                        'type': 0,
                        'deviceId': self.selectedDevice.get('id'),
                        'ticketSignId': ticketSignID,
                        'gateNo': self.selectedDevice.get('name'),
                        'comment': '票機線上核銷'
                    }
                    self.db.insertMemberCheckIn(insertFields)
                    uniqueTicketIDs.append(ticketID)
                else:
                    rePrintTicketIDs.append(ticketID)
            else:
                # 檢查是否有每天入場一次條件
                if checkinNumLimitDay == 1:
                    params = {'ticketSignID': ticketSignID, "date": self.todayDate}
                    checkinByDayRes = self.memberCheckIn(params)
                    if not checkinByDayRes:
                        insertFields = {
                            'type': 0,
                            'deviceId': self.selectedDevice.get('id'),
                            'ticketSignId': ticketSignID,
                            'gateNo': self.selectedDevice.get('name'),
                            'comment': '票機線上核銷'
                        }
                        self.db.insertMemberCheckIn(insertFields)
                        uniqueTicketIDs.append(ticketID)
                    else:
                        rePrintTicketIDs.append(ticketID)
                else:
                    checkinRes = self.memberCheckIn(params)
                    if checkinRes is None:
                        insertFields = {
                            'type': 0,
                            'deviceId': self.selectedDevice.get('id'),
                            'ticketSignId': ticketSignID,
                            'gateNo': self.selectedDevice.get('name'),
                            'comment': '票機線上核銷'
                        }
                        self.db.insertMemberCheckIn(insertFields)
                        uniqueTicketIDs.append(ticketID)
                    elif len(checkinRes) < checkinNum:
                        insertFields = {
                            'type': 0,
                            'deviceId': self.selectedDevice.get('id'),
                            'ticketSignId': ticketSignID,
                            'gateNo': self.selectedDevice.get('name'),
                            'comment': '票機線上核銷'
                        }
                        self.db.insertMemberCheckIn(insertFields)
                        uniqueTicketIDs.append(ticketID)
                    else:
                        rePrintTicketIDs.append(ticketID)

        # 取得活動票券圖檔
        if uniqueTicketIDs:
            outPutData = self.refactorImageData(uniqueTicketIDs)
            if outPutData and self.printerPapperCheck() :
                self.printThread.member = member
                self.printThread.outPutData = outPutData
                self.printThread.start()
        if rePrintTicketIDs:
            checkedDatas = {'member': {'name': member['name']}, 'ticketID': rePrintTicketIDs}
            self.customMsgBox.show("Warning", f"會員 : {member['name']} - 已核銷入場，是否需要重印票券?", checkedDatas)

    def offlineReimburse(self, scanResult):
        # 離線核銷
        if self.bindTicket == '':
            self.customMsgBox.show("Error", "請先綁定活動資料再使用。")
            return 

        memberData = self.members.get(scanResult, [])
        if len(memberData) != 0 :
            ticketPrintID = set()
            rePrintTicketIDs = []

            for ticketID  in memberData['ticket_id']:
                details = memberData["ticket_id"][ticketID]
                if details['checkin_num'] == 1:
                    if len(details['checkin_log']) == 0:
                        self.offlineCheckinData['ticketSignID'].append(details['ticket_sign_id'])
                        ticketPrintID.add(ticketID)
                    else:
                        rePrintTicketIDs.append(ticketID)
                else:
                    # 檢查入場條件
                    if details['checkin_num_limit_day'] == 1:
                        if len(details['checkin_log']) == 0:
                            self.offlineCheckinData['ticketSignID'].append(details['ticket_sign_id'])
                            ticketPrintID.add(ticketID)
                        elif len(details['checkin_log']) < details['checkin_num']:
                            daliyCheck = [log for log in details['checkin_log'] if log['ticket_checkin_at'] == self.todayDate]
                            # 逐筆確認已checkin_log時間
                            if len(daliyCheck) < 1:
                                self.offlineCheckinData['ticketSignID'].append(details['ticket_sign_id'])
                                ticketPrintID.add(ticketID)
                            else:
                                rePrintTicketIDs.append(ticketID)
                        else:
                            rePrintTicketIDs.append(ticketID)
                    else:
                        if len(details['checkin_log']) == 0:
                            self.offlineCheckinData['ticketSignID'].append(details['ticket_sign_id'])
                            ticketPrintID.add(ticketID)
                        elif len(details['checkin_log']) < details['checkin_num']:
                            self.offlineCheckinData['ticketSignID'].append(details['ticket_sign_id'])
                            ticketPrintID.add(ticketID)
                        else:
                            rePrintTicketIDs.append(ticketID)
            if ticketPrintID:
                outPutData = self.refactorImageData(ticketPrintID)
                if outPutData and self.printerPapperCheck():
                    self.printThread.member = memberData
                    self.printThread.outPutData = outPutData
                    self.printThread.start()
            if rePrintTicketIDs:
                checkedDatas = {'member': {'name':memberData['name']}, 'ticketID': rePrintTicketIDs}
                self.customMsgBox.show("Warning", f"會員 : {memberData['name']} - 已核銷入場，是否需要重印票券?", checkedDatas)
                return
        else:
            self.customMsgBox.show("Warning", "查無該會員資料!")

    def refactorImageData(self, ticketID):
        # 離線活動Banner圖檔重整
        matchingData = []
        for t in self.ticketBanner:
            if t['id'] in ticketID:
                matchingData.append(t['pilImage'])
        return matchingData 

    def getTicketImage(self, ticketID):
        # 離線活動圖檔下載
        imageData = self.db.getTicketBannerByID(ticketID)
        result = []
        
        for data in imageData:
            tmp = []
            pilImage1 = ''
            pilImage2 = ''

            if data.get('pos_image1') != '':
                pilImage1 = self.printer.downloadImages(f"{self.targetUrl}{data['exhibit_id']}/{data['pos_image1']}")
            tmp.append({'image':pilImage1,'text':data['pos_text1'], 'fontSize': data['pos_font_size1']})

            if data.get('pos_image2') != '':
                pilImage2 = self.printer.downloadImages(f"{self.targetUrl}{data['exhibit_id']}/{data['pos_image2']}")
            
            if data.get('pos_image2') != '' and data.get('pos_text2') != '':
                tmp.append({'image':pilImage2,'text':data['pos_text2'], 'fontSize':data['pos_font_size2']})

            result.append({'id':data['id'],'pilImage':tmp})
        return result

    def insertCheckinData(self):
        # 定時插入核銷資料
        try:
            self.intranetTest.testLink()
            if not self.intranetTest.getHtmlLinkStatus:
                self.customMsgBox.show("Warning", "連線錯誤!")
            else :
                if self.offlineCheckinData and self.offlineCheckinData['ticketSignID'] != []: 
                    for ticketSignID in self.offlineCheckinData['ticketSignID']:
                        insertFields = {
                            'type':0,
                            'deviceId': self.selectedDevice.get('id'),
                            'ticketSignId': ticketSignID,
                            'gateNo': self.selectedDevice.get('name'),
                            'comment': '票機離線核銷'
                        }
                        self.offlineCheckInRow += int(self.db.insertMemberCheckIn(insertFields))
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
            checkinRes = self.db.memberCheckIn(ticketSignID)
            return checkinRes
        except Exception as e:
            self.customMsgBox.show("Warning", e)
            return False

    def offlineInit(self, data):
        # 離線核銷資料初始化
        try:
            # 報名會員資料
            self.members = self.db.getMemberSignTicketByTicketID(self.bindTicket)
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
                self.timerInsertCheckinData.start(6 * 1000)
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(traceback_str)
            self.customMsgBox.show("Warning", e)
            return False

    def onInputButtonClicked(self):
        # 判斷核銷方式
        phoneNumber = self.ui.telInputLabel.text()
        cidNumber = self.ui.cidInputLabel.text()

        self.ui.telInputLabel.clear()
        self.ui.cidInputLabel.clear()
        if phoneNumber == '' or cidNumber == '' or len(phoneNumber) != 10 or len(cidNumber) != 6:
            self.customMsgBox.show("Warning", "請輸入手機號碼及身分證後六碼。")
            return
        else :
            memberNo = self.getMemberPhoneBindMemberNo.get(phoneNumber)

            if not memberNo:
                self.customMsgBox.show("Error", "查無此號碼資料。")
                return
            if memberNo['cid'] != cidNumber:
                self.customMsgBox.show("Warning", "身分證不正確。")
                return

            if self.offlineValue:
                self.offlineReimburse(memberNo['member_no'])
            else:
                self.onlineReimburse(memberNo['member_no'])