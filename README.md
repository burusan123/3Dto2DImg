# 3D Room Designer

3D Room Designerは、画像処理の勉強用のPythonスクリプトです。ワールド座標とローカル座標を変換します。学生の方はこのソースコードが勉強の役に立つことを祈っています・

Pythonで実装された簡易的な3D室内設計ビューアーです。このアプリケーションを使用することで、3D空間内で家具を配置し、様々な角度から室内レイアウトを確認することができます。

## 特徴

- 3D空間内での家具の配置と表示
- カメラ視点の自由な移動と回転
- **ズーム機能による視野の調整**
- **YAML設定ファイルによる柔軟なカスタマイズ**
- 拡張性の高いオブジェクト指向設計
- 直感的なキーボード操作

## 必要条件

- Python 3.6以上
- OpenCV (`opencv-python`)
- NumPy
- PyYAML

## インストール

1. このリポジトリをクローンします：

   ```bash
   git clone https://github.com/yourusername/3d-room-designer.git
   ```

2. プロジェクトディレクトリに移動します：

   ```bash
   cd 3Dto2DImg
   ```

3. 必要なパッケージをインストールします：

   ```bash
   pip install -r requirements.txt
   ```

## 使用方法

1. 以下のコマンドでアプリケーションを起動します：

   ```bash
   python src/room_designer.py
   ```

2. 3D Room Designerウィンドウが表示されます。

3. 以下のキーを使用して3D空間内を移動・操作できます：
   - **W/S**: 前後に移動
   - **A/D**: 左右に移動
   - **Q/E**: 視点を回転
   - **R/F**: 上下に移動
   - **Z/X**: ズームイン/ズームアウト
   - **マウス**: 家具をドラッグ&ドロップで移動
   - **P**: 座標データをエクスポート（JSON形式）
   - **Esc**: アプリケーションを終了

## 建築設計図・3DCAD対応機能

### 座標精度管理

本アプリケーションは建築設計図や3DCADへの連携を考慮した座標精度管理機能を搭載しています。

#### 精度モード

設定ファイルで以下の精度モードを選択できます：

- **integer**: 整数のみ（例: 150 mm）
- **decimal_1**: 小数点第1位まで（例: 150.5 mm）
- **decimal_2**: 小数点第2位まで（例: 150.25 mm）
- **decimal_3**: 小数点第3位まで（例: 150.125 mm）
- **full**: フル精度（制限なし）

#### グリッドスナップ

家具をドラッグする際、設定されたグリッドサイズに自動的にスナップします。
例：グリッドサイズ10mmの場合、145.7mmは150mmに自動調整されます。

#### 単位系サポート

以下の単位系に対応：
- **mm** (ミリメートル)
- **cm** (センチメートル)
- **m** (メートル)
- **inch** (インチ)
- **feet** (フィート)

#### 座標データのエクスポート

**P**キーを押すことで、現在の部屋と家具の座標データをJSON形式でエクスポートできます。

エクスポートされるデータには以下が含まれます：
- エクスポート日時
- 使用している単位系と精度モード
- 部屋のサイズ
- 各家具の正確な位置・サイズ
- 人間が読みやすいフォーマットされた座標

**エクスポート例:**
```json
{
  "export_date": "2025-11-02T15:30:00",
  "unit_system": "mm",
  "precision_mode": "decimal_1",
  "room": {
    "width": 500.0,
    "depth": 500.0,
    "height": 250.0,
    "unit": "mm"
  },
  "furnitures": [
    {
      "name": "テーブル",
      "position": {
        "x": 150.0,
        "y": 200.0,
        "z": 0.0
      },
      "dimensions": {
        "width": 150.0,
        "height": 75.0,
        "depth": 100.0
      },
      "formatted_position": "(150.0, 200.0, 0.0) mm"
    }
  ]
}
```

このJSONファイルは3DCADソフトウェアやBIMツールへのインポートに使用できます。

## 設定ファイルによるカスタマイズ

### 設定ファイルの場所

デフォルトの設定ファイルは `config/default_config.yaml` にあります。

### カスタム設定ファイルの使用

独自の設定ファイルを作成して使用することができます：

```python
from src.room_designer import RoomDesigner

# カスタム設定ファイルを指定
designer = RoomDesigner(config_path="my_custom_config.yaml")
designer.run()
```

### 設定項目

設定ファイルでは以下の項目をカスタマイズできます：

#### ウィンドウ設定
- `window.width`: ウィンドウの幅
- `window.height`: ウィンドウの高さ

#### 座標精度設定（建築設計図・3DCAD対応）
- `coordinate_precision.mode`: 精度モード
  - `integer`: 整数のみ (例: 150)
  - `decimal_1`: 小数点第1位まで (例: 150.5)
  - `decimal_2`: 小数点第2位まで (例: 150.25)
  - `decimal_3`: 小数点第3位まで (例: 150.125)
  - `full`: フル精度（制限なし）
- `coordinate_precision.grid_snap.enabled`: グリッドスナップの有効化
- `coordinate_precision.grid_snap.size`: グリッドサイズ
- `coordinate_precision.unit.system`: 単位系 (mm, cm, m, inch, feet)
- `coordinate_precision.unit.display`: 単位表示の有効化

#### カメラ設定
- `camera.focal_length`: 初期焦点距離（ズームレベル）
- `camera.min_focal_length`: 最小焦点距離（最大ズームアウト）
- `camera.max_focal_length`: 最大焦点距離（最大ズームイン）
- `camera.zoom_step`: ズームステップ
- `camera.initial_position`: カメラの初期位置 (x, y, z)
- `camera.initial_rotation`: カメラの初期回転 (roll, pitch, yaw)
- `camera.movement_speed`: カメラ移動速度
- `camera.rotation_speed`: カメラ回転速度

#### 部屋設定
- `room.width`: 部屋の幅
- `room.depth`: 部屋の奥行き
- `room.height`: 部屋の高さ
- `room.color`: 部屋の輪郭線の色 [R, G, B]

#### 家具設定
- `furnitures`: 家具のリスト
  - `name`: 家具の名前
  - `position`: 位置 (x, y, z)
  - `size`: サイズ (width, height, depth)
  - `color`: 色 [R, G, B]

#### UI設定
- `ui.instructions`: 操作説明の表示設定
- `ui.zoom_display`: ズームレベル表示設定

### 設定例

```yaml
# 家具を追加する例
furnitures:
  - name: "デスク"
    position:
      x: 200
      y: 200
      z: 0
    size:
      width: 120
      height: 75
      depth: 60
    color: [139, 69, 19]  # 茶色
```

## プロジェクト構造

```
3Dto2DImg/
├── config/
│   └── default_config.yaml    # デフォルト設定ファイル
├── src/
│   ├── calc3Dto2D.py          # 3D→2D座標変換モジュール
│   ├── config_loader.py       # 設定ファイル読み込みモジュール
│   └── room_designer.py       # メインアプリケーション
├── requirements.txt           # 依存パッケージ
└── README.md                  # このファイル
```

## アーキテクチャ

### モジュール設計

- **calc3Dto2D.py**: カメラモデルを実装し、3D座標を2D画像座標に変換
- **config_loader.py**: YAML設定ファイルを読み込み、構造化されたデータを提供
- **room_designer.py**: UIとメインロジックを管理

### クラス構成

- `Drawable`: 描画可能オブジェクトの抽象基底クラス
- `Furniture`: 家具クラス（直方体のワイヤーフレーム）
- `Room`: 部屋クラス（家具のコレクション管理）
- `RoomDesigner`: メインビューアークラス
- `Tranceform3D2D`: 3D-2D座標変換クラス
- `ConfigLoader`: 設定ファイル管理クラス

## 拡張方法

### 新しい家具タイプの追加

`Drawable`クラスを継承して新しい描画可能オブジェクトを作成できます：

```python
class CustomFurniture(Drawable):
    def draw(self, img: np.ndarray, transform: Tranceform3D2D):
        # カスタム描画処理を実装
        pass
```

### 設定ファイルのプログラム的な生成

```python
from src.config_loader import ConfigLoader

config = ConfigLoader()
# 設定を変更
config._config['room']['width'] = 600
# 新しいファイルとして保存
config.save('new_config.yaml')
```

## 貢献

バグの報告や機能の提案は、Issueを通じて行ってください。プルリクエストも歓迎します。

## ライセンス

このプロジェクトは[MITライセンス](LICENSE)の下で公開されています。

## 謝辞

このプロジェクトは、OpenCV、NumPy、PyYAMLライブラリを使用しています。これらの素晴らしいツールを提供してくれているコミュニティに感謝します。