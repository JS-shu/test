import json

from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtCore import QUrl

class TopLinkIntranet:
    def __init__(self, parent=None):
        self.parent = parent
        self.network_manager = QNetworkAccessManager()
        self.htmlLinkReply = None
        
    def getHtmlLinkStatus(self):
        if self.htmlLinkReply != 200:
            return False
        else:
            return True
    
    def testLink(self):
        try:
            url = f"https://api.top-link.com.tw/device/Connect/test?device={self.parent.selectedDevice.get('key', 0)}"
            request = QNetworkRequest(QUrl(url))
            reply = self.network_manager.get(request)
            
            # 連接 finished 信號
            reply.finished.connect(self.handleNetworkReply)
            
        except Exception as e:
            self.parent.customMsgBox.show("Warning", str(e))

    def handleNetworkReply(self):
        # 處理異步請求的回應
        try:
            reply = self.parent.sender()  # 獲取發送信號的 QNetworkReply 對象
            if reply.error() == QNetworkReply.NetworkError.NoError:
                response_data  = bytes(reply.readAll().data()).decode('utf-8')
                response_dict = json.loads(response_data)
                self.htmlLinkReply = response_dict.get('status', None)
            else:
                error_message = reply.errorString()
                print(f"Error: {error_message}")
        except Exception as e:
            self.parent.customMsgBox.show("Warning", str(e))