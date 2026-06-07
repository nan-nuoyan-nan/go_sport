import sys 
import time
import os
import threading

cur = os.path.dirname(os.path.abspath(__file__))
lib = os.path.join(cur,'../lib/python/arm64')
sys.path.append(lib)
import robot_interface as sdk

class Sport:
    """
    Go1 运动控制 - 实时注入模式
    
    用法:
        s = Sport()
        s.start()                           # 后台启动
        s.will_run = {'type':'move','vx':0.3,'t':3}  # 注入动作
        # 动作完成后 will_run 自动清空
    """
    
    def __init__(self):
        # 初始化UDP通信
        HIGHLEVEL = 0xee
        self.udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
        self.cmd = sdk.HighCmd()
        self.dog = sdk.HighState()
        self.udp.InitCmdData(self.cmd)
        
        self.motiontime = 0         # 全局计时器
        self.start_tick = 0         # 动作开始时刻
        self.will_run = {}          # 外部注入的动作
        self.running = False
        
    def start(self):
        """后台启动主循环"""
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()
        
    def _loop(self):
        """500Hz主循环"""
        while self.running:
            time.sleep(0.002)
            self.motiontime += 1
            
            self.udp.Recv()
            self.udp.GetRecv(self.dog)
            
            # 默认站立
            self._stand()
            
            # 执行注入的动作
            if self.will_run:
                t = self.will_run.get('t', 0)
                
                if self.start_tick == 0:
                    self.start_tick = self.motiontime
                    print(f"[Sport] 开始: {self.will_run}")
                
                self._apply(self.will_run)
                
                # 时间到，清空
                if t > 0 and self.motiontime - self.start_tick >= int(t * 500):
                    print(f"[Sport] 完成")
                    self.will_run = {}
                    self.start_tick = 0
            else:
                self.start_tick = 0
            
            self.udp.SetSend(self.cmd)
            self.udp.Send()
            
    def _stand(self):
        """默认站立状态"""
        self.cmd.mode = 1
        self.cmd.gaitType = 0
        self.cmd.velocity = [0, 0]
        self.cmd.yawSpeed = 0
        self.cmd.footRaiseHeight = 0
        self.cmd.bodyHeight = 0
        self.cmd.euler = [0, 0, 0]
        
    def _apply(self, a):
        """应用动作参数"""
        typ = a.get('type', 'stand')
        
        if typ == 'move':
            self.cmd.mode = 2
            self.cmd.gaitType = a.get('gait', 1)
            self.cmd.velocity = [a.get('vx', 0), a.get('vy', 0)]
            self.cmd.yawSpeed = 0
            self.cmd.footRaiseHeight = a.get('foot', 0)
            
        elif typ == 'turn':
            self.cmd.mode = 2
            self.cmd.gaitType = a.get('gait', 1)
            self.cmd.velocity = [0, 0]
            self.cmd.yawSpeed = a.get('wz', 0)
            self.cmd.footRaiseHeight = a.get('foot', 0)
            
        elif typ == 'move_turn':
            self.cmd.mode = 2
            self.cmd.gaitType = a.get('gait', 1)
            self.cmd.velocity = [a.get('vx', 0), a.get('vy', 0)]
            self.cmd.yawSpeed = a.get('wz', 0)
            self.cmd.footRaiseHeight = a.get('foot', 0)
            
        elif typ == 'leap':
            self.cmd.mode = 2
            self.cmd.gaitType = 2
            self.cmd.velocity = [a.get('vx', 0.15), 0]
            self.cmd.yawSpeed = 0
            self.cmd.footRaiseHeight = a.get('foot', 0.1)
            self.cmd.bodyHeight = a.get('height', 0.03)
            self.cmd.euler = [0, -0.05, 0]


if __name__ == '__main__':
    s = Sport()
    s.start()
    print("[Sport] 已启动")
    
    # 测试：直走3秒
    s.will_run = {'type': 'move', 'vx': 0.3, 'gait': 1, 't': 3}
    
    import time
    while s.will_run:
        time.sleep(0.1)
    print("[Test] 完成")
