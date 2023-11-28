import cv2
import numpy as np
from pyzbar.pyzbar import ZBarSymbol,decode 

# 變數用於跟蹤先前檢測到的 QR 碼的資料
previousBarcodeData = None

def decoder(image):

    global previousBarcodeData  # 使用全局變數

    try:
        gray_img = cv2.cvtColor(image,0)
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
                string = "Data: " + str(barcodeData) + " | Type: " + str(barcodeType)
                
                cv2.putText(frame, string, (x,y), cv2.FONT_HERSHEY_SIMPLEX,0.8,(0,0,255), 2)
                # 檢查是否為新的 QR 碼
                if barcodeData != previousBarcodeData:
                    previousBarcodeData = barcodeData  # 更新先前檢測到的 QR 碼資料
                    return barcodeData
    except Exception as e:
        print(e)

# 設定視窗大小
width = 640
height = 480

# 開啟相機並設定視窗大小
cap = cv2.VideoCapture(1)
cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Image', width, height)

while True:
    ret, frame = cap.read()
    result = decoder(frame)
    if result:
        print(result)
    if not ret:
        print("Can't receive frame (stream end?). Exiting ...")
        break
    cv2.imshow('Image', frame)
    code = cv2.waitKey(1)
    if code == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()