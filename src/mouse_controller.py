"""
マウス操作を管理するモジュール

UE5スタイルのカメラ操作を提供します：
- 左ドラッグ: 前後移動 + Yaw回転
- 右ドラッグ: Pitch/Yaw回転（フリールック）
- 左+右ドラッグ: Y/Z軸移動（左右・上下）
- ホイールドラッグ: Y/Z軸移動（左右・上下）
- ホイール回転: ズームイン/アウト
"""

import cv2
from typing import Optional, Tuple, Callable
from calc3Dto2D import Tranceform3D2D
from coordinate_precision import CoordinatePrecision


class MouseController:
    """マウス操作を管理するクラス"""
    
    def __init__(self, config: dict):
        """
        初期化
        
        :param config: マウス操作の設定辞書
        """
        # ホイールドラッグ設定
        self.mouse_drag_sensitivity = config['mouse_drag']['sensitivity']
        self.mouse_drag_invert_x = config['mouse_drag']['invert_x']
        self.mouse_drag_invert_y = config['mouse_drag']['invert_y']
        
        # 右クリックドラッグ（ビュー回転）設定
        self.mouse_view_rotation_sensitivity = config['mouse_view_rotation']['sensitivity']
        self.mouse_view_rotation_invert_x = config['mouse_view_rotation']['invert_x']
        self.mouse_view_rotation_invert_y = config['mouse_view_rotation']['invert_y']
        self.mouse_view_rotation_min_pitch = config['mouse_view_rotation']['min_pitch']
        self.mouse_view_rotation_max_pitch = config['mouse_view_rotation']['max_pitch']
        
        # ズーム設定
        self.min_focal_length = config['zoom']['min_focal_length']
        self.max_focal_length = config['zoom']['max_focal_length']
        self.zoom_step = config['zoom']['zoom_step']
        
        # 家具ドラッグ用の状態
        self.furniture_dragging = False
        self.furniture_drag_offset_x = 0.0
        self.furniture_drag_offset_y = 0.0
        
        # ホイールドラッグによるカメラ移動用の状態
        self.camera_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_cam_x = 0.0
        self.pan_start_cam_y = 0.0
        self.pan_start_cam_z = 0.0
        
        # 左ドラッグによるUE5スタイルカメラ移動用の状態
        self.ue5_camera_moving = False
        self.ue5_move_start_x = 0
        self.ue5_move_start_y = 0
        self.ue5_move_start_cam_x = 0.0
        self.ue5_move_start_cam_y = 0.0
        self.ue5_move_start_yaw = 0.0
        
        # 右クリックドラッグによるカメラビュー回転用の状態
        self.view_rotating = False
        self.view_rotation_start_x = 0
        self.view_rotation_start_y = 0
        self.view_rotation_start_pitch = 0.0
        self.view_rotation_start_yaw = 0.0
        
        # 右+左同時ドラッグによるY/Z軸移動用の状態
        self.both_buttons_moving = False
        self.both_buttons_start_x = 0
        self.both_buttons_start_y = 0
        self.both_buttons_start_cam_x = 0.0
        self.both_buttons_start_cam_y = 0.0
        self.both_buttons_start_cam_z = 0.0
    
    def handle_mouse_event(self, event: int, x: int, y: int, flags: int, 
                          camera_state: dict,
                          furniture_hit_test: Optional[Callable] = None,
                          screen_to_world: Optional[Callable] = None) -> dict:
        """
        マウスイベントを処理する
        
        :param event: OpenCVのマウスイベント
        :param x: マウスのx座標
        :param y: マウスのy座標
        :param flags: OpenCVのフラグ
        :param camera_state: カメラの現在状態（x, y, z, pitch, yaw, focal_length）
        :param furniture_hit_test: 家具のヒットテスト関数
        :param screen_to_world: スクリーン座標をワールド座標に変換する関数
        :return: 更新されたカメラ状態とアクション情報
        """
        result = {
            'camera_updated': False,
            'furniture_action': None,  # 'select', 'drag', 'deselect'
            'camera_x': camera_state['x'],
            'camera_y': camera_state['y'],
            'camera_z': camera_state['z'],
            'camera_pitch': camera_state['pitch'],
            'camera_yaw': camera_state['yaw'],
            'focal_length': camera_state['focal_length'],
            'selected_furniture': None,
            'drag_offset': None
        }
        
        if event == cv2.EVENT_LBUTTONDOWN:
            self._handle_left_button_down(x, y, flags, camera_state, furniture_hit_test, 
                                         screen_to_world, result)
        
        elif event == cv2.EVENT_MBUTTONDOWN:
            self._handle_middle_button_down(x, y, camera_state)
        
        elif event == cv2.EVENT_MOUSEMOVE:
            self._handle_mouse_move(x, y, camera_state, screen_to_world, result)
        
        elif event == cv2.EVENT_LBUTTONUP:
            self._handle_left_button_up(x, y, camera_state, result)
        
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._handle_right_button_down(x, y, camera_state)
        
        elif event == cv2.EVENT_RBUTTONUP:
            self._handle_right_button_up(x, y, camera_state, result)
        
        elif event == cv2.EVENT_MBUTTONUP:
            self._handle_middle_button_up()
        
        elif event == cv2.EVENT_MOUSEWHEEL:
            self._handle_mouse_wheel(flags, result)
        
        return result
    
    def _handle_left_button_down(self, x: int, y: int, flags: int, camera_state: dict,
                                 furniture_hit_test: Optional[Callable],
                                 screen_to_world: Optional[Callable],
                                 result: dict):
        """左ボタン押下処理"""
        # 右ボタンも押されている場合は両ボタンモード
        if self.view_rotating:
            self.both_buttons_moving = True
            self.both_buttons_start_x = x
            self.both_buttons_start_y = y
            self.both_buttons_start_cam_x = camera_state['x']
            self.both_buttons_start_cam_y = camera_state['y']
            self.both_buttons_start_cam_z = camera_state['z']
            # 他のモードを無効化
            self.view_rotating = False
            self.ue5_camera_moving = False
            self.furniture_dragging = False
            return
        
        # Shiftキーが押されているか確認（強制的にカメラ移動モード）
        shift_pressed = (flags & cv2.EVENT_FLAG_SHIFTKEY) != 0
        
        if not shift_pressed and furniture_hit_test:
            # 家具を探す
            furniture = furniture_hit_test(x, y)
            
            if furniture:
                # 家具を選択
                self.furniture_dragging = True
                result['furniture_action'] = 'select'
                result['selected_furniture'] = furniture
                
                # クリック位置を3D座標に変換してオフセットを計算
                if screen_to_world:
                    click_world_pos = screen_to_world(x, y)
                    if click_world_pos:
                        click_world_x, click_world_y = click_world_pos
                        self.furniture_drag_offset_x = furniture.x - click_world_x
                        self.furniture_drag_offset_y = furniture.y - click_world_y
                        result['drag_offset'] = (self.furniture_drag_offset_x, self.furniture_drag_offset_y)
                return
        
        # 家具がない場合、またはShift押下時はUE5スタイルカメラ移動開始
        self.ue5_camera_moving = True
        self.ue5_move_start_x = x
        self.ue5_move_start_y = y
        self.ue5_move_start_cam_x = camera_state['x']
        self.ue5_move_start_cam_y = camera_state['y']
        self.ue5_move_start_yaw = camera_state['yaw']
    
    def _handle_middle_button_down(self, x: int, y: int, camera_state: dict):
        """ホイールボタン押下処理"""
        self.camera_panning = True
        self.pan_start_x = x
        self.pan_start_y = y
        self.pan_start_cam_x = camera_state['x']
        self.pan_start_cam_y = camera_state['y']
        self.pan_start_cam_z = camera_state['z']
    
    def _handle_mouse_move(self, x: int, y: int, camera_state: dict,
                          screen_to_world: Optional[Callable], result: dict):
        """マウス移動処理"""
        if self.both_buttons_moving:
            # 右+左同時ドラッグ: カメラの右方向/Z軸移動（左右・上下移動）
            import math
            delta_x = x - self.both_buttons_start_x
            delta_y = y - self.both_buttons_start_y
            
            # カメラの右方向に沿って移動（カメラの向きに対して横方向）
            # 現在のYaw角度からカメラの右方向ベクトルを計算
            yaw_rad = math.radians(camera_state['yaw'])
            
            # 新しい回転順序でのカメラ右方向:
            # Yaw=0:   [0, 1, 0] = +Y方向（右方）
            # Yaw=90:  [1, 0, 0] = +X方向（前方）
            # Yaw=180: [0,-1, 0] = -Y方向（左方）
            # Yaw=270: [-1,0, 0] = -X方向（後方）
            right_x = math.sin(yaw_rad)
            right_y = math.cos(yaw_rad)
            
            # カメラを右方向に移動
            move_right = delta_x * self.mouse_drag_sensitivity
            result['camera_x'] = self.both_buttons_start_cam_x + move_right * right_x
            result['camera_y'] = self.both_buttons_start_cam_y + move_right * right_y
            
            # Z軸移動（上下）
            move_amount = -delta_y * self.mouse_drag_sensitivity
            result['camera_z'] = max(10, self.both_buttons_start_cam_z + move_amount)
            
            result['camera_updated'] = True
        
        elif self.furniture_dragging:
            # 家具のドラッグ
            if screen_to_world:
                world_pos = screen_to_world(x, y)
                if world_pos:
                    result['furniture_action'] = 'drag'
                    result['drag_position'] = (
                        world_pos[0] + self.furniture_drag_offset_x,
                        world_pos[1] + self.furniture_drag_offset_y
                    )
        
        elif self.ue5_camera_moving:
            # UE5スタイルのカメラ移動（左ドラッグ）
            delta_x = x - self.ue5_move_start_x
            delta_y = y - self.ue5_move_start_y
            
            # Yaw回転（左右を向く）
            delta_yaw = delta_x * self.mouse_view_rotation_sensitivity
            current_yaw = self.ue5_move_start_yaw + delta_yaw
            result['camera_yaw'] = current_yaw
            
            # 前後移動（カメラの向いている方向に沿って移動）
            # 現在のYaw角度からカメラの前方向ベクトルを計算
            import math
            yaw_rad = math.radians(current_yaw)
            
            # 新しい回転順序 (Rx @ Ry @ Rz) でのカメラ前方向:
            # Yaw=0:   [1, 0, 0] = +X方向（前方）
            # Yaw=90:  [0,-1, 0] = -Y方向（左方）
            # Yaw=180: [-1,0, 0] = -X方向（後方）
            # Yaw=270: [0, 1, 0] = +Y方向（右方）
            # マウスを下にドラッグ（delta_y > 0）すると前進
            move_amount = delta_y * self.mouse_drag_sensitivity
            
            # カメラの前方向ベクトル（水平面上）
            forward_x = math.cos(yaw_rad)
            forward_y = -math.sin(yaw_rad)  # 符号を反転
            
            # カメラを前方向に移動
            result['camera_x'] = self.ue5_move_start_cam_x + move_amount * forward_x
            result['camera_y'] = self.ue5_move_start_cam_y + move_amount * forward_y
            
            result['camera_updated'] = True
        
        elif self.camera_panning:
            # カメラのドラッグ（ホイールボタン）: カメラの右方向/Z軸移動
            import math
            delta_x = x - self.pan_start_x
            delta_y = y - self.pan_start_y
            
            # 設定に基づいて方向を反転
            x_direction = -1 if self.mouse_drag_invert_x else 1
            y_direction = -1 if self.mouse_drag_invert_y else 1
            
            # カメラの右方向に沿って移動（カメラの向きに対して横方向）
            yaw_rad = math.radians(camera_state['yaw'])
            
            # 新しい回転順序でのカメラ右方向:
            # Yaw=0:   [0, 1, 0] = +Y方向（右方）
            # Yaw=90:  [1, 0, 0] = +X方向（前方）
            # Yaw=180: [0,-1, 0] = -Y方向（左方）
            # Yaw=270: [-1,0, 0] = -X方向（後方）
            right_x = math.sin(yaw_rad)
            right_y = math.cos(yaw_rad)
            
            # カメラを右方向に移動
            move_right = -delta_x * self.mouse_drag_sensitivity * x_direction
            result['camera_x'] = self.pan_start_cam_x + move_right * right_x
            result['camera_y'] = self.pan_start_cam_y + move_right * right_y
            
            # Z軸移動（上下）
            result['camera_z'] = max(10, self.pan_start_cam_z + delta_y * self.mouse_drag_sensitivity * y_direction)
            
            result['camera_updated'] = True
        
        elif self.view_rotating:
            # カメラビューの回転（右クリックドラッグ - UE5スタイル）
            delta_x = x - self.view_rotation_start_x
            delta_y = y - self.view_rotation_start_y
            
            # 設定に基づいて方向を反転
            x_direction = -1 if self.mouse_view_rotation_invert_x else 1
            y_direction = -1 if self.mouse_view_rotation_invert_y else 1
            
            # 角度に変換
            delta_yaw = delta_x * self.mouse_view_rotation_sensitivity * x_direction
            delta_pitch = delta_y * self.mouse_view_rotation_sensitivity * y_direction
            
            # カメラの向きを更新
            result['camera_yaw'] = self.view_rotation_start_yaw + delta_yaw
            result['camera_pitch'] = max(self.mouse_view_rotation_min_pitch,
                                        min(self.mouse_view_rotation_max_pitch,
                                           self.view_rotation_start_pitch + delta_pitch))
            
            result['camera_updated'] = True
    
    def _handle_left_button_up(self, x: int, y: int, camera_state: dict, result: dict):
        """左ボタン解放処理"""
        if self.both_buttons_moving:
            # 両ボタンモードから左を離した場合、右クリック回転モードに切り替え
            self.both_buttons_moving = False
            self.view_rotating = True
            self.view_rotation_start_x = x
            self.view_rotation_start_y = y
            self.view_rotation_start_pitch = camera_state['pitch']
            self.view_rotation_start_yaw = camera_state['yaw']
        else:
            if self.furniture_dragging:
                result['furniture_action'] = 'drop'
            self.furniture_dragging = False
            self.ue5_camera_moving = False
    
    def _handle_right_button_down(self, x: int, y: int, camera_state: dict):
        """右ボタン押下処理"""
        # 左ボタンも押されている場合は両ボタンモード
        if self.ue5_camera_moving or self.furniture_dragging:
            self.both_buttons_moving = True
            self.both_buttons_start_x = x
            self.both_buttons_start_y = y
            self.both_buttons_start_cam_x = camera_state['x']
            self.both_buttons_start_cam_y = camera_state['y']
            self.both_buttons_start_cam_z = camera_state['z']
            # 他のモードを無効化
            self.ue5_camera_moving = False
            self.furniture_dragging = False
            self.view_rotating = False
            return
        
        self.view_rotating = True
        self.view_rotation_start_x = x
        self.view_rotation_start_y = y
        self.view_rotation_start_pitch = camera_state['pitch']
        self.view_rotation_start_yaw = camera_state['yaw']
    
    def _handle_right_button_up(self, x: int, y: int, camera_state: dict, result: dict):
        """右ボタン解放処理"""
        if self.both_buttons_moving:
            # 両ボタンモードから右を離した場合、左ドラッグモードに切り替え
            self.both_buttons_moving = False
            self.ue5_camera_moving = True
            self.ue5_move_start_x = x
            self.ue5_move_start_y = y
            self.ue5_move_start_cam_x = camera_state['x']
            self.ue5_move_start_cam_y = camera_state['y']
            self.ue5_move_start_yaw = camera_state['yaw']
        else:
            self.view_rotating = False
    
    def _handle_middle_button_up(self):
        """ホイールボタン解放処理"""
        self.camera_panning = False
    
    def _handle_mouse_wheel(self, flags: int, result: dict):
        """ホイール回転処理"""
        delta = flags >> 16
        current_focal = result['focal_length']
        
        if delta > 0:
            # ズームイン
            result['focal_length'] = min(current_focal + self.zoom_step, self.max_focal_length)
        else:
            # ズームアウト
            result['focal_length'] = max(current_focal - self.zoom_step, self.min_focal_length)
        
        result['camera_updated'] = True
    
    def is_dragging_furniture(self) -> bool:
        """家具をドラッグ中かどうか"""
        return self.furniture_dragging
    
    def is_rotating_view(self) -> bool:
        """ビューを回転中かどうか"""
        return self.view_rotating
    
    def is_panning_camera(self) -> bool:
        """カメラをパン中かどうか"""
        return self.camera_panning
    
    def is_moving_ue5_style(self) -> bool:
        """UE5スタイルで移動中かどうか"""
        return self.ue5_camera_moving
    
    def is_moving_both_buttons(self) -> bool:
        """両ボタンで移動中かどうか"""
        return self.both_buttons_moving

