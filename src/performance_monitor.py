"""
パフォーマンスモニタリングモジュール

FPS計測とパフォーマンス統計を提供します。
"""

import time
from collections import deque
from typing import Dict, Optional


class PerformanceMonitor:
    """パフォーマンス計測クラス"""
    
    def __init__(self, window_size: int = 60):
        """
        初期化メソッド
        
        :param window_size: FPS計算用のフレーム数ウィンドウサイズ
        """
        self.window_size = window_size
        self.frame_times = deque(maxlen=window_size)
        self.last_frame_time = time.perf_counter()
        self.frame_count = 0
        self.section_times: Dict[str, deque] = {}
        self.current_section_start: Optional[float] = None
        self.current_section_name: Optional[str] = None
    
    def start_frame(self):
        """新しいフレームの計測を開始"""
        current_time = time.perf_counter()
        if self.frame_count > 0:
            frame_time = current_time - self.last_frame_time
            self.frame_times.append(frame_time)
        self.last_frame_time = current_time
        self.frame_count += 1
    
    def get_fps(self) -> float:
        """
        現在のFPSを取得
        
        :return: FPS値
        """
        if len(self.frame_times) == 0:
            return 0.0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        if avg_frame_time > 0:
            return 1.0 / avg_frame_time
        return 0.0
    
    def get_frame_time_ms(self) -> float:
        """
        平均フレーム時間を取得（ミリ秒）
        
        :return: フレーム時間（ms）
        """
        if len(self.frame_times) == 0:
            return 0.0
        return (sum(self.frame_times) / len(self.frame_times)) * 1000.0
    
    def start_section(self, section_name: str):
        """
        セクションの計測を開始
        
        :param section_name: セクション名
        """
        self.current_section_name = section_name
        self.current_section_start = time.perf_counter()
    
    def end_section(self):
        """現在のセクションの計測を終了"""
        if self.current_section_start is None or self.current_section_name is None:
            return
        
        elapsed = time.perf_counter() - self.current_section_start
        
        if self.current_section_name not in self.section_times:
            self.section_times[self.current_section_name] = deque(maxlen=self.window_size)
        
        self.section_times[self.current_section_name].append(elapsed)
        self.current_section_start = None
        self.current_section_name = None
    
    def get_section_time_ms(self, section_name: str) -> float:
        """
        指定セクションの平均時間を取得（ミリ秒）
        
        :param section_name: セクション名
        :return: 平均時間（ms）
        """
        if section_name not in self.section_times or len(self.section_times[section_name]) == 0:
            return 0.0
        times = self.section_times[section_name]
        return (sum(times) / len(times)) * 1000.0
    
    def get_section_percentage(self, section_name: str) -> float:
        """
        セクションがフレーム全体に占める割合を取得
        
        :param section_name: セクション名
        :return: 割合（0-100%）
        """
        if len(self.frame_times) == 0:
            return 0.0
        
        section_time_ms = self.get_section_time_ms(section_name)
        frame_time_ms = self.get_frame_time_ms()
        
        if frame_time_ms > 0:
            return (section_time_ms / frame_time_ms) * 100.0
        return 0.0
    
    def get_stats(self) -> Dict[str, float]:
        """
        統計情報を取得
        
        :return: 統計情報の辞書
        """
        stats = {
            'fps': self.get_fps(),
            'frame_time_ms': self.get_frame_time_ms(),
            'frame_count': self.frame_count
        }
        
        for section_name in self.section_times.keys():
            stats[f'{section_name}_ms'] = self.get_section_time_ms(section_name)
            stats[f'{section_name}_pct'] = self.get_section_percentage(section_name)
        
        return stats
    
    def reset(self):
        """統計情報をリセット"""
        self.frame_times.clear()
        self.section_times.clear()
        self.frame_count = 0
        self.last_frame_time = time.perf_counter()

