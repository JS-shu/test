import serial.tools.list_ports, sys

class UsbDeviceCheck:
    def __init__(self, parent=None):
        self.parent = parent
        self.customMsgBox = parent.customMsgBox

    def checkUsbLink(self):
        try:
            # USB設備連線檢查(WP-720 setting), vid & pid 目前為寫死的方式
            target_vid = 0x22A0
            target_pid = 0x000A
            self.usbDviceResult = self.checkUsbDevice(target_vid, target_pid)

            if self.usbDviceResult:
                self.customMsgBox.show("Information", "WP-720 已連接!")
            else:
                self.customMsgBox.show("Warning", "WP-720 未連接，請先連接設備!")
                sys.exit()
        except Exception as e:
            print(e)
            self.customMsgBox.show("Error", f"{e}")
            sys.exit()

    def checkUsbDevice(self, vid, pid):
        try:
            target_hwid = f"VID:PID={vid:04X}:{pid:04X}"
            for port in serial.tools.list_ports.comports():
                if target_hwid in port.hwid:
                    return port
            return False
        except Exception as e:
            print(e)
            self.customMsgBox.show("Error", f"{e}")
            sys.exit()