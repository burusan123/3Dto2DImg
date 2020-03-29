
import numpy as np

def computeMatrixFromAngles(x, y, z):

   R = np.zeros((3, 3))
   R[0,0] = np.cos(y)*np.cos(z) - np.sin(x)*np.sin(y)*np.sin(z)
   R[0,1] = -np.cos(x)*np.sin(z);
   R[0,2] = np.sin(y)*np.cos(z) + np.sin(x)*np.cos(y)*np.sin(z);
   R[1,0] = np.cos(y)*np.sin(z) + np.sin(x)*np.sin(y)*np.cos(z);
   R[1,1] = np.cos(x)*np.cos(z);
   R[1,2] = np.sin(y)*np.sin(z) - np.sin(x)*np.cos(y)*np.cos(z);
   R[2,0] = - np.cos(x)*np.sin(y);
   R[2,1] = np.sin(x);
   R[2,2] = np.cos(x)*np.cos(y);

   return R

def computeAnglesFromMatrix(R:np, angle_x, angle_y, angle_z):

  threshold = 0.001;

  if(abs(R[2,1] - 1.0) < threshold): # R(2,1) = sin(x) = 1の時
    angle_x = np.PI / 2;
    angle_y = 0;
    angle_z = atan2(R[1,0], R[0,0])
  elif(abs(R[2,1] + 1.0) < threshold): # R(2,1) = sin(x) = -1の時
    angle_x = - np.PI / 2;
    angle_y = 0;
    angle_z = atan2(R[1,0], R[0,0])
  else:
    angle_x = asin(R[2,1]);
    angle_y = atan2(-R[2,0], R[2,2])
    angle_z = atan2(-R[0,1], R[1,1])
  