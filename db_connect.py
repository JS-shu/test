import pymysql
from collections import defaultdict
from configparser import ConfigParser
from datetime import datetime


class db_connect:
    def __init__(self, parent,config_file='config.ini'):
        self.parent = parent
        self.customMsgBox = self.parent.customMsgBox
        self.config_file = config_file
        self.connection = None
        self.read_config()

    def connect(self):
<<<<<<< HEAD
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        except Exception as e:
            print(f"Error: {e}")
            self.customMsgBox.show("資料庫連線失敗", "資料庫連線失敗", "error")
            return False

    def read_config(self):
        try:
            config = ConfigParser()
            config.read(self.config_file)
            
            self.host = config.get('database', 'host')
            self.user = config.get('database', 'user')
            self.password = config.get('database', 'password')
            self.database = config.get('database', 'database')
        except Exception as e:
            print(f"Error: {e}")
            self.customMsgBox("讀取設定檔失敗", "讀取設定檔失敗", "error")

    def disconnect(self):
        try:
            if self.connection and self.connection.open:
                self.connection.close()
        except Exception as e:
            print(f"Error: {e}")
            self.customMsgBox("資料庫斷線失敗", "資料庫斷線失敗", "error")
=======
        self.connection = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def disconnect(self):
        if self.connection and self.connection.open:
            self.connection.close()
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2

    def getDevices(self):
        # 取得活動核銷綁定裝置
        try:
            with self.connection.cursor() as cursor:
                sql = "SELECT * FROM new_ticket_device"
                cursor.execute(sql)
                devices = cursor.fetchall()

                return devices
        except Exception as e:
            print(f"Error: {e}")
            self.customMsgBox("取得裝置失敗", "取得裝置失敗", "error")

<<<<<<< HEAD
    def getMemberTicketSignData(self, data):
        # 取得會員資料
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT m.name, s.id AS id, s.ticket_id AS ticket_id FROM new_ticket_sign AS s LEFT JOIN new_member AS m ON s.member_id = m.id WHERE m.no = {data['no']} AND ticket_id IN ({data['ticketID']})";
                cursor.execute(sql)
                data = cursor.fetchall()
                
                result = defaultdict(lambda: {'name': '', 'ticketData': []})

                for item in data:
                    name = item['name']
                    ticket_data = {'id': item['id'], 'ticket_id': item['ticket_id']}
                    result[name]['name'] = name
                    result[name]['ticketData'].append(ticket_data)

                result_list = list(result.values())[0]
                return result_list
        except Exception as e:
            print(f"Error: {e}")
            self.customMsgBox("取得會員資料失敗", "取得會員資料失敗", "error")
=======
    def getMember(self, approveCode):
        # 線上流程使用,根據掃描到的QRcode進行approveCode驗證
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT * FROM new_member WHERE approve_code = '{approveCode}'"
                cursor.execute(sql)
                member = cursor.fetchone()

                return member 
        except Exception as e:
            print(f"Error: {e}")
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2

    def getMemberSignTicketByTicketID(self, ticketID):
        # 根據核銷裝置綁定的ticketID取得已登記參與活動的會員
        try:
            with self.connection.cursor() as cursor:
<<<<<<< HEAD
                sql = f"SELECT s.member_id,s.id, s.name, s.ticket_id, m.no AS member_no FROM new_ticket_sign AS s LEFT JOIN new_member AS m on s.member_id = m.id WHERE ticket_id in ({ticketID})";
=======
                sql = f"SELECT s.member_id,s.id, s.name, s.ticket_id, m.approve_code AS member_approve_code FROM new_ticket_sign AS s LEFT JOIN new_member AS m on s.member_id = m.id WHERE ticket_id in ({ticketID})";
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2
                cursor.execute(sql)
                members = cursor.fetchall()
                result_dict = defaultdict(list)

                for member in members:
<<<<<<< HEAD
                    member_no = member.get('member_no')

                    if not member_no:
                        continue

                    if member_no not in result_dict:
                        result_dict[member_no] = {'member_id':member.get('member_id'),'name': member.get('name', ''), 'ticket_id': []}
