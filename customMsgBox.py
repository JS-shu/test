from PyQt6.QtWidgets import QMessageBox, QPushButton, QLineEdit, QDialog, QVBoxLayout


class CustomMsgBox:
    def __init__(self, parent=None):
        self.parent = parent
        self.ui = self.parent.ui
        

    def show(self, title, text, checkedDatas=[]):
        msgBox = QMessageBox()
        msgBox.setStyleSheet(self.ui.QMessageStyle)
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
            rePrintBtn.clicked.connect(lambda: self.reprintCheck(checkedDatas))

        msgBox.setText(f"\n\n{text}\n\n")
        msgBox.exec()

    def reprintCheck(self, checkedDatas):
        # 設備碼核對確認窗框
        self.ui.deviceKeyInput = QLineEdit()
        self.ui.deviceKeyInput.resize(400, 20)
        self.ui.deviceKeyInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.deviceKeyInput.setPlaceholderText("請輸入設備碼")

        toggle_button = QPushButton('Toggle Password')
        toggle_button.clicked.connect(self.toggle_password)

        dialog = QDialog()
        dialog.setWindowTitle('設備碼驗證')
        dialog.resize(600, 300)
        dialog.setStyleSheet(self.ui.QMessageStyle)

        # QVBoxLayout 佈局
        layout = QVBoxLayout(dialog)
        layout.addWidget(self.ui.deviceKeyInput)
        layout.addWidget(toggle_button)

        okBtn = QPushButton("確定", dialog)
        okBtn.clicked.connect(dialog.accept)
        layout.addWidget(okBtn)

        cancelBtn = QPushButton("取消", dialog)
        cancelBtn.clicked.connect(dialog.reject)
        layout.addWidget(cancelBtn)

        # click觸發事件
        dialog.accepted.connect(lambda: self.acceptDialog(checkedDatas))
        dialog.rejected.connect(self.rejectDialog)
        dialog.exec()

    def toggle_password(self):
        # 切換設備碼明暗碼
        try:
            current_mode = self.ui.deviceKeyInput.echoMode()
            if current_mode == QLineEdit.EchoMode.Normal:
                new_mode = QLineEdit.EchoMode.Password
            else:
                new_mode = QLineEdit.EchoMode.Normal

            self.ui.deviceKeyInput.setEchoMode(new_mode)
        except Exception as e:
            print(f"Error: {e}")

    def acceptDialog(self, checkedDatas):
        try:
            deviceKey = self.ui.deviceKeyInput.text()

            if (deviceKey == self.parent.selectedDevice.get('winpos_key')):
                if len(checkedDatas) != 0:
                    if 'member_id' in checkedDatas:
                        # 離線
                        checkTicketID = checkedDatas.get('ticket_id', [])
                        if checkTicketID:
                            ticketIDs = [list(ticket.keys())[0] for ticket in checkTicketID]
                        imageUrls = self.parent.offlineReformImageData(ticketIDs)
                        if imageUrls:
                            # if (self.parent.printerPapperCheck()):
                            #     self.parent.printer.printTickets('offline', checkedDatas, imageUrls) # 列印票券
                                print(imageUrls)
                    else :
                        # 線上
                        ticketIDs = [data['ticketID'] for data in checkedDatas]
                        sTicketIDs = ','.join(map(str, ticketIDs))
                        imageUrls = self.parent.onlinReformImageData(sTicketIDs)

                        if imageUrls:
                            # if (self.parent.printerPapperCheck()):
                            #     self.parent.printer.printTickets('online', False, imageUrls) # 列印票券
                                print(imageUrls)
            else:
                self.show("Warning", "設備碼錯誤!")
        except Exception as e:
            self.show("Warning", e)

    def rejectDialog(self):
        # 取消設備碼輸入
        print("Rejected")