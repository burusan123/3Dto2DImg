"""
テキスト描画モジュール

日本語を含むテキストをOpenCV画像に描画するための機能を提供します。
PIL(Pillow)を使用して日本語フォントをサポートします。
"""

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Optional
from abc import ABC, abstractmethod


class TextRenderer(ABC):
    """テキスト描画の抽象基底クラス"""
    
    @abstractmethod
    def draw_text(self, img: np.ndarray, text: str, position: Tuple[int, int], 
                  font_size: int, color: Tuple[int, int, int], 
                  outline: bool = False, outline_color: Tuple[int, int, int] = (0, 0, 0),
                  outline_width: int = 1) -> np.ndarray:
        """
        テキストを画像に描画する
        
        :param img: 描画対象の画像（numpy配列）
        :param text: 描画するテキスト
        :param position: テキストの位置 (x, y)
        :param font_size: フォントサイズ
        :param color: テキストの色 (R, G, B)
        :param outline: 縁取りを描画するか
        :param outline_color: 縁取りの色 (R, G, B)
        :param outline_width: 縁取りの幅
        :return: テキストが描画された画像
        """
        pass


class PILTextRenderer(TextRenderer):
    """PIL/Pillowを使用した日本語対応テキスト描画クラス"""
    
    def __init__(self, font_path: Optional[str] = None):
        """
        初期化メソッド
        
        :param font_path: 使用するフォントファイルのパス（Noneの場合はデフォルトフォント）
        """
        self.font_path = font_path
        self._font_cache = {}  # フォントキャッシュ
    
    def _get_font(self, size: int) -> ImageFont.FreeTypeFont:
        """
        指定されたサイズのフォントを取得（キャッシュ機能付き）
        
        :param size: フォントサイズ
        :return: フォントオブジェクト
        """
        if size in self._font_cache:
            return self._font_cache[size]
        
        try:
            if self.font_path:
                # 指定されたフォントを使用
                font = ImageFont.truetype(self.font_path, size)
            else:
                # Windowsのデフォルト日本語フォントを試行
                try:
                    # MS Gothic（Windows標準）
                    font = ImageFont.truetype("msgothic.ttc", size)
                except:
                    try:
                        # メイリオ（Windows標準）
                        font = ImageFont.truetype("meiryo.ttc", size)
                    except:
                        try:
                            # Yu Gothic（Windows標準）
                            font = ImageFont.truetype("yugothic.ttc", size)
                        except:
                            # どれも利用できない場合はデフォルトフォント
                            font = ImageFont.load_default()
        except Exception as e:
            # フォント読み込みに失敗した場合はデフォルトフォント
            print(f"フォント読み込みエラー: {e}")
            font = ImageFont.load_default()
        
        self._font_cache[size] = font
        return font
    
    def draw_text(self, img: np.ndarray, text: str, position: Tuple[int, int], 
                  font_size: int, color: Tuple[int, int, int], 
                  outline: bool = False, outline_color: Tuple[int, int, int] = (0, 0, 0),
                  outline_width: int = 1) -> np.ndarray:
        """
        PIL/Pillowを使用してテキストを画像に描画する
        
        :param img: 描画対象の画像（numpy配列、BGR形式）
        :param text: 描画するテキスト
        :param position: テキストの位置 (x, y)
        :param font_size: フォントサイズ
        :param color: テキストの色 (R, G, B)
        :param outline: 縁取りを描画するか
        :param outline_color: 縁取りの色 (R, G, B)
        :param outline_width: 縁取りの幅
        :return: テキストが描画された画像
        """
        # OpenCV画像（BGR）をPIL画像（RGB）に変換
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        # フォントを取得
        font = self._get_font(font_size)
        
        # 位置を調整（中心揃えのため）
        try:
            # テキストのバウンディングボックスを取得
            bbox = draw.textbbox(position, text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # 中心揃えの位置を計算
            adjusted_x = position[0] - text_width // 2
            adjusted_y = position[1] - text_height // 2
            adjusted_position = (adjusted_x, adjusted_y)
        except:
            # textbboxが使えない場合は元の位置を使用
            adjusted_position = position
        
        # 縁取りを描画
        if outline:
            # 縁取りのために周囲に複数回描画
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        outline_pos = (adjusted_position[0] + dx, adjusted_position[1] + dy)
                        draw.text(outline_pos, text, font=font, fill=outline_color)
        
        # メインテキストを描画（RGBをそのまま使用）
        draw.text(adjusted_position, text, font=font, fill=color)
        
        # PIL画像（RGB）をOpenCV画像（BGR）に変換
        img_bgr = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
        
        return img_bgr


class OpenCVTextRenderer(TextRenderer):
    """OpenCVの標準機能を使用したテキスト描画クラス（ASCII文字のみ対応）"""
    
    def draw_text(self, img: np.ndarray, text: str, position: Tuple[int, int], 
                  font_size: int, color: Tuple[int, int, int], 
                  outline: bool = False, outline_color: Tuple[int, int, int] = (0, 0, 0),
                  outline_width: int = 1) -> np.ndarray:
        """
        OpenCVを使用してテキストを画像に描画する（ASCII文字のみ）
        
        :param img: 描画対象の画像（numpy配列、BGR形式）
        :param text: 描画するテキスト
        :param position: テキストの位置 (x, y)
        :param font_size: フォントサイズ（0.3-2.0程度）
        :param color: テキストの色 (R, G, B) - 内部でBGRに変換
        :param outline: 縁取りを描画するか
        :param outline_color: 縁取りの色 (R, G, B) - 内部でBGRに変換
        :param outline_width: 縁取りの幅
        :return: テキストが描画された画像
        """
        # フォントスケールの調整
        scale = font_size / 20.0  # 適切なスケールに変換
        thickness = max(1, int(scale * 2))
        
        # 色をBGRに変換
        color_bgr = (color[2], color[1], color[0])
        outline_color_bgr = (outline_color[2], outline_color[1], outline_color[0])
        
        # 縁取りを描画
        if outline:
            cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                       scale, outline_color_bgr, thickness + outline_width, cv2.LINE_AA)
        
        # メインテキストを描画
        cv2.putText(img, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                   scale, color_bgr, thickness, cv2.LINE_AA)
        
        return img


class TextRendererFactory:
    """テキストレンダラーのファクトリークラス"""
    
    @staticmethod
    def create_renderer(renderer_type: str = "pil", font_path: Optional[str] = None) -> TextRenderer:
        """
        テキストレンダラーを作成する
        
        :param renderer_type: レンダラーのタイプ（"pil" または "opencv"）
        :param font_path: フォントファイルのパス（PILレンダラーの場合のみ）
        :return: TextRendererインスタンス
        """
        if renderer_type.lower() == "pil":
            return PILTextRenderer(font_path)
        elif renderer_type.lower() == "opencv":
            return OpenCVTextRenderer()
        else:
            raise ValueError(f"未対応のレンダラータイプ: {renderer_type}")

