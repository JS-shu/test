import sys
import cv2
import numpy as np
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QGraphicsScene, QGraphicsView
from pyzbar.pyzbar import ZBarSymbol, decode

class ScannerThread(QThread):
    scan_result = pyqtSignal(str)
    frame_signal = pyqtSignal(np.ndarray)

    def __init__(self):
        super().__init__()

    def run(self):
        previousBarcodeData = None

        def decoder(image):
            nonlocal previousBarcodeData

            try:
                gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                barcode1 = decode(gray_img, symbols=[ZBarSymbol.QRCODE])
                barcode2 = cv2.QRCodeDetector().detectAndDecodeMulti(gray_img)

                if barcode1:
                    print(barcode1)

                if barcode2[1]:
                    print('=========================================')
                    print(barcode2[0], barcode2[1][0])
                    self.scan_result.emit(barcode2[1][0])
                
            except Exception as e:
                print(e)

        cap = cv2.VideoCapture(1)

        while True:
            ret, frame = cap.read()
            frame = cv2.resize(frame, (640, 480))

            decoder(frame)
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break

            self.frame_signal.emit(frame)
            code = cv2.waitKey(1)
            if code == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()


class ScannerApp(QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setWindowTitle('QR Code Scanner')
        self.setGeometry(100, 100, 640, 480)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setMinimumSize(QSize(640, 480))
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.image_item = self.scene.addPixmap(QPixmap())

        self.result_label = QLabel('Scan Result: ', self)

        self.scan_button = QPushButton('Scan', self)
        self.scan_button.clicked.connect(self.startScanning)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.result_label)
        layout.addWidget(self.scan_button)
        self.setLayout(layout)

        self.scanner_thread = ScannerThread()
        self.scanner_thread.scan_result.connect(self.updateScanResult)
        self.scanner_thread.frame_signal.connect(self.updateFrame)

    def startScanning(self):
        if not self.scanner_thread.isRunning():
            self.scanner_thread.start()

    def updateScanResult(self, result):
        self.result_label.setText(f'Scan Result: {result}')

    def updateFrame(self, frame):
        height, width, channel = frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        self.image_item.setPixmap(QPixmap(q_image))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    scanner_app = ScannerApp()
    scanner_app.show()
    sys.exit(app.exec())


# GUI with QRcode detect and decode