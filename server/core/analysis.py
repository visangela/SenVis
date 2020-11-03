"""
Various processing and optimization tasks in the TT format
"""

# -----------------------------------------------------------------------------
# Authors:      Rafael Ballester-Ripoll <rballester@ifi.uzh.ch>
#
# Copyright:    ttrecipes project (c) 2017-2018
#               VMMLab - University of Zurich
#
# ttrecipes is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ttrecipes is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with ttrecipes.  If not, see <http://www.gnu.org/licenses/>.
# -----------------------------------------------------------------------------

from __future__ import (absolute_import, division,
                        print_function, unicode_literals, )
from future.builtins import range

import numpy as np
import tt
from tt.optimize import tt_min
import copy
import scipy

import ttrecipes as tr


def search_subspace(t, Xs, Ys, tsq=None, tmin=None, tmax=None, hinv=True, vinv=True, dims=None, eps=1e-3):
    """
    Find a region that bests match a given template (both have to be axis-aligned).

    :param Xs: a list of M ndarrays (each of dimension M) encoding the positions to be searched. Note: non-rectangular regions will be extended to their axis-aligned bounding box
    :param Ys: an ndarray of dimension M containing the values to be searched. Must have the same size as the elements of Xs
    :param hinv: whether to search with invariance to horizontal translation (default: True). If True, the values in Xs must lie between 0 and 1
    :param vinv: whether to search with invariance to vertical translation (default: True). If True, the values in Ys must lie between 0 and 1
    :param dims: the dimensions along which the subspace should be searched. Must be a list with M elements. If None (default), the best tuple of M dimensions will be chosen
    :return: match: the center of the best-matching window; dims: the dimensions along which the best subspace was found; borders: a list of M pairs
     (start, end) with the coordinates for the region

    TODO: support non-invariances
    TODO: support search in 2D and more
    TODO: use masks

    """

    N = t.d
    M = Ys.ndim
    if M != 1:
        raise NotImplementedError("Only 1D search is supported for now")
    if hinv == False or vinv == False:
        raise NotImplementedError
    assert len(Xs) == M
    assert np.all([X.ndim == M for X in Xs])
    if hinv:
        assert np.all([np.all(X >= 0) for X in Xs])
        assert np.all([np.all(X <= 1) for X in Xs])
    if vinv:
        assert np.all(Ys >= 0)
        assert np.all(Ys <= 1)
    if dims is not None:
        assert len(dims) == M

    if dims == None:
        dims = np.arange(N)
    inds = np.argsort(Xs[0]) # Sort the values, in case they are reversed
    Xs[0] = Xs[0][inds]
    Ys = Ys[inds]
    record_value = float('inf')

    for dim in dims:
        Xs_adj = (Xs[0]-np.min(Xs[0])-1e-9)*t.n[dim]  # Xs adjusted to this dimension's grid ticks
        Ys_adj = scipy.interpolate.interp1d(Xs_adj, Ys)(np.arange(np.floor(Xs_adj[-1])+1))  # Adjusted Ys
        Ys_adj = Ys_adj*(tmax - tmin) + tmin  # Ys are now mapped to the tensor output's range
        Ys_adj -= np.mean(Ys_adj)  # Vertical invariance

        # Compute the loss tensor: for each position, the squared norm (dot product of itself) of a windowed fiber
        # consisting of the difference between the original fiber (x minus its mean t, for vertical invariance) and
        # the vertically-centered template fiber y (with zero mean). We use the expansion:
        # (x - t - y)*(x - t - y) = x*x - 2*x*t - 2*x*y + 2*t*y + t*t + y*y = x*x - t*t - 2*x*y + y*y
        # where we have used that mean(y) = 0

        if tsq is None:  # This part may be reused by subsequent queries, so we memoize it
            tsq = tt.multifuncrs2([t], lambda x: x**2, eps=eps, verb=False)

        box_filter = np.ones([1, Ys_adj.size, 1]) / Ys_adj.size  # To average TT cores along their 2nd dimension

        cores = tt.vector.to_list(tsq)
        cores[dim] = scipy.signal.convolve(cores[dim], box_filter, mode='valid')
        tsquarebox = tt.vector.from_list(cores)

        cores = tt.vector.to_list(t)
        cores[dim] = scipy.signal.convolve(cores[dim], box_filter, mode='valid')
        tbox = tt.vector.from_list(cores)
        tboxsquare = tt.multifuncrs2([tbox], lambda x: x**2, eps=eps, verb=False)

        cores = tt.vector.to_list(t)
        cores[dim] = scipy.signal.convolve(cores[dim], np.reshape(Ys_adj[::-1], [1, Ys_adj.size, 1]), mode='valid')
        tconv = tt.vector.from_list(cores)

        tfinal = Ys_adj.size*tsquarebox - Ys_adj.size*tboxsquare - 2*tconv + np.dot(Ys_adj,Ys_adj)*tt.ones(tsquarebox.n)

        # Find an approximate minimum
        value, match = tt_min.min_tens(tfinal, rmax=5, nswp=5, verb=False)

        if value < record_value:
            record_value = value
            record_match = [int(m) for m in match]
            record_match[dim] += len(Ys_adj)/2  # Sum half the window size to get the final focus point
            record_dim = [dim]
            record_borders = [[record_match[dim] - len(Ys_adj)/2, record_match[dim]+len(Ys_adj)/2-1]]

    return record_match, record_dim, record_borders


def best_subspace(t, ndim=1, target='max', mode='cross', eps=1e-6, verbose=False, **kwargs):
    """
    Find an axis-aligned subspace of a certain dimensionality that has the highest/lowest variance. Example applications:
    - In visualization, to find interesting subspaces
    - In factor fixing (sensitivity analysis), to find the set of parameters (and their values) that will minimize the uncertainty of a model

    TODO: only uniform independently distributed inputs are supported now

    :param t: a TT
    :param ndim: dimensionality of the subspace sought (default is 2)
    :param target: if 'max' (default), the highest variance will be sought; if 'min', the lowest one
    :param mode: 'cross' (default) or 'kronecker'
    :param verbose:
    :param kwargs: arguments for the cross-approximation
    :return: (a) a list of indices, with slice(None) in the free subspace's dimensions, and (b) the variance of that subspace

    """

    assert mode in ('cross', 'kronecker')
    assert target in ('max', 'min')

    # Build up a tensor that contains variances of all possible subspaces of any dimensionality, using the formula E(X^2) - E(X)^2
    if mode == 'cross':
        cores = tt.vector.to_list(tt.multifuncrs2([t], lambda x: x ** 2, eps=eps, verb=verbose, **kwargs))
    else:
        cores = tt.vector.to_list((t*t).round(0))
    cores = [np.concatenate([np.mean(core, axis=1, keepdims=True), core], axis=1) for core in cores]
    part1 = tt.vector.from_list(cores)  # E(X^2)

    cores = tt.vector.to_list(t)
    cores = [np.concatenate([np.mean(core, axis=1, keepdims=True), core], axis=1) for core in cores]
    part2 = tt.vector.from_list(cores)
    if mode == 'cross':
        part2 = tt.multifuncrs2([part2], lambda x: x ** 2, eps=eps, verb=verbose, **kwargs)
    else:
        part2 = (part2*part2).round(0)  # E(X)^2

    variances = (part1 - part2).round(0)

    # Filter out encoded subspaces that do not have the target dimensionality
    mask = tt.vector.to_list(tr.core.hamming_eq_mask(t.d, t.d-ndim))
    mask = [np.concatenate([core[:, 0:1, :], np.repeat(core[:, 1:, :], sh, axis=1)], axis=1) for core, sh in zip(mask, t.n)]
    mask = tt.vector.from_list(mask)

    # Find and return the best candidate
    if target == 'max':
        prod = tt.vector.round(variances*mask, eps=eps)
        val, point = tt_min.min_tens(-prod, verb=verbose)
        val = -val
    else:
        shift = -1e3*tt_min.min_tens(-variances, verb=False, rmax=1)[0]
        variances_shifted = variances - tt.vector.from_list([np.ones([1, sh+1, 1]) for sh in t.n])*shift
        val, point = tt_min.min_tens(variances_shifted*mask, verb=verbose)
        val += shift
    nones = np.where(np.array(point) == 0)[0]
    point = [p - 1 for p in point]
    for i in nones:
        point[i] = slice(None)
    return point, val


def moments(t, modes, order, centered=False, normalized=False, keepdims=False, eps=1e-3, verbose=False, **kwargs):
    """
    Given an N-dimensional TT and a list of M modes, returns a TT of dimension N - M that contains the k-th order moments along these modes

    :param t: a TT
    :param modes: a list of M integers
    :param order: an integer
    :param centered: if True the moments will be computed about their mean. Default is False
    :param normalized: if True the moments will be divided by sigma^order. Default is False
    :param eps: accuracy for cross-approximation (default is 1e-3)
    :return: a TT of dimension N - M

    """

    N = t.d
    assert np.all(0 <= np.array(modes))
    assert np.all(np.array(modes) < N)
    if not hasattr(modes, '__len__'):
        modes = [modes]
    assert len(modes) == len(set(modes))  # Modes may not be repeated
    assert 1 <= len(modes) <= N

    if centered or normalized:
        central_cores = []
        cores = tt.vector.to_list(t)
        for n in range(N):
            if n in modes:
                central_cores.append(np.repeat(np.mean(cores[n], axis=1, keepdims=True), cores[n].shape[1], axis=1))
            else:
                central_cores.append(cores[n])
        central = t - tt.vector.from_list(central_cores)
    if centered:
        if order == 1:
            moments = copy.deepcopy(central)
        else:
            moments = tt.multifuncrs2([central], lambda x: x**order, eps=eps, verb=verbose, **kwargs)
    else:
        if order == 1:
            moments = copy.deepcopy(t)
        else:
            moments = tt.multifuncrs2([t], lambda x: x**order, eps=eps, verb=verbose, **kwargs)
    cores = tt.vector.to_list(moments)
    for mode in modes:
        cores[mode] = np.mean(cores[mode], axis=1, keepdims=True)
    moments = tt.vector.from_list(cores)
    if normalized:
        central = tt.multifuncrs2([central], lambda x: x**2, eps=eps, verb=verbose, **kwargs)
        cores = tt.vector.to_list(central)
        for mode in modes:
            cores[mode] = np.mean(cores[mode], axis=1, keepdims=True)
        variances = tt.vector.from_list(cores)
        moments = tt.multifuncrs2([moments, variances], lambda x: x[:, 0] / (x[:, 1] ** (order/2.)), eps=eps, verb=verbose, **kwargs)
    if not keepdims:
        moments = tr.core.squeeze(moments, modes=modes)
    return moments


def means(t, modes, **kwargs):
    """
    Convenience function for the first moment (see :func: `moments`)
    """

    return moments(t, modes, order=1, centered=False, normalized=False, **kwargs)


def variances(t, modes, **kwargs):
    """
    Convenience function for the second centered unnormalized moment (see :func: `moments`)
    """

    return moments(t, modes, order=2, centered=True, normalized=False, **kwargs)


# 0, 2
# 0 1 2 3 4
# 2 1 0 3 4

# 0 1
# 1 0

# 0 1 2 3 4 5
# 1 0 2 3 4 5
# 2 0 1 3 4 5
# 3 0 1 2 4 5
# 4 0 1 2 3 5
# 5 0 1 2 3 4

# 0 1 2 3 4 5
# 1 0 2 3 4 5
# 2 1 0 3 4 5
# 3 1 2 0 4 5
# 4 1 2 3 0 5
# 5 1 2 3 4 0

# 1 0 2 3 4 5
# 0 1 2 3 4 5
# 0 2 1 3 4 5
# 0 3 2 1 4 5
# 0 4 2 3 1 5
# 0 5 1 2 3 4

# 0 1 2 :
# 0 : 2 3
# t1 x y z : s
# s2 x y z t :
# x y z t1 s
# x y z t s2


# 0 - 1
# 1 0 -

# 0 1 2
# 1 0 2
# 2 0 1

# f(x1, r, s) = f(x2, r, s) forall r, s
# t(x1, r, s) = f(r, x2, s) forall r, s

# 0 - 1 2
# 1 0 - 2
# 2 0 1 -

# x, r, s, t
# f(x1, r, s, t) = f(x2, r, s, t) forall r, s, t
# f(x1, s, t) = f(x2, r, t)
# t(x1, s, t) = t(r, x2, t) forall r, s, t

# f(x1, x1, x2, t) = f(x2, x1, x2, t)

# x 1 2
# 0 y 2

# 0 1 2 3 4
# 2 1 0 3 4
# 0 1 2 3 4

def pca_ensemble(t, modes, degree=3, orthogonal=False, anchor_mean=True, eps=1e-3, verbose=False):
    """
    Given a tensor and a list of modes, consider the space of subtensors obtained
    by fixing these modes. Find a PCA basis for that space and return the coefficients
    for each subtensor

    :param t: a TT
    :param modes: the ensemble modes. Can also be a list of lists; in that case
    the ensembles will share bases
    :param degree: how large a PCA basis to take (default is 3)
    :param orthogonal:
    :param anchor_mean:
    :param eps: relative tolerance while permuting modes. Default is 1e-3
    :param verbose:
    :return: (ensemble, preserved):
        - ensemble: a TT of size M1 x ... x Mk x `degree`, where M1, etc. are the sizes of `t` along `modes`
        - preserved: the fraction (between 0 and 1; higher is better) of norm preserved by the embedding

    """

    N = t.d
    if verbose:
        print('Computing PCA ensemble...')
    if not hasattr(modes, '__len__'):
        modes = [modes]
    modesarray = np.array(modes)
    single = False
    if modesarray.ndim == 1:
        single = True
        modesarray = np.array([modesarray])
    if not all([len(modesarray[m]) == len(modesarray[0]) for m in range(len(modesarray))]):
        raise ValueError("All mode lists must have the same length")
    # modesarray = np.array([[3, 6], [1, 4]])
    # Group target modes next to each other
    first = int(np.round(np.mean(modesarray.flatten())-modesarray.shape[1]/2.))
    # print(np.rint(0.50000))

    import matplotlib.pyplot as plt
    plt.figure()
    # plt.plot(t.full()[20, :] - np.mean(t.full()[20, :]))
    # plt.plot(t.full()[:, 4] - np.mean(t.full()[:, 4]))
    # plt.imshow(t.full(), origin='lower')
    # print(t.full()[17, :])
    # print(t.full()[:, 4])
    # print(t.full()[17, :] - np.mean(t.full()[17, :]))
    # print(t.full()[:, 4] - np.mean(t.full()[:, 4]))
    # plt.show()
    # assert 0

    print(modesarray, first)
    stack = []
    for modes in modesarray:
        if len(modes) != len(np.unique(modes)):
            raise ValueError('Modes may not be repeated')
        assert 0 <= np.min(modes)
        assert np.max(modes) < N

        if verbose:
            print('\tTransposing tensor... 0', end='')
        # part1 = np.arange(first)
        all1 = list(range(first))
        all2 = list(range(first, N))
        part1 = np.setdiff1d(all1, modes)
        part2 = np.setdiff1d(all2, modes)
        print('We now transpose to', list(part1)+list(modes)+list(part2))
        ttransp = tr.core.transpose(t, list(part1)+list(modes)+list(part2), eps=eps)
        for m in modes:
            if m in all1:
                all1[all1.index(m)] = -1
            if m in all2:
                all2[all2.index(m)] = -1
        all1.append(-2)  # Extra dimension to stack the tensors
        print(all1, all2)
        converted = np.array(all1+list(modes)+all2)
        assert first == np.where(converted == -2)[0][0]
        # shape = t.n[modes]
        idx = np.where(converted < 0)[0]
        shape = np.ones_like(idx)
        shape[np.where(converted[idx] == -1)[0]] = t.n[modes]
        # shape[np.where(converted[idx] == -1)[0]] = 1
        print('idx = {}, shape = {}'.format(idx, shape))
        # idx1 = []
        # idx2 = np.setdiff1d(np.arange(first, N), part2)
        # print('idx1:', idx1)
        # print('idx2:', idx2)
        ttransp = tr.core.insert_dummies(ttransp, idx, shape=shape)
        print('shape:', shape)
        # print(ttransp)
        # print(ttransp[[0, 0, 0, 0]+[0]*6])
        # print(ttransp[[0, 0, 0, 1]+[0]*6])
        # print(ttransp[[0, 0, 0, 2]+[0]*6])
        # print(ttransp)
        #
        # print((1./np.prod(t.n[modes])))
        # assert 0
        # ttransp *= (np.prod(t.n[modes]))
        # cores = tt.vector.to_list(ttransp)
        # cores[2] /= 32
        # ttransp = tt.vector.from_list(cores)
        stack.append(ttransp)
    stack = tr.core.concatenate(stack, axis=first, eps=eps)

    # first = first-1
    last = first+len(modes)+1
    # print(first, last)
    # print(t, first, last)
    # assert 0
    # print(stack)
    # print(stack[0, 15, 0, 25])
    # print(t[15, 25])
    # print(stack[0, 15, 0, 15])
    # print(t[15, 15])
    # print(stack[0, 13, 0, 25])
    # print(t[13, 25])
    # print(stack[1, 25, 12, 25])
    # print(t[12, 25])
    # blah = stack.full()
    # blah = blah - np.mean(blah, axis=(2, 3), keepdims=True)
    # print(np.mean(blah, axis=(2, 3), keepdims=True).shape)
    # print(blah.shape, np.linalg.norm(blah))
    # print(first, last)
    # print(modesarray)
    t = stack
    # assert 0
    # print('*******')
    # print(t)
    # print(tt.vector.round(t, eps=eps))
    # # print(tt.vector.norm(t))
    # assert 0

    if anchor_mean:
        # We now project each vector on the subspace spanned by the constant vector
        # This is achieved by subtracting each vector's within-mean
        cores = copy.deepcopy(tt.vector.to_list(t))
        for n in range(t.d):
            if n < first or n >= last:
                cores[n] = np.repeat(np.mean(cores[n], axis=1, keepdims=True), cores[n].shape[1], axis=1)
        withinmeanrep = tt.vector.from_list(cores)
        print("Let's do means")
        print('t=', t)
        print('modes =', list(range(first))+list(range(last, t.d)))
        withinmean = tr.core.means(t, modes=list(range(first))+list(range(last, t.d)))
        t = tt.vector.round(t-withinmeanrep, eps=eps)
        degree -= 1

    # print(tt.vector.norm(t))
    # assert 0
    # print(withinmean)
    # assert 0
    # withinmeanrep2 = withinmeanrep - tr.core.constant_tt(shape=withinmean.n, fill=tr.core.mean(withinmeanrep))
    withinmean2 = withinmean - tr.core.constant_tt(shape=withinmean.n, fill=tr.core.mean(withinmean))
    # sumsq = np.sum(withinmean2)
    # print(withinmean2)
    # sumsq1 = tr.core.variances(withinmean2, modes=np.arange(len(modes))).full() #* np.prod(t.n)
    # sumsq1 = np.asscalar(sumsq1)
    sumsq1 = np.asscalar(np.sum(withinmean2.full()**2))# * np.prod(t.n[np.delete(np.arange(N), modes)])
    # targetsq1 = np.var(withinmean.full())*np.prod(t.n[modes])

    sumsq1 = np.sqrt(sumsq1)
    # targetsq1 = np.sqrt(targetsq1)
    print('sumsq1 = {}'.format(sumsq1))
    # print('sumsq1 = {}, targetsq1 = {}, sumsq1/targetsq1 = {}'.format(sumsq1, targetsq1, sumsq1/targetsq1))

    # print(np.sqrt(sumsq1/targetsq1))
    # print(tt.vector.norm(withinmean2)**2)
    # sumsq = np.sum(withinmean2.full()**2)
    # print(sumsq)
    # assert 0

    # Subtract the cross-mean (mean of the collection of vectors)
    cores = copy.deepcopy(tt.vector.to_list(t))
    for n in range(first, last):
        cores[n] = np.repeat(np.mean(cores[n], axis=1, keepdims=True), cores[n].shape[1], axis=1)
    crossmean = tt.vector.from_list(cores)
    t = tt.vector.round(t-crossmean, eps=eps)

    # sumsq2 = tt.vector.norm(t) / np.sqrt(np.prod(t.n[np.delete(np.arange(N), modes)]))
    # sumsq2 = tt.vector.norm(t) / np.sqrt(np.prod(t.n[np.delete(np.arange(t.d), [0, 1])]))
    sumsq2 = tt.vector.norm(t) / np.sqrt(np.prod(t.n[np.arange(first)])*np.prod(t.n[np.arange(last, t.d)]))
    # sumsq2 = np.sum(tr.core.variances(t, modes=list(range(final_pos))+list(range(final_pos+len(modes), N))).full())\
    #          * np.prod(t.n[modes])
    # sumsq2 = np.sqrt(sumsq2)
    print('sumsq2 = {}'.format(sumsq2))
    # t = t*(sumsq2 / sumsq1 * targetsq1)
    # print('Now 0:', tt.vector.norm(t))
    # t *= (targetsq1 / sumsq1)
    # print('Now 1:', tt.vector.norm(t))
    # assert 0
    # print(t)


    # Orthogonalize to the left and right of these modes
    cores = tt.vector.to_list(t)
    if verbose:
        print('\n\tOrthogonalization...')
    for i in range(first):
        tr.core.left_orthogonalize(cores, i)
    for i in range(t.d-1, last-1, -1):
        tr.core.right_orthogonalize(cores, i)

    # Cut out the relevant sequence of modes
    cores = cores[first:last]
    # print(first, last, len(cores))
    # assert 0

    # Convert the sequence into a TT (convert ranks to spatial modes)
    cores = [np.eye(cores[0].shape[0])[np.newaxis, :, :]] + cores + [np.eye(cores[-1].shape[2])[:, :, np.newaxis]]
    t = tt.vector.from_list(cores)
    # sumsq2 = np.sum(t.full()**2)/(64**(N-2))
    # print(sumsq2)
    # print(t)
    # assert 0

    # Put the rank modes together at the very right
    if verbose:
        print('\tPutting rank modes together...')
    t = tr.core.shift_mode(t, 0, t.d-2, eps=eps)
    cores = tt.vector.to_list(t)

    # Merge the two rank dimensions into one
    cores[-2] = np.einsum('iaj,jbk->ikab', cores[-2], cores[-1])
    del cores[-1]
    cores[-1] = np.reshape(cores[-1], [-1, cores[-1].shape[2]*cores[-1].shape[3], 1])
    t = tt.vector.from_list(cores)

    # Subtract the cross-mean (mean of the collection of vectors)
    # print('t1:', t)
    # cores = [np.repeat(np.mean(c, axis=1, keepdims=True), c.shape[1], axis=1) for c in cores[:-1]] + [cores[-1]]
    # crossmean = tt.vector.from_list(cores)
    # t = tt.vector.round(t-crossmean, eps=eps)
    # print('t2:', t)
    print('Norma ara:', tt.vector.norm(t))
    norm = tt.vector.norm(t)
    if norm > 0:
        t *= (sumsq2 / norm)
    print('Norma ara:', tt.vector.norm(t))
    # print(t)

    # Compute the truncated PCA of the space spanned by the rank modes
    if verbose:
        print('\tPCA compression...')
    cores = tt.vector.to_list(t)
    tr.core.orthogonalize(cores, t.d-1)

    print('********')
    t = tt.vector.from_list(cores)
    print(t)
    for i in range(32):
        print(i, tt.vector.norm(t[0, i, :] - t[1, 24, :]))
    # assert 0
    # sumsq2 = np.sum(cores[-1]**2)
    # sumsq2 = np.sum(tr.core.variances(tt.vector.from_list(cores), modes=[0, 1]).full())
    # print(tt.vector.from_list(cores).full().shape)
    # sumsq2 = np.sum(np.sum(tt.vector.from_list(cores).full()**2, axis=-1)) / np.prod(tt.vector.from_list(cores).n)
    # print(tr.core.means(tt.vector.from_list(cores), modes=[0, 1]).full())
    # print(sumsq2)
    # assert 0
    cores[-1] = cores[-1][..., 0]
    svd = np.linalg.svd(cores[-1], full_matrices=False)
    cores[-1] = svd[0][:, :degree]
    if not orthogonal:
        cores[-1] = cores[-1].dot(np.diag(svd[1][:degree]))
    cores[-1] = cores[-1][:, :, np.newaxis]
    if cores[-1].shape[1] < degree:  # Degenerate case: add a slice of zeros
        cores[-1] = np.concatenate([cores[-1], np.zeros([cores[-1].shape[0], degree-cores[-1].shape[1],
                                                         cores[-1].shape[2]])], axis=1)
    t = tt.vector.from_list(cores)

    # print('********')
    # t = tt.vector.from_list(cores)
    # print(t)
    # for i in range(32):
    #     print(i, tt.vector.norm(t[0, i, :] - t[1, 24, :]))
    # assert 0
    # print('Norma ara:', tt.vector.norm(t))
    # t *= (1./tt.vector.norm(t))
    # assert 0

    # print('Now:', np.sqrt(np.var(t.full())))
    if anchor_mean:
        withinmean = tt.vector.from_list(tt.vector.to_list(withinmean) + [np.ones([1, 1, 1])])
        # print('**********')
        # print(withinmean, t)
        # print(tt.vector.norm(withinmean))
        # print(tt.vector.norm(t))
        # assert 0
        t = tr.core.concatenate([withinmean, t], axis=withinmean.d-1, eps=eps)

    if verbose:
        print()
    print(t.full())
    # assert 0
    # print(tt.vector.norm(t))
    print()
    # print(np.sum(t.full()**2))
    # print(t)
    tfull = t.full()
    # print(print(np.mean(np.mean(t.full(), axis=0), axis=0)))
    print('Obtained:')
    print(np.linalg.norm(tfull[..., 0]-np.mean(tfull[..., 0])))
    print(np.linalg.norm(withinmean2.full()))
    obtained = np.linalg.norm(tfull[..., 1:]-np.mean(tfull[..., 1:]))
    print(obtained)
    print()
    preserved = (sumsq1**2 + obtained**2) / (sumsq1**2 + sumsq2**2)
    print('This embedding preserves {:g}% of the original norm'.format(preserved*100))
    # print(np.sqrt(np.var(t[..., 0])))
    # print(np.sqrt(np.var(t[..., 1:])))
    # print(t[0, :, 0].full().flatten()[:10])
    # print(t[0, :, 1].full().flatten()[:10])
    # print(t[0, :, 2].full().flatten()[:10])
    # assert 0
    tlist = []
    for n in range(t.n[0]):
        tlist.append(t[[n] + [slice(None)]*(t.d-1)])
    if single:
        tlist = tlist[0]
    print()
    print('***************** tlist:', tlist)
    # assert 0
    return tlist, preserved









def pca_ensemble2(t, modes, degree=3, orthogonal=False, anchor_mean=True, eps=1e-3, verbose=False):
    """
    Given a tensor and a list of modes, consider the space of subtensors obtained
    by fixing these modes. Find a PCA basis for that space and return the coefficients
    for each subtensor

    :param t: a TT
    :param modes: the ensemble modes
    :param degree: how large a PCA basis to take (default is 3)
    :param orthogonal:
    :param anchor_mean:
    :param eps: relative tolerance while permuting modes. Default is 1e-3
    :param verbose:
    :return: (ensemble, preserved):
        - ensemble: a TT of size M1 x ... x Mk x `degree`, where M1, etc. are the sizes of `t` along `modes`
        - preserved: the fraction (between 0 and 1; higher is better) of norm preserved by the embedding
        - residual: the tensor containing the trailing R-degree principal components

    """

    # modes = [3, 6]
    # N = t.d
    # part1 = np.arange(modes[0])
    # part2 = np.setdiff1d(np.arange(modes[0], N), modes)
    # # print('**************', modes, ' **** ', list(part1)+list(modes)+list(part2))
    # order = list(part1)+list(modes)+list(part2)
    # idx = np.empty(len(order))
    # idx[order] = np.arange(len(order))
    # d = t.d
    # print(order)
    # assert 0
    # tr.core.transpose(t, order)
    # assert 0

    N = t.d
    shape = t.n
    if not hasattr(modes, '__len__'):
        modes = [modes]
    modesarray = np.array(modes)
    if modesarray.ndim == 1:
        modesarray = np.array([modesarray])
    if not all([len(modesarray[m]) == len(modesarray[0]) for m in range(len(modesarray))]):
        raise ValueError("All mode lists must have the same length")
    for modes in modesarray:
        if len(modes) != len(np.unique(modes)):
            raise ValueError('Modes may not be repeated')
        assert 0 <= np.min(modes)
        assert np.max(modes) < N

        if verbose:
            print('Computing PCA ensemble...')

        # Group target modes next to each other
        if verbose:
            print('\tTransposing tensor... 0', end='')
        # idx = list(range(N))
        # def list_shift(idx, mode, shift):
        #     assert mode + shift >= 0
        #     assert mode + shift < len(idx)
        #     idx.insert(mode+shift, int(idx[mode]))
        #     del idx[mode]
        # pivot = modes[0]  # We will organize modes from left-to-right after this one
        # for i in range(1, len(modes)):
        #     source = idx.index(modes[i])
        #     target = idx.index(pivot) + i
        #     if source < target:
        #         target -= 1
        #     t = tr.core.shift_mode(t, source, target-source, eps=eps)
        #     list_shift(idx, source, target-source)
        #     if verbose:
        #         print(' {}'.format(i), end='')
        # final_pos = idx.index(pivot)

        # part1 = np.arange(modes[0])
        part1 = np.setdiff1d(np.arange(modes[0]), modes)
        part2 = np.setdiff1d(np.arange(modes[0], N), modes)
        print('**************', modes, ' **** ', list(part1)+list(modes)+list(part2))
        order = list(part1)+list(modes)+list(part2)
        # t = tt.core.tools.permute(t, list(part1)+list(modes)+list(part2), eps=eps)
        t = tr.core.transpose(t, order, eps=eps)
        print(t)
        # assert 0
        # final_pos = modes[0]
        final_pos = order.index(modes[0])
        # final_pos = min(modes)

        if anchor_mean:
            # We now project each vector on the subspace spanned by the constant vector
            # This is achieved by subtracting each vector's within-mean
            cores = copy.deepcopy(tt.vector.to_list(t))
            for n in range(N):
                if n < final_pos or n >= final_pos+len(modes):
                    cores[n] = np.repeat(np.mean(cores[n], axis=1, keepdims=True), cores[n].shape[1], axis=1)
            withinmeanrep = tt.vector.from_list(cores)
            withinmean = tr.core.means(t, modes=list(range(final_pos))+list(range(final_pos+len(modes), N)))
            t = tt.vector.round(t-withinmeanrep, eps=eps)
            degree -= 1


        # withinmeanrep2 = withinmeanrep - tr.core.constant_tt(shape=withinmean.n, fill=tr.core.mean(withinmeanrep))
        withinmean2 = withinmean - tr.core.constant_tt(shape=withinmean.n, fill=tr.core.mean(withinmean))
        # sumsq = np.sum(withinmean2)
        # print(withinmean2)
        # sumsq1 = tr.core.variances(withinmean2, modes=np.arange(len(modes))).full() #* np.prod(t.n)
        # sumsq1 = np.asscalar(sumsq1)
        sumsq1 = np.asscalar(np.sum(withinmean2.full()**2))# * np.prod(t.n[np.delete(np.arange(N), modes)])
        # targetsq1 = np.var(withinmean.full())*np.prod(t.n[modes])

        sumsq1 = np.sqrt(sumsq1)
        # targetsq1 = np.sqrt(targetsq1)
        print('sumsq1 = {}'.format(sumsq1))
        # print('sumsq1 = {}, targetsq1 = {}, sumsq1/targetsq1 = {}'.format(sumsq1, targetsq1, sumsq1/targetsq1))

        # print(np.sqrt(sumsq1/targetsq1))
        # print(tt.vector.norm(withinmean2)**2)
        # sumsq = np.sum(withinmean2.full()**2)
        # print(sumsq)
        # print(modes)
        # assert 0

        # Subtract the cross-mean (mean of the collection of vectors)
        cores = copy.deepcopy(tt.vector.to_list(t))
        print(t, final_pos, final_pos+len(modes))
        for n in range(final_pos, final_pos+len(modes)):
            cores[n] = np.repeat(np.mean(cores[n], axis=1, keepdims=True), cores[n].shape[1], axis=1)
        crossmean = tt.vector.from_list(cores)
        t = tt.vector.round(t-crossmean, eps=eps)


        sumsq2 = tt.vector.norm(t) / np.sqrt(np.prod(shape[np.delete(np.arange(N), modes)]))
        # sumsq2 = np.sum(tr.core.variances(t, modes=list(range(final_pos))+list(range(final_pos+len(modes), N))).full())\
        #          * np.prod(t.n[modes])
        # sumsq2 = np.sqrt(sumsq2)
        print('sumsq2 = {}'.format(sumsq2))
        # t = t*(sumsq2 / sumsq1 * targetsq1)
        # print('Now 0:', tt.vector.norm(t))
        # t *= (targetsq1 / sumsq1)
        # print('Now 1:', tt.vector.norm(t))
        # assert 0
        # print(t)

        # Orthogonalize to the left and right of these modes
        cores = tt.vector.to_list(t)
        if verbose:
            print('\n\tOrthogonalization...')
        for i in range(final_pos):
            tr.core.left_orthogonalize(cores, i)
        for i in range(N-1, final_pos+len(modes)-1, -1):
            tr.core.right_orthogonalize(cores, i)

        # Cut out the relevant sequence of modes
        cores = cores[final_pos:final_pos+len(modes)]

        # Convert the sequence into a TT (convert ranks to spatial modes)
        cores = [np.eye(cores[0].shape[0])[np.newaxis, :, :]] + cores + [np.eye(cores[-1].shape[2])[:, :, np.newaxis]]
        t = tt.vector.from_list(cores)
        # sumsq2 = np.sum(t.full()**2)/(64**(N-2))
        # print(sumsq2)
        # assert 0

        # Put the rank modes together at the very right
        if verbose:
            print('\tPutting rank modes together...')
        t = tr.core.shift_mode(t, 0, t.d-2, eps=eps)
        cores = tt.vector.to_list(t)

        # Merge the two rank dimensions into one
        cores[-2] = np.einsum('iaj,jbk->ikab', cores[-2], cores[-1])
        del cores[-1]
        cores[-1] = np.reshape(cores[-1], [-1, cores[-1].shape[2]*cores[-1].shape[3], 1])
        t = tt.vector.from_list(cores)

        # Subtract the cross-mean (mean of the collection of vectors)
        # print('t1:', t)
        # cores = [np.repeat(np.mean(c, axis=1, keepdims=True), c.shape[1], axis=1) for c in cores[:-1]] + [cores[-1]]
        # crossmean = tt.vector.from_list(cores)
        # t = tt.vector.round(t-crossmean, eps=eps)
        # print('t2:', t)
        print('Norma ara:', tt.vector.norm(t))
        norm = tt.vector.norm(t)
        if norm > 0:
            t *= (sumsq2 / norm)
        print('Norma ara:', tt.vector.norm(t))
        print(t)

        # Compute the truncated PCA of the space spanned by the rank modes
        if verbose:
            print('\tPCA compression...')
        cores = tt.vector.to_list(t)
        tr.core.orthogonalize(cores, t.d-1)
        # sumsq2 = np.sum(cores[-1]**2)
        # sumsq2 = np.sum(tr.core.variances(tt.vector.from_list(cores), modes=[0, 1]).full())
        # print(tt.vector.from_list(cores).full().shape)
        # sumsq2 = np.sum(np.sum(tt.vector.from_list(cores).full()**2, axis=-1)) / np.prod(tt.vector.from_list(cores).n)
        # print(tr.core.means(tt.vector.from_list(cores), modes=[0, 1]).full())
        # print(sumsq2)
        # assert 0
        cores[-1] = cores[-1][..., 0]
        svd = np.linalg.svd(cores[-1], full_matrices=False)

        # Compute error
        cores2 = copy.deepcopy(cores)
        cores2[-1] = svd[0][:, degree:].dot(np.diag(svd[1])[degree:])[:, :, np.newaxis]
        error = tt.vector.from_list(cores2)

        cores[-1] = svd[0][:, :degree]
        if not orthogonal:
            cores[-1] = cores[-1].dot(np.diag(svd[1][:degree]))
        cores[-1] = cores[-1][:, :, np.newaxis]
        if cores[-1].shape[1] < degree:  # Degenerate case: add a slice of zeros
            cores[-1] = np.concatenate([cores[-1], np.zeros([cores[-1].shape[0], degree-cores[-1].shape[1],
                                                             cores[-1].shape[2]])], axis=1)
        t = tt.vector.from_list(cores)

        # print('Norma ara:', tt.vector.norm(t))
        # t *= (1./tt.vector.norm(t))
        # assert 0

        # print('Now:', np.sqrt(np.var(t.full())))
        if anchor_mean:
            withinmean = tt.vector.from_list(tt.vector.to_list(withinmean) + [np.ones([1, 1, 1])])
            t = tr.core.concatenate([withinmean, t], axis=len(modes), eps=eps)

        if verbose:
            print()

    # print(tt.vector.norm(t))
    print()
    # print(np.sum(t.full()**2))
    # print(t)
    tfull = t.full()
    # print(print(np.mean(np.mean(t.full(), axis=0), axis=0)))
    print('Obtained:')
    print(np.linalg.norm(tfull[..., 0]-np.mean(tfull[..., 0])))
    print(np.linalg.norm(withinmean2.full()))
    obtained = np.linalg.norm(tfull[..., 1:]-np.mean(tfull[..., 1:]))
    print(obtained)
    print()
    preserved = (sumsq1**2 + obtained**2) / (sumsq1**2 + sumsq2**2)
    print('This embedding preserves {:g}% of the original norm'.format(preserved*100))
    # print(np.sqrt(np.var(t[..., 0])))
    # print(np.sqrt(np.var(t[..., 1:])))
    # assert 0
    return t, preserved, error


# def pca_ensemble(t, modes, degree=3, orthogonal=False, anchor_mean=True, eps=1e-3, verbose=False):
#     """
#     Given a tensor and a list of modes, consider the space of subtensors obtained
#     by fixing these modes. Find a PCA basis for that space and return the coefficients
#     for each subtensor
#
#     :param t: a TT
#     :param modes: the ensemble modes
#     :param degree: how large a PCA basis to take (default is 3)
#     :param orthogonal:
#     :param anchor_mean:
#     :param eps: relative tolerance while permuting modes. Default is 1e-3
#     :param verbose:
#     :return: M1 x ... x Mk x degree, where M1, etc. are the sizes of `t` along `modes`
#
#     """
#
#     N = t.d
#     if not hasattr(modes, '__len__'):
#         modes = [modes]
#     if len(modes) != len(np.unique(modes)):
#         raise ValueError('Modes may not be repeated')
#     assert 0 <= np.min(modes)
#     assert np.max(modes) < N
#
#     if verbose:
#         print('Computing PCA ensemble...')
#
#     # Group target modes next to each other
#     if verbose:
#         print('\tTransposing tensor... 0', end='')
#     idx = list(range(N))
#     def list_shift(idx, mode, shift):
#         assert mode + shift >= 0
#         assert mode + shift < len(idx)
#         tmp = idx[mode]
#         del idx[mode]
#         if shift < 0:
#             idx.insert(mode+shift, tmp)
#         else:
#             idx.insert(mode+shift, tmp)
#     pivot = modes[0]  # We will organize modes from left-to-right after this one
#     for i in range(1, len(modes)):
#         source = idx.index(modes[i])
#         target = idx.index(pivot) + i
#         if source < target:
#             target -= 1
#         t = tr.core.shift_mode(t, source, target-source, eps=eps)
#         list_shift(idx, source, target-source)
#         if verbose:
#             print(' {}'.format(i), end='')
#     final_pos = idx.index(pivot)
#
#     if anchor_mean:
#         # We now project each vector on the subspace spanned by the constant vector
#         # This is achieved by subtracting each vector's within-mean
#         cores = copy.deepcopy(tt.vector.to_list(t))
#         for n in range(N):
#             if n < final_pos or n >= final_pos+len(modes):
#                 cores[n] = np.repeat(np.mean(cores[n], axis=1, keepdims=True), cores[n].shape[1], axis=1)
#         tmeanrep = tt.vector.from_list(cores)
#         withinmean = tr.core.means(t, modes=list(range(final_pos))+list(range(final_pos+len(modes), N)))
#         t = tt.vector.round(t-tmeanrep, eps=eps)
#         degree -= 1
#
#     # Orthogonalize to the left and right of these modes
#     cores = tt.vector.to_list(t)
#     if verbose:
#         print('\n\tOrthogonalization...')
#     for i in range(final_pos):
#         tr.core.left_orthogonalize(cores, i)
#     for i in range(N-1, final_pos+len(modes)-1, -1):
#         tr.core.right_orthogonalize(cores, i)
#
#     # Cut out the relevant sequence of modes
#     cores = cores[final_pos:final_pos+len(modes)]
#
#     # Convert the sequence into a TT (convert ranks to spatial modes)
#     cores = [np.eye(cores[0].shape[0])[np.newaxis, :, :]] + cores + [np.eye(cores[-1].shape[2])[:, :, np.newaxis]]
#     t = tt.vector.from_list(cores)
#
#     # Put the rank modes together at the very right
#     if verbose:
#         print('\tPutting rank modes together...')
#     t = tr.core.shift_mode(t, 0, t.d-2, eps=eps)
#     cores = tt.vector.to_list(t)
#
#     # Merge the two rank dimensions into one
#     cores[-2] = np.einsum('iaj,jbk->ikab', cores[-2], cores[-1])
#     del cores[-1]
#     cores[-1] = np.reshape(cores[-1], [-1, cores[-1].shape[2]*cores[-1].shape[3], 1])
#
#     # Subtract the cross-mean (mean of the collection of vectors)
#     t = tt.vector.from_list(cores)
#     cores = [np.repeat(np.mean(c, axis=1, keepdims=True), c.shape[1], axis=1) for c in cores[:-1]] + [cores[-1]]
#     crossmean = tt.vector.from_list(cores)
#     t = tt.vector.round(t-crossmean, eps=eps)
#
#     # Compute the truncated PCA of the space spanned by the rank modes
#     if verbose:
#         print('\tPCA compression...')
#     cores = tt.vector.to_list(t)
#     tr.core.orthogonalize(cores, t.d-1)
#     cores[-1] = cores[-1][..., 0]
#     svd = np.linalg.svd(cores[-1], full_matrices=False)
#     cores[-1] = svd[0][:, :degree]
#     if not orthogonal:
#         cores[-1] = cores[-1].dot(np.diag(svd[1][:degree]))
#     cores[-1] = cores[-1][:, :, np.newaxis]
#     if cores[-1].shape[1] < degree:  # Degenerate case: add a slice of zeros
#         cores[-1] = np.concatenate([cores[-1], np.zeros([cores[-1].shape[0], degree-cores[-1].shape[1],
#                                                          cores[-1].shape[2]])], axis=1)
#     t = tt.vector.from_list(cores)
#
#     if anchor_mean:
#         withinmean = tt.vector.from_list(tt.vector.to_list(withinmean) + [np.ones([1, 1, 1])])
#         t = tr.core.concatenate([withinmean, t], axis=len(modes), eps=eps)
#
#     if verbose:
#         print()
#
#     return t


# def pca_ensemble(t, modes, degree=3, eps='same', verbose=False):
#     """
#     Given a tensor and a list of modes, consider the space of subtensors obtained
#     by fixing these modes. Find a PCA basis for that space and return the coefficients
#     for each subtensor
#
#     :param t: a TT
#     :param modes: the ensemble modes
#     :param degree: how large a PCA basis to take (default is 3)
#     :param eps: relative tolerance while permuting modes. Default behavior is to
#     preserve the original number of ranks
#     :param verbose:
#     :return: M1 x ... x Mk x degree, where M1, etc. are the sizes of `t` along `modes`
#
#     """
#
#     N = t.d
#
#     if verbose:
#         print('Computing PCA ensemble...')
#
#     # Group target modes next to each other
#     if verbose:
#         print('\tTransposing tensor... 0', end='')
#     modes = np.sort(modes)
#     for i in range(1, len(modes)):
#         t = tr.core.shift_mode(t, modes[i], modes[0] + i - modes[i], eps=eps)
#         if verbose:
#             print(' {}'.format(i), end='')
#     cores = tt.vector.to_list(t)
#
#     # Orthogonalize to the left and right of these modes
#     if verbose:
#         print('\n\tOrthogonalization...')
#     for i in range(modes[0]):
#         tr.core.left_orthogonalize(cores, i)
#     for i in range(N-1, modes[0]+len(modes)-1, -1):
#         tr.core.right_orthogonalize(cores, i)
#
#     # Decompress (end ranks are not 1 in general)
#     if verbose:
#         print('\tMerging spatial dimensions...')
#     subtensors = tt.vector.from_list(cores[modes[0]:modes[0]+len(modes)])
#     stack = tr.core.full(subtensors, keep_end_ranks=True)
#
#     # Merge all spatial dimensions in one
#     stack = np.transpose(stack, [0, stack.ndim-1] + list(range(1, stack.ndim-1)))
#     stack = np.reshape(stack, [stack.shape[0]*stack.shape[1], -1])
#
#     # Compress (PCA) along the spatial dimension
#     if verbose:
#         print('\tPCA compression...')
#     svd = np.linalg.svd(stack, full_matrices=False)
#     ensemble = np.diag(svd[1][:degree]).dot(svd[2][:degree, :]).T
#
#     # Reorganize the ensemble as expected
#     ensemble = np.reshape(ensemble, list(subtensors.n) + [degree])
#
#     if verbose:
#         print('\tDone')
#
#     return ensemble
