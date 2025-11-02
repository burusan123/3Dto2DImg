"""座標精度管理モジュール - 建築設計図・3DCAD対応"""

from typing import Tuple, Union
from enum import Enum


class PrecisionMode(Enum):
    """座標精度モード"""
    INTEGER = "integer"           # 整数のみ
    DECIMAL_1 = "decimal_1"       # 小数点第1位まで
    DECIMAL_2 = "decimal_2"       # 小数点第2位まで
    DECIMAL_3 = "decimal_3"       # 小数点第3位まで
    FULL = "full"                 # フル精度


class UnitSystem(Enum):
    """単位系"""
    MM = "mm"           # ミリメートル
    CM = "cm"           # センチメートル
    M = "m"             # メートル
    INCH = "inch"       # インチ
    FEET = "feet"       # フィート


class CoordinatePrecision:
    """座標精度管理クラス"""
    
    def __init__(self, mode: str = "decimal_1", grid_snap_enabled: bool = True, 
                 grid_snap_size: float = 10.0, unit_system: str = "mm"):
        """
        初期化メソッド
        
        :param mode: 精度モード（"integer", "decimal_1", "decimal_2", "decimal_3", "full"）
        :param grid_snap_enabled: グリッドスナップの有効化
        :param grid_snap_size: グリッドサイズ
        :param unit_system: 単位系
        """
        self.mode = PrecisionMode(mode)
        self.grid_snap_enabled = grid_snap_enabled
        self.grid_snap_size = grid_snap_size
        self.unit_system = UnitSystem(unit_system)
        
        # 精度モードに応じた小数点桁数
        self.decimal_places = {
            PrecisionMode.INTEGER: 0,
            PrecisionMode.DECIMAL_1: 1,
            PrecisionMode.DECIMAL_2: 2,
            PrecisionMode.DECIMAL_3: 3,
            PrecisionMode.FULL: None  # 制限なし
        }
    
    def quantize(self, value: float) -> float:
        """
        値を設定された精度に量子化する
        
        :param value: 元の値
        :return: 量子化された値
        """
        if self.mode == PrecisionMode.FULL:
            return value
        
        decimal_places = self.decimal_places[self.mode]
        return round(value, decimal_places)
    
    def snap_to_grid(self, value: float) -> float:
        """
        値をグリッドにスナップする
        
        :param value: 元の値
        :return: グリッドスナップされた値
        """
        if not self.grid_snap_enabled or self.grid_snap_size <= 0:
            return value
        
        snapped = round(value / self.grid_snap_size) * self.grid_snap_size
        return snapped
    
    def process_coordinate(self, x: float, y: float, z: float = 0.0) -> Tuple[float, float, float]:
        """
        座標を処理（グリッドスナップ + 精度量子化）
        
        :param x: x座標
        :param y: y座標
        :param z: z座標
        :return: 処理後の座標
        """
        # グリッドスナップを適用
        if self.grid_snap_enabled:
            x = self.snap_to_grid(x)
            y = self.snap_to_grid(y)
            z = self.snap_to_grid(z)
        
        # 精度量子化を適用
        x = self.quantize(x)
        y = self.quantize(y)
        z = self.quantize(z)
        
        return x, y, z
    
    def format_value(self, value: float, include_unit: bool = True) -> str:
        """
        値をフォーマットして文字列として返す
        
        :param value: 値
        :param include_unit: 単位を含めるか
        :return: フォーマットされた文字列
        """
        # 精度に応じてフォーマット
        if self.mode == PrecisionMode.INTEGER:
            formatted = f"{int(value)}"
        elif self.mode == PrecisionMode.FULL:
            formatted = f"{value}"
        else:
            decimal_places = self.decimal_places[self.mode]
            formatted = f"{value:.{decimal_places}f}"
        
        # 単位を追加
        if include_unit:
            formatted += f" {self.unit_system.value}"
        
        return formatted
    
    def format_coordinate(self, x: float, y: float, z: float = None, include_unit: bool = True) -> str:
        """
        座標をフォーマットして文字列として返す
        
        :param x: x座標
        :param y: y座標
        :param z: z座標（Noneの場合は2D座標）
        :param include_unit: 単位を含めるか
        :return: フォーマットされた座標文字列
        """
        if z is None:
            return f"({self.format_value(x, False)}, {self.format_value(y, False)})"
        else:
            coord_str = f"({self.format_value(x, False)}, {self.format_value(y, False)}, {self.format_value(z, False)})"
        
        if include_unit:
            coord_str += f" {self.unit_system.value}"
        
        return coord_str
    
    def get_unit_display_name(self) -> str:
        """
        単位系の表示名を取得
        
        :return: 単位系の表示名
        """
        unit_names = {
            UnitSystem.MM: "ミリメートル",
            UnitSystem.CM: "センチメートル",
            UnitSystem.M: "メートル",
            UnitSystem.INCH: "インチ",
            UnitSystem.FEET: "フィート"
        }
        return unit_names.get(self.unit_system, self.unit_system.value)
    
    def get_precision_display_name(self) -> str:
        """
        精度モードの表示名を取得
        
        :return: 精度モードの表示名
        """
        precision_names = {
            PrecisionMode.INTEGER: "整数",
            PrecisionMode.DECIMAL_1: "小数点第1位",
            PrecisionMode.DECIMAL_2: "小数点第2位",
            PrecisionMode.DECIMAL_3: "小数点第3位",
            PrecisionMode.FULL: "フル精度"
        }
        return precision_names.get(self.mode, self.mode.value)
    
    def export_to_dict(self, x: float, y: float, z: float, name: str = "") -> dict:
        """
        座標を辞書形式でエクスポート（CAD/設計図用）
        
        :param x: x座標
        :param y: y座標
        :param z: z座標
        :param name: オブジェクト名
        :return: 座標情報の辞書
        """
        return {
            "name": name,
            "x": self.quantize(x),
            "y": self.quantize(y),
            "z": self.quantize(z),
            "unit": self.unit_system.value,
            "precision": self.mode.value,
            "formatted": self.format_coordinate(x, y, z)
        }

