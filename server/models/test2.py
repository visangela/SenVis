def get_model():

	def function(Xs):
	    x1 = Xs[:, 0]
	    x2 = Xs[:, 1]
	    return (x1 - 1)**2 + 2*(2*x2**2 - x1)**2

	axes = [dict(name='x1', domain=(-10, 10)),
	        dict(name='x2', domain=(-10, 10))]

	return function, axes
