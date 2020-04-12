
import numpy as np
import math

class Tranceform3D2D:
    #カメラ内部パラメータ
    _fx = 0.0
    _fy = 0.0
    _cx = 0.0
    _cy = 0.0

    #カメラ外部パラメータ
    _roll = 0
    _pitch = 0
    _yaw = 0
    _t1 = 0
    _t2 = 0
    _t3 = 0

    #歪みパラメータ
    _k1 = 0.0
    _k2 = 0.0
    _k3 = 0.0
    _p1 = 0.0
    _p2 = 0.0


    _R = np.zeros((3, 3))

    def __init__(self, fx, fy, cx, cy):
        self._fx = fx
        self._fy = fy
        self._cx = cx
        self._cy = cy

    def SetDistortionParameter(self, k1, k2, k3, p1, p2):
        self._k1 = k1
        self._k2 = k2
        self._k3 = k3
        self._p1 = p1
        self._p2 = p2


    def Cvt3Dto2D(self, x_mm, y_mm, z_mm):

        x1 = (self._R[0,0] * x_mm + self._R[0,1] * y_mm + self._R[0,2] * z_mm + self._t1) / \
                    (self._R[2,0]*x_mm + self._R[2,1] * y_mm + self._R[2,2] * z_mm + self._t3)
        y1 = (self._R[1,0] * x_mm + self._R[1,1] * y_mm + self._R[1,2] * z_mm + self._t2) / \
                    (self._R[2,0]*x_mm + self._R[2,1] * y_mm + self._R[2,2] * z_mm + self._t3)

        r = math.sqrt(x1**2 + y1**2)
        k_radial = 1 + self._k1 * pow(r, 2) + self._k2 * pow(r, 4) + self._k3 * pow(r, 6)
        x2 = x1 * k_radial + 2 * self._p1 * x1 * y1 + self._p2 *(r**2 + 2 * x1**2)
        y2 = y1 * k_radial + self._p1 * (r**2 + 2 * y1**2) + 2 * self._p2 * x1 * y1

        x_pix = self._fx * x2 + self._cx
        y_pix = self._fy * y2 + self._cy

        return int(x_pix), int(y_pix)

    def SetExternalParameter(self, x, y, z, t1, t2, t3):
        rad_roll = math.radians(x)
        rad_pitch = math.radians(y)
        rad_yaw = math.radians(z)

        self._t1 = t1
        self._t2 = t2
        self._t3 = t3

        self._R[0,0] = np.cos(rad_pitch)*np.cos(rad_yaw) - np.sin(rad_roll)*np.sin(rad_pitch)*np.sin(rad_yaw)
        self._R[0,1] = -np.cos(rad_roll)*np.sin(rad_yaw);
        self._R[0,2] = np.sin(rad_pitch)*np.cos(rad_yaw) + np.sin(rad_roll)*np.cos(rad_pitch)*np.sin(rad_yaw);
        self._R[1,0] = np.cos(rad_pitch)*np.sin(rad_yaw) + np.sin(rad_roll)*np.sin(rad_pitch)*np.cos(rad_yaw);
        self._R[1,1] = np.cos(rad_roll)*np.cos(rad_yaw);
        self._R[1,2] = np.sin(rad_pitch)*np.sin(rad_yaw) - np.sin(rad_roll)*np.cos(rad_pitch)*np.cos(rad_yaw);
        self._R[2,0] = - np.cos(rad_roll)*np.sin(rad_pitch);
        self._R[2,1] = np.sin(rad_roll);
        self._R[2,2] = np.cos(rad_roll)*np.cos(rad_pitch);

        return self._R

    def computeAnglesFromMatrix(R:np, angle_roll, angle_pitch, angle_yaw):

      threshold = 0.001;

      if(abs(R[2,1] - 1.0) < threshold): # R(2,1) = sin(x) = 1の時
        angle_roll = np.PI / 2;
        angle_pitch = 0;
        angle_yaw = atan2(R[1,0], R[0,0])
      elif(abs(R[2,1] + 1.0) < threshold): # R(2,1) = sin(x) = -1の時
        angle_roll = - np.PI / 2;
        angle_pitch = 0;
        angle_yaw = atan2(R[1,0], R[0,0])
      else:
        angle_roll = asin(R[2,1]);
        angle_pitch = atan2(-R[2,0], R[2,2])
        angle_yaw = atan2(-R[0,1], R[1,1])
  