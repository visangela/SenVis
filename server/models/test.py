import numpy as np

def get_model():

	def function(Xs):
	    C_T = Xs[:, 0]
	    kwake = Xs[:, 1]
	    d0 = Xs[:, 2]
	    x = Xs[:, 3]
	    return (1 - np.sqrt(1 - C_T)) / (1 + 2*kwake*x/d0)**2

	axes = [dict(name='C_T', domain=(0.4, 0.8)),
	        dict(name='k_{wake}', domain=(0.1, 0.2)),
	        dict(name='d_0', domain=(1, 80)),
	        dict(name='x', domain=(1, 200))]

	return function, axes
