import numpy as np
import cv2
from abc import ABC, abstractmethod
from typing import List, Tuple
from calc3Dto2D import Tranceform3D2D

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

    def draw(self, img: np.ndarray, transform: Tranceform3D2D):
        """家具を画像に描画する"""
        vertices = self.get_vertices()
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        
        for edge in edges:
            start = transform.cvt_3d_to_2d(*vertices[edge[0]])
            end = transform.cvt_3d_to_2d(*vertices[edge[1]])
            cv2.line(img, start, end, self.color, 2)

        # 家具の名前を表示
        center = transform.cvt_3d_to_2d(self.x + self.width/2, self.y + self.depth/2, self.z + self.height)
        cv2.putText(img, self.name, center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

class Room:
    """部屋クラス"""
    
    def __init__(self, width: float, depth: float, height: float):
        """
        初期化メソッド
        
        :param width: 部屋の幅
        :param depth: 部屋の奥行き
        :param height: 部屋の高さ
        """
        self.width = width
        self.depth = depth
        self.height = height
        self.furnitures: List[Furniture] = []

    def add_furniture(self, furniture: Furniture):
        """家具を部屋に追加する"""
        self.furnitures.append(furniture)

    def draw(self, img: np.ndarray, transform: Tranceform3D2D):
        """部屋と家具を画像に描画する"""
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
            start = transform.cvt_3d_to_2d(*vertices[edge[0]])
            end = transform.cvt_3d_to_2d(*vertices[edge[1]])
            cv2.line(img, start, end, (128, 128, 128), 1)

        # 家具を描画
        for furniture in self.furnitures:
            furniture.draw(img, transform)

class RoomDesigner:
    """3D室内設計ビューアークラス"""
    
    def __init__(self, width: int, height: int):
        """
        初期化メソッド
        
        :param width: ウィンドウの幅
        :param height: ウィンドウの高さ
        """
        self.width = width
        self.height = height
        self.center_x, self.center_y = width / 2, height / 2
        
        # カメラパラメータ
        fx, fy = 600, 600
        self.transform = Tranceform3D2D(fx, fy, self.center_x, self.center_y)
        
        # カメラの初期位置
        self.camera_x, self.camera_y, self.camera_z = 0, -500, 300
        self.camera_pitch = 30
        
        # 部屋の作成
        self.room = Room(500, 500, 250)
        self._add_sample_furnitures()

    def _add_sample_furnitures(self):
        """サンプルの家具を追加する"""
        self.room.add_furniture(Furniture("テーブル", 150, 200, 0, 150, 75, 100, (0, 255, 0)))
        self.room.add_furniture(Furniture("椅子1", 100, 150, 0, 50, 50, 80, (0, 0, 255)))
        self.room.add_furniture(Furniture("椅子2", 300, 150, 0, 50, 50, 80, (0, 0, 255)))
        self.room.add_furniture(Furniture("ソファ", 50, 400, 0, 200, 80, 100, (255, 0, 0)))
        self.room.add_furniture(Furniture("本棚", 400, 50, 0, 80, 200, 40, (255, 255, 0)))

    def run(self):
        """メインループ"""
        cv2.namedWindow("3D Room Designer")

        while True:
            img = np.zeros((self.height, self.width, 3), dtype=np.uint8)

            # カメラの位置と角度を設定
            self.transform.set_external_parameter(0, self.camera_pitch, 0, self.camera_x, self.camera_y, self.camera_z)

            # 部屋と家具を描画
            self.room.draw(img, self.transform)

            # 操作説明を表示
            self._draw_instructions(img)

            cv2.imshow("3D Room Designer", img)

            if self._handle_input():
                break

        cv2.destroyAllWindows()

    def _draw_instructions(self, img: np.ndarray):
        """操作説明を画像に描画する"""
        instructions = [
            "W/S: Move Forward/Backward",
            "A/D: Move Left/Right",
            "Q/E: Rotate View",
            "R/F: Move Up/Down",
            "Esc: Quit"
        ]
        for i, instruction in enumerate(instructions):
            cv2.putText(img, instruction, (10, 30 + i*30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

    def _handle_input(self) -> bool:
        """
        キー入力を処理する
        
        :return: プログラムを終了するかどうか
        """
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # Esc key
            return True
        elif key == ord('w'):
            self.camera_y += 10
        elif key == ord('s'):
            self.camera_y -= 10
        elif key == ord('a'):
            self.camera_x -= 10
        elif key == ord('d'):
            self.camera_x += 10
        elif key == ord('q'):
            self.camera_pitch = min(self.camera_pitch + 5, 89)
        elif key == ord('e'):
            self.camera_pitch = max(self.camera_pitch - 5, -89)
        elif key == ord('r'):
            self.camera_z += 10
        elif key == ord('f'):
            self.camera_z = max(self.camera_z - 10, 10)
        return False

if __name__ == "__main__":
    designer = RoomDesigner(1280, 720)
    designer.run()