def get_model():
	# reference: 
	# https://www.mdpi.com/2077-0383/9/2/462
	# https://www.sciencedirect.com/science/article/pii/S246804272030004X
	# domains are estimated by using mean and standard deviation from the papers

	def function(Xs):
		c = Xs[:, 0]
		beta = Xs[:, 1]
		q = Xs[:, 2]
		theta = Xs[:, 3]
		o = Xs[:, 4]
		delta_I = Xs[:, 5]
		gamma_I = Xs[:, 6]
		gamma_A = Xs[:, 7]
		alpha = Xs[:, 8]
		return 8570000 * ( (beta * o * c * (1 - q)) / (delta_I + alpha + gamma_I) + (beta * c * theta * (1 - o) * (1 - q)) / (gamma_A))

	axes = [dict(name='c: Contact rate', domain=(12.069, 17.493)),
	        dict(name='beta: Probability of transmission per contact', domain=(1.74453e-8, 2.45769e-8)),
	        dict(name='q: Quarantined rate of exposed individuals', domain=(0, 3.79832e-7)),
	        dict(name='theta', domain=(0,1)),
	        dict(name='o: symptoms among infected individuals', domain=(0.720659, 1.016021)),
	        dict(name='delta_I: Transition rate of symptomatic infected individuals to the quarantined infected class', domain=(0.068715, 0.196605)),
	        dict(name='gamma_I: Recovery rate of symptomatic infected individuals', domain=(0.173885, 0.486695)),
	        dict(name='gamma_A: Recovery rate of asymptomatic infected individuals', domain=(0.035317 , 0.244243)),
	        dict(name='alpha: Disease-induced death rate', domain=(0, 3.83253))]

	return function, axes
