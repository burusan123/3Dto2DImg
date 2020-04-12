
import numpy as np
import cv2
import math
import _3D2D

#世界座標 単位mm
setting_z_mm = 50000
setting_x_mm = 500
setting_y_mm = 1700

#解像度設定
width = 1920
height = 1080
center_x = width / 2
center_y = height / 2

#カメラ内部パラメータ
fx = 648.04012214
fy = 652.62477735
cx = center_x
cy = center_y

#カメラ外部パラメータの回転行列で使用する角度
x = 0
y = 0
z = 0

#カメラ外部パラメータ　並進ベクトル
t1 = 0
t2 = 0
t3 = 0

#カメラ歪みパラメータ
k1 = -2.23845891e-01
k2 = -7.32573873e-01
p1 = -7.30350307e-04
p2 = -1.68303803e-03
k3 = 0.00000000e+00

#描画する格子
step = 10
start_pos_x_mm = int(-setting_x_mm / 2)
start_pos_y_mm = int(-setting_y_mm / 2)
end_pos_x_mm = int(setting_x_mm / 2)
end_pos_y_mm = int(setting_y_mm / 2)
step_x = int(setting_x_mm / step)
step_y = int(setting_x_mm / step)


cv2.namedWindow("3D", cv2.WINDOW_AUTOSIZE)
key = 0
while (key != ord("q")):    
    img = np.zeros((height, width,3), dtype=np.uint8)

    tranceform = _3D2D.Tranceform3D2D(fx,fy,cx,cy)
    tranceform.SetExternalParameter(x, y, z, t1, t2, t3)
    tranceform.SetDistortionParameter(k1, k2, k3, p1, p2)

    #　格子計算
    for y_mm in range(start_pos_y_mm, end_pos_y_mm, step_y):
        for x_mm in range(start_pos_x_mm, end_pos_x_mm, step_x):
            #　世界座標を画像座標に変換する
            x_pix, y_pix = tranceform.Cvt3Dto2D(x_mm, y_mm, setting_z_mm)

            if x_pix < width and 0 < x_pix and y_pix < height and y_pix > 0:
                img[y_pix, x_pix, 0] = 255
                img[y_pix, x_pix, 1] = 255
                img[y_pix, x_pix, 2] = 255

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




