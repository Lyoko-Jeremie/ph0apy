# %%
import time

from js import printString
from js import sendCmd
from js import getBufMsgList
from js import jsSleepWithCallbackEvery

from typing import List, Dict, Any, Tuple, Union, Literal
from functools import reduce


class FH0A:
    COUNT: int = 1
    RESPONSE_TIMEOUT: int = 10
    uav_statement: Dict[str, Dict[str, Any]] = {}
    cmd_table: Dict[int, Tuple[str, Union[str, None]]] = {}
    tag: int = 1

    def __init__(self,
                 response_timeout=RESPONSE_TIMEOUT):
        self.response_timeout = response_timeout

    def sleep(self, wait_time: int) -> None:
        """
        wait 函数用于等待
        :param wait_time: 等待时间，单位为秒
        """
        jsSleepWithCallbackEvery(
            wait_time * 1000, 50,
            lambda: self._receive_msg()
        )
        # startTime = time.time() * 1000
        # endTime = time.time() * 1000
        # last = 0
        # while endTime - startTime < wait_time * 1000:
        #     if (endTime - startTime) > (last * 50):
        #         self._receive_msg()
        #         last = last + 1
        #     endTime = time.time() * 1000
        # pass

    def _split_state(self, acc: Dict, x: str) -> Dict:
        if ':' in x:
            p = x.split(':')
            acc[p[0]] = p[1]
        return acc

    def _receive_msg(self) -> None:
        """
        解析返回数据
        :return: None
        """
        msgs: List[str] = getBufMsgList().split('\n')
        for msg in msgs:
            m: List[str] = msg.split(' ')
            if len(m) >= 3:
                if m[1] == '0' and m[2] == 'status':
                    states: str = m[3]
                    st: Dict[str, Any] = reduce(
                        self._split_state,
                        states.split(';'),
                        {}
                    )
                    if m[0] in self.uav_statement:
                        self.uav_statement[m[0]].update(st)
                    else:
                        self.uav_statement[m[0]] = st
                    # update `is_flying` state from h/lock_flag info
                    if 'lock_flag' in self.uav_statement[m[0]]:
                        self.uav_statement[m[0]]['is_flying'] = self.uav_statement[m[0]]['lock_flag']
                    if 'loc_x' in self.uav_statement[m[0]]:
                        self.uav_statement[m[0]]['x'] = self.uav_statement[m[0]]['loc_x']
                    if 'loc_y' in self.uav_statement[m[0]]:
                        self.uav_statement[m[0]]['y'] = self.uav_statement[m[0]]['loc_y']
                    if 'high' in self.uav_statement[m[0]]:
                        self.uav_statement[m[0]]['h'] = self.uav_statement[m[0]]['high']
                elif m[1] != '0':
                    # cmd table
                    cId = int(m[1]) - 1
                    if cId in self.cmd_table:
                        tt = self.cmd_table[cId]
                        self.cmd_table[cId] = (tt[0], msg)
                    pass
            pass

    def _sendCmd(self, command: str, cmdId: int) -> bool:
        self.tag = self.tag + 1
        # cmd table
        self.cmd_table[cmdId] = (command, None)
        self._receive_msg()
        return sendCmd(command)

    def _open(self, port: str) -> bool:
        """
        command函数用于连接无人机
        :param port:飞鸿0A无人机为端口号 COM3 ，TT无人机为ip地址
        :return:连接状态是否成功，是则返回True,否则返回False
        """
        # if port in self.uav_statement:
        #     return True
        # command = port + ' ' + str(self.tag * 2 + 1) + ' command'
        command = f"{port} {self.tag * 2 + 1} open"
        back = self._sendCmd(command, self.tag * 2 + 1)
        # return back
        return True

    # 飞鸿的ip字符串为端口号，TT的ip字符串为ip地址
    def add_uav(self, port: str) -> None:
        """
        input_uav函数用于添加无人机
        :param port:飞鸿0A无人机的ip字符串为端口号，TT无人机的ip字符串为ip地址
        """
        if self._open(port):
            y = {'x': '', 'y': '', 'h': '', 'is_flying': False}
            self.uav_statement[port] = y
            self._receive_msg()

    def get_position(self, port: str) -> Tuple[str, str, str]:
        """
        get_position函数用于获取无人机当前位置
        :param port: 无人机端口号
        :return:h,x,y
        """
        self._receive_msg()
        if port in self.uav_statement:
            st: Dict[str, Any] = self.uav_statement[port]
            return st['x'], st['y'], st['h']
        h = x = y = ''
        return h, x, y

    def get_state(self, port: str) -> Union[Dict, None]:
        """
        get_position函数用于获取无人机当前位置
        :param port: 无人机端口号
        :return:h,x,y
        """
        self._receive_msg()
        if port in self.uav_statement:
            st: Dict[str, Any] = self.uav_statement[port]
            return st
        return None

    def is_tag_ok(self, port: str):
        """
        is_dot_ok 函数用于检查无人机当前是否已经检测到指定二维码
        :param port: 无人机端口号
        :return: "0" or "1"
        """
        return self.uav_statement[port].get('is_tag_ok', '0')

    def is_dot_ok(self, port: str):
        """
        is_dot_ok 函数用于检查无人机当前是否已经检测到指定颜色色块 或 已经检测到交点
        :param port: 无人机端口号
        :return: "0" or "1"
        """
        return self.uav_statement[port].get('is_dot_ok', '0')

    def show_uav_list(self) -> None:
        """
        show_uav_list函数用于查看所有无人机
        :return:string
        """
        self._receive_msg()
        for (port, state) in self.uav_statement.items():
            print("port: {0} state: {1}".format(port, state))

    def _send_commond_without_return(self, command: str, cmdId: int) -> bool:
        return self._sendCmd(str(command), cmdId)

    def _send_commond_with_return(self, command: str, cmdId: int, timeout: int = RESPONSE_TIMEOUT) -> Union[str, None]:
        self._sendCmd(str(command), cmdId)
        timestamp = time.time()

        while 1:
            jsSleepWithCallbackEvery(
                200, 20,
                lambda: self._receive_msg()
            )
            if time.time() - timestamp > timeout:
                return None
            if self.cmd_table[cmdId][1] != None:
                continue
            else:
                return self.cmd_table[cmdId][1]

    def land(self, port: str) -> Literal[True]:
        """
        land函数用于控制无人机降落
        :param port: 无人机端口号
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return True
        command = f"{port} {self.tag * 2 + 1} land"
        back = self._send_commond_without_return(command, self.tag * 2 + 1)
        # back = self._send_commond_with_return(command, self.tag * 2 + 1, timeout = 20)

        self.uav_statement[port]['is_flying'] = False
        return True

    def emergency(self, port: str) -> Literal[True]:
        """
        emergency 函数用于控制无人机紧急降落
        :param port: 无人机端口号
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return True
        command = f"{port} {self.tag * 2 + 1} emergency"
        back = self._send_commond_without_return(command, self.tag * 2 + 1)
        # back = self._send_commond_with_return(command, self.tag * 2 + 1, timeout = 20)

        self.uav_statement[port]['is_flying'] = False
        return True

    def takeoff(self, port: str, high: int) -> Literal[True]:
        """
        takeoff函数用于控制无人机起飞
        :param port: 无人机端口号
        :param high:起飞高度（厘米）
        """
        self._receive_msg()
        # if self.uav_statement[port]['is_flying']:
        #     return True
        command = f"{port} {self.tag * 2 + 1} takeoff {high}"
        back = self._send_commond_without_return(command, self.tag * 2 + 1)
        # back = self._send_commond_with_return(command, self.tag * 2 + 1, timeout = 20)

        self.uav_statement[port]['is_flying'] = True
        return True

    def up(self, port: str, distance: int) -> bool:
        """
        up 向上移动
        :param port: 无人机端口号
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} up {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def down(self, port: str, distance: int) -> bool:
        """
        down 向下移动
        :param port: 无人机端口号
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} down {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def forward(self, port: str, distance: int) -> bool:
        """
        forward 向前移动
        :param port: 无人机端口号
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} forward {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def back(self, port: str, distance: int) -> bool:
        """
        back 向后移动
        :param port: 无人机端口号
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} back {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def left(self, port: str, distance: int) -> bool:
        """
        left 向左移动
        :param port: 无人机端口号
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} left {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def right(self, port: str, distance: int) -> bool:
        """
        right 向右移动
        :param port: 无人机端口号
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} right {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def _move(self, port: str, direct: int, distance: int) -> bool:
        """
        move 函数用于控制无人机移动
        :param port: 无人机端口号
        :param direct:移动方向（1上2下3前4后5左6右）
        :param distance:移动距离（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} move {direct} {distance}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def goto(self, port: str, x: int, y: int, h: int) -> bool:
        """
        goto 函数用于控制无人机到达指定位置
        :param port: 无人机端口号
        :param x: x轴方向位置（厘米）
        :param y: y轴方向位置（厘米）
        :param h: 高度（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} goto {x} {y} {h}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def flip(self, port: str, direction: str) -> bool:
        """
        flip函数用于控制无人机翻滚
        :param port: 无人机端口号
        :param direction: 翻滚方向（f前 b后 l左 r右）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} flip {direction} 1"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def rotate(self, port: str, degree: int) -> bool:
        """
        rotate函数用于控制无人机自转
        :param port: 无人机端口号
        :param degree: 自转方向和大小（正数顺时针，负数逆时针，单位为度数）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} rotate {degree}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def cw(self, port: str, degree: int) -> bool:
        """
        cw 控制无人机顺时针自转
        :param port: 无人机端口号
        :param degree: 自转角度度数
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} cw {degree}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def ccw(self, port: str, degree: int) -> bool:
        """
        ccw 函数用于控制无人机逆时针自转
        :param port: 无人机端口号
        :param degree: 自转角度度数
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} ccw {degree}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def speed(self, port: str, speed: int) -> bool:
        """
        speed函数用于控制无人机飞行速度
        :param port: 无人机端口号
        :param speed: 飞行速度（0-200厘米/秒）
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} setSpeed {speed}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def high(self, port: str, high: int) -> bool:
        """
        high用于控制无人机飞行高度
        :param port: 无人机端口号
        :param high: 飞行高度（厘米）
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} setHeight {high}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def led(self, port: str, r: int, g: int, b: int) -> bool:
        """
        led函数控制无人机灯光
        :param port: 无人机端口号
        :param r: 灯光颜色R通道
        :param g: 灯光颜色G通道
        :param b: 灯光颜色B通道
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} light {r} {g} {b}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def bln(self, port: str, r: int, g: int, b: int) -> bool:
        """
        led函数控制无人机灯光
        :param port: 无人机端口号
        :param r: 灯光颜色R通道
        :param g: 灯光颜色G通道
        :param b: 灯光颜色B通道
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} bln {r} {g} {b}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def rainbow(self, port: str, r: int, g: int, b: int) -> bool:
        """
        led函数控制无人机灯光
        :param port: 无人机端口号
        :param r: 灯光颜色R通道
        :param g: 灯光颜色G通道
        :param b: 灯光颜色B通道
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} rainbow {r} {g} {b}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def mode(self, port: str, mode: int) -> bool:
        """
        mode函数用于切换飞行模式
        :param port: 无人机端口号
        :param mode:飞行模式（1常规2巡线3跟随4单机编队）
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} airplane_mode {mode}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    # def _visionMode(self, port: str, mode: int) -> bool:
    #     """
    #     visionMode函数用于设置视觉工作模式
    #     :param port: 无人机端口号
    #     :param mode:视觉工作模式（1点检测2线检测3标签检测4二维码扫描5条形码扫描）
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} visionMode {mode}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    def color_detect(self, port: str, L_L: int, L_H: int, A_L: int, A_H: int, B_L: int, B_H: int) -> bool:
        """
        visionColor函数用于设置视觉工作模式为色块检测
        :param port: 无人机端口号
        :param L_L: 色块L通道的最低检测值
        :param L_H: 色块L通道的最高检测植
        :param A_L: 色块A通道的最低检测植
        :param A_H: 色块A通道的最高检测值
        :param B_L: 色块B通道的最低检测植
        :param B_H: 色块B通道的最高检测植z
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} colorDetect {L_L} {L_H} {A_L} {A_H} {B_L} {B_H}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def color_detect_label(self, port: str, label: str) -> bool:
        """
        visionColor函数用于设置视觉工作模式为色块检测
        :param port: 无人机端口号
        :param label: 预定义色彩标签名
        """
        self._receive_msg()
        # if not self.uav_statement[port]['is_flying']:
        #     return False
        command = f"{port} {self.tag * 2 + 1} colorDetectLabel {label}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    # def patrol_line_direction(self, port: str, direction: int) -> bool:
    #     """
    #     patrol_line_direction函数用于切换无人机巡线方向
    #     :param port: 无人机端口号
    #     :param direction:巡线方向（1前2后3左4右）
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} patrol_line_direction {direction}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    # def distinguish_label(self, port: str, id: int) -> bool:
    #     """
    #     distinguish_label函数用于指定识别某个标签号
    #     :param port: 无人机端口号
    #     :param id:目标标签号，设置后只识别该号标签
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} distiniguish_label {id}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    # def toward_move_label(self, port: str, direction: int, distance: int, id: int) -> bool:
    #     """
    #     toward_move_label函数指定无人机移动某距离寻找某号标签
    #     :param port: 无人机端口号
    #     :param direction:移动方向（1上2下3前4后5左6右）
    #     :param distance:移动距离（厘米）
    #     :param id:目标标签号，移动过程中看到该标签会自动悬停在上方
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} toward_move_label {direction} {distance} {id}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    # def obstacle_range(self, port: str, distance: int) -> bool:
    #     """
    #     obstacle_range函数用于设置障碍物检测范围
    #     :param port: 无人机端口号
    #     :param distance:检测范围（厘米）
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} obstacle_range {distance}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    # def solenoid(self, port: str, switch: int) -> bool:
    #     """
    #     solenoid函数用于无人机电磁铁控制
    #     :param port: 无人机端口号
    #     :param switch:电磁铁控制（0关闭1打开）
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} solenoid {switch}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    # def steering(self, port: str, angle: int) -> bool:
    #     """
    #     steering函数用于无人机舵机控制
    #     :param port: 无人机端口号
    #     :param angle:舵机角度（+/-90度）
    #     """
    #     self._receive_msg()
    #     if not self.uav_statement[port]['is_flying']:
    #         return False
    #     command = f"{port} {self.tag * 2 + 1} steering {angle}"
    #     self._send_commond_without_return(command, self.tag * 2 + 1)
    #     return True

    def stop(self, port: str) -> bool:
        return self.hover(port)

    def hover(self, port: str) -> bool:
        """
        hover 函数用于控制无人机悬停
        :param port: 无人机端口号
        """
        self._receive_msg()
        if not self.uav_statement[port]['is_flying']:
            return False
        command = f"{port} {self.tag * 2 + 1} hover"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    # def end(self) -> None:
    #     """
    #     end函数用于降落所有编队无人机
    #     """
    #     for (port, uav) in self.uav_statement.items():
    #         if uav['is_flying']:
    #             self.land(port)

    def set_single_setting(self, port: str, mode: int, channel: int, address: int):
        self._receive_msg()
        command = f"{port} {self.tag * 2 + 1} single_setting {mode} {channel} {address}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        pass

    def set_multiply_setting(self, port: str, mode: int, airplaneNumber: int, channel: int, address: int):
        self._receive_msg()
        command = f"{port} {self.tag * 2 + 1} multiply_setting {mode} {airplaneNumber} {channel} {address}"
        self._send_commond_without_return(command, self.tag * 2 + 1)
        return True

    def cleanup(self):
        """
        cleanup函数用于清理内部状态表
        :return:
        """
        self.uav_statement = {}
        self.cmd_table = {}

    # def __del__(self):
    #     self.end()
