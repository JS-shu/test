import pymysql, traceback
from collections import defaultdict
from configparser import ConfigParser
from datetime import datetime


class DbConnect:
    def __init__(self, parent,config_file='config.ini'):
        self.parent = parent
        self.customMsgBox = self.parent.customMsgBox
        self.config_file = config_file
        self.connection = None
        self.read_config()

    def connect(self):
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
            self.customMsgBox.show('Warning',"資料庫連線失敗")
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
            self.customMsgBox.show('Warning',"讀取設定檔失敗")

    def disconnect(self):
        try:
            if self.connection and self.connection.open:
                self.connection.close()
        except Exception as e:
            print(f"Error: {e}")
            self.customMsgBox.show('Warning',"資料庫斷線失敗")

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
            self.customMsgBox.show('Warning',"取得裝置失敗")

    def getMemberTicketSignData(self, data):
        # 取得會員資料
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT m.name, s.id AS id, s.ticket_id AS ticket_id, t.checkin_num AS checkin_num, t.checkin_num_limit_day AS checkin_num_limit_day FROM new_ticket_sign AS s LEFT JOIN new_member AS m ON s.member_id = m.id LEFT JOIN new_ticket AS t ON t.id = s.ticket_id WHERE m.no = {data['no']} AND ticket_id IN ({data['ticketID']})";
                cursor.execute(sql)
                data = cursor.fetchall()
                
                result = defaultdict(lambda: {'name': '', 'ticketData': []})

                if not data :
                    return False
                for item in data:
                    name = item['name']
                    ticket_data = {'id': item['id'], 'ticket_id': item['ticket_id'], 'checkin_num': item['checkin_num'], 'checkin_num_limit_day': item['checkin_num_limit_day']}
                    result[name]['name'] = name
                    result[name]['ticketData'].append(ticket_data)

                result_list = list(result.values())[0]
                return result_list
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e} \n Traceback: {traceback_str}")
            self.customMsgBox.show('Warning',"取得會員資料失敗")

    def getMemberSignTicketByTicketID(self, ticketID):
    # 根據核銷裝置綁定的ticketID取得已登記參與活動的會員
        try:
            self.connection.begin()
            with self.connection.cursor() as cursor:
                sql = f"SELECT s.member_id,s.id, s.name, s.ticket_id, m.no AS member_no, t.checkin_num AS checkin_num, t.checkin_num_limit_day AS checkin_num_limit_day, c.id AS ticket_checkin_id, DATE_FORMAT(c.checkin_at, '%Y-%m-%d') AS ticket_checkin_at FROM new_ticket_sign AS s LEFT JOIN new_member AS m on s.member_id = m.id LEFT JOIN new_ticket AS t on t.id = s.ticket_id LEFT JOIN new_ticket_checkin AS c on c.ticket_sign_id = s.id WHERE ticket_id in ({ticketID})"
                cursor.execute(sql)
                datas = cursor.fetchall()
                result = {}
                for item in datas:
                    member_no = str(item['member_no'])
                    if member_no not in result:
                        result[member_no] = {
                            "member_id": item['member_id'],
                            "name": item['name'],
                            "ticket_id": {}
                        }

                    ticket_id = item['ticket_id']
                    if ticket_id not in result[member_no]['ticket_id']:
                        result[member_no]['ticket_id'][ticket_id] = {
                            "ticket_sign_id": item['id'],
                            "checkin_num": item['checkin_num'],
                            "checkin_num_limit_day": item['checkin_num_limit_day'],
                            "checkin_log": []
                        }

                    if item['ticket_checkin_id'] is not None and item['ticket_checkin_at'] is not None:
                        result[member_no]['ticket_id'][ticket_id]['checkin_log'].append({
                            "ticket_checkin_id": item['ticket_checkin_id'],
                            "ticket_checkin_at": item['ticket_checkin_at']
                        })
            self.connection.commit()
            return result
        except Exception as e:
            self.connection.rollback()
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e} \n Traceback: {traceback_str}")

    def getTicketBannerByID(self, ticketID):
        # 取得活動Banner，作為票券列印使用
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT t.id AS id, t.exhibit_id AS exhibit_id, pd.pos_image1 AS pos_image1, pd.pos_image2 AS pos_image2, pd.pos_text1 AS pos_text1, pd.pos_text2 AS pos_text2, pd.pos_font_size1 AS pos_font_size1, pd.pos_font_size2 AS pos_font_size2 FROM new_ticket t LEFT JOIN new_ticket_pos_data AS pd ON t.id = pd.ticket_id WHERE t.id IN ({ticketID})";
                cursor.execute(sql)
                data = cursor.fetchall()
                return data
        except Exception as e:
            traceback_str = traceback.format_exc()
            print(f"An exception occurred: {e} \n Traceback: {traceback_str}")

    def insertMemberCheckIn(self, datas):
        # 寫入報名資料
        type = 0
        deviceId = datas.get('deviceId', 0)
        ticketSignId = datas.get('ticketSignId', 0)
        gateNo = datas.get('gateNo', 0)
        nowDate = datetime.now()
        comment = datas.get('comment', '')
        try:
            self.connection.begin()
            with self.connection.cursor() as cursor:
                sql = "INSERT INTO new_ticket_checkin SET type=%s, device_id=%s, ticket_sign_id=%s, gate_no=%s, comment=%s, create_at=%s, checkin_at=%s"
                cursor.execute(sql, (type, deviceId, ticketSignId, gateNo, comment, nowDate, nowDate))
            self.connection.commit()
            return cursor.rowcount
        except Exception as e:
            self.connection.rollback()
            print(f"Error: {e}")

    def memberCheckIn(self, params):
        # 檢查報名資料是否已存在
        ticketSignID = params.get('ticketSignID', 0)
        date = params.get('date', '')
        try:
            self.connection.begin()
            with self.connection.cursor() as cursor:
                if date != '':
                    sql = f"SELECT id FROM new_ticket_checkin WHERE ticket_sign_id = {ticketSignID} AND DATE(create_at) = '{date}'"
                else:
                    sql = f"SELECT id FROM new_ticket_checkin WHERE ticket_sign_id = {ticketSignID}"
                cursor.execute(sql)
                checkin = cursor.fetchall()
            self.connection.commit()
            return checkin
        except Exception as e:
            self.connection.rollback()
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
        except Exception as e:
            print(f"Error: {e}")

    def getMemberPhoneBindMemberNo(self, ticketID):
        # 根據核銷裝置綁定的ticketID取得已登記參與活動的會員
        try:
            with self.connection.cursor() as cursor:
                sql = f"SELECT m.phone_number AS phone_number, m.no AS member_no, m.cid AS cid FROM new_ticket_sign s LEFT JOIN new_member AS m on s.member_id = m.id WHERE ticket_id in ({ticketID}) GROUP BY member_no";
                cursor.execute(sql)
                data = cursor.fetchall()

                # result = {item['phone_number']: item['member_no'] for item in data}

                result = {item['phone_number']: {'member_no':item['member_no'], 'cid':item['cid']} for item in data}
                return result
        except Exception as e:
            print(f"Error: {e}")