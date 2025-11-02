import numpy as np
import cv2
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
from calc3Dto2D import Tranceform3D2D
from config_loader import ConfigLoader
from coordinate_precision import CoordinatePrecision

class Drawable(ABC):
    """描画可能なオブジェクトの抽象基底クラス"""
    
    @abstractmethod
    def draw(self, img: np.ndarray, transform: Tranceform3D2D):
        """
        オブジェクトを画像に描画する
        
        :param img: 描画対象の画像
        :param transform: 3D to 2D変換オブジェクト
        """
        pass

class Furniture(Drawable):
    """家具クラス"""
    
    def __init__(self, name: str, x: float, y: float, z: float, width: float, height: float, depth: float, color: Tuple[int, int, int]):
        """
        初期化メソッド
        
        :param name: 家具の名前
        :param x: x座標
        :param y: y座標
        :param z: z座標
        :param width: 幅
        :param height: 高さ
        :param depth: 奥行き
        :param color: 色 (R, G, B)
        """
        self.name = name
        self.x, self.y, self.z = x, y, z
        self.width, self.height, self.depth = width, height, depth
        self.color = color
        self.is_selected = False  # 選択状態

    def get_vertices(self) -> List[Tuple[float, float, float]]:
        """家具の頂点座標を取得する"""
        return [
            (self.x, self.y, self.z),
            (self.x + self.width, self.y, self.z),
            (self.x + self.width, self.y + self.depth, self.z),
            (self.x, self.y + self.depth, self.z),
            (self.x, self.y, self.z + self.height),
            (self.x + self.width, self.y, self.z + self.height),
            (self.x + self.width, self.y + self.depth, self.z + self.height),
            (self.x, self.y + self.depth, self.z + self.height),
        ]
    
    def get_center_2d(self, transform: Tranceform3D2D) -> Tuple[int, int]:
        """家具の中心の2D座標を取得する"""
        center_x = self.x + self.width / 2
        center_y = self.y + self.depth / 2
        center_z = self.z
        return transform.cvt_3d_to_2d(center_x, center_y, center_z)
    
    def is_point_inside_2d(self, px: int, py: int, transform: Tranceform3D2D, img_width: int, img_height: int) -> bool:
        """
        2D画面上の点が家具の投影領域内にあるかを判定する
        
        :param px: 画面上のx座標
        :param py: 画面上のy座標
        :param transform: 座標変換オブジェクト
        :param img_width: 画像幅
        :param img_height: 画像高さ
        :return: 領域内ならTrue
        """
        # 床面の4つの頂点を2D投影
        vertices_2d = []
        for i in range(4):  # 床面の4頂点
            vertex = self.get_vertices()[i]
            if transform.is_point_visible(vertex[0], vertex[1], vertex[2], img_width, img_height):
                x2d, y2d = transform.cvt_3d_to_2d(vertex[0], vertex[1], vertex[2])
                vertices_2d.append((x2d, y2d))
        
        # 頂点が4つ揃っている場合のみ判定
        if len(vertices_2d) == 4:
            # 多角形の内外判定（Ray Casting Algorithm）
            return self._point_in_polygon(px, py, vertices_2d)
        
        return False
    
    @staticmethod
    def _point_in_polygon(px: int, py: int, polygon: List[Tuple[int, int]]) -> bool:
        """
        点が多角形内にあるかを判定（Ray Casting Algorithm）
        
        :param px: 点のx座標
        :param py: 点のy座標
        :param polygon: 多角形の頂点リスト
        :return: 内部ならTrue
        """
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if py > min(p1y, p2y):
                if py <= max(p1y, p2y):
                    if px <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (py - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or px <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside
    
    def move_to(self, x: float, y: float, precision: Optional[CoordinatePrecision] = None):
        """
        家具を指定座標に移動する（床面のみ、z座標は維持）
        
        :param x: 新しいx座標
        :param y: 新しいy座標
        :param precision: 座標精度管理オブジェクト
        """
        if precision:
            x, y, _ = precision.process_coordinate(x, y, self.z)
        self.x = x
        self.y = y
    
    def get_position_info(self, precision: Optional[CoordinatePrecision] = None) -> str:
        """
        家具の位置情報を文字列で取得
        
        :param precision: 座標精度管理オブジェクト
        :return: 位置情報の文字列
        """
        if precision:
            return f"{self.name}: {precision.format_coordinate(self.x, self.y, self.z)}"
        else:
            return f"{self.name}: ({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"

    def draw(self, img: np.ndarray, transform: Tranceform3D2D):
        """家具を画像に描画する"""
        vertices = self.get_vertices()
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        
        img_height, img_width = img.shape[:2]
        
        # 選択状態に応じて色と線の太さを変更
        line_color = (255, 255, 0) if self.is_selected else self.color  # 選択時は黄色
        line_thickness = 3 if self.is_selected else 2
        
        for edge in edges:
            # 線分のクリッピングを使用
            result = transform.clip_line_to_screen(
                vertices[edge[0]], 
                vertices[edge[1]], 
                img_width, 
                img_height
            )
            
            # 描画可能な場合のみ描画
            if result is not None:
                start, end = result
                cv2.line(img, start, end, line_color, line_thickness)

        # 家具の名前を表示（中心点が可視の場合のみ）
        center_x = self.x + self.width / 2
        center_y = self.y + self.depth / 2
        center_z = self.z + self.height
        
        if transform.is_point_visible(center_x, center_y, center_z, img_width, img_height):
            center = transform.cvt_3d_to_2d(center_x, center_y, center_z)
            text_color = (255, 255, 0) if self.is_selected else (255, 255, 255)
            cv2.putText(img, self.name, center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 1, cv2.LINE_AA)

class Room:
    """部屋クラス"""
    
    def __init__(self, width: float, depth: float, height: float, color: Tuple[int, int, int] = (128, 128, 128)):
        """
        初期化メソッド
        
        :param width: 部屋の幅
        :param depth: 部屋の奥行き
        :param height: 部屋の高さ
        :param color: 部屋の輪郭線の色
        """
        self.width = width
        self.depth = depth
        self.height = height
        self.color = color
        self.furnitures: List[Furniture] = []

    def add_furniture(self, furniture: Furniture):
        """家具を部屋に追加する"""
        self.furnitures.append(furniture)
    
    def find_furniture_at_point(self, px: int, py: int, transform: Tranceform3D2D, img_width: int, img_height: int) -> Optional[Furniture]:
        """
        画面上の点にある家具を検索する（手前から順に）
        
        :param px: 画面上のx座標
        :param py: 画面上のy座標
        :param transform: 座標変換オブジェクト
        :param img_width: 画像幅
        :param img_height: 画像高さ
        :return: ヒットした家具、なければNone
        """
        # カメラからの距離でソート（手前の家具を優先）
        furniture_with_depth = []
        for furniture in self.furnitures:
            center_x = furniture.x + furniture.width / 2
            center_y = furniture.y + furniture.depth / 2
            center_z = furniture.z
            _, _, depth = transform.cvt_3d_to_2d_with_depth(center_x, center_y, center_z)
            if depth > 0:  # カメラの前にある家具のみ
                furniture_with_depth.append((furniture, depth))
        
        # 距離でソート（近い順）
        furniture_with_depth.sort(key=lambda x: x[1])
        
        # 手前から順にヒットテスト
        for furniture, _ in furniture_with_depth:
            if furniture.is_point_inside_2d(px, py, transform, img_width, img_height):
                return furniture
        
        return None

    def draw(self, img: np.ndarray, transform: Tranceform3D2D):
        """部屋と家具を画像に描画する"""
        img_height, img_width = img.shape[:2]
        
        # 部屋の輪郭を描画
        vertices = [
            (0, 0, 0), (self.width, 0, 0), (self.width, self.depth, 0), (0, self.depth, 0),
            (0, 0, self.height), (self.width, 0, self.height), (self.width, self.depth, self.height), (0, self.depth, self.height)
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        
        for edge in edges:
            # 線分のクリッピングを使用
            result = transform.clip_line_to_screen(
                vertices[edge[0]], 
                vertices[edge[1]], 
                img_width, 
                img_height
            )
            
            # 描画可能な場合のみ描画
            if result is not None:
                start, end = result
                cv2.line(img, start, end, self.color, 1)

        # 家具を描画
        for furniture in self.furnitures:
            furniture.draw(img, transform)

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
        
        # ホイールドラッグ設定
        self.mouse_drag_sensitivity = self.config.get_mouse_drag_sensitivity()
        self.mouse_drag_invert_x = self.config.get_mouse_drag_invert_x()
        self.mouse_drag_invert_y = self.config.get_mouse_drag_invert_y()
        
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
        
        # ドラッグ＆ドロップ用の状態
        self.selected_furniture: Optional[Furniture] = None
        self.dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        
        # ホイールドラッグによるカメラ移動用の状態
        self.camera_dragging = False
        self.camera_drag_start_x = 0
        self.camera_drag_start_y = 0
        self.camera_drag_start_cam_x = 0.0
        self.camera_drag_start_cam_y = 0.0
        
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
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)

            # ズーム（焦点距離）を適用
            self.transform.set_focal_length(self.focal_length, self.focal_length)
            
            # カメラの位置と角度を設定（roll, pitch, yawを全て使用）
            self.transform.set_external_parameter(
                self.camera_roll, 
                self.camera_pitch, 
                self.camera_yaw, 
                self.camera_x, 
                self.camera_y, 
                self.camera_z
            )

            # 部屋と家具を描画
            self.room.draw(img, self.transform)

            # 操作説明を表示
            self._draw_instructions(img)
            
            # ズームレベルを表示
            self._draw_zoom_level(img)
            
            # 座標精度情報を表示
            self._draw_precision_info(img)
            
            # 選択中の家具の座標を表示
            if self.selected_furniture:
                pos_text = self.selected_furniture.get_position_info(self.precision)
                cv2.putText(img, pos_text, (10, self.height - 80), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (255, 255, 0), 2, cv2.LINE_AA)
            
            # ドラッグ中の情報を表示
            if self.dragging and self.selected_furniture:
                drag_text = f"Dragging: {self.selected_furniture.name}"
                cv2.putText(img, drag_text, (10, self.height - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 255, 0), 2, cv2.LINE_AA)
            
            # カメラドラッグ中の情報を表示
            if self.camera_dragging:
                camera_drag_text = "Camera Pan (Middle Button Drag)"
                cv2.putText(img, camera_drag_text, (10, self.height - 50), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.6, (0, 255, 255), 2, cv2.LINE_AA)

            cv2.imshow("3D Room Designer", img)
            
            # 平面図を描画して表示（有効な場合のみ）
            if self.top_view_config['enabled']:
                top_view_img = self._draw_top_view()
                cv2.imshow("Top View", top_view_img)

            if self._handle_input():
                break

        # 終了時に家具の配置を保存（自動保存が有効な場合）
        if self.auto_save_layout:
            self._save_furniture_layout()
        
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
        if event == cv2.EVENT_LBUTTONDOWN:
            # 左クリック: 家具の選択開始
            furniture = self.room.find_furniture_at_point(x, y, self.transform, self.width, self.height)
            
            if furniture:
                # 以前の選択を解除
                if self.selected_furniture:
                    self.selected_furniture.is_selected = False
                
                # 新しい家具を選択
                self.selected_furniture = furniture
                furniture.is_selected = True
                self.dragging = True
                
                # クリック位置を3D座標に変換
                click_world_pos = self._screen_to_world(x, y)
                if click_world_pos is not None:
                    click_world_x, click_world_y = click_world_pos
                    # 家具の位置とクリック位置の差分を保存（オフセット）
                    self.drag_offset_x = furniture.x - click_world_x
                    self.drag_offset_y = furniture.y - click_world_y
                else:
                    # 変換できない場合は家具の中心を基準にする
                    self.drag_offset_x = 0.0
                    self.drag_offset_y = 0.0
            else:
                # 空白をクリックした場合は選択解除
                if self.selected_furniture:
                    self.selected_furniture.is_selected = False
                    self.selected_furniture = None
        
        elif event == cv2.EVENT_MBUTTONDOWN:
            # ホイールクリック: カメラ移動開始
            self.camera_dragging = True
            self.camera_drag_start_x = x
            self.camera_drag_start_y = y
            self.camera_drag_start_cam_x = self.camera_x
            self.camera_drag_start_cam_y = self.camera_y
        
        elif event == cv2.EVENT_MOUSEMOVE:
            # マウス移動: ドラッグ中の処理
            if self.dragging and self.selected_furniture:
                # 家具のドラッグ
                # 2D座標を3D座標に逆変換（床面上）
                world_pos = self._screen_to_world(x, y)
                if world_pos is not None:
                    world_x, world_y = world_pos
                    # オフセットを適用（クリックした位置と家具の位置の差分を保持）
                    world_x += self.drag_offset_x
                    world_y += self.drag_offset_y
                    # 部屋の範囲内に制限
                    world_x = max(0, min(world_x, self.room.width - self.selected_furniture.width))
                    world_y = max(0, min(world_y, self.room.depth - self.selected_furniture.depth))
                    # 座標精度を適用して移動
                    self.selected_furniture.move_to(world_x, world_y, self.precision)
            
            elif self.camera_dragging:
                # カメラのドラッグ（ホイールボタン）
                # マウスの移動量を計算
                delta_x = x - self.camera_drag_start_x
                delta_y = y - self.camera_drag_start_y
                
                # 設定に基づいて方向を反転
                x_direction = -1 if self.mouse_drag_invert_x else 1
                y_direction = -1 if self.mouse_drag_invert_y else 1
                
                # カメラ座標を更新（設定に応じた方向）
                self.camera_x = self.camera_drag_start_cam_x + delta_x * self.mouse_drag_sensitivity * x_direction
                self.camera_y = self.camera_drag_start_cam_y - delta_y * self.mouse_drag_sensitivity * y_direction
        
        elif event == cv2.EVENT_LBUTTONUP:
            # 左クリック解放: ドラッグ終了
            self.dragging = False
        
        elif event == cv2.EVENT_MBUTTONUP:
            # ホイールボタン解放: カメラドラッグ終了
            self.camera_dragging = False
        
        elif event == cv2.EVENT_MOUSEWHEEL:
            # ホイール回転: ズームイン/アウト
            # flagsの上位16ビットにホイールの回転量が格納されている
            # 正の値: 上方向（ズームイン）、負の値: 下方向（ズームアウト）
            delta = flags >> 16
            if delta > 0:
                # ズームイン
                self.focal_length = min(self.focal_length + self.zoom_step, self.max_focal_length)
            else:
                # ズームアウト
                self.focal_length = max(self.focal_length - self.zoom_step, self.min_focal_length)
    
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
            "Q/E: Rotate View",
            "R/F: Move Up/Down",
            "Z/X or Wheel: Zoom In/Out",
            "Mouse Left: Drag furniture",
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
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Esc key
            return True
        elif key == ord('w'):
            self.camera_y += self.movement_speed
        elif key == ord('s'):
            self.camera_y -= self.movement_speed
        elif key == ord('a'):
            self.camera_x -= self.movement_speed
        elif key == ord('d'):
            self.camera_x += self.movement_speed
        elif key == ord('q'):
            self.camera_pitch = min(self.camera_pitch + self.rotation_speed, 89)
        elif key == ord('e'):
            self.camera_pitch = max(self.camera_pitch - self.rotation_speed, -89)
        elif key == ord('r'):
            self.camera_z += self.movement_speed
        elif key == ord('f'):
            self.camera_z = max(self.camera_z - self.movement_speed, 10)
        elif key == ord('z'):
            # ズームイン（焦点距離を増加）
            self.focal_length = min(self.focal_length + self.zoom_step, self.max_focal_length)
        elif key == ord('x'):
            # ズームアウト（焦点距離を減少）
            self.focal_length = max(self.focal_length - self.zoom_step, self.min_focal_length)
        elif key == ord('p'):
            # 座標データをエクスポート（JSON形式）
            self._export_coordinates()
        return False
    
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
        """
        終了時に家具の配置を保存する
        """
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
        """
        起動時に保存された家具の配置を読み込む
        """
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
        
        # 座標変換関数
        # 注: roll=180でカメラが真下を見る場合、3DビューではX軸が反転しないが
        # Y軸が反転する。Top Viewでは分かりやすくするため、3Dビューと同じ向きにする
        def world_to_screen(x, y):
            # X軸はそのまま、Y軸を反転させる（画面座標系では下が正なので）
            screen_x = int(margin + x * scale)
            screen_y = int(view_size - margin - y * scale)  # Y軸を反転
            return screen_x, screen_y
        
        # 部屋の輪郭を描画
        room_corners = [
            (0, 0),
            (self.room.width, 0),
            (self.room.width, self.room.depth),
            (0, self.room.depth)
        ]
        
        for i in range(4):
            p1 = world_to_screen(*room_corners[i])
            p2 = world_to_screen(*room_corners[(i + 1) % 4])
            cv2.line(top_view_img, p1, p2, room_color, 2)
        
        # 家具を描画
        for furniture in self.room.furnitures:
            # 家具の4隅
            corners = [
                (furniture.x, furniture.y),
                (furniture.x + furniture.width, furniture.y),
                (furniture.x + furniture.width, furniture.y + furniture.depth),
                (furniture.x, furniture.y + furniture.depth)
            ]
            
            # 家具の輪郭を描画
            line_thickness = 3 if furniture.is_selected else 2
            line_color = selected_color if furniture.is_selected else furniture.color
            
            for i in range(4):
                p1 = world_to_screen(*corners[i])
                p2 = world_to_screen(*corners[(i + 1) % 4])
                cv2.line(top_view_img, p1, p2, line_color, line_thickness)
            
            # 家具を塗りつぶす（半透明）
            pts = np.array([world_to_screen(*c) for c in corners], dtype=np.int32)
            overlay = top_view_img.copy()
            cv2.fillPoly(overlay, [pts], furniture.color)
            cv2.addWeighted(overlay, 0.3, top_view_img, 0.7, 0, top_view_img)
            
            # 家具の名前を表示
            center = world_to_screen(
                furniture.x + furniture.width / 2,
                furniture.y + furniture.depth / 2
            )
            text_color = (0, 0, 0)
            cv2.putText(top_view_img, furniture.name, center, cv2.FONT_HERSHEY_SIMPLEX, 
                       0.4, text_color, 1, cv2.LINE_AA)
        
        # カメラの位置と視線方向を描画
        camera_pos = world_to_screen(self.camera_x, self.camera_y)
        
        # カメラ位置を円で表示
        cv2.circle(top_view_img, camera_pos, 8, camera_color, -1)
        cv2.circle(top_view_img, camera_pos, 10, camera_color, 2)
        
        # 視線方向を矢印で表示（pitch角を考慮して前方向）
        view_direction_length = 40
        # camera_pitchが正の時は下向き、負の時は上向きを見ているが、
        # 平面図では常にY軸正方向を前方として表示
        view_end_x = camera_pos[0]
        view_end_y = camera_pos[1] + int(view_direction_length)
        cv2.arrowedLine(top_view_img, camera_pos, (view_end_x, view_end_y), 
                       view_dir_color, 2, tipLength=0.3)
        
        # カメラの視野角を描画（FOV）
        fov_angle = 60  # 視野角（度）
        fov_length = 80
        fov_angle_rad = np.radians(fov_angle / 2)
        
        # 左側の視野線
        left_x = camera_pos[0] + int(fov_length * np.sin(-fov_angle_rad))
        left_y = camera_pos[1] + int(fov_length * np.cos(-fov_angle_rad))
        cv2.line(top_view_img, camera_pos, (left_x, left_y), fov_color, 1)
        
        # 右側の視野線
        right_x = camera_pos[0] + int(fov_length * np.sin(fov_angle_rad))
        right_y = camera_pos[1] + int(fov_length * np.cos(fov_angle_rad))
        cv2.line(top_view_img, camera_pos, (right_x, right_y), fov_color, 1)
        
        # タイトルを表示
        cv2.putText(top_view_img, "Top View (Floor Plan)", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
        
        # カメラ情報を表示
        cam_info = f"Camera: ({self.camera_x:.0f}, {self.camera_y:.0f}, {self.camera_z:.0f})"
        cv2.putText(top_view_img, cam_info, (10, view_size - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
        
        return top_view_img

if __name__ == "__main__":
    designer = RoomDesigner()
    designer.run()