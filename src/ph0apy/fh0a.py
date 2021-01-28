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
        :param port:飞鸿0A无人机的ip字符串为端口号，大疆TT无人机的ip字符串为ip地址
        """
        if self._connect(port):
            y = {'x': '', 'y': '', 'h': ''}
            self.uav_statement[port] = y
            self._receive_msg()

    def get_position(self, port: str):
        """
        get_position函数用于获取无人机当前位置
        :param port:无人机插入序号
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

    def land(self, port: int):
        """
        land函数用于控制无人机降落
        :param port:无人机插入序号
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' land'
        back = self.__send_commond_with_return(command, timeout=20)

        if back == 'ok':
            self.__update_uav_statement(self.uav_statement[port]['port'], True)
            return True
        elif back == 'error':
            return False

    def takeoff(self, port: int, high: int):
        """
        takeoff函数用于控制无人机起飞
        :param port:无人机插入序号
        :param high:起飞高度（厘米）
        """
        if self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' takeoff ' + str(high)
        back = self.__send_commond_with_return(command, timeout=20)

        if back == 'ok':
            self.__update_uav_statement(self.uav_statement[port]['port'], True)
            return True
        elif back == 'error':
            return False

    # %% TODO rewrite/review above code   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    def move(self, port: int, direct: int, distance: int):
        """
        move函数用于控制无人机移动
        :param port:无人机插入序号
        :param direct:移动方向（1上2下3前4后5左6右）
        :param distance:移动距离（厘米）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' move ' + str(direct) + ' ' + str(
            distance)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def arrive(self, port: int, x: int, y: int, z: int):
        """
        arrive函数用于控制无人机到达指定位置
        :param port: 无人机插入序号
        :param x:x轴方向位置（厘米）
        :param y:y轴方向位置（厘米）
        :param z:z轴方向位置（厘米）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' arrive ' + str(x) + ' ' + str(
            y) + ' ' + str(z)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def flip(self, port: int, direction: int, circle: int):
        """
        flip函数用于控制无人机翻滚
        :param port:无人机插入序号
        :param direction:翻滚方向（1前2后3左4右）
        :param circle:翻滚圈数（<=2）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' flip ' + str(
            direction) + ' ' + str(
            circle)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def rotate(self, port: int, degree: int):
        """
        rotate函数用于控制无人机自转
        :param port:无人机插入序号
        :param degree:自转方向和大小（正数顺时针，负数逆时针，单位为度数）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' rotate ' + str(degree)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def speed(self, port: int, speed: int):
        """
        speed函数用于控制无人机飞行速度
        :param port:无人机插入序号
        :param speed:飞行速度（0-200厘米/秒）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' speed ' + str(speed)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def high(self, port: int, high: int):
        """
        high用于控制无人机飞行高度
        :param port:无人机插入序号
        :param high:飞行高度（厘米）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' high ' + str(high)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def led(self, port: int, mode: int, r: int, g: int, b: int):
        """
        led函数控制无人机灯光
        :param port:无人机插入序号
        :param mode:灯光模式（0常亮1呼吸灯2七彩变换）
        :param r:灯光颜色R通道
        :param g:灯光颜色G通道
        :param b:灯光颜色B通道
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' led ' + str(mode) + ' ' + str(
            r) + ' ' + str(g) + ' ' + str(b)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def mode(self, port: int, mode: int):
        """
        mode函数用于切换飞行模式
        :param port:无人机插入序号
        :param mode:飞行模式（1常规2巡线3跟随4单机编队）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' mode ' + str(mode)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def visionMode(self, port: int, mode: int):
        """
        visionMode函数用于设置视觉工作模式
        :param port:无人机插入序号
        :param mode:视觉工作模式（1点检测2线检测3标签检测4二维码扫描5条形码扫描）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' visionMode ' + str(mode)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def visionColor(self, port: int, L_L: int, L_H: int, A_L: int, A_H: int, B_L: int, B_H: int, mode: int = 6):
        """
        visionColor函数用于设置视觉工作模式为色块检测
        :param port:无人机插入序号
        :param L_L:色块L通道的最低检测值
        :param L_H:色块L通道的最高检测植
        :param A_L:色块A通道的最低检测植
        :param A_H:色块A通道的最高检测值
        :param B_L:色块B通道的最低检测植
        :param B_H:色块B通道的最高检测植
        :param mode:mode=6
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + \
                  ' visionColor ' + str(mode) + ' ' + str(L_L) + ' ' + str(L_H) + ' ' + \
                  str(A_L) + ' ' + str(A_H) + ' ' + str(B_L) + ' ' + str(B_H)
        self.__send_commond_without_return(command)
        return True

    def patrol_line_direction(self, port: int, direction: int):
        """
        patrol_line_direction函数用于切换无人机巡线方向
        :param port:无人机插入序号
        :param direction:巡线方向（1前2后3左4右）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' patrol_line_direction ' + str(
            direction)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def distinguish_label(self, port: int, id: int):
        """
        distinguish_label函数用于指定识别某个标签号
        :param port:无人机插入序号
        :param id:目标标签号，设置后只识别该号标签
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' distiniguish_label ' + str(id)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def toward_move_label(self, port: int, direction: int, distance: int, id: int):
        """
        toward_move_label函数指定无人机移动某距离寻找某号标签
        :param port:无人机插入序号
        :param direction:移动方向（1上2下3前4后5左6右）
        :param distance:移动距离（厘米）
        :param id:目标标签号，移动过程中看到该标签会自动悬停在上方
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' toward_move_label ' + str(
            direction) + ' ' + str(distance) + ' ' + str(id)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def obstacle_range(self, port: int, distance: int):
        """
        obstacle_range函数用于设置障碍物检测范围
        :param port:无人机插入序号
        :param distance:检测范围（厘米）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' obstacle_range ' + str(distance)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def solenoid(self, port: int, switch: int):
        """
        solenoid函数用于无人机电磁铁控制
        :param port:无人机插入序号
        :param switch:电磁铁控制（0关闭1打开）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' solenoid ' + str(switch)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def steering(self, port: int, angle: int):
        """
        steering函数用于无人机舵机控制
        :param port:无人机插入序号
        :param angle:舵机角度（+/-90度）
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' steering ' + str(angle)
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def hover(self, port: int):
        """
        hover函数用于控制无人机悬停
        :param port: 无人机插入序号
        """
        if not self.uav_statement[port]['is_flying']:
            return False
        command = self.uav_statement[port]['port'] + ' ' + str(self.tag * 2 + 1) + ' hover'
        self.__send_commond_without_return(command, self.tag * 2 + 1)
        return True

    # %% TODO rewrite/review follow code
    def end(self):
        """
        end函数用于降落所有编队无人机
        """
        for (port, uav) in self.uav_statement.items():
            if uav['is_flying']:
                self.land(port)

    def __del__(self):
        self.end()