=======
                    approve_code = member.get('member_approve_code')

                    if not approve_code:
                        continue

                    if approve_code not in result_dict:
                        result_dict[approve_code] = {'member_id':member.get('member_id'),'name': member.get('name', ''), 'ticket_id': []}
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2

                        ticket_id = member.get('ticket_id')
                        ticket_sign_id = member.get('id', '')
                        ticket_dict = {ticket_id: {'ticket_sign_id': ticket_sign_id}}
<<<<<<< HEAD
                        result_dict[member_no]['ticket_id'].append(ticket_dict)
=======
                        result_dict[approve_code]['ticket_id'].append(ticket_dict)
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2
                    else :
                        ticket_id = member.get('ticket_id')
                        ticket_sign_id = member.get('id', '')
                        ticket_dict = {ticket_id: {'ticket_sign_id': ticket_sign_id}}
<<<<<<< HEAD
                        result_dict[member_no]['ticket_id'].append(ticket_dict)
=======
                        result_dict[approve_code]['ticket_id'].append(ticket_dict)
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2
                return result_dict
        except Exception as e:
            print(f"Error: {e}")

<<<<<<< HEAD
=======
    def getMemberTickets(self, memberID, ticketID):
        # 線上核銷使用，根據會員&核銷裝置綁定的ticketID取得已登記的活動
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT id, ticket_id, exhibit_id, member_id, income_id, ticket_no, member_no, approve_code, `name`,email, phone_number, cid  FROM new_ticket_sign WHERE member_id = {memberID} AND ticket_id IN ({ticketID})";
                cursor.execute(sql)
                memberInTicketSign = cursor.fetchall()

                return memberInTicketSign
        except Exception as e:
            print(f"Error: {e}")

>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2
    def getTicketBannerByID(self, ticketID):
        # 取得活動Banner，作為票券列印使用
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT id, exhibit_id, image FROM new_ticket WHERE id IN ({ticketID})";
                cursor.execute(sql)
                memberInTicketSign = cursor.fetchall()

                return memberInTicketSign
        except Exception as e:
            print(f"Error: {e}")

    def getTicketByID(self, ticketID):
        # 取得活動
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT id, name FROM new_ticket WHERE id ={ticketID}";
                cursor.execute(sql)
                ticket = cursor.fetchone()

                return ticket
        except Exception as e:
            print(f"Error: {e}")

    def insertMemberCheckIn(self, datas):
        # 寫入報名資料
        type = 0
        deviceId = datas.get('deviceId', 0)
        ticketSignId = datas.get('ticketSignId', 0)
        gateNo = datas.get('gateNo', 0)
        nowDate = datetime.now()
        comment = datas.get('comment', '')
        try:
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO new_ticket_checkin SET type=%s, device_id=%s, ticket_sign_id=%s, gate_no=%s, comment=%s, create_at=%s, checkin_at=%s"
                cursor.execute(sql, (type, deviceId, ticketSignId, gateNo, comment, nowDate, nowDate))
                self.connection.commit()

                return cursor.rowcount
        except Exception as e:
            print(f"Error: {e}")

<<<<<<< HEAD
    def memberCheckIn(self, ticketSignId):
=======
    def checkMemberCheckIn(self, ticketSignId):
>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2
        # 檢查報名資料是否已存在
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT id FROM new_ticket_checkin WHERE ticket_sign_id = {ticketSignId}"
                cursor.execute(sql)
                checkin = cursor.fetchone()

                return checkin
        except Exception as e:
            print(f"Error: {e}")
    
    def getMemberCheckIn(self, ticketID):
        # 根據核銷裝置綁定的ticketID取得已登記參與活動的會員
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT s.member_id, m.name, s.id, s.ticket_id FROM new_ticket_checkin AS c LEFT JOIN new_ticket_sign AS s on s.id = c.ticket_sign_id LEFT JOIN new_member as m ON m.id = s.member_id WHERE s.ticket_id in ({ticketID}) GROUP BY s.member_id";
                cursor.execute(sql)
                members = cursor.fetchall()

                result = set()
                for member in members:
                    result.add(member['member_id'])

                return list(result)
<<<<<<< HEAD
=======

>>>>>>> a44558cd81f58cab7e3057d623fd2c742aedcfe2
        except Exception as e:
            print(f"Error: {e}")