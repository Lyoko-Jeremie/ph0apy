# %%
import time
from js import sendCmd
from js import getBufMsgList
from js import jsSleepWithCallbackEvery

from typing import List, Dict, Any
from functools import reduce


class FH0A:
    COUNT: int = 1
    RESPONSE_TIMEOUT: int = 10
    uav_statement: Dict[str, Dict[str, Any]] = {}
    cmd_table: Dict[int, str] = {}

    def __init__(self,
                 response_timeout=RESPONSE_TIMEOUT):
        self.response_timeout = response_timeout

    def sleep(self, wait_time: int):
        """
        wait函数用于等待
        :param wait_time:等待时间，单位为秒
        """
        jsSleepWithCallbackEvery(
            wait_time * 1000, 50,
            lambda: self.__receive_msg()
        )

    @staticmethod
    def _split_state(acc: Dict, x: str):
        if ':' in x:
            p = x.split(':')
            acc[p[0]] = p[1]
        return acc

    def _receive_msg(self):
        """
        解析返回数据
        :return: None
        """
        msgs: List[str] = getBufMsgList()
        for msg in msgs:
            m: List[str] = msg.split(' ')
            if len(m) >= 3:
                if m[1] == '0' and m[2] == 'state':
                    states: str = m[3]
                    st = reduce(
                        self._split_state,
                        states.split(';'),
                        {}
                    )
                    if m[0] in self.uav_statement:
                        self.uav_statement[m[0]].update(st)
                    else:
                        self.uav_statement[m[0]] = st
                else:
                    # TODO cmd table
                    pass
            pass

    def _sendCmd(self, command: str, cmdId: int):
        self.tag = self.tag + 1
        # TODO cmd table
        self.cmd_table[cmdId] = command
        return sendCmd(command)

    def _connect(self, port: str) -> bool:
        """
        command函数用于连接无人机
        :param port:飞鸿0A无人机为端口号 COM3 ，大疆TT无人机为ip地址
        :return:连接状态是否成功，是则返回True,否则返回False
        """
        if port in self.uav_statement:
            return True
        command = port + ' ' + str(self.tag * 2 + 1) + ' command'
        back = self._sendCmd(command, self.tag * 2 + 1)
        # return back
        return True

    # 飞鸿的ip字符串为端口号，TT的ip字符串为ip地址
    def add_uav(self, port: str):
        """
        input_uav函数用于添加无人机
        :param ip:飞鸿0A无人机的ip字符串为端口号，大疆TT无人机的ip字符串为ip地址
        """
        if self._connect(port):
            y = {}
            self.uav_statement[port] = y
            self._receive_msg()

    def get_position(self, port: str):
        """
        get_position函数用于获取无人机当前位置
        :param ip:无人机插入序号
        :return:h,x,y
        """
        if port in self.uav_statement:
            st = self.uav_statement[port]
            return st['x'], st['y'], st['h']
        h = x = y = ''
        return h, x, y

    def show_uav_list(self):
        """
        show_uav_list函数用于查看所有无人机
        :return:string
        """
        for (port, state) in self.uav_statement.items():
            print("port: {0} state: {1}".format(port, state))


    def __send_commond_without_return(self, command: str, cmdId: int):
        self._sendCmd(str(command), cmdId)

    # %% TODO rewrite/review follow code   vvvvvvvvvvvvvvvvvvvvvvvvvv

    def __send_commond_with_return(self, command: str, timeout: int = RESPONSE_TIMEOUT) -> str:
        timestamp = time.time()
        self._sendCmd(str(command))

        answer = []
        while 1:
            answer = self.__get_state_list()
            if time.time() - timestamp <= timeout:
                if answer != '':
                    answers = answer.split(',')
                    for x in range(len(answers)):
                        y1 = answers[x].split()
                        y2 = command.split()
                        if y1[0] == y2[0] and y1[1] == int(y2[1]) + 1 and y1[2] == 'ok':
                            return 'ok'
            elif time.time() - timestamp > timeout:
                return 'error'

    def __get_state_list(self):
        msgs = getBufMsgList()
        state_msgs = ''.join(filter(lambda x: 'state' not in x, msgs))

        if state_msgs != '':
            return state_msgs

    def land(self, ip: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' land'
        back = self.__send_commond_with_return(command, timeout=20)
        self.tag = self.tag + 1

        if back == 'ok':
            self.__update_uav_statement(self.uav_statement[ip]['ip'], True)
            return True
        elif back == 'error':
            return False

    def takeoff(self, ip: int, high: int):
        if self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' takeoff ' + str(high)
        back = self.__send_commond_with_return(command, timeout=20)
        self.tag = self.tag + 1

        if back == 'ok':
            self.__update_uav_statement(self.uav_statement[ip]['ip'], True)
            return True
        elif back == 'error':
            return False

    # %% TODO rewrite/review above code   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def move(self, ip: int, direct: int, distance: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' move ' + str(direct) + ' ' + str(
            distance)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def arrive(self, ip: int, x: int, y: int, z: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' arrive ' + str(x) + ' ' + str(
            y) + ' ' + str(z)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def flip(self, ip: int, direction: int, circle: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' flip ' + str(direction) + ' ' + str(
            circle)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def rotate(self, ip: int, degree: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' rotate ' + str(degree)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def speed(self, ip: int, speed: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' speed ' + str(speed)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def high(self, ip: int, high: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' high ' + str(high)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def led(self, ip: int, mode: int, r: int, g: int, b: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' led ' + str(mode) + ' ' + str(
            r) + ' ' + str(g) + ' ' + str(b)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def mode(self, ip: int, mode: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' mode ' + str(mode)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def visionMode(self, ip: int, mode: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' visionMode ' + str(mode)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def visionColor(self, ip: int, mode: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' visionColor ' + str(mode)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def patrol_line_direction(self, ip: int, direction: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' patrol_line_direction ' + str(
            direction)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def distinguish_label(self, ip: int, id: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' distiniguish_label ' + str(id)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def toward_move_label(self, ip: int, direction: int, distance: int, id: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' toward_move_label ' + str(
            direction) + ' ' + str(distance) + ' ' + str(id)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def obstacle_range(self, ip: int, distance: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' obstacle_range ' + str(distance)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def solenoid(self, ip: int, switch: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' solenoid ' + str(switch)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def steering(self, ip: int, angle: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' steering ' + str(angle)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def hover(self, ip: int):
        if not self.uav_statement[ip]['is_flying']:
            return False
        command = self.uav_statement[ip]['ip'] + ' ' + str(self.tag * 2 + 1) + ' hover'
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    # %% TODO rewrite/review follow code
    def end(self):
        for (port, uav) in self.uav_statement.items():
            if uav['is_flying']:
                self.land(port)

    def __del__(self):
        self.end()
