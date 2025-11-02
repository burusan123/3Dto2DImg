import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional


class ConfigLoader:
    """設定ファイルを読み込むクラス"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初期化メソッド
        
        :param config_path: 設定ファイルのパス（Noneの場合はデフォルト設定を使用）
        """
        if config_path is None:
            # デフォルト設定ファイルのパスを取得
            current_dir = Path(__file__).parent
            config_path = current_dir.parent / "config" / "default_config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            if self._config is None:
                raise ValueError("設定ファイルが空です")
        except FileNotFoundError:
            raise FileNotFoundError(f"設定ファイルが見つかりません: {self.config_path}")
        except yaml.YAMLError as e:
            raise ValueError(f"YAMLファイルの解析に失敗しました: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        設定値を取得する（ドット記法をサポート）
        
        :param key: キー（例: "camera.focal_length"）
        :param default: デフォルト値
        :return: 設定値
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    # ウィンドウ設定
    def get_window_size(self) -> Tuple[int, int]:
        """ウィンドウサイズを取得"""
        width = self.get('window.width', 1280)
        height = self.get('window.height', 720)
        return width, height
    
    # アプリケーション設定
    def get_furniture_layout_file(self) -> str:
        """家具配置の保存ファイル名を取得"""
        return self.get('application.furniture_layout_file', 'furniture_layout.json')
    
    def get_auto_save_layout(self) -> bool:
        """自動保存が有効かを取得"""
        return self.get('application.auto_save_layout', True)
    
    # カメラ設定
    def get_camera_focal_length(self) -> float:
        """カメラの初期焦点距離を取得"""
        return self.get('camera.focal_length', 600.0)
    
    def get_camera_focal_length_range(self) -> Tuple[float, float]:
        """カメラの焦点距離範囲を取得"""
        min_fl = self.get('camera.min_focal_length', 200.0)
        max_fl = self.get('camera.max_focal_length', 2000.0)
        return min_fl, max_fl
    
    def get_camera_zoom_step(self) -> float:
        """ズームステップを取得"""
        return self.get('camera.zoom_step', 50.0)
    
    def get_camera_initial_position(self) -> Tuple[float, float, float]:
        """カメラの初期位置を取得"""
        x = self.get('camera.initial_position.x', 0.0)
        y = self.get('camera.initial_position.y', -500.0)
        z = self.get('camera.initial_position.z', 300.0)
        return x, y, z
    
    def get_camera_initial_rotation(self) -> Tuple[float, float, float]:
        """カメラの初期回転を取得"""
        roll = self.get('camera.initial_rotation.roll', 0.0)
        pitch = self.get('camera.initial_rotation.pitch', 30.0)
        yaw = self.get('camera.initial_rotation.yaw', 0.0)
        return roll, pitch, yaw
    
    def get_camera_movement_speed(self) -> float:
        """カメラの移動速度を取得"""
        return self.get('camera.movement_speed', 10.0)
    
    def get_camera_rotation_speed(self) -> float:
        """カメラの回転速度を取得"""
        return self.get('camera.rotation_speed', 5.0)
    
    def get_mouse_drag_sensitivity(self) -> float:
        """ホイールドラッグの感度を取得"""
        return self.get('camera.mouse_drag.sensitivity', 2.0)
    
    def get_mouse_drag_invert_x(self) -> bool:
        """ホイールドラッグのX軸反転設定を取得"""
        return self.get('camera.mouse_drag.invert_x', False)
    
    def get_mouse_drag_invert_y(self) -> bool:
        """ホイールドラッグのY軸反転設定を取得"""
        return self.get('camera.mouse_drag.invert_y', False)
    
    def get_mouse_view_rotation_sensitivity(self) -> float:
        """マウス右クリックビュー回転の感度を取得"""
        return self.get('camera.mouse_view_rotation.sensitivity', 0.2)
    
    def get_mouse_view_rotation_invert_x(self) -> bool:
        """マウス右クリックビュー回転のX軸反転設定を取得"""
        return self.get('camera.mouse_view_rotation.invert_x', False)
    
    def get_mouse_view_rotation_invert_y(self) -> bool:
        """マウス右クリックビュー回転のY軸反転設定を取得"""
        return self.get('camera.mouse_view_rotation.invert_y', False)
    
    def get_mouse_view_rotation_min_pitch(self) -> float:
        """マウス右クリックビュー回転のpitch最小値を取得"""
        return self.get('camera.mouse_view_rotation.min_pitch', -90)
    
    def get_mouse_view_rotation_max_pitch(self) -> float:
        """マウス右クリックビュー回転のpitch最大値を取得"""
        return self.get('camera.mouse_view_rotation.max_pitch', 90)
    
    # 部屋設定
    def get_room_dimensions(self) -> Tuple[float, float, float]:
        """部屋のサイズを取得"""
        width = self.get('room.width', 500.0)
        depth = self.get('room.depth', 500.0)
        height = self.get('room.height', 250.0)
        return width, depth, height
    
    def get_room_color(self) -> Tuple[int, int, int]:
        """部屋の色を取得"""
        color = self.get('room.color', [128, 128, 128])
        return tuple(color)
    
    # 家具設定
    def get_furnitures(self) -> List[Dict[str, Any]]:
        """家具の設定リストを取得"""
        furnitures = self.get('furnitures', [])
        
        # 各家具のデータを整形
        result = []
        for furniture in furnitures:
            result.append({
                'name': furniture.get('name', 'Unknown'),
                'x': furniture.get('position', {}).get('x', 0.0),
                'y': furniture.get('position', {}).get('y', 0.0),
                'z': furniture.get('position', {}).get('z', 0.0),
                'width': furniture.get('size', {}).get('width', 50.0),
                'height': furniture.get('size', {}).get('height', 50.0),
                'depth': furniture.get('size', {}).get('depth', 50.0),
                'color': tuple(furniture.get('color', [255, 255, 255]))
            })
        
        return result
    
    # UI設定
    def get_instructions_config(self) -> Dict[str, Any]:
        """操作説明の表示設定を取得"""
        return {
            'font_scale': self.get('ui.instructions.font_scale', 0.5),
            'color': tuple(self.get('ui.instructions.color', [255, 255, 255])),
            'thickness': self.get('ui.instructions.thickness', 1),
            'position': tuple(self.get('ui.instructions.position', [10, 30])),
            'line_spacing': self.get('ui.instructions.line_spacing', 30)
        }
    
    def get_zoom_display_config(self) -> Dict[str, Any]:
        """ズームレベル表示設定を取得"""
        return {
            'font_scale': self.get('ui.zoom_display.font_scale', 0.6),
            'color': tuple(self.get('ui.zoom_display.color', [0, 255, 255])),
            'thickness': self.get('ui.zoom_display.thickness', 2),
            'position': tuple(self.get('ui.zoom_display.position', [10, -20]))
        }
    
    def get_top_view_config(self) -> Dict[str, Any]:
        """平面図表示設定を取得"""
        return {
            'enabled': self.get('ui.top_view.enabled', True),
            'size': self.get('ui.top_view.size', 600),
            'margin': self.get('ui.top_view.margin', 50),
            'background_color': tuple(self.get('ui.top_view.background_color', [255, 255, 255])),
            'room_color': tuple(self.get('ui.top_view.room_color', [100, 100, 100])),
            'camera_color': tuple(self.get('ui.top_view.camera_color', [0, 0, 255])),
            'view_direction_color': tuple(self.get('ui.top_view.view_direction_color', [255, 0, 0])),
            'fov_color': tuple(self.get('ui.top_view.fov_color', [255, 100, 100])),
            'selected_color': tuple(self.get('ui.top_view.selected_color', [0, 200, 200])),
            # 目盛り設定
            'grid': {
                'enabled': self.get('ui.top_view.grid.enabled', True),
                'interval': self.get('ui.top_view.grid.interval', 300),
                'line_color': tuple(self.get('ui.top_view.grid.line_color', [200, 200, 200])),
                'line_thickness': self.get('ui.top_view.grid.line_thickness', 1),
                'major_interval': self.get('ui.top_view.grid.major_interval', 5),
                'major_line_thickness': self.get('ui.top_view.grid.major_line_thickness', 2),
                'major_line_color': tuple(self.get('ui.top_view.grid.major_line_color', [150, 150, 150])),
                'label_color': tuple(self.get('ui.top_view.grid.label_color', [100, 100, 100])),
                'label_font_scale': self.get('ui.top_view.grid.label_font_scale', 0.4),
                'label_show': self.get('ui.top_view.grid.label_show', True)
            }
        }
    
    # 座標精度設定
    def get_coordinate_precision_mode(self) -> str:
        """座標精度モードを取得"""
        return self.get('coordinate_precision.mode', 'decimal_1')
    
    def get_grid_snap_enabled(self) -> bool:
        """グリッドスナップが有効かを取得"""
        return self.get('coordinate_precision.grid_snap.enabled', True)
    
    def get_grid_snap_size(self) -> float:
        """グリッドスナップサイズを取得"""
        return self.get('coordinate_precision.grid_snap.size', 10.0)
    
    def get_unit_system(self) -> str:
        """単位系を取得"""
        return self.get('coordinate_precision.unit.system', 'mm')
    
    def get_unit_display_enabled(self) -> bool:
        """単位表示が有効かを取得"""
        return self.get('coordinate_precision.unit.display', True)
    
    def reload(self):
        """設定ファイルを再読み込みする"""
        self._load_config()
    
    def save(self, config_path: Optional[str] = None):
        """
        現在の設定を保存する
        
        :param config_path: 保存先のパス（Noneの場合は元のファイルに上書き）
        """
        if config_path is None:
            config_path = self.config_path
        else:
            config_path = Path(config_path)
        
        # ディレクトリが存在しない場合は作成
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

