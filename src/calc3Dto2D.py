import numpy as np
import math
from typing import Tuple

class Tranceform3D2D:
    """3D座標を2D座標に変換するクラス"""
    
    def __init__(self, fx: float, fy: float, cx: float, cy: float):
        """
        初期化メソッド
        
        :param fx: x軸の焦点距離
        :param fy: y軸の焦点距離
        :param cx: x軸の主点座標
        :param cy: y軸の主点座標
        """
        self._fx, self._fy = fx, fy
        self._cx, self._cy = cx, cy
        self._R = np.eye(3)
        self._t = np.zeros(3)

    def set_external_parameter(self, roll: float, pitch: float, yaw: float, tx: float, ty: float, tz: float):
        """
        外部パラメータを設定する
        
        :param roll: ロール角（度）
        :param pitch: ピッチ角（度）
        :param yaw: ヨー角（度）
        :param tx: x軸の並進
        :param ty: y軸の並進
        :param tz: z軸の並進
        """
        # 回転行列の計算
        Rx = self._rotation_matrix(roll, 0)
        Ry = self._rotation_matrix(pitch, 1)
        Rz = self._rotation_matrix(yaw, 2)
        self._R = Rz @ Ry @ Rx
        self._t = np.array([tx, ty, tz])

    @staticmethod
    def _rotation_matrix(angle: float, axis: int) -> np.ndarray:
        """
        回転行列を生成する
        
        :param angle: 回転角（度）
        :param axis: 回転軸（0: x, 1: y, 2: z）
        :return: 回転行列
        """
        rad = math.radians(angle)
        c, s = math.cos(rad), math.sin(rad)
        if axis == 0:  # X axis
            return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        elif axis == 1:  # Y axis
            return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
        elif axis == 2:  # Z axis
            return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        else:
            raise ValueError("Invalid axis. Must be 0, 1, or 2.")

    def cvt_3d_to_2d(self, x: float, y: float, z: float) -> Tuple[int, int]:
        """
        3D座標を2D座標に変換する
        
        :param x: 3D空間のx座標
        :param y: 3D空間のy座標
        :param z: 3D空間のz座標
        :return: 2D画像上の(x, y)座標
        """
        point_3d = np.array([x, y, z])
        point_camera = self._R @ point_3d + self._t
        x_2d = self._fx * point_camera[0] / point_camera[2] + self._cx
        y_2d = self._fy * point_camera[1] / point_camera[2] + self._cy
        return int(x_2d), int(y_2d)