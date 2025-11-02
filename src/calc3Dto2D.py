import numpy as np
import math
from typing import Tuple, Optional

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
    
    def set_focal_length(self, fx: float, fy: float):
        """
        焦点距離を設定する（ズーム機能）
        
        :param fx: x軸の焦点距離
        :param fy: y軸の焦点距離
        """
        self._fx, self._fy = fx, fy
    
    def get_focal_length(self) -> Tuple[float, float]:
        """
        現在の焦点距離を取得する
        
        :return: (fx, fy)のタプル
        """
        return self._fx, self._fy

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
    
    def cvt_3d_to_2d_with_depth(self, x: float, y: float, z: float) -> Tuple[int, int, float]:
        """
        3D座標を2D座標に変換し、深度情報も返す
        
        :param x: 3D空間のx座標
        :param y: 3D空間のy座標
        :param z: 3D空間のz座標
        :return: 2D画像上の(x, y)座標とカメラ座標系でのz値（深度）
        """
        point_3d = np.array([x, y, z])
        point_camera = self._R @ point_3d + self._t
        depth = point_camera[2]
        
        # 深度が正の場合のみ投影計算
        if depth > 0:
            x_2d = self._fx * point_camera[0] / depth + self._cx
            y_2d = self._fy * point_camera[1] / depth + self._cy
            return int(x_2d), int(y_2d), depth
        else:
            # カメラの後ろにある場合は画面外の座標を返す
            return -10000, -10000, depth
    
    def is_point_visible(self, x: float, y: float, z: float, img_width: int, img_height: int, 
                        margin: float = 100) -> bool:
        """
        点が画面内に表示可能かどうかを判定する
        
        :param x: 3D空間のx座標
        :param y: 3D空間のy座標
        :param z: 3D空間のz座標
        :param img_width: 画像の幅
        :param img_height: 画像の高さ
        :param margin: 画面外判定のマージン（ピクセル）
        :return: 表示可能ならTrue
        """
        x_2d, y_2d, depth = self.cvt_3d_to_2d_with_depth(x, y, z)
        
        # カメラの後ろにある場合は不可視
        if depth <= 0:
            return False
        
        # 画面内（マージン含む）にあるか判定
        return (-margin <= x_2d <= img_width + margin and 
                -margin <= y_2d <= img_height + margin)
    
    def clip_line_to_screen(self, p1_3d: Tuple[float, float, float], 
                           p2_3d: Tuple[float, float, float],
                           img_width: int, img_height: int) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """
        3D空間の線分を画面空間にクリッピングする
        
        :param p1_3d: 始点の3D座標 (x, y, z)
        :param p2_3d: 終点の3D座標 (x, y, z)
        :param img_width: 画像の幅
        :param img_height: 画像の高さ
        :return: クリッピング後の2D座標ペア、または描画不要の場合はNone
        """
        x1_2d, y1_2d, depth1 = self.cvt_3d_to_2d_with_depth(*p1_3d)
        x2_2d, y2_2d, depth2 = self.cvt_3d_to_2d_with_depth(*p2_3d)
        
        # 両方の点がカメラの後ろにある場合は描画しない
        if depth1 <= 0 and depth2 <= 0:
            return None
        
        # 片方がカメラの後ろにある場合の処理
        if depth1 <= 0 or depth2 <= 0:
            # カメラの近くで線分を打ち切る（簡易的な処理）
            if depth1 <= 0:
                # p1がカメラの後ろ
                if abs(depth1 - depth2) > 0.001:
                    # 線形補間でカメラ平面との交点を求める
                    t = (0.1 - depth1) / (depth2 - depth1)
                    if 0 < t < 1:
                        x1_3d = p1_3d[0] + t * (p2_3d[0] - p1_3d[0])
                        y1_3d = p1_3d[1] + t * (p2_3d[1] - p1_3d[1])
                        z1_3d = p1_3d[2] + t * (p2_3d[2] - p1_3d[2])
                        x1_2d, y1_2d, _ = self.cvt_3d_to_2d_with_depth(x1_3d, y1_3d, z1_3d)
                    else:
                        return None
                else:
                    return None
            else:
                # p2がカメラの後ろ
                if abs(depth1 - depth2) > 0.001:
                    t = (0.1 - depth1) / (depth2 - depth1)
                    if 0 < t < 1:
                        x2_3d = p1_3d[0] + t * (p2_3d[0] - p1_3d[0])
                        y2_3d = p1_3d[1] + t * (p2_3d[1] - p1_3d[1])
                        z2_3d = p1_3d[2] + t * (p2_3d[2] - p1_3d[2])
                        x2_2d, y2_2d, _ = self.cvt_3d_to_2d_with_depth(x2_3d, y2_3d, z2_3d)
                    else:
                        return None
                else:
                    return None
        
        # 画面外の座標をクリッピング（Cohen-Sutherlandアルゴリズムの簡易版）
        margin = 10000  # 大きなマージンを取って、極端な座標をクリップ
        x1_2d = max(-margin, min(img_width + margin, x1_2d))
        y1_2d = max(-margin, min(img_height + margin, y1_2d))
        x2_2d = max(-margin, min(img_width + margin, x2_2d))
        y2_2d = max(-margin, min(img_height + margin, y2_2d))
        
        return (x1_2d, y1_2d), (x2_2d, y2_2d)