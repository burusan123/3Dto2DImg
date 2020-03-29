
import numpy as np
import cv2
import math
import _3D2D

#世界座標 単位mm
setting_z_mm = 3000
setting_x_mm = 2000
setting_y_mm = 2000

#解像度設定
width = 1920
height = 1080
center_x = width / 2
center_y = height / 2

#カメラ内部パラメータ
fx = 648.04012214
fy = 652.62477735
cx = 0
cy = 0

#カメラ外部パラメータの回転行列で使用する角度
x = 0
y = 0
z = 0

#カメラ外部パラメータ　並進ベクトル
t1 = 0
t2 = 0
t3 = 0

#描画する格子
step = 30
start_pos_x_mm = -setting_x_mm / 2
start_pos_y_mm = -setting_y_mm / 2
step_x = setting_x_mm / step
step_y = setting_x_mm / step

cv2.namedWindow("3D", cv2.WINDOW_AUTOSIZE)
key = 0
while (key != ord("q")):
    rad_x = math.radians(x)
    rad_y = math.radians(y)
    rad_z = math.radians(z)
    
    img = np.zeros((height, width,3), dtype=np.uint8)

    #　格子計算
    y_mm = start_pos_y_mm
    for pix_y in range(step):
        x_mm = start_pos_x_mm
        for pix_x in range(step):

            #　世界座標を画像座標に変換する
            r = _3D2D.computeMatrixFromAngles(rad_x, rad_y, rad_z)
            x_pix = fx * (r[0,0] * x_mm + r[0,1] * y_mm + r[0,2] * setting_z_mm + t1) / \
                    (r[2,0]*x_mm + r[2,1] * y_mm + r[2,2] * setting_z_mm + t3) + cx
            y_pix = fy * (r[1,0] * x_mm + r[1,1] * y_mm + r[1,2] * setting_z_mm + t2) / \
                    (r[2,0]*x_mm + r[2,1] * y_mm + r[2,2] * setting_z_mm + t3) + cy

            #　世界座標はカメラ中心が0,0の座標のため、座標変換する
            x_pix = int(center_x + x_pix)
            y_pix = int(center_y + y_pix)

            if x_pix < width and 0 < x_pix and y_pix < height and y_pix > 0:
                img[y_pix, x_pix, 0] = 255
                img[y_pix, x_pix, 1] = 255
                img[y_pix, x_pix, 2] = 255

            x_mm += step_x
        y_mm += step_y

    cv2.imshow("3D",img)
    key = cv2.waitKey(0) & 0xff
    if (key == ord('w')):
        x += 1
    elif (key == ord('s')):
        x -= 1
    elif (key == ord('a')):
        y -= 1
    elif (key == ord('d')):
        y += 1
    elif (key == ord(',')):
        z += 1
    elif (key == ord('.')):
        z -= 1
    elif (key == ord('1')):
       fx += 50
    elif (key == ord('2')):
       fx -= 50
    elif (key == ord('3')):
       fy += 50
    elif (key == ord('4')):
       fy -= 50
    elif (key == ord('5')):
       cx += 50
    elif (key == ord('6')):
       cx -= 50
    elif (key == ord('7')):
       cy += 50
    elif (key == ord('8')):
       cy -= 50
    elif (key == ord('9')):
       setting_z_mm += 50
    elif (key == ord('0')):
        setting_z_mm -= 50
    else:
        print(key)

    #print("x, y, z: " + str(x) + "," + str(y) + "," + str(z))




