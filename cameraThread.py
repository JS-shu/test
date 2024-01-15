import cv2, numpy as np, traceback
from PyQt6.QtCore import  QThread, pyqtSignal


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