def get_model():

	def function(Xs):
	    x1 = Xs[:, 0]
	    x2 = Xs[:, 1]
	    x3 = Xs[:, 2]
	    x4 = Xs[:, 3]
	    return x1*2.4 + x2*0.5 - x3*1.2 - x4*2

	axes = [dict(name='x_1: ', domain=(-10, 10)),
	        dict(name='x_2: ', domain=(-10, 10)),
	        dict(name='x_3: ', domain=(-10, 10)),
	        dict(name='x_4: ', domain=(-10, 10))]

	return function, axes
