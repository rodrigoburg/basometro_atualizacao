def rice(vetor):
	if ( len(vetor) <= 1 ):
		return null
	n_one = 0
	n_zero = 0
	for i in vetor: # Calcula o numero de 1 e 0 
		if i == 0:
			n_zero += 1
		elif i == 1:
			n_one += 1
		else:
			continue
	rice = (n_one - n_zero)/(n_one + n_zero)
	return rice






