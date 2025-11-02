"""
描画可能オブジェクトの抽象基底クラスモジュール

3D空間に描画可能なオブジェクトの基本インターフェースを定義します。
"""

import numpy as np
from abc import ABC, abstractmethod
from calc3Dto2D import Tranceform3D2D


class Drawable(ABC):
    """描画可能なオブジェクトの抽象基底クラス"""
    
    @abstractmethod
    def draw(self, img: np.ndarray, transform: Tranceform3D2D, text_renderer=None):
        """
        オブジェクトを画像に描画する
        
        :param img: 描画対象の画像
        :param transform: 3D to 2D変換オブジェクト
        :param text_renderer: テキスト描画用レンダラー（オプション）
        """
        pass

