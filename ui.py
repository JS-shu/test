from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QFormLayout, QGraphicsScene, QGraphicsView, QLineEdit, QPushButton


class Ui_MainWindow(object):
    def __init__(self):
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
        self.cameraLabel = QLabel('')
        self.cameraLabel.setStyleSheet("border: 2px dashed #fb4934; border-radius: 10px;")

        # 右半部
        # 離線核銷更新資訊
        self.offlineTitleInfoLabel = QLabel('')
        self.offlineInfoLabel = QLabel('')
        self.offlineTitleInfoLabel.setFont(self.labelTitleFont)
        self.offlineInfoLabel.setFont(self.labelTitleFont)
        self.offlineTitleInfoLabel.setStyleSheet("color: #d79921;font-size: 18px;")
        self.offlineInfoLabel.setStyleSheet("color: #d79921;font-size: 18px;")

        # 鏡頭選擇
        self.cameraTitleLable = QLabel("鏡頭")
        self.cameraInfoLabel = QLabel('')
        self.cameraCombobox = QComboBox()
        self.cameraCombobox.addItem("請選擇鏡頭", -1)
        self.cameraTitleLable.setFont(self.labelTitleFont)
        self.cameraInfoLabel.setFont(self.labelFont)
        self.cameraCombobox.setFont(self.labelFont)

        # 是否離線核銷
        self.offlineLabel = QLabel("核銷方式")
        self.offlineCombobox = QComboBox()
        self.offlineCombobox.addItem("請選擇是否離線核銷")
        self.offlineCombobox.addItem("離線", 1)
        self.offlineCombobox.addItem("線上", 0)
        self.offlineLabel.setFont(self.labelTitleFont)
        self.offlineCombobox.setFont(self.labelFont)

        # 設備選單
        self.deviceTitleLabel = QLabel("裝置綁定")
        self.deviceNameLabel = QLabel('')
        self.deviceCombobox = QComboBox()
        self.deviceCombobox.addItem("請選擇掃描裝置", -1)

        self.deviceTitleLabel.setFont(self.labelTitleFont)
        self.deviceNameLabel.setFont(self.labelFont)
        self.deviceNameLabel.setStyleSheet("color: #fb4934;font-size: 22px")
        self.deviceCombobox.setFont(self.labelFont)

        # 會員 & 活動資訊
        self.memberLabel = QLabel('')
        self.memberNameLabel = QLabel('')
        self.memberLabel.setFont(self.labelTitleFont)
        self.memberNameLabel.setFont(self.labelFont)

        # 創建輸入框
        self.inputLabel = QLineEdit('')
        self.inputLabel.setPlaceholderText('輸入手機號碼...')
        self.inputButton = QPushButton('送出')
        self.inputButton.setStyleSheet("max-width: 60px; font-size: 18px;")
        self.inputLabel.setStyleSheet("width: 250px; font-size: 18px;")
        self.inputLabel.hide()
        self.inputButton.hide()

    def guiSetting(self, MainWindow):
        # Layout
        leftLayout = QVBoxLayout()
        leftLayout.addWidget(self.cameraLabel)
        rightLayout = QFormLayout()
        
        # 離線核銷更新資訊
        rightLayout.addRow(self.offlineTitleInfoLabel, self.offlineInfoLabel)

        # 鏡頭資訊
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
        mainLayout = QHBoxLayout(MainWindow)
        mainLayout.addLayout(leftLayout, 3)
        mainLayout.addLayout(rightLayout, 1)

        rightLayout.addRow(self.inputLabel, self.inputButton)
        # 設置樣式
        MainWindow.setStyleSheet("""
            background-color: #504945;
            color: #ebdbb2;
        """)

        MainWindow.setWindowTitle("QR Code Scanner")
        # 起始座標大小
        MainWindow.setGeometry(100, 100, 1220, 500)
        
        MainWindow.scene = QGraphicsScene()
        MainWindow.view = QGraphicsView(MainWindow.scene)
        MainWindow.view.setMinimumSize(QSize(640, 480))
        MainWindow.image_item = MainWindow.scene.addPixmap(QPixmap())