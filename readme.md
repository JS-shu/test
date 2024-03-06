# 上聯出票機核銷系統
    目前婦幼展、寵物展等擁有大量活動需要兌換，且都採取人工核銷並兌換票券給消費者，需要耗費大量的人力跟時間在核對身份。故為了縮減排隊時間與人力，開發一可以讓消費者自行報導核銷並出票的機制。
## 目錄
- 安裝
    - `pip install numpy==1.26.3`
    - `pip install opencv_python==4.8.1.78`
    - `pip install Pillow==10.2.0`
    - `pip install pygrabber==0.2`
    - `pip install PyMySQL==1.1.0`
    - `pip install PyQt6==6.6.1`
    - `pip install PyQt6_sip==13.6.0`
    - `pip install pyserial==3.5`
    - `pip install python_escpos==3.0`
    - `pip install pyzbar==0.1.9`
    - `pip install requests==2.31.0`
- 使用
    - ```python start.py```即可執行
    - 經過`pyinstaller`打包後的.exe, 進行點擊亦可執行
    
    - start.py
        ```
            import sys
            from PyQt6.QtWidgets import QApplication
            from main import MainWindow 
        ```
    - main.py
        ```
            import cv2, numpy as np, sys, traceback

            from dbConnect import DbConnect
            from customMsgBox import CustomMsgBox
            from printqrcode import QRCodePrinter
            from topLinkIntranet import TopLinkIntranet
            from ui import Ui_MainWindow

            from datetime import datetime
            from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
            from PyQt6.QtGui import QPixmap, QImage, QPainter, QPainterPath
            from PyQt6.QtWidgets import QWidget
            from pyzbar.pyzbar import ZBarSymbol, decode
            from pygrabber.dshow_graph import FilterGraph
        ```
    - topLinkIntranet.py
        ```
            import json
            from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
            from PyQt6.QtCore import QUrl
        ```
    - printcode.py
        ```
            import io
            from PIL import Image
            from escpos.printer import Serial
            import requests
        ```
    - dbConnect.py
        ```
            import pymysql
            from collections import defaultdict
            from datetime import datetime
        ```
    - ui.py
        ```
            from PyQt6.QtGui import QPixmap, QFont
            from PyQt6.QtCore import QSize
            from PyQt6.QtWidgets import QLabel, QComboBox, QVBoxLayout, QHBoxLayout, QFormLayout, QGraphicsScene, QGraphicsView
        ```