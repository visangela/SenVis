import tntorch as tn
import torch
torch.set_default_dtype(torch.float64)
import numpy as np


class DirectionalCovariance(object):
    """
    The directional covariance w.r.t. variables {x1...xk} is the covariance
    between the input model and the function (x1+...+xk), divided by the function's std
    """

    def __init__(self, t, verbose=False):

        N = t.dim()
        self.N = N

        # Center the model (make it have mean 0)
        t -= tn.mean(t)

        # Compute the directional function: x1 + ... + xk for
        # every subset of variables
        cores = []
        for n in range(N):
            I = t.shape[n]
            c = torch.eye(2)[:, None, :].repeat(1, 2*I, 1)
            c[1, I:, 0] = torch.linspace(0, 1, I)
            cores.append(c)
        cores[0] = cores[0][1:2, ...]
        cores[N-1] = cores[N-1][..., 0:1]
        vecs = tn.Tensor(cores)

        # Center all directional functions (make them have mean 0)
        cores = []
        for n in range(N):
             I = t.shape[n]
             c1 = torch.mean(vecs.cores[n][:, :I, :], dim=1, keepdim=True).repeat(1, I, 1)
             c2 = torch.mean(vecs.cores[n][:, I:, :], dim=1, keepdim=True).repeat(1, I, 1)
             cores.append(torch.cat([c1, c2], dim=1))
        vecs_means = tn.Tensor(cores)
        vecs -= vecs_means

        # Compute the variance of all directional functions
        vecs_sq = vecs*vecs
        cores = []
        for n in range(N):
             I = t.shape[n]
             c1 = torch.mean(vecs_sq.cores[n][:, :I, :], dim=1, keepdim=True)
             c2 = torch.mean(vecs_sq.cores[n][:, I:, :], dim=1, keepdim=True)
             cores.append(torch.cat([c1, c2], dim=1))
        vecs_variance = tn.Tensor(cores)
        vecs_variance += tn.none(N)  # To avoid division by 0

        # Compute covariances between the model and all directional functions
        trep = tn.Tensor([c.repeat(1, 2, 1) for c in t.cores])
        covs = tn.cross(tensors=[trep, vecs], function=lambda x, y: x*y, verbose=verbose)
        for n in range(N):
            I = t.shape[n]
            c1 = torch.mean(covs.cores[n][:, :I, :], dim=1, keepdim=True)
            c2 = torch.mean(covs.cores[n][:, I:, :], dim=1, keepdim=True)
            covs.cores[n] = torch.cat([c1, c2], dim=1)

        # Tensor containing all 2^N desired indices
        result = tn.cross(tensors=[covs, vecs_variance], function=lambda x, y: x / torch.sqrt(y), verbose=verbose)

        # Normalize result so that the largest index in absolute value is 1.
        # That should be useful for color coding
        result /= max(torch.abs(tn.minimum(result)), torch.abs(tn.maximum(result)))

        self.result = result

    def index(self, variables):
        """
        Compute the covariance index w.r.t. given variables.

        :param variables: a list of integers
        :return: a real number
        """

        if len(variables) == 0:
            return 0
        if not all(np.unique(variables) == np.array(variables)):
            raise ValueError('There are repeated variables')

        # Read out the desired index
        idx = np.zeros(self.N, dtype=np.int)
        idx[np.array(variables)] = 1
        return self.result[tuple(idx)].item()


# Examples of use
if __name__ == '__main__':
    x, y = tn.meshgrid(32, 32)
    model = x+y  # This is the function f(x, y) = x+y
    dc = DirectionalCovariance(model)
    print('Index with respect to {x}:', dc.index([0]))
    print('Index with respect to {y}:', dc.index([1]))
    print('Index with respect to {x, y}:', dc.index([0, 1]))
