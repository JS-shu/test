import io
import requests
from PIL import Image
from escpos.printer import Network

# 下載 QR 碼圖片
url = "https://dykt84bvm7etr.cloudfront.net/uploadfiles/1110/ticket/Az4zIDaL6GNv.jpg"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
response = requests.get(url, headers=headers)

# 檢查是否成功取得圖片
if response.status_code == 200:
    img = Image.open(io.BytesIO(response.content))

    # 最長長度設置
    paper_width = 255

    # # 計算縮放比例
    scale_factor = min(paper_width / img.height, 1.0)
    # scale_factor = min(paper_width / img.width, 1.0)

    # 調整圖片大小以保持原始寬高比例，並確保寬度不超過80mm
    new_img = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.LANCZOS)
    

    print(new_img)
    # 初始化打印機
    printer_ip = "10.168.168.87"
    printer = Network(printer_ip)

    # 設定打印機參數（可以根據需要進行調整）
    printer.image(new_img)
    # printer.cut(mode='PART')
    printer.cut()

else:
    print(f"Failed to fetch image. Status code: {response.status_code}")


# winpos 圖檔打印