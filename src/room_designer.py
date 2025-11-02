"""
3D室内設計ビューアーモジュール

3D空間で部屋と家具を配置・編集するためのメインアプリケーションクラスを提供します。
"""

import numpy as np
import cv2
from typing import Optional, Tuple
from calc3Dto2D import Tranceform3D2D
from config_loader import ConfigLoader
from coordinate_precision import CoordinatePrecision
from mouse_controller import MouseController
from keyboard_controller import KeyboardController
from text_renderer import TextRendererFactory
from furniture import Furniture
from room import Room
from performance_monitor import PerformanceMonitor
from threaded_renderer import ThreadedRenderer


class RoomDesigner:
    """3D室内設計ビューアークラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化メソッド
        
        :param config_path: 設定ファイルのパス（Noneの場合はデフォルト設定を使用）
        """
        # 設定ファイルを読み込む
        self.config = ConfigLoader(config_path)
        
        # ウィンドウ設定
        self.width, self.height = self.config.get_window_size()
        self.center_x, self.center_y = self.width / 2, self.height / 2
        
        # カメラパラメータ
        self.focal_length = self.config.get_camera_focal_length()
        self.min_focal_length, self.max_focal_length = self.config.get_camera_focal_length_range()
        self.zoom_step = self.config.get_camera_zoom_step()
        self.transform = Tranceform3D2D(self.focal_length, self.focal_length, self.center_x, self.center_y)
        
        # カメラの初期位置と回転
        self.camera_x, self.camera_y, self.camera_z = self.config.get_camera_initial_position()
        roll, pitch, yaw = self.config.get_camera_initial_rotation()
        self.camera_roll = roll    # X軸周りの回転（上下を見る）
        self.camera_pitch = pitch  # Y軸周りの回転（左右を向く）
        self.camera_yaw = yaw      # Z軸周りの回転（水平回転）
        
        # カメラの移動・回転速度
        self.movement_speed = self.config.get_camera_movement_speed()
        self.rotation_speed = self.config.get_camera_rotation_speed()
        
        # マウスコントローラーを初期化
        mouse_config = {
            'mouse_drag': {
                'sensitivity': self.config.get_mouse_drag_sensitivity(),
                'invert_x': self.config.get_mouse_drag_invert_x(),
                'invert_y': self.config.get_mouse_drag_invert_y()
            },
            'mouse_view_rotation': {
                'sensitivity': self.config.get_mouse_view_rotation_sensitivity(),
                'invert_x': self.config.get_mouse_view_rotation_invert_x(),
                'invert_y': self.config.get_mouse_view_rotation_invert_y(),
                'min_pitch': self.config.get_mouse_view_rotation_min_pitch(),
                'max_pitch': self.config.get_mouse_view_rotation_max_pitch()
            },
            'zoom': {
                'min_focal_length': self.min_focal_length,
                'max_focal_length': self.max_focal_length,
                'zoom_step': self.zoom_step
            }
        }
        self.mouse_controller = MouseController(mouse_config)
        
        # キーボードコントローラーを初期化
        keyboard_config = {
            'movement_speed': self.movement_speed,
            'rotation_speed': self.rotation_speed,
            'zoom': {
                'min_focal_length': self.min_focal_length,
                'max_focal_length': self.max_focal_length,
                'zoom_step': self.zoom_step
            },
            'min_camera_height': 10,
            'min_pitch': -89,
            'max_pitch': 89
        }
        self.keyboard_controller = KeyboardController(keyboard_config)
        
        # 選択中の家具
        self.selected_furniture: Optional[Furniture] = None
        
        # UI設定
        self.instructions_config = self.config.get_instructions_config()
        self.zoom_display_config = self.config.get_zoom_display_config()
        self.top_view_config = self.config.get_top_view_config()
        
        # アプリケーション設定
        self.furniture_layout_file = self.config.get_furniture_layout_file()
        self.auto_save_layout = self.config.get_auto_save_layout()
        
        # 座標精度設定
        self.precision = CoordinatePrecision(
            mode=self.config.get_coordinate_precision_mode(),
            grid_snap_enabled=self.config.get_grid_snap_enabled(),
            grid_snap_size=self.config.get_grid_snap_size(),
            unit_system=self.config.get_unit_system()
        )
        self.unit_display_enabled = self.config.get_unit_display_enabled()
        
        # テキストレンダラーを初期化（日本語対応）
        self.text_renderer = TextRendererFactory.create_renderer("pil")
        
        # パフォーマンス最適化モジュールを初期化
        self.performance_monitor = PerformanceMonitor(window_size=60)
        self.threaded_renderer = ThreadedRenderer()  # CPUコア数-1のスレッド数
        self.show_fps = True  # FPS表示フラグ
        
        # 部屋の作成
        room_width, room_depth, room_height = self.config.get_room_dimensions()
        room_color = self.config.get_room_color()
        self.room = Room(room_width, room_depth, room_height, room_color)
        
        # 家具を設定から読み込んで追加
        self._load_furnitures_from_config()

    def _load_furnitures_from_config(self):
        """設定ファイルから家具を読み込む"""
        furnitures = self.config.get_furnitures()
        for furniture_data in furnitures:
            furniture = Furniture(
                name=furniture_data['name'],
                x=furniture_data['x'],
                y=furniture_data['y'],
                z=furniture_data['z'],
                width=furniture_data['width'],
                height=furniture_data['height'],
                depth=furniture_data['depth'],
                color=furniture_data['color']
            )
            self.room.add_furniture(furniture)
        
        # 保存された配置があれば読み込む
        self._load_furniture_layout()

    def run(self):
        """メインループ"""
        cv2.namedWindow("3D Room Designer")
        
        # 平面図が有効な場合はウィンドウを作成
        if self.top_view_config['enabled']:
            cv2.namedWindow("Top View")
        
        # マウスイベントのコールバックを設定
        cv2.setMouseCallback("3D Room Designer", self._mouse_callback)

        while True:
            # フレーム計測開始
            self.performance_monitor.start_frame()
            
            # 描画開始
            self.performance_monitor.start_section('total_render')
            
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)

            # ズーム（焦点距離）を適用
            self.transform.set_focal_length(self.focal_length, self.focal_length)
            
            # カメラの位置と角度を設定（roll, pitch, yawを全て使用）
            self.performance_monitor.start_section('camera_setup')
            self.transform.set_external_parameter(
                self.camera_roll, 
                self.camera_pitch, 
                self.camera_yaw, 
                self.camera_x, 
                self.camera_y, 
                self.camera_z
            )
            self.performance_monitor.end_section()

            # 部屋と家具を描画（text_rendererを渡す）
            self.performance_monitor.start_section('scene_render')
            self.room.draw(img, self.transform, self.text_renderer, self.threaded_renderer)
            self.performance_monitor.end_section()

            # UI要素を描画
            self.performance_monitor.start_section('ui_render')
            # 操作説明を表示
            self._draw_instructions(img)
            
            # ズームレベルを表示
            self._draw_zoom_level(img)
            
            # 座標精度情報を表示
            self._draw_precision_info(img)
            
            # FPS情報を表示
            if self.show_fps:
                self._draw_fps_info(img)
            
            # 選択中の家具の座標を表示
            if self.selected_furniture:
                pos_text = self.selected_furniture.get_position_info(self.precision)
                cv2.putText(img, pos_text, (10, self.height - 80), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (255, 255, 0), 2, cv2.LINE_AA)
            
            # ドラッグ中の情報を表示
            if self.mouse_controller.is_dragging_furniture() and self.selected_furniture:
                drag_text = f"Dragging: {self.selected_furniture.name}"
                cv2.putText(img, drag_text, (10, self.height - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 255, 0), 2, cv2.LINE_AA)
            
            # カメラドラッグ中の情報を表示
            if self.mouse_controller.is_panning_camera():
                camera_drag_text = "Camera Pan (Middle Button Drag)"
                cv2.putText(img, camera_drag_text, (10, self.height - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 255, 255), 2, cv2.LINE_AA)
            
            # カメラ回転中の情報を表示（デバッグ用）
            if self.mouse_controller.is_rotating_view():
                view_rotation_text = f"View Rotation: Pitch={self.camera_pitch:.1f}, Yaw={self.camera_yaw:.1f}, Roll={self.camera_roll:.1f}"
                cv2.putText(img, view_rotation_text, (10, self.height - 80), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (255, 0, 255), 2, cv2.LINE_AA)
            self.performance_monitor.end_section()

            self.performance_monitor.end_section()  # total_render

            cv2.imshow("3D Room Designer", img)
            
            # 平面図を描画して表示（有効な場合のみ）
            if self.top_view_config['enabled']:
                self.performance_monitor.start_section('top_view_render')
                top_view_img = self._draw_top_view()
                cv2.imshow("Top View", top_view_img)
                self.performance_monitor.end_section()

            if self._handle_input():
                break

        # 終了時に家具の配置を保存（自動保存が有効な場合）
        if self.auto_save_layout:
            self._save_furniture_layout()
        
        # リソースのクリーンアップ
        self.threaded_renderer.shutdown()
        cv2.destroyAllWindows()
    
    def _mouse_callback(self, event, x, y, flags, param):
        """
        マウスイベントのコールバック
        
        :param event: イベントタイプ
        :param x: マウスのx座標
        :param y: マウスのy座標
        :param flags: フラグ
        :param param: パラメータ
        """
        # カメラの現在状態を準備
        camera_state = {
            'x': self.camera_x,
            'y': self.camera_y,
            'z': self.camera_z,
            'pitch': self.camera_pitch,
            'yaw': self.camera_yaw,
            'focal_length': self.focal_length
        }
        
        # 家具のヒットテスト関数
        def furniture_hit_test(px: int, py: int) -> Optional[Furniture]:
            return self.room.find_furniture_at_point(px, py, self.transform, self.width, self.height)
        
        # マウスイベントを処理
        result = self.mouse_controller.handle_mouse_event(
            event, x, y, flags,
            camera_state,
            furniture_hit_test,
            self._screen_to_world
        )
        
        # カメラ状態を更新
        if result['camera_updated']:
            self.camera_x = result['camera_x']
            self.camera_y = result['camera_y']
            self.camera_z = result['camera_z']
            self.camera_pitch = result['camera_pitch']
            self.camera_yaw = result['camera_yaw']
            self.focal_length = result['focal_length']
        
        # 家具の操作を処理
        if result['furniture_action'] == 'select':
            # 以前の選択を解除
            if self.selected_furniture:
                self.selected_furniture.is_selected = False
            
            # 新しい家具を選択
            furniture = result['selected_furniture']
            if furniture:
                furniture.is_selected = True
                self.selected_furniture = furniture
        
        elif result['furniture_action'] == 'drag':
            # 家具をドラッグ
            if self.selected_furniture and result['drag_position']:
                world_x, world_y = result['drag_position']
                # 部屋の範囲内に制限
                world_x = max(0, min(world_x, self.room.width - self.selected_furniture.width))
                world_y = max(0, min(world_y, self.room.depth - self.selected_furniture.depth))
                # 座標精度を適用して移動
                self.selected_furniture.move_to(world_x, world_y, self.precision)
        
        elif result['furniture_action'] == 'drop':
            # ドラッグ終了（特に処理なし）
            pass
    
    def _screen_to_world(self, screen_x: int, screen_y: int) -> Optional[Tuple[float, float]]:
        """
        画面座標を床面（z=0）のワールド座標に変換
        
        :param screen_x: 画面上のx座標
        :param screen_y: 画面上のy座標
        :return: ワールド座標(x, y)、変換できない場合はNone
        """
        # 画面座標から正規化座標へ
        fx, fy = self.transform.get_focal_length()
        cx, cy = self.center_x, self.center_y
        
        # レイキャスティングで床面との交点を求める
        # カメラ座標系でのレイの方向
        ray_x = (screen_x - cx) / fx
        ray_y = (screen_y - cy) / fy
        ray_z = 1.0
        
        # カメラ座標系からワールド座標系へ
        ray_camera = np.array([ray_x, ray_y, ray_z])
        R_inv = self.transform._R.T  # 回転行列の逆行列（転置）
        ray_world = R_inv @ ray_camera
        
        # カメラの位置（ワールド座標系）
        camera_pos = self.transform._t
        
        # 床面（z=0）との交点を計算
        if abs(ray_world[2]) > 0.001:  # ゼロ除算を避ける
            t = -camera_pos[2] / ray_world[2]
            if t > 0:  # カメラの前方
                intersection = camera_pos + t * ray_world
                return float(intersection[0]), float(intersection[1])
        
        return None

    def _draw_instructions(self, img: np.ndarray):
        """操作説明を画像に描画する"""
        instructions = [
            "W/S: Move Forward/Backward",
            "A/D: Move Left/Right",
            "Q/E: Rotate View Left/Right (Yaw)",
            "R/F: Move Up/Down",
            "Z/X or Wheel: Zoom In/Out",
            "Mouse Left: Move forward/back + Yaw (UE5)",
            "Mouse Left (on furniture): Drag furniture",
            "Shift+Mouse Left: Force camera move",
            "Mouse Right: Rotate view (UE5 style)",
            "Mouse Left+Right: Move up/down (UE5)",
            "Mouse Middle: Pan camera",
            "P: Export coordinates",
            "Esc: Quit"
        ]
        config = self.instructions_config
        x, y = config['position']
        for i, instruction in enumerate(instructions):
            pos_y = y + i * config['line_spacing']
            cv2.putText(img, instruction, (x, pos_y), cv2.FONT_HERSHEY_SIMPLEX, 
                       config['font_scale'], config['color'], config['thickness'], cv2.LINE_AA)
    
    def _draw_zoom_level(self, img: np.ndarray):
        """ズームレベルを画像に描画する"""
        zoom_percentage = int((self.focal_length - self.min_focal_length) / 
                              (self.max_focal_length - self.min_focal_length) * 100)
        zoom_text = f"Zoom: {zoom_percentage}% (f={self.focal_length:.0f})"
        
        config = self.zoom_display_config
        x, y = config['position']
        # 負の値は画面下からのオフセット
        if y < 0:
            y = self.height + y
        
        cv2.putText(img, zoom_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                   config['font_scale'], config['color'], config['thickness'], cv2.LINE_AA)
    
    def _draw_precision_info(self, img: np.ndarray):
        """座標精度情報を画像に描画する"""
        if not self.unit_display_enabled:
            return
        
        # 精度モードとグリッドスナップ情報
        precision_text = f"Precision: {self.precision.get_precision_display_name()}"
        if self.precision.grid_snap_enabled:
            precision_text += f" | Grid: {self.precision.format_value(self.precision.grid_snap_size)}"
        
        # 画面右上に表示
        x = self.width - 400
        y = 30
        cv2.putText(img, precision_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.5, (200, 200, 200), 1, cv2.LINE_AA)
    
    def _draw_fps_info(self, img: np.ndarray):
        """FPS情報を画像に描画する"""
        fps = self.performance_monitor.get_fps()
        frame_time_ms = self.performance_monitor.get_frame_time_ms()
        
        # FPS情報
        fps_text = f"FPS: {fps:.1f} ({frame_time_ms:.1f}ms)"
        
        # 画面左下に表示
        x = 10
        y = self.height - 120
        cv2.putText(img, fps_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.6, (0, 255, 0), 2, cv2.LINE_AA)
        
        # セクション別の時間を表示
        y_offset = 20
        for section_name in ['scene_render', 'ui_render', 'top_view_render']:
            section_time = self.performance_monitor.get_section_time_ms(section_name)
            section_pct = self.performance_monitor.get_section_percentage(section_name)
            if section_time > 0:
                section_text = f"  {section_name}: {section_time:.1f}ms ({section_pct:.0f}%)"
                y += y_offset
                cv2.putText(img, section_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.4, (150, 150, 150), 1, cv2.LINE_AA)
        
        # スレッド数を表示
        y += y_offset
        thread_text = f"  Threads: {self.threaded_renderer.num_threads}"
        cv2.putText(img, thread_text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                   0.4, (150, 150, 150), 1, cv2.LINE_AA)

    def _handle_input(self) -> bool:
        """
        キー入力を処理する
        
        :return: プログラムを終了するかどうか
        """
        # ウィンドウが閉じられたかをチェック
        # getWindowProperty()が-1を返す場合、ウィンドウが閉じられている
        if cv2.getWindowProperty("3D Room Designer", cv2.WND_PROP_VISIBLE) < 1:
            return True
        
        # Top Viewウィンドウが有効な場合、そちらもチェック
        if self.top_view_config['enabled']:
            if cv2.getWindowProperty("Top View", cv2.WND_PROP_VISIBLE) < 1:
                return True
        
        # カメラの現在状態を準備
        camera_state = {
            'x': self.camera_x,
            'y': self.camera_y,
            'z': self.camera_z,
            'pitch': self.camera_pitch,
            'yaw': self.camera_yaw,
            'roll': self.camera_roll,
            'focal_length': self.focal_length
        }
        
        # キーボード入力を処理
        result = self.keyboard_controller.handle_keyboard_input(
            camera_state,
            export_callback=self._export_coordinates
        )
        
        # カメラ状態を更新
        if result['camera_updated']:
            self.camera_x = result['camera_x']
            self.camera_y = result['camera_y']
            self.camera_z = result['camera_z']
            self.camera_pitch = result['camera_pitch']
            self.camera_yaw = result['camera_yaw']
            self.camera_roll = result['camera_roll']
            self.focal_length = result['focal_length']
        
        return result['exit']
    
    def _export_coordinates(self):
        """座標データをエクスポートする（CAD/設計図用）"""
        import json
        from datetime import datetime
        
        # 出力データを構築
        export_data = {
            "export_date": datetime.now().isoformat(),
            "unit_system": self.precision.unit_system.value,
            "precision_mode": self.precision.mode.value,
            "room": {
                "width": self.precision.quantize(self.room.width),
                "depth": self.precision.quantize(self.room.depth),
                "height": self.precision.quantize(self.room.height),
                "unit": self.precision.unit_system.value
            },
            "furnitures": []
        }
        
        # 各家具の情報を追加
        for furniture in self.room.furnitures:
            furniture_data = {
                "name": furniture.name,
                "position": {
                    "x": self.precision.quantize(furniture.x),
                    "y": self.precision.quantize(furniture.y),
                    "z": self.precision.quantize(furniture.z)
                },
                "dimensions": {
                    "width": self.precision.quantize(furniture.width),
                    "height": self.precision.quantize(furniture.height),
                    "depth": self.precision.quantize(furniture.depth)
                },
                "color": furniture.color,
                "formatted_position": self.precision.format_coordinate(furniture.x, furniture.y, furniture.z)
            }
            export_data["furnitures"].append(furniture_data)
        
        # ファイルに保存
        filename = f"room_design_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"座標データをエクスポートしました: {filename}")
        print(f"精度: {self.precision.get_precision_display_name()}, 単位: {self.precision.unit_system.value}")
    
    def _save_furniture_layout(self):
        """終了時に家具の配置を保存する"""
        import json
        from datetime import datetime
        
        # 設定ファイルから保存ファイル名を取得
        save_file = self.furniture_layout_file
        
        # 保存データを構築
        save_data = {
            "last_saved": datetime.now().isoformat(),
            "furnitures": []
        }
        
        # 各家具の位置情報を保存
        for furniture in self.room.furnitures:
            furniture_data = {
                "name": furniture.name,
                "x": furniture.x,
                "y": furniture.y,
                "z": furniture.z,
                "width": furniture.width,
                "height": furniture.height,
                "depth": furniture.depth,
                "color": list(furniture.color)  # タプルをリストに変換
            }
            save_data["furnitures"].append(furniture_data)
        
        # ファイルに保存
        try:
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"家具の配置を保存しました: {save_file}")
        except Exception as e:
            print(f"配置の保存に失敗しました: {e}")
    
    def _load_furniture_layout(self):
        """起動時に保存された家具の配置を読み込む"""
        import json
        import os
        
        # 設定ファイルから保存ファイル名を取得
        save_file = self.furniture_layout_file
        
        # ファイルが存在しない場合は何もしない
        if not os.path.exists(save_file):
            return
        
        try:
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 保存された家具データを読み込む
            saved_furnitures = save_data.get("furnitures", [])
            
            # 既存の家具と保存された家具を名前でマッチング
            for saved_furn in saved_furnitures:
                # 同じ名前の家具を探す
                for furniture in self.room.furnitures:
                    if furniture.name == saved_furn["name"]:
                        # 位置を復元
                        furniture.x = saved_furn["x"]
                        furniture.y = saved_furn["y"]
                        furniture.z = saved_furn["z"]
                        # サイズも復元（変更されている可能性があるため）
                        furniture.width = saved_furn["width"]
                        furniture.height = saved_furn["height"]
                        furniture.depth = saved_furn["depth"]
                        # 色も復元
                        furniture.color = tuple(saved_furn["color"])
                        break
            
            print(f"家具の配置を読み込みました: {save_file}")
            print(f"最終保存日時: {save_data.get('last_saved', '不明')}")
        except Exception as e:
            print(f"配置の読み込みに失敗しました: {e}")
    
    def _draw_top_view(self) -> np.ndarray:
        """
        上からの投影図（平面図）を描画する
        
        :return: 平面図の画像
        """
        # 設定から値を取得
        config = self.top_view_config
        view_size = config['size']
        margin = config['margin']
        bg_color = config['background_color']
        room_color = config['room_color']
        camera_color = config['camera_color']
        view_dir_color = config['view_direction_color']
        fov_color = config['fov_color']
        selected_color = config['selected_color']
        
        # 画像を作成
        top_view_img = np.ones((view_size, view_size, 3), dtype=np.uint8) * np.array(bg_color, dtype=np.uint8)
        
        # 部屋のサイズに応じてスケールを計算
        scale_x = (view_size - 2 * margin) / self.room.width
        scale_y = (view_size - 2 * margin) / self.room.depth
        scale = min(scale_x, scale_y)
        
        # 座標変換関数（UE5スタイル: X=前、Y=右）
        def world_to_screen(x, y):
            screen_x = int(margin + y * scale)          # Y軸（右）→ 画面X（横）
            screen_y = int(margin + x * scale)          # X軸（前）→ 画面Y（縦）
            return screen_x, screen_y
        
        # グリッドを描画
        self._draw_top_view_grid(top_view_img, config, world_to_screen)
        
        # 部屋の輪郭を描画
        self._draw_top_view_room(top_view_img, room_color, world_to_screen)
        
        # 家具を描画
        self._draw_top_view_furnitures(top_view_img, selected_color, world_to_screen)
        
        # カメラを描画
        self._draw_top_view_camera(top_view_img, camera_color, view_dir_color, fov_color, world_to_screen)
        
        # タイトルとカメラ情報を表示
        cv2.putText(top_view_img, "Top View (Floor Plan)", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
        
        cam_info = f"Camera: ({self.camera_x:.0f}, {self.camera_y:.0f}, {self.camera_z:.0f})"
        cv2.putText(top_view_img, cam_info, (10, view_size - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        
        return top_view_img
    
    def _draw_top_view_grid(self, img: np.ndarray, config: dict, world_to_screen):
        """平面図のグリッドを描画する"""
        grid_config = config['grid']
        if not grid_config['enabled']:
            return
        
        grid_interval = grid_config['interval']
        line_color = grid_config['line_color']
        line_thickness = grid_config['line_thickness']
        major_interval = grid_config['major_interval']
        major_line_thickness = grid_config['major_line_thickness']
        major_line_color = grid_config['major_line_color']
        label_color = grid_config['label_color']
        label_font_scale = grid_config['label_font_scale']
        label_show = grid_config['label_show']
        
        # X軸方向の目盛り
        x = 0
        grid_count = 0
        while x <= self.room.width:
            is_major = (grid_count % major_interval == 0)
            color = major_line_color if is_major else line_color
            thickness = major_line_thickness if is_major else line_thickness
            
            p1 = world_to_screen(x, 0)
            p2 = world_to_screen(x, self.room.depth)
            cv2.line(img, p1, p2, color, thickness)
            
            if label_show and is_major and x > 0:
                label = f"{int(x)}"
                label_pos = world_to_screen(x, 0)
                label_pos = (label_pos[0] - 10, label_pos[1] + 15)
                cv2.putText(img, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX,
                           label_font_scale, label_color, 1, cv2.LINE_AA)
            
            x += grid_interval
            grid_count += 1
        
        # Y軸方向の目盛り
        y = 0
        grid_count = 0
        while y <= self.room.depth:
            is_major = (grid_count % major_interval == 0)
            color = major_line_color if is_major else line_color
            thickness = major_line_thickness if is_major else line_thickness
            
            p1 = world_to_screen(0, y)
            p2 = world_to_screen(self.room.width, y)
            cv2.line(img, p1, p2, color, thickness)
            
            if label_show and is_major and y > 0:
                label = f"{int(y)}"
                label_pos = world_to_screen(0, y)
                label_pos = (label_pos[0] - 35, label_pos[1] + 5)
                cv2.putText(img, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX,
                           label_font_scale, label_color, 1, cv2.LINE_AA)
            
            y += grid_interval
            grid_count += 1
    
    def _draw_top_view_room(self, img: np.ndarray, room_color: Tuple[int, int, int], world_to_screen):
        """平面図の部屋輪郭を描画する"""
        room_corners = [
            (0, 0),
            (self.room.width, 0),
            (self.room.width, self.room.depth),
            (0, self.room.depth)
        ]
        
        for i in range(4):
            p1 = world_to_screen(*room_corners[i])
            p2 = world_to_screen(*room_corners[(i + 1) % 4])
            cv2.line(img, p1, p2, room_color, 2)
    
    def _draw_top_view_furnitures(self, img: np.ndarray, selected_color: Tuple[int, int, int], world_to_screen):
        """平面図の家具を描画する"""
        for furniture in self.room.furnitures:
            corners = [
                (furniture.x, furniture.y),
                (furniture.x + furniture.depth, furniture.y),
                (furniture.x + furniture.depth, furniture.y + furniture.width),
                (furniture.x, furniture.y + furniture.width)
            ]
            
            line_thickness = 3 if furniture.is_selected else 2
            line_color = selected_color if furniture.is_selected else furniture.color
            
            for i in range(4):
                p1 = world_to_screen(*corners[i])
                p2 = world_to_screen(*corners[(i + 1) % 4])
                cv2.line(img, p1, p2, line_color, line_thickness)
            
            # 塗りつぶし
            pts = np.array([world_to_screen(*c) for c in corners], dtype=np.int32)
            overlay = img.copy()
            cv2.fillPoly(overlay, [pts], furniture.color)
            cv2.addWeighted(overlay, 0.3, img, 0.7, 0, img)
            
            # 名前を表示（最適化: OpenCVで直接描画）
            center = world_to_screen(
                furniture.x + furniture.width / 2,
                furniture.y + furniture.depth / 2
            )
            text_color = (0, 0, 0)
            # OpenCVで描画（高速化）
            cv2.putText(img, furniture.name, center, cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, text_color, 1, cv2.LINE_AA)
    
    def _draw_top_view_camera(self, img: np.ndarray, camera_color: Tuple[int, int, int], 
                             view_dir_color: Tuple[int, int, int], fov_color: Tuple[int, int, int],
                             world_to_screen):
        """平面図のカメラを描画する"""
        camera_pos = world_to_screen(self.camera_x, self.camera_y)
        
        # カメラ位置
        cv2.circle(img, camera_pos, 8, camera_color, -1)
        cv2.circle(img, camera_pos, 10, camera_color, 2)
        
        # 視線方向
        view_direction_length = 40
        view_end_x = camera_pos[0]
        view_end_y = camera_pos[1] + int(view_direction_length)
        cv2.arrowedLine(img, camera_pos, (view_end_x, view_end_y), 
                       view_dir_color, 2, tipLength=0.3)
        
        # 視野角（FOV）
        fov_angle = 60
        fov_length = 80
        fov_angle_rad = np.radians(fov_angle / 2)
        
        left_x = camera_pos[0] + int(fov_length * np.sin(-fov_angle_rad))
        left_y = camera_pos[1] + int(fov_length * np.cos(-fov_angle_rad))
        cv2.line(img, camera_pos, (left_x, left_y), fov_color, 1)
        
        right_x = camera_pos[0] + int(fov_length * np.sin(fov_angle_rad))
        right_y = camera_pos[1] + int(fov_length * np.cos(fov_angle_rad))
        cv2.line(img, camera_pos, (right_x, right_y), fov_color, 1)


if __name__ == "__main__":
    designer = RoomDesigner()
    designer.run()
