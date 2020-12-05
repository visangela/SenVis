import tntorch as tn
import torch
import numpy as np


class AllIndices():

    def __init__(self, t, eps=1e-9, verbose=False):

        # if isinstance(t, tt.core.vector.vector):
        #     t = tn.Tensor([torch.Tensor(c) for c in tt.vector.to_list(t)])

        ###########################################
        # Precompute all 4 types of Sobol indices #
        ###########################################

        t = t
        N = t.dim()
        tsq = t.decompress_tucker_factors()
        for n in range(N):
            tsq.cores[n] = torch.cat([torch.mean(tsq.cores[n], dim=1, keepdim=True), tsq.cores[n]], dim=1)
        tsq = tn.cross(tensors=[tsq], function=lambda x: x ** 2, eps=eps, verbose=verbose)

        st_cores = []
        for n in range(N):
            st_cores.append(torch.cat(
                [tsq.cores[n][:, :1, :], torch.mean(tsq.cores[n][:, 1:, :], dim=1, keepdim=True) - tsq.cores[n][:, :1, :]],
                dim=1))
        st = tn.Tensor(st_cores)
        var = tn.sum(st) - st[(0,) * N]
        self.st = tn.round_tt(st / var, eps=eps)
        self.st -= tn.none(N)*self.st[(0,)*N]  # Set element 0, ..., 0 to zero
        self.sst = tn.Tensor([torch.cat([c[:, :1, :] + c[:, 1:2, :], c[:, 1:2, :]], dim=1) for c in self.st.cores])
        self.cst = tn.Tensor([torch.cat([c[:, :1, :], c[:, :1, :] + c[:, 1:2, :]], dim=1) for c in self.st.cores])
        self.tst = 1-tn.Tensor([torch.cat([c[:, :1, :] + c[:, 1:2, :], c[:, :1, :]], dim=1) for c in self.st.cores])


        ##########################################
        # Precompute all directional covariances #
        ##########################################

        # # Center the model (make it have mean 0)
        # t = t.clone() - tn.mean(t)

        # # Compute the directional function: x1 + ... + xk for
        # # every subset of variables
        # cores = []
        # for n in range(N):
        #     I = t.shape[n]
        #     c = torch.eye(2)[:, None, :].repeat(1, 2 * I, 1)
        #     c[1, I:, 0] = torch.linspace(0, 1, I)
        #     cores.append(c)
        # cores[0] = cores[0][1:2, ...]
        # cores[N - 1] = cores[N - 1][..., 0:1]
        # vecs = tn.Tensor(cores)

        # # Center all directional functions (make them have mean 0)
        # cores = []
        # for n in range(N):
        #     I = t.shape[n]
        #     c1 = torch.mean(vecs.cores[n][:, :I, :], dim=1, keepdim=True).repeat(1, I, 1)
        #     c2 = torch.mean(vecs.cores[n][:, I:, :], dim=1, keepdim=True).repeat(1, I, 1)
        #     cores.append(torch.cat([c1, c2], dim=1))
        # vecs_means = tn.Tensor(cores)
        # vecs -= vecs_means

        # # Compute the variance of all directional functions
        # vecs_sq = vecs * vecs
        # cores = []
        # for n in range(N):
        #     I = t.shape[n]
        #     c1 = torch.mean(vecs_sq.cores[n][:, :I, :], dim=1, keepdim=True)
        #     c2 = torch.mean(vecs_sq.cores[n][:, I:, :], dim=1, keepdim=True)
        #     cores.append(torch.cat([c1, c2], dim=1))
        # vecs_variance = tn.Tensor(cores)
        # vecs_variance += tn.none(N)  # To avoid division by 0

        # # Compute covariances between the model and all directional functions
        # trep = tn.Tensor([c.repeat(1, 2, 1) for c in t.cores])
        # covs = tn.cross(tensors=[trep, vecs], function=lambda x, y: x * y, verbose=verbose)
        # for n in range(N):
        #     I = t.shape[n]
        #     c1 = torch.mean(covs.cores[n][:, :I, :], dim=1, keepdim=True)
        #     c2 = torch.mean(covs.cores[n][:, I:, :], dim=1, keepdim=True)
        #     covs.cores[n] = torch.cat([c1, c2], dim=1)

        # # Tensor containing all 2^N desired indices
        # dircov = tn.cross(tensors=[covs, vecs_variance], function=lambda x, y: x / torch.sqrt(y), verbose=verbose)

        # # Normalize result so that the largest index in absolute value is 1.
        # # That should be useful for color coding
        # dircov /= max(torch.abs(tn.minimum(dircov)), torch.abs(tn.maximum(dircov)))

        # self.dircov = dircov

    def _get_index(self, variables, tensor):
        
        if len(variables) == 0:
            return 0

        # Read out the desired index
        idx = np.zeros(tensor.dim(), dtype=np.int)
        idx[np.array(variables)] = 1
        return tensor[tuple(idx)].item()

    def variance_component(self, variables):
        return self._get_index(variables, self.st)

    def superset_index(self, variables):
        return self._get_index(variables, self.sst)

    def closed_index(self, variables):
        return self._get_index(variables, self.cst)

    def total_index(self, variables):
        return self._get_index(variables, self.tst)

    # def directional_covariance(self, variables):
    #     return self._get_index(variables, self.dircov)


if __name__ == '__main__':  # For example and testing purposes
    torch.manual_seed(0)
    I = 32
    N = 4
    R = 5
    t = tn.rand([I]*N, ranks_tt=R)
    ind = AllIndices(t)

    s = tn.symbols(N)

    print('Variance component example:')
    print(ind.variance_component([0, 1]))
    print(tn.sobol(t, mask=tn.only(s[0]&s[1])).item())
    print()

    print('Superset index example:')
    print(ind.superset_index([0, 1]))
    print(tn.sobol(t, mask=s[0]&s[1]).item())
    print()

    print('Closed index example:')
    print(ind.closed_index([0, 1]))
    print(tn.sobol(t, mask=tn.only(s[0] | s[1])).item())
    print()

    print('Variance component example:')
    print(ind.total_index([0, 1]))
    print(tn.sobol(t, mask=s[0]|s[1]).item())
    print()