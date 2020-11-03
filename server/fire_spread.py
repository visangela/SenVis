import functools
import itertools
import pprint
import random
import time
import numpy as np
import scipy as sp
import scipy.stats
from tabulate import tabulate
try:
    import matplotlib
    import matplotlib.pyplot as plt
except ImportError:
    matplotlib = None
    plt = None

import tt
import ttrecipes as tr



def get_model():

    def var_metrics(fun=None, axes=None, t=None, default_bins=100, effective_threshold=0.95,
                    dist_fraction=0.00005, fun_mode="array",
                    eps=1e-5, verbose=False, cross_kwargs=None, random_seed=None):

        if fun is None:
            assert t is not None
            axes = [dict(name='x_{}'.format(n), domain=np.arange(t.n[n])) for n in range(t.d)]
        if t is None:
            assert fun is not None
            assert axes is not None
        N = len(axes)
        names, ticks_list, marginals = tr.models.parse_axes(
            axes, default_bins=default_bins, dist_fraction=dist_fraction)

        axes = list(zip(names, ticks_list, marginals))

        if cross_kwargs is None:
            cross_kwargs = dict()

        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)

        if verbose:
            print("\n-> Building surrogate model")
        pdf = tt.vector.from_list([marg[np.newaxis, :, np.newaxis] for marg in marginals])


        def fun_premultiplied(Xs):
            return fun(Xs) * tr.core.sparse_reco(pdf, tr.core.coordinates_to_indices(Xs, ticks_list=ticks_list))


        if t is None:
            model_time = time.time()
            tt_pdf, n_samples = tr.core.cross(ticks_list, fun_premultiplied, mode=fun_mode,
                                              return_n_samples=True, eps=eps, verbose=verbose,
                                              **cross_kwargs)
            model_time = time.time() - model_time
        else:
            tt_pdf = t * pdf
            n_samples = None
            model_time = None

        return tt_pdf, marginals


    f, axes = tr.models.get_fire_spread(wind_factor=5.0)  # You can tune wind_factor if you want different results

    print("+ Computing tensor approximations of variance-based sensitivity metrics...")
    tt_pdf, marginals = var_metrics(f, axes, default_bins=64, verbose=1, eps=1e-4,
        random_seed=1, cross_kwargs=dict(kickrank=4),)


    # Create a tntorch tensor with the resulting model
    import tntorch as tn
    import torch
    t = tn.Tensor([torch.Tensor(c) for c in tt.vector.to_list(tt_pdf)])
    N = t.dim()
    for n in range(N):
        marginals[n] = torch.Tensor(marginals[n])
        t.cores[n] /= marginals[n][None, :, None]

    return N, t, axes 

    # # Test
    # s = tn.symbols(N)
    # print('Testing -- this value should be around 0.105:', tn.sobol(t, tn.only(s[0]), marginals=marginals))

    # # Save the tensor and the marginals
    # import pickle
    # with open('fire_spread.pkl', 'wb') as f:
    #     pickle.dump([t, marginals], f)