import pymysql

class db_connect:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None 

    def connect(self):
        # 建立資料庫連線
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def disconnect(self):
        # 關閉資料庫連線
        if self.connection and self.connection.open:
            self.connection.close()

    def getDevices(self):
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM new_ticket_device"
                cursor.execute(sql)

                devices = cursor.fetchall()

                return devices
        except Exception as e:
            print(f"Error: {e}")

    def getMember(self, approveCode):
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT * FROM new_member WHERE approve_code = '{approveCode}'"
                print(sql)
                cursor.execute(sql)
                member = cursor.fetchone()
                return member 
        except Exception as e:
            print(f"Error: {e}")
