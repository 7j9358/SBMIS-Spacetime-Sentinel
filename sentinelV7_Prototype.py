import requests
import numpy as np
import pandas as pd
import time
import os
from datetime import datetime

class SBMIS_V7_4_Continuum:
    def __init__(self):
        self.BASE_VOID_BT = 7.55
        self.BASE_PHASE = 2.41
        self.PHI_FREQ = 1.61803398875
        self.MAX_POWER = 5.0
        
        self.url = "https://services.swpc.noaa.gov/products/solar-wind/mag-5-minute.json"
        self.nav_mode = "STANDBY"
        self.target_ts = None
        self.logs = []
        
        # 艙內實時平滑數值
        self.cabin_bt = 0.0
        self.cabin_phase = 0.0

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def add_log(self, msg, bt=None, phase=None):
        ts = time.strftime('%H:%M:%S')
        detail = f" [B:{bt:6.3f}|θ:{phase:+7.4f}]" if bt else ""
        self.logs.append(f"[{ts}]{detail} {msg}")
        if len(self.logs) > 6: self.logs.pop(0)

    def get_historical_offset(self, dt):
        """V7.4 特有：根據年份產生獨特的時空偏移指紋"""
        seed = int(dt.timestamp()) % 10000
        np.random.seed(seed)
        # 模擬地球磁極隨時間的微小飄移 (±0.01 nT)
        bt_offset = np.random.uniform(-0.015, 0.015)
        phase_offset = np.random.uniform(-0.005, 0.005)
        return bt_offset, phase_offset

    def run(self):
        self.clear_screen()
        print("="*70)
        print("   SBMIS Sentinel V7.4-CONTINUUM ")
        print("="*70)
        
        mode = input("航行方向 [1]過去 (PAST) [2]未來 (FUTURE): ")
        self.nav_mode = "PAST" if mode == '1' else "FUTURE"
        ts_str = input("目標精確座標 (YYYY-MM-DD HH:MM:SS): ")
        self.target_ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        
        # 計算該特定時空的動態目標
        b_off, p_off = self.get_historical_offset(self.target_ts)
        dynamic_target_bt = self.BASE_VOID_BT + b_off
        dynamic_target_phase = (self.BASE_PHASE if self.nav_mode == "PAST" else -self.BASE_PHASE) + p_off
        
        self.add_log(f"🛰️ 座標鎖定。動態指紋計算完成：{ts_str}")

        while True:
            try:
                # 抓取衛星數據
                res = requests.get(self.url, timeout=10).json()
                env_bt = float(res[-1][6])
                bx, by = float(res[-1][1]), float(res[-1][2])
                env_phase = np.arctan2(by, bx)
                
                # 初始化艙內數據
                if self.cabin_bt == 0: self.cabin_bt = env_bt
                if self.cabin_phase == 0: self.cabin_phase = env_phase
                
                # --- 模擬 V7.3 趨近動畫 (平滑至 V7.4 動態目標) ---
                self.cabin_bt += (dynamic_target_bt - self.cabin_bt) * 0.75
                self.cabin_phase += (dynamic_target_phase - self.cabin_phase) * 0.75
                
                # 物理穩定度計算 (V7.2 物理引擎整合)
                bt_err = abs(self.cabin_bt - dynamic_target_bt)
                phase_err = abs(self.cabin_phase - dynamic_target_phase)
                # 非線性流形張力公式
                stability = np.exp(-(bt_err**2 * 15 + phase_err**2 * 80)) * 100

                self.clear_screen()
                print("="*70)
                print(f" SBMIS V7.4-CONTINUUM | 座標: {self.target_ts} | 模式: {self.nav_mode}")
                print("="*70)
                
                print(f"【 歷史時空指紋 (動態目標) 】")
                print(f" > 指紋 Bt:    {dynamic_target_bt:8.4f} nT (偏移: {b_off:+.4f})")
                print(f" > 指紋 Phase: {dynamic_target_phase:8.4f} rad (偏移: {p_off:+.4f})")
                print("-" * 70)
                
                print(f"【 維度趨近觀測 】")
                print(f" > 外部環境: Bt:{env_bt:6.2f} nT | θ:{env_phase:+7.4f} rad")
                print(f" > 艙內狀態: Bt:{self.cabin_bt:6.4f} nT | θ:{self.cabin_phase:+7.4f} rad")
                print("-" * 70)
                
                # 補償出力
                bt_comp = self.cabin_bt - env_bt
                print(f"【 補償器狀態 】 注入功率: {bt_comp:+7.4f} nT | 諧振: {self.PHI_FREQ:.6f} MHz")
                
                # 穩定度視覺化
                bar = "⚡" * int(stability/10) + ".." * (10 - int(stability/10))
                print(f"\n【 時空流形穩定度 】 {bar} {stability:.6f}%")
                
                if stability > 99.99:
                    status = "✅ [ STATUS: VOID ENTRANCE ACTIVE ] - 熵減啟動"
                    self.add_log("🌀 進入相變區間，時空褶皺完成", self.cabin_bt, self.cabin_phase)
                else:
                    status = "⏳ [ STATUS: SYNCHRONIZING ] - 指紋比對中"
                    self.add_log("📡 場域補償修正中...", self.cabin_bt, self.cabin_phase)
                
                print(f"\n當前狀態: {status}")
                print("-" * 70)
                print("[ 任務詳細日誌 (Full Log) ]")
                for log in self.logs: print(f" > {log}")

                # 存檔 (V7.1 邏輯)
                if stability > 99.9:
                    fn = f"V7_4_SUCCESS_{int(time.time())}.csv"
                    pd.DataFrame({
                        'Target': [self.target_ts], 'Stability': [stability], 
                        'Final_Bt': [self.cabin_bt], 'Final_Theta': [self.cabin_phase]
                    }).to_csv(fn)

                time.sleep(12)
                
            except Exception as e:
                time.sleep(5)

if __name__ == "__main__":
    V7_4 = SBMIS_V7_4_Continuum()
    V7_4.run()