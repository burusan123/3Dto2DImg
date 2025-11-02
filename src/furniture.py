"""
家具クラスモジュール

3D空間における家具オブジェクトの定義と描画機能を提供します。
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from drawable import Drawable
from calc3Dto2D import Tranceform3D2D
from coordinate_precision import CoordinatePrecision


class Furniture(Drawable):
    """家具クラス"""
    
    def __init__(self, name: str, x: float, y: float, z: float, 
                 width: float, height: float, depth: float, 
                 color: Tuple[int, int, int]):
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
        """
        家具の頂点座標を取得する（UE5スタイル）
        
        座標系: X=前、Y=右、Z=上
        サイズ: width=幅（Y方向）、depth=奥行き（X方向）、height=高さ（Z方向）
        """
        return [
            # 底面の4頂点（Z=self.z）
            (self.x, self.y, self.z),
            (self.x + self.depth, self.y, self.z),  # X方向にdepth（奥行き）
            (self.x + self.depth, self.y + self.width, self.z),  # Y方向にwidth（幅）
            (self.x, self.y + self.width, self.z),
            # 上面の4頂点（Z=self.z + height）
            (self.x, self.y, self.z + self.height),
            (self.x + self.depth, self.y, self.z + self.height),
            (self.x + self.depth, self.y + self.width, self.z + self.height),
            (self.x, self.y + self.width, self.z + self.height),
        ]
    
    def get_center_2d(self, transform: Tranceform3D2D) -> Tuple[int, int]:
        """家具の中心の2D座標を取得する（UE5スタイル）"""
        center_x = self.x + self.depth / 2  # X方向にdepth/2
        center_y = self.y + self.width / 2  # Y方向にwidth/2
        center_z = self.z
        return transform.cvt_3d_to_2d(center_x, center_y, center_z)
    
    def is_point_inside_2d(self, px: int, py: int, transform: Tranceform3D2D, 
                          img_width: int, img_height: int) -> bool:
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

    def get_faces(self) -> List[Tuple[List[int], Tuple[float, float, float]]]:
        """
        家具の面を取得する（頂点インデックスと法線ベクトル）
        
        頂点インデックス:
          0-3: 底面 (Z=z)
          4-7: 上面 (Z=z+height)
        
        :return: [(頂点インデックスリスト, 法線ベクトル), ...]
        """
        return [
            # 底面（下向き: -Z）
            ([0, 3, 2, 1], (0, 0, -1)),
            # 上面（上向き: +Z）
            ([4, 5, 6, 7], (0, 0, 1)),
            # 前面（-X方向を向く）
            ([0, 1, 5, 4], (-1, 0, 0)),
            # 後面（+X方向を向く）
            ([2, 3, 7, 6], (1, 0, 0)),
            # 左面（-Y方向を向く）
            ([0, 4, 7, 3], (0, -1, 0)),
            # 右面（+Y方向を向く）
            ([1, 2, 6, 5], (0, 1, 0)),
        ]
    
    def draw(self, img: np.ndarray, transform: Tranceform3D2D, text_renderer=None):
        """家具を画像に描画する（面を考慮・最適化版）"""
        vertices = self.get_vertices()
        img_height, img_width = img.shape[:2]
        
        # カメラ位置を取得（1回のみ）
        camera_pos = np.array(transform.get_camera_position())
        
        # 選択状態に応じて色を変更（事前計算）
        face_color = (255, 255, 0) if self.is_selected else self.color
        line_color = (255, 255, 255) if self.is_selected else (50, 50, 50)
        line_thickness = 2 if self.is_selected else 1
        
        # 面を描画（バックフェースカリングと深度ソート）
        faces_with_depth = []
        
        for face_indices, normal in self.get_faces():
            # 面の中心点を計算
            face_center = np.mean([vertices[i] for i in face_indices], axis=0)
            
            # バックフェースカリングを無効化（全ての面を表示）
            # これにより、どの角度から見ても家具が完全に表示される
            
            # 深度を計算（カメラからの距離）
            _, _, depth = transform.cvt_3d_to_2d_with_depth(*face_center)
            if depth > 0:  # カメラの前にある面のみ
                faces_with_depth.append((face_indices, depth))
        
        # 面が1つもない場合は早期リターン
        if not faces_with_depth:
            return
        
        # 深度でソート（遠い順に描画）
        faces_with_depth.sort(key=lambda x: x[1], reverse=True)
        
        # 面を描画（最適化: 半透明描画を削除）
        for face_indices, _ in faces_with_depth:
            # 2D座標に変換（事前にチェック）
            points_2d = []
            for idx in face_indices:
                vertex = vertices[idx]
                if transform.is_point_visible(*vertex, img_width, img_height):
                    pt = transform.cvt_3d_to_2d(*vertex)
                    points_2d.append(pt)
                else:
                    # 1つでも見えない頂点があれば面全体をスキップ
                    break
            else:
                # すべての頂点が可視の場合のみ描画
                if len(points_2d) >= 3:
                    pts = np.array(points_2d, dtype=np.int32)
                    
                    # 面を直接塗りつぶし（高速化）
                    cv2.fillPoly(img, [pts], face_color)
                    
                    # 輪郭線を描画
                    cv2.polylines(img, [pts], isClosed=True, color=line_color, thickness=line_thickness)

        # 家具の名前を表示（中心点が可視の場合のみ）
        center_x = self.x + self.depth / 2
        center_y = self.y + self.width / 2
        center_z = self.z + self.height
        
        if transform.is_point_visible(center_x, center_y, center_z, img_width, img_height):
            center = transform.cvt_3d_to_2d(center_x, center_y, center_z)
            text_color = (0, 0, 0) if self.is_selected else (255, 255, 255)
            
            # PILベースのテキストレンダラーで日本語を描画
            if text_renderer:
                # 縁取りを追加して可読性を向上
                outline_color = (255, 255, 255) if self.is_selected else (0, 0, 0)
                img[:] = text_renderer.draw_text(img, self.name, center, font_size=20, 
                                                 color=text_color, outline=True, 
                                                 outline_color=outline_color, outline_width=1)
            else:
                # フォールバック: OpenCVで直接描画（英数字のみ対応）
                cv2.putText(img, self.name, center, cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, text_color, 2, cv2.LINE_AA)

