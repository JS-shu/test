import cv2

cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# 檢查支援的尺寸
supported_widths = []
supported_heights = []

for width in range(100, 2000, 100):
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    ret, _ = cap.read()
    if ret:
        supported_widths.append(width)
    else:
        break

for height in range(100, 2000, 100):
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    ret, _ = cap.read()
    if ret:
        supported_heights.append(height)
    else:
        break

cap.release()

print("Supported widths:", supported_widths)
print("Supported heights:", supported_heights)
