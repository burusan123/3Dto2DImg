"""
部屋クラスモジュール

3D空間における部屋の定義と描画機能を提供します。
"""

import numpy as np
import cv2
from typing import List, Tuple, Optional
from drawable import Drawable
from furniture import Furniture
from calc3Dto2D import Tranceform3D2D


class Room:
    """部屋クラス"""
    
    def __init__(self, width: float, depth: float, height: float, 
                 color: Tuple[int, int, int] = (128, 128, 128)):
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
    
    def find_furniture_at_point(self, px: int, py: int, transform: Tranceform3D2D, 
                               img_width: int, img_height: int) -> Optional[Furniture]:
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
    
    def draw_axes(self, img: np.ndarray, transform: Tranceform3D2D, 
                  origin: Tuple[float, float, float] = (0, 0, 0), length: float = 100):
        """
        座標軸を描画する（UE5スタイル: X=前/赤、Y=右/緑、Z=上/青）
        
        :param img: 描画先の画像
        :param transform: 座標変換オブジェクト
        :param origin: 軸の原点座標
        :param length: 軸の長さ
        """
        ox, oy, oz = origin
        img_height, img_width = img.shape[:2]
        
        # 各軸の終点
        axes = [
            ("X (Forward)", (ox + length, oy, oz), (0, 0, 255)),     # X軸: 前方向 = 赤
            ("Y (Right)",   (ox, oy + length, oz), (0, 255, 0)),     # Y軸: 右方向 = 緑
            ("Z (Up)",      (ox, oy, oz + length), (255, 0, 0)),     # Z軸: 上方向 = 青
        ]
        
        # 各軸を描画
        for label, end_point, color in axes:
            result = transform.clip_line_to_screen((ox, oy, oz), end_point, img_width, img_height)
            if result:
                p1, p2 = result
                # 軸を描画（太めの線）
                cv2.line(img, p1, p2, color, 3, cv2.LINE_AA)
                # 矢印を描画
                cv2.arrowedLine(img, p1, p2, color, 3, cv2.LINE_AA, tipLength=0.2)
                # ラベルを描画
                cv2.putText(img, label.split()[0], (p2[0] + 10, p2[1]), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

    def draw(self, img: np.ndarray, transform: Tranceform3D2D, text_renderer=None, threaded_renderer=None):
        """部屋と家具を画像に描画する（面を考慮）"""
        img_height, img_width = img.shape[:2]
        
        # 座標軸を描画（原点から）
        self.draw_axes(img, transform, origin=(0, 0, 0), length=150)
        
        # カメラ位置を取得
        camera_pos = transform.get_camera_position()
        
        # 部屋の面を定義（UE5スタイル: X=前、Y=右、Z=上）
        vertices = [
            (0, 0, 0),                      # 0: 原点
            (self.depth, 0, 0),             # 1: X方向（前）
            (self.depth, self.width, 0),    # 2: X,Y方向
            (0, self.width, 0),             # 3: Y方向（右）
            (0, 0, self.height),            # 4: Z方向（上）
            (self.depth, 0, self.height),   # 5: X,Z方向
            (self.depth, self.width, self.height),  # 6: X,Y,Z方向
            (0, self.width, self.height),   # 7: Y,Z方向
        ]
        
        # 部屋の面（内側を向く法線）
        room_faces = [
            # 床（上向き: +Z）
            ([0, 1, 2, 3], (0, 0, 1)),
            # 天井（下向き: -Z）
            ([4, 7, 6, 5], (0, 0, -1)),
            # 前壁（-X方向）
            ([0, 3, 7, 4], (-1, 0, 0)),
            # 後壁（+X方向）
            ([1, 5, 6, 2], (1, 0, 0)),
            # 左壁（-Y方向）
            ([0, 4, 5, 1], (0, -1, 0)),
            # 右壁（+Y方向）
            ([3, 2, 6, 7], (0, 1, 0)),
        ]
        
        # 部屋の面を描画（バックフェースカリングと深度ソート）
        room_faces_with_depth = []
        camera_pos_np = np.array(camera_pos)  # NumPy配列に変換（1回のみ）
        
        for face_indices, normal in room_faces:
            # 面の中心点を計算
            face_center = np.mean([vertices[i] for i in face_indices], axis=0)
            
            # カメラから面への方向ベクトル（NumPy配列で高速化）
            view_vector = face_center - camera_pos_np
            
            # 部屋のバックフェースカリング（内側を向く法線のみ描画）
            # 部屋は通常内側から見るため、外側を向く面は描画しない
            dot_product = np.dot(normal, view_vector)
            if dot_product > 0.01:  # 外側を向いている場合は描画しない
                continue
            
            # 深度を計算
            _, _, depth = transform.cvt_3d_to_2d_with_depth(*face_center)
            if depth > 0:
                room_faces_with_depth.append((face_indices, depth))
        
        # 面がない場合は早期リターン
        if not room_faces_with_depth:
            return
        
        # 深度でソート（遠い順に描画）
        room_faces_with_depth.sort(key=lambda x: x[1], reverse=True)
        
        # 部屋の面を描画（最適化: 半透明をやめて直接描画）
        room_color = (100, 100, 100)
        for face_indices, _ in room_faces_with_depth:
            # 2D座標に変換
            points_2d = []
            for idx in face_indices:
                vertex = vertices[idx]
                if transform.is_point_visible(*vertex, img_width, img_height):
                    pt = transform.cvt_3d_to_2d(*vertex)
                    points_2d.append(pt)
                else:
                    # 1つでも見えない頂点があればスキップ
                    break
            else:
                # すべての頂点が可視の場合のみ描画
                if len(points_2d) >= 3:
                    pts = np.array(points_2d, dtype=np.int32)
                    
                    # 半透明描画を削除し、直接描画（高速化）
                    cv2.fillPoly(img, [pts], room_color)
                    
                    # 輪郭線を描画
                    cv2.polylines(img, [pts], isClosed=True, color=self.color, thickness=1)
        
        # 家具を深度順に描画
        furniture_with_depth = []
        for furniture in self.furnitures:
            center_x = furniture.x + furniture.depth / 2
            center_y = furniture.y + furniture.width / 2
            center_z = furniture.z + furniture.height / 2
            _, _, depth = transform.cvt_3d_to_2d_with_depth(center_x, center_y, center_z)
            if depth > 0:
                furniture_with_depth.append((furniture, depth))
        
        # 深度でソート（遠い順に描画）
        furniture_with_depth.sort(key=lambda x: x[1], reverse=True)
        
        # 家具を描画（マルチスレッドまたは通常描画）
        # 家具が10個以上の場合のみマルチスレッド化（オーバーヘッドを避ける）
        if threaded_renderer and len(furniture_with_depth) >= 10:
            # マルチスレッド描画（家具が多い場合）
            img[:] = threaded_renderer.render_furnitures_parallel(
                img, furniture_with_depth, transform, text_renderer
            )
        else:
            # 通常描画（家具が少ない場合・より高速）
            for furniture, _ in furniture_with_depth:
                furniture.draw(img, transform, text_renderer)

