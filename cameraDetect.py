import cv2, sys, traceback

from cameraThread import CameraThread
from pygrabber.dshow_graph import FilterGraph

class CameraDetect:
    def __init__(self, parent=None):
        self.ui = parent.ui
        self.parent = parent
        self.customMsgBox = parent.customMsgBox
        self.cameraDevices = []
        self.selectedCamera = 0
        self.cameraThread = None

    def cameraInit(self):
            try:
                avalibaleCamera = self.getAvailableCamera()
                if avalibaleCamera and avalibaleCamera != []:
                    index = 0
                    for camera in avalibaleCamera:
                        self.ui.cameraCombobox.addItem(f"鏡頭 - {camera} - {index}", index)
                        index += 1
                else :
                    self.customMsgBox.show("Warning", "無法取得相機, 程式將關閉!")
                    sys.exit()
                # 核銷機制異動觸發事件
                self.ui.cameraCombobox.currentIndexChanged.connect(self.cameraChanged)
            except Exception as e:
                print(f"An exception occurred: {e}")
                traceback_str = traceback.format_exc()
                print(traceback_str)
                print(e)

    def cameraChanged(self, index):
        try:
            selectedCameraOption = self.ui.cameraCombobox.itemData(index)
            if index == 0:
                self.customMsgBox.show("Warning", "請選擇相機")
            else:    
                if selectedCameraOption != self.selectedCamera or self.selectedCamera == 0:
                    self.customMsgBox.show("Warning", f"已選擇 鏡頭-{self.cameraDevices[selectedCameraOption]}!")
                    self.selectedCamera = selectedCameraOption

            # 相機線程
            if self.cameraThread and self.cameraThread.isRunning():
                self.cameraThread.frameSignal.disconnect()
                self.cameraThread.releaseCamera()
                self.cameraThread.quit()
                self.cameraThread.wait()

            self.cameraThread = CameraThread(self.selectedCamera)
            self.cameraThread.frameSignal.connect(self.parent.updateCameraView)
            self.cameraThread.start()
        except Exception as e:
            print(f"An exception occurred: {e}")
            traceback_str = traceback.format_exc()
            print(traceback_str)
            print(e)    

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
            self.customMsgBox.show("Warning", e)
            return False