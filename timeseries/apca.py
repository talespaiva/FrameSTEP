# INCOMPLETE implementation of APCA

#Papers:
#[Locally Adaptive Dimensionality Reduction for Indexing Large Time Series Databases]
# (https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/apca_indexing_journal.pdf)
#[Wavelets for Computer Graphics: A Primer]
# (http://grail.cs.washington.edu/wp-content/uploads/2015/08/stollnitz-1995-wfc1.pdf)

import pywt
import numpy as np
import matplotlib.pyplot as plt

haar = pywt.Wavelet('haar')
C = [7, 5, 5, 3, 3, 3, 4, 6]
M = pywt.dwt_max_level(len(C), haar.rec_len)

# Apply DWT
cA, cD1, cD2, cD3 = pywt.wavedec(C, haar, level=M)/np.sqrt(np.power(2, M-1))

all_coefs = np.concatenate([cD1, cD2, cD3])
ind = np.argpartition(abs(all_coefs), -(M))[-(M):]
rec_coef = np.zeros(len(ind)-1)
rec_coef = np.sort(all_coefs[ind])[::-1]
rec_coef = np.sort(rec_coef)[::-1]
cA = np.repeat(cA, M)

# Reconstruct signal
rec = pywt.idwt(cA, rec_coef, 'haar')
x = rec
rec = [[a, b] for a, b in zip(rec, rec)]
rec = np.array(rec).flatten()
print('recovered signal:', rec)

#plt.figure()
#plt.plot(C, '-o', drawstyle='steps-mid')
#plt.plot(rec, '-o', drawstyle='steps-mid')
#plt.show()