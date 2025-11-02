# 3D Room Designer

3D Room Designerは、画像処理の勉強用のPythonスクリプトです。ワールド座標とローカル座標を変換します。学生の方はこのソースコードが勉強の役に立つことを祈っています・

Pythonで実装された簡易的な3D室内設計ビューアーです。このアプリケーションを使用することで、3D空間内で家具を配置し、様々な角度から室内レイアウトを確認することができます。

## 特徴

- 3D空間内での家具の配置と表示
- カメラ視点の自由な移動と回転
- **ズーム機能による視野の調整（Z/Xキー、マウスホイール）**
- **上からの投影図（平面図）を別ウィンドウで表示**
- **家具配置の自動保存・復元機能**
- **ドラッグ&ドロップによる直感的な家具移動**
- **マウス中ボタンドラッグによるカメラパン**
- **YAML設定ファイルによる柔軟なカスタマイズ**
- **建築設計図・3DCAD対応の座標精度管理**
- 拡張性の高いオブジェクト指向設計
- 直感的なキーボード・マウス操作

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

3. 平面図（Top View）ウィンドウも同時に表示されます（設定で無効化可能）。

4. 以下のキーを使用して3D空間内を移動・操作できます：
   - **W/S**: 前後に移動
   - **A/D**: 左右に移動
   - **Q/E**: 視点を回転
   - **R/F**: 上下に移動
   - **Z/X または マウスホイール**: ズームイン/ズームアウト
   - **マウス左ボタン**: 家具をドラッグ&ドロップで移動
   - **マウス中ボタン（ホイールドラッグ）**: カメラをパン（平行移動）
   - **P**: 座標データをエクスポート（JSON形式）
   - **Esc**: アプリケーションを終了

5. アプリケーション終了時に、家具の配置が自動的に保存されます。次回起動時に前回の配置が復元されます。

## 家具配置の自動保存機能

### 概要

アプリケーションを終了すると、現在の家具の配置（位置・サイズ・色）が自動的に保存されます。次回起動時には、保存された配置が自動的に復元されるため、作業の続きから始めることができます。

### 保存される情報

- 各家具の位置（x, y, z座標）
- 各家具のサイズ（幅、高さ、奥行き）
- 各家具の色
- 最終保存日時

### 設定

`config/default_config.yaml`の`application`セクションで自動保存の設定をカスタマイズできます：

```yaml
application:
  # 家具配置の自動保存ファイル
  furniture_layout_file: "furniture_layout.json"
  # 自動保存の有効化
  auto_save_layout: true
```

**設定項目:**
- `furniture_layout_file`: 保存ファイルのパス（デフォルト: `furniture_layout.json`）
- `auto_save_layout`: 自動保存の有効化（`true`: 有効、`false`: 無効）

### 保存ファイルの形式

保存ファイルはJSON形式で、以下のような構造になっています：

```json
{
  "last_saved": "2025-11-02T18:30:00.123456",
  "furnitures": [
    {
      "name": "テーブル",
      "x": 150.0,
      "y": 200.0,
      "z": 0.0,
      "width": 150.0,
      "height": 75.0,
      "depth": 100.0,
      "color": [0, 255, 0]
    }
  ]
}
```

### 注意事項

- カメラの位置や向きは保存されません（常に設定ファイルの初期値から開始）
- 家具の追加・削除は設定ファイルで行う必要があります
- 保存ファイルが存在しない場合は、設定ファイルの初期配置が使用されます
- 自動保存を無効にしたい場合は、`auto_save_layout: false`に設定してください

## 平面図（Top View）機能

### 概要

別ウィンドウで上からの投影図（平面図）を表示します。この機能により、3Dビューと平面図を同時に確認しながら、より直感的に室内レイアウトを設計できます。

### 表示内容

- **部屋の輪郭**: グレーの線で部屋の範囲を表示
- **家具**: 各家具を色付きの矩形で表示（半透明）
  - 選択中の家具はシアン色でハイライト表示
  - 家具の名前が中央に表示
- **カメラ位置**: 赤い円で現在のカメラ位置を表示
- **視線方向**: 青い矢印でカメラの向きを表示
- **視野角（FOV）**: 薄赤の線でカメラの視野範囲を表示

### 設定のカスタマイズ

`config/default_config.yaml`の`ui.top_view`セクションで平面図の設定をカスタマイズできます：

```yaml
ui:
  top_view:
    enabled: true         # 平面図表示の有効化
    size: 600            # ウィンドウサイズ（正方形）
    margin: 50           # 描画マージン
    background_color: [255, 255, 255]  # 背景色（白）
    room_color: [100, 100, 100]        # 部屋の輪郭色（グレー）
    camera_color: [0, 0, 255]          # カメラ位置の色（赤）
    view_direction_color: [255, 0, 0]  # 視線方向の色（青）
    fov_color: [255, 100, 100]         # 視野角の色（薄赤）
    selected_color: [0, 200, 200]      # 選択中の家具の色（シアン）
```

### 利用シーン

- **レイアウト確認**: 3Dビューと平面図を比較して、家具の配置を確認
- **カメラ位置の把握**: 現在のカメラ位置と視線方向を俯瞰的に確認
- **設計図作成**: 平面図をスクリーンショットして設計資料として活用
- **建築図面との照合**: 平面図を見ながら3Dモデルを調整

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
- `camera.mouse_drag.sensitivity`: ホイールドラッグの感度
- `camera.mouse_drag.invert_x`: X軸の反転（true/false）
- `camera.mouse_drag.invert_y`: Y軸の反転（true/false）

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

#### ホイールドラッグ設定の詳細

マウス中ボタンでのカメラパン（移動）の動作をカスタマイズできます：

```yaml
camera:
  mouse_drag:
    sensitivity: 2.0  # ドラッグの感度（大きいほど敏感）
    invert_x: false   # X軸を反転
    invert_y: false   # Y軸を反転
```

**設定パラメータ:**
- `sensitivity`: マウス移動量に対するカメラ移動量の倍率（デフォルト: 2.0）
  - 大きくすると少しのマウス移動で大きくカメラが動く
  - 小さくすると精密な操作が可能
- `invert_x`: X軸（左右）の反転
  - `false` (デフォルト): マウス右 → カメラ右、マウス左 → カメラ左
  - `true`: マウス右 → カメラ左、マウス左 → カメラ右
- `invert_y`: Y軸（前後）の反転
  - `false` (デフォルト): マウス下 → カメラ後退、マウス上 → カメラ前進
  - `true`: マウス下 → カメラ前進、マウス上 → カメラ後退

## 座標系と回転の理解

### ワールド座標系

このアプリケーションは右手座標系を使用しています：

- **X軸**: 右方向（部屋の幅方向）
- **Y軸**: 前方向（部屋の奥行き方向）
- **Z軸**: 上方向（部屋の高さ方向）

```
        Z (上)
        |
        |
        |_______ Y (前)
       /
      /
     X (右)
```

### カメラの姿勢

#### 初期姿勢（roll=0, pitch=0, yaw=0）
- カメラはZ軸の正の方向を向く（上を見ている）
- カメラの上方向はY軸の負の方向

#### 回転パラメータ

| **パラメータ** | **回転軸** | **動作** | **特殊な値** |
|-------------|----------|---------|-----------|
| **roll** | X軸周り | 上下を見る | 0度=上を見る, 180度=真下を見る（トップビュー） |
| **pitch** | Y軸周り | 左右を向く | 正=右を向く, 負=左を向く |
| **yaw** | Z軸周り | 水平回転 | 正=反時計回り, 負=時計回り |

#### トップビューの設定

真上からの俯瞰図（トップビュー）を実現するには：

```yaml
camera:
  initial_position:
    x: 250    # 部屋の中心
    y: 250    # 部屋の中心
    z: 900    # 十分な高さ
  
  initial_rotation:
    roll: 180   # X軸周りに180度 = 真下を向く
    pitch: 0    # 左右の回転なし
    yaw: 0      # 水平回転なし
```

**説明**: カメラを真上に配置し、X軸周りに180度回転することで真下を向けます。これにより、カメラ座標系のZ軸（前方）がワールド座標系のZ軸負の方向を向き、床面が正しく見えます。

### 他の視点の例

#### 斜め上から見下ろす（デフォルトの3Dビュー）
```yaml
initial_position: {x: 0, y: -500, z: 300}
initial_rotation: {roll: -30, pitch: 0, yaw: 0}
```

#### 正面から見る
```yaml
initial_position: {x: 250, y: -200, z: 125}
initial_rotation: {roll: 0, pitch: 0, yaw: 0}
```

#### 横から見る
```yaml
initial_position: {x: -200, y: 250, z: 125}
initial_rotation: {roll: 0, pitch: 90, yaw: 0}
```

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