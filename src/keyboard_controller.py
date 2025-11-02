"""
キーボード操作を管理するモジュール

カメラの移動・回転・ズーム操作を提供します：
- W/S: 前後移動
- A/D: 左右移動
- R/F: 上下移動
- Q/E: 視点回転
- Z/X: ズームイン/アウト
- P: 座標エクスポート
- Esc: 終了
"""

import cv2
from typing import Optional, Callable


class KeyboardController:
    """キーボード操作を管理するクラス"""
    
    def __init__(self, config: dict):
        """
        初期化
        
        :param config: キーボード操作の設定辞書
        """
        # カメラ移動・回転速度
        self.movement_speed = config['movement_speed']
        self.rotation_speed = config['rotation_speed']
        
        # ズーム設定
        self.min_focal_length = config['zoom']['min_focal_length']
        self.max_focal_length = config['zoom']['max_focal_length']
        self.zoom_step = config['zoom']['zoom_step']
        
        # 最小カメラ高さ
        self.min_camera_height = config.get('min_camera_height', 10)
        
        # 最小・最大Pitch角度
        self.min_pitch = config.get('min_pitch', -89)
        self.max_pitch = config.get('max_pitch', 89)
    
    def handle_keyboard_input(self, camera_state: dict, 
                              export_callback: Optional[Callable] = None) -> dict:
        """
        キーボード入力を処理する
        
        :param camera_state: カメラの現在状態（x, y, z, pitch, yaw, roll, focal_length）
        :param export_callback: 座標エクスポート用のコールバック関数
        :return: 更新結果 {'exit': bool, 'camera_updated': bool, 'camera_x', 'camera_y', 'camera_z', 
                          'camera_pitch', 'camera_yaw', 'camera_roll', 'focal_length'}
        """
        result = {
            'exit': False,
            'camera_updated': False,
            'camera_x': camera_state['x'],
            'camera_y': camera_state['y'],
            'camera_z': camera_state['z'],
            'camera_pitch': camera_state['pitch'],
            'camera_yaw': camera_state['yaw'],
            'camera_roll': camera_state['roll'],
            'focal_length': camera_state['focal_length']
        }
        
        # キー入力を取得
        key = cv2.waitKey(1) & 0xFF
        
        if key == 255:  # キー入力なし
            return result
        
        # キー入力を処理
        if key == 27:  # Esc key
            result['exit'] = True
        
        elif key == ord('w'):  # 前方移動（カメラの向いている方向）
            import math
            yaw_rad = math.radians(camera_state['yaw'])
            # カメラの前方向ベクトル
            forward_x = math.cos(yaw_rad)
            forward_y = -math.sin(yaw_rad)
            result['camera_x'] -= forward_x * self.movement_speed
            result['camera_y'] -= forward_y * self.movement_speed
            result['camera_updated'] = True
        
        elif key == ord('s'):  # 後方移動（カメラの向きと逆方向）
            import math
            yaw_rad = math.radians(camera_state['yaw'])
            # カメラの前方向ベクトル
            forward_x = math.cos(yaw_rad)
            forward_y = -math.sin(yaw_rad)
            result['camera_x'] += forward_x * self.movement_speed
            result['camera_y'] += forward_y * self.movement_speed
            result['camera_updated'] = True
        
        elif key == ord('a'):  # 左移動（カメラの左方向）
            import math
            yaw_rad = math.radians(camera_state['yaw'])
            # カメラの右方向ベクトル
            right_x = math.sin(yaw_rad)
            right_y = math.cos(yaw_rad)
            result['camera_x'] -= right_x * self.movement_speed
            result['camera_y'] -= right_y * self.movement_speed
            result['camera_updated'] = True
        
        elif key == ord('d'):  # 右移動（カメラの右方向）
            import math
            yaw_rad = math.radians(camera_state['yaw'])
            # カメラの右方向ベクトル
            right_x = math.sin(yaw_rad)
            right_y = math.cos(yaw_rad)
            result['camera_x'] += right_x * self.movement_speed
            result['camera_y'] += right_y * self.movement_speed
            result['camera_updated'] = True
        
        elif key == ord('q'):  # 左を向く（Yaw回転）
            result['camera_yaw'] -= self.rotation_speed
            result['camera_updated'] = True
        
        elif key == ord('e'):  # 右を向く（Yaw回転）
            result['camera_yaw'] += self.rotation_speed
            result['camera_updated'] = True
        
        elif key == ord('r'):  # 上昇
            result['camera_z'] += self.movement_speed
            result['camera_updated'] = True
        
        elif key == ord('f'):  # 下降
            result['camera_z'] = max(result['camera_z'] - self.movement_speed, self.min_camera_height)
            result['camera_updated'] = True
        
        elif key == ord('z'):  # ズームイン
            result['focal_length'] = min(result['focal_length'] + self.zoom_step, self.max_focal_length)
            result['camera_updated'] = True
        
        elif key == ord('x'):  # ズームアウト
            result['focal_length'] = max(result['focal_length'] - self.zoom_step, self.min_focal_length)
            result['camera_updated'] = True
        
        elif key == ord('p'):  # 座標エクスポート
            if export_callback:
                export_callback()
        
        return result

