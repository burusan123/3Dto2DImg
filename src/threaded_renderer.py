"""
マルチスレッド描画エンジンモジュール

CPU並列化による高速描画を実現します。
"""

import numpy as np
import cv2
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Callable, Optional
import multiprocessing


class ThreadedRenderer:
    """マルチスレッド描画エンジンクラス"""
    
    def __init__(self, num_threads: Optional[int] = None):
        """
        初期化メソッド
        
        :param num_threads: 使用するスレッド数（Noneの場合はCPUコア数-1、最大4スレッド）
        """
        if num_threads is None:
            # CPUコア数-1（最低でも1スレッド、最大4スレッド）
            cpu_count = multiprocessing.cpu_count()
            num_threads = max(1, min(4, cpu_count - 1))
        
        self.num_threads = num_threads
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
    
    def render_furnitures_parallel(self, img: np.ndarray, furnitures_with_depth: List[Tuple], 
                                   transform, text_renderer) -> np.ndarray:
        """
        家具を並列描画する
        
        :param img: 描画対象の画像
        :param furnitures_with_depth: [(furniture, depth), ...] のリスト
        :param transform: 3D to 2D変換オブジェクト
        :param text_renderer: テキストレンダラー
        :return: 描画済み画像
        """
        if len(furnitures_with_depth) == 0:
            return img
        
        # 家具を並列処理用にチャンク分割
        chunk_size = max(1, len(furnitures_with_depth) // self.num_threads)
        chunks = [furnitures_with_depth[i:i + chunk_size] 
                 for i in range(0, len(furnitures_with_depth), chunk_size)]
        
        # 各チャンクを並列描画
        futures = []
        for chunk in chunks:
            future = self.executor.submit(
                self._render_furniture_chunk,
                img.copy(),
                chunk,
                transform,
                text_renderer
            )
            futures.append(future)
        
        # 結果を統合（アルファブレンディング）
        result_img = img.copy()
        for future in as_completed(futures):
            chunk_img = future.result()
            # 変更があった部分のみを合成
            mask = np.any(chunk_img != img, axis=2)
            result_img[mask] = chunk_img[mask]
        
        return result_img
    
    @staticmethod
    def _render_furniture_chunk(img: np.ndarray, furniture_chunk: List[Tuple],
                                transform, text_renderer) -> np.ndarray:
        """
        家具チャンクを描画（スレッドで実行）
        
        :param img: 描画対象の画像（コピー）
        :param furniture_chunk: 家具とdepthのリスト
        :param transform: 3D to 2D変換オブジェクト
        :param text_renderer: テキストレンダラー
        :return: 描画済み画像
        """
        for furniture, _ in furniture_chunk:
            furniture.draw(img, transform, text_renderer)
        return img
    
    def render_room_faces_parallel(self, img: np.ndarray, faces_data: List[Tuple],
                                   vertices: List[Tuple], transform, 
                                   room_color: Tuple[int, int, int],
                                   line_color: Tuple[int, int, int]) -> np.ndarray:
        """
        部屋の面を並列描画する
        
        :param img: 描画対象の画像
        :param faces_data: [(face_indices, depth), ...] のリスト
        :param vertices: 頂点座標リスト
        :param transform: 3D to 2D変換オブジェクト
        :param room_color: 面の色
        :param line_color: 輪郭線の色
        :return: 描画済み画像
        """
        if len(faces_data) == 0:
            return img
        
        # 面を並列処理用にチャンク分割
        chunk_size = max(1, len(faces_data) // self.num_threads)
        chunks = [faces_data[i:i + chunk_size] 
                 for i in range(0, len(faces_data), chunk_size)]
        
        # 各チャンクを並列描画
        futures = []
        for chunk in chunks:
            future = self.executor.submit(
                self._render_face_chunk,
                img.copy(),
                chunk,
                vertices,
                transform,
                room_color,
                line_color
            )
            futures.append(future)
        
        # 結果を統合
        result_img = img.copy()
        for future in as_completed(futures):
            chunk_img = future.result()
            mask = np.any(chunk_img != img, axis=2)
            result_img[mask] = chunk_img[mask]
        
        return result_img
    
    @staticmethod
    def _render_face_chunk(img: np.ndarray, face_chunk: List[Tuple],
                          vertices: List[Tuple], transform,
                          room_color: Tuple[int, int, int],
                          line_color: Tuple[int, int, int]) -> np.ndarray:
        """
        面チャンクを描画（スレッドで実行）
        
        :param img: 描画対象の画像（コピー）
        :param face_chunk: 面データのリスト
        :param vertices: 頂点座標リスト
        :param transform: 3D to 2D変換オブジェクト
        :param room_color: 面の色
        :param line_color: 輪郭線の色
        :return: 描画済み画像
        """
        img_height, img_width = img.shape[:2]
        
        for face_indices, _ in face_chunk:
            # 2D座標に変換
            points_2d = []
            all_visible = True
            for idx in face_indices:
                if transform.is_point_visible(*vertices[idx], img_width, img_height):
                    pt = transform.cvt_3d_to_2d(*vertices[idx])
                    points_2d.append(pt)
                else:
                    all_visible = False
                    break
            
            # すべての頂点が可視の場合のみ描画
            if all_visible and len(points_2d) >= 3:
                pts = np.array(points_2d, dtype=np.int32)
                
                # 面を塗りつぶし（薄い半透明）
                overlay = img.copy()
                cv2.fillPoly(overlay, [pts], room_color)
                cv2.addWeighted(overlay, 0.1, img, 0.9, 0, img)
                
                # 輪郭線を描画
                cv2.polylines(img, [pts], isClosed=True, color=line_color, thickness=1)
        
        return img
    
    def shutdown(self):
        """スレッドプールをシャットダウン"""
        self.executor.shutdown(wait=True)
    
    def __del__(self):
        """デストラクタ"""
        self.shutdown()


class RenderCache:
    """描画キャッシュクラス"""
    
    def __init__(self, max_cache_size: int = 100):
        """
        初期化メソッド
        
        :param max_cache_size: キャッシュの最大サイズ
        """
        self.max_cache_size = max_cache_size
        self.cache = {}
        self.access_count = {}
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """
        キャッシュから取得
        
        :param key: キャッシュキー
        :return: キャッシュされた画像、なければNone
        """
        if key in self.cache:
            self.access_count[key] = self.access_count.get(key, 0) + 1
            return self.cache[key].copy()
        return None
    
    def put(self, key: str, value: np.ndarray):
        """
        キャッシュに保存
        
        :param key: キャッシュキー
        :param value: 保存する画像
        """
        # キャッシュサイズ制限
        if len(self.cache) >= self.max_cache_size:
            # 最も使用されていないアイテムを削除（LFU）
            min_key = min(self.access_count, key=self.access_count.get)
            del self.cache[min_key]
            del self.access_count[min_key]
        
        self.cache[key] = value.copy()
        self.access_count[key] = 1
    
    def clear(self):
        """キャッシュをクリア"""
        self.cache.clear()
        self.access_count.clear()
    
    def get_size(self) -> int:
        """キャッシュサイズを取得"""
        return len(self.cache)


class DrawCallBatcher:
    """描画呼び出しバッチャークラス"""
    
    def __init__(self):
        """初期化メソッド"""
        self.batches = {
            'lines': [],
            'rectangles': [],
            'circles': [],
            'polygons': [],
            'text': []
        }
    
    def add_line(self, img: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int],
                color: Tuple[int, int, int], thickness: int = 1):
        """線描画をバッチに追加"""
        self.batches['lines'].append((img, pt1, pt2, color, thickness))
    
    def add_rectangle(self, img: np.ndarray, pt1: Tuple[int, int], pt2: Tuple[int, int],
                     color: Tuple[int, int, int], thickness: int = 1):
        """矩形描画をバッチに追加"""
        self.batches['rectangles'].append((img, pt1, pt2, color, thickness))
    
    def add_circle(self, img: np.ndarray, center: Tuple[int, int], radius: int,
                  color: Tuple[int, int, int], thickness: int = 1):
        """円描画をバッチに追加"""
        self.batches['circles'].append((img, center, radius, color, thickness))
    
    def add_polygon(self, img: np.ndarray, points: np.ndarray, 
                   color: Tuple[int, int, int], is_closed: bool = True):
        """ポリゴン描画をバッチに追加"""
        self.batches['polygons'].append((img, points, color, is_closed))
    
    def execute_batches(self):
        """バッチ描画を実行"""
        # 線を一括描画
        for img, pt1, pt2, color, thickness in self.batches['lines']:
            cv2.line(img, pt1, pt2, color, thickness, cv2.LINE_AA)
        
        # 矩形を一括描画
        for img, pt1, pt2, color, thickness in self.batches['rectangles']:
            cv2.rectangle(img, pt1, pt2, color, thickness, cv2.LINE_AA)
        
        # 円を一括描画
        for img, center, radius, color, thickness in self.batches['circles']:
            cv2.circle(img, center, radius, color, thickness, cv2.LINE_AA)
        
        # ポリゴンを一括描画
        for img, points, color, is_closed in self.batches['polygons']:
            cv2.polylines(img, [points], is_closed, color, 1, cv2.LINE_AA)
        
        self.clear()
    
    def clear(self):
        """バッチをクリア"""
        for batch_list in self.batches.values():
            batch_list.clear()

