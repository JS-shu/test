# 使用官方的 Python 映像作為基礎映像
FROM python

# 設定工作目錄
WORKDIR /app

# 複製本地代碼到容器內
COPY . /app

# 安裝相關庫
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx libzbar-dev

# 安裝應用程序的依賴項
RUN pip install -r requirements.txt  

# 安裝 opencv-python, pyzbar, numpy
# RUN pip install opencv-python pyzbar numpy

# 告訴 Docker 使用的入口點命令
CMD ["python", "hello.py"]  
