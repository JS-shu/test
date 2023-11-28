import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QPushButton, QVBoxLayout, QHBoxLayout, QFormLayout, QGraphicsScene, QGraphicsView
from PyQt6.QtGui import QPalette, QColor, QPixmap, QImage
from db_connect import db_connect
from PyQt6.QtCore import QThread, pyqtSignal, QSize
from pyzbar.pyzbar import ZBarSymbol, decode
from PyQt6.QtWidgets import QMessageBox

class CameraThread(QThread):
    frame_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

    def run(self):
        cap = cv2.VideoCapture(1)
        while True:
            ret, frame = cap.read()
            if not ret:
                print("無法接收畫面。正在退出...")
                break

            self.frame_signal.emit(frame)
        cap.release()

class MainWindow(QWidget):
    def __init__(self):
        self.previousBarcodeData = ''
        super().__init__()

        self.db = db_connect(host='', user='readonly_test', password='', database='')
        self.db.connect()

        devices = self.db.getDevices()

        # 左半部
        # 相機嵌入框畫面
        self.camera_label = QLabel("Camera View")
        self.camera_label.setStyleSheet("border: 2px dotted gray;")

        # 右半部
        # 設備選單
        self.device_label = QLabel("Device:")
        self.device_name_label = QLabel("")
        self.device_combobox = QComboBox()
        self.device_combobox.addItem("請選擇掃描裝置", -1)
        # 回填設備選單選項
        for device in devices:
            self.device_combobox.addItem(device['name'], device['id'])
        # 設備選單異動觸發事件
        self.device_combobox.currentIndexChanged.connect(self.device_changed)

        # 會員 & 活動資訊
        self.member_label = QLabel("Member:")
        self.member_name_label = QLabel("")
        self.activity_label = QLabel("Activity:")
        self.activity_combobox = QComboBox()
        self.activity_combobox.addItem("Please scan member first")
        self.activity_combobox.setEnabled(False)

        self.print_button = QPushButton("Print")
        self.print_button.setEnabled(False)  # 初始狀態設為不可用

        # Layout
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.camera_label)

        right_layout = QFormLayout()
        right_layout.addRow(self.device_label, self.device_name_label)
        right_layout.addRow(self.device_combobox)
        
        # Add spacing to push the next widgets to the bottom
        right_layout.addRow(QLabel(""))
        right_layout.addRow(QLabel(""))

        right_layout.addRow(self.member_label, self.member_name_label)
        right_layout.addRow(self.activity_label, self.activity_combobox)
        right_layout.addRow(self.print_button)

        main_layout = QHBoxLayout(self)
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        # 設置樣式
        self.set_styles()
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
        self.camera_thread = CameraThread()
        self.camera_thread.frame_signal.connect(self.update_camera_view)

    def update_camera_view(self,frame):

        result = self.decoder(frame)
        if result:
            ''' 
                根據result (QRcode approve code)丟回SQL驗證會員,
                會員資料 對應new_ticket 
            '''
            member = self.db.getMember(result)
            print(member)

        # 在相機標籤中顯示畫面
        frame = cv2.resize(frame, (640, 480))
        height, width, channel = frame.shape
        bytes_per_line = channel * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_image)
        self.camera_label.setPixmap(pixmap)

        
    def decoder(self, image):
        try:
            gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            barcode = decode(gray_img, symbols=[ZBarSymbol.QRCODE])

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

    def set_styles(self):
        # 設定暗色系 Gruvbox 顏色主題
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(40, 40, 40))  # 背景色
        palette.setColor(QPalette.ColorRole.WindowText, QColor(235, 219, 178))  # 前景色
        palette.setColor(QPalette.ColorRole.Button, QColor(94, 60, 59))  # 按鈕背景色
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(235, 219, 178))  # 按鈕前景色
        self.setPalette(palette)

    def device_changed(self, index):
        device_id = self.device_combobox.itemData(index)
        if device_id != -1:
            device_name = self.device_combobox.currentText()

            # 顯示對話框
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setWindowTitle("Device Information")
            msg_box.setText(f"Device ID: {device_id}\nDevice Name: {device_name}")
            msg_box.exec()

            self.device_name_label.setText(f"{device_name}")
            # 啟動相機線程
            self.camera_thread.start()
        else:
            self.device_name_label.clear()

        self.print_button.setEnabled(device_id != -1)  # 如果有選擇設備，啟用列印按鈕

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
