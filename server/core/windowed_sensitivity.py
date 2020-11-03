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
import copy
import scipy as sp
import scipy.signal
import tt

import ttrecipes as tr


def windowed_sobol_tt(t, ws, mode='same', normalize=True, non_scalar_outputs=(), eps=1e-6, verbose=False, **kwargs):
    """
    Compute a windowed Sobol tensor out of a TT tensor, i.e. a tensor that stores 2^N Sobol tensors for all possible
    rectangular subwindows of a given size. For each axis, entries 0, ... I-1 encode '0's in a regular Sobol tensor, while entries I, ..., 2*I-1 encode the '1's.

    TODO: non-uniform pdfs

    Warning: normalized Sobol indices may become inaccurate over regions of low variance!

    :param t:
    :param ws: window sizes (integer or list of integers). For even window sizes and mode 'same', the center is rounded
    up. For example, the first window of size 2 is [0], the second is [0, 1], the third [1, 2], etc.
    :param mode: 'same' (default) or 'valid'. See scipy.signal.convolve
    :param normalize: if True (default) the indices of each region will sum 1 (i.e. the true Sobol indices). This will
    likely be problematic if the tensor contains windows with little or no variance. If False, the indices will sum
    to the variance in that region
    :param non_scalar_outputs: list of modes (default: empty). Sobol indices get averaged along these modes
    :param eps:
    :param verbose:
    :param kwargs: other args for the cross-approximation
    :return: (wst, normalization):
        - wst: a windowed Sobol tensor, represented as a TT matrix: rows represent window positions, columns Sobol
        indices. Each row sums 1. If `mode` is 'same', it has size 2*I for each dimension. If 'valid', 2*(I-w+1)
        - normalization: a TT with the variance for each window

    """

    N = t.d
    non_scalar_outputs = np.asarray(non_scalar_outputs, dtype=np.int)
    if not hasattr(ws, '__len__'):
        ws = [ws]*N
    ws = np.array(ws)
    ws[non_scalar_outputs] = 1
    assert np.all(ws >= 1)
    assert np.all(ws <= t.n)
    assert mode in ('same', 'valid')

    if verbose:
        print('Computing windowed Sobol tensor with window sizes {}...'.format(ws))
    cores = tt.vector.to_list(t)
    boxes = [None]*N
    weights = [None]*N
    for n in range(N):
        boxes[n] = np.ones(ws[n])[np.newaxis, :, np.newaxis]
        # To normalize the box convolutions
        weights[n] = 1 / scipy.signal.convolve(np.ones([1, cores[n].shape[1], 1]), boxes[n], mode=mode)
        cores[n] = np.concatenate([sp.signal.convolve(cores[n], boxes[n], mode=mode) * weights[n], cores[n]], axis=1)
    t2 = tt.vector.from_list(cores)
    t2 = tt.multifuncrs2([t2], lambda x: x**2, eps=eps, verb=verbose, **kwargs)

    cores = tt.vector.to_list(t2)
    normalization_cores = []
    mean_cores = []
    meancorner_cores = []
    for n in range(N):
        split = t.n[n]
        if mode == 'valid':
            split = split-ws[n]+1
        idx = np.concatenate([np.arange(split), np.arange(split)])
        mean_core = cores[n][:, :split, :]
        mean_core = mean_core[:, idx, :]
        mean_cores.append(mean_core)
        meancorner_core = np.concatenate([cores[n][:, :split, :], np.zeros([cores[n].shape[0], split, cores[n].shape[
            2]])], axis=1)
        meancorner_cores.append(meancorner_core)
        cores[n] = np.concatenate([cores[n][:, :split, :], sp.signal.convolve(cores[n][:, split:, :], boxes[n], mode=mode) * weights[n] - cores[n][:, :split, :]], axis=1)
        normalization_core = cores[n][:, :split, :] + cores[n][:, split:, :]
        normalization_core = normalization_core[:, idx, :]
        normalization_cores.append(normalization_core)
    normalization = tt.vector.from_list(normalization_cores)
    mean = tt.vector.from_list(mean_cores)
    meancorner = tt.vector.from_list(meancorner_cores)
    normalization = tt.vector.round(normalization - mean, eps=1e-14)
    t3 = tt.vector.from_list(cores)
    t3 = (t3-meancorner).round(1e-14)  # Make 0 all indices corresponding to the empty set {}

    if len(non_scalar_outputs) > 0:
        cores = tt.vector.to_list(t3)
        normalization_cores = tt.vector.to_list(normalization)
        for nso in non_scalar_outputs:
            cores[nso] = np.sum(cores[nso][:, :cores[nso].shape[1]//2, :], axis=1, keepdims=True)
            normalization_cores[nso] = np.sum(normalization_cores[nso][:, :normalization_cores[nso].shape[1]//2, :], axis=1, keepdims=True)
        t3 = tt.vector.from_list(cores)
        t3 = tr.core.squeeze(t3, modes=non_scalar_outputs)
        normalization = tt.vector.from_list(normalization_cores)
        normalization = tr.core.squeeze(normalization, modes=non_scalar_outputs)

    if normalize:
        def fun(Xs):  # "Safer" division, but can still run into trouble over flat regions
            result = Xs[:, 0] / (Xs[:, 1] + eps)
            result[result < 0] = 0
            result[result > 1] = 1
            return result
        result = tt.multifuncrs2([t3, normalization], fun, eps=eps, verb=verbose, **kwargs)
    else:
        result = t3

    result = tt.vector.round(result, eps=1e-14)
    result = tt.matrix.from_list([np.transpose(np.reshape(core, [core.shape[0], 2, core.shape[1]//2, core.shape[2]]),
                                               [0, 2, 1, 3]) for core in tt.vector.to_list(result)])
    return result, tt.vector.from_list([c[:, slice(0, c.shape[1]//2), :] for c in tt.vector.to_list(normalization)])
    #normalization[[slice(0, sh//2) for sh in normalization.n]]


def windowed_get_sobol(wst, pos):
    """
    Gets the Sobol' tensor corresponding to a specific point of a windowed Sobol tensor

    :param wst: a windowed Sobol tensor, with size (I * 2)^N
    :param pos: where to read
    :return: a 2^N Sobol TT tensor

    """

    return tt.vector.round(wst.tt[[[p, p+sh] for sh, p in zip(wst.n, pos)]], eps=0)


def windowed_mean_dimension(wst, mode='cross', eps=1e-6, verbose=False, **kwargs):
    """
    Given a windowed Sobol TT, return a TT with the mean dimension of every window

    :param wst:
    :return:

    """

    assert mode in ('matvec', 'cross')
    N = wst.tt.d

    if verbose:
        print('Computing windowed mean dimension tensor...')
    if mode == 'matvec':
        return tt.matvec(wst, tr.core.hamming_weight(N))
    else:
        wst = wst.tt

        cores = tt.vector.to_list(tr.core.hamming_weight(N))
        for n in range(N):
            cores[n] = cores[n][:, np.concatenate([np.zeros(wst.n[n]//2, dtype=np.int), np.ones(wst.n[n]//2, dtype=np.int)]), :]
        h = tt.vector.from_list(cores)

        wmd = tt.multifuncrs2([wst, h], lambda x: x[:, 0] * x[:, 1], eps=eps, verb=verbose, **kwargs)
        wmd = tt.vector.from_list([core[:, :core.shape[1]//2, :] + core[:, core.shape[1]//2:, :] for core in tt.vector.to_list(wmd)])
        return wmd


def general_sobol_tt(t, hyperparameters=(), non_scalar_outputs=(), **kwargs):
    """
    Compute Sobol indices for a TT that has hyperparameters and/or non-scalar outputs. This function is a wrapper for `windowed_sobol_tt`

    For a hyperparameter: each of its values is assumed to determine a Sobol TT. So if there are H hyperparameters, the resulting Sobol TT has H extra dimensions

    For a non-scalar output: its entire mode range is considered "as a whole" when computing Sobol variances, i.e. that mode does not result in a Sobol index at all

    :param t: a TT of dimension N + O + H
    :param hyperparameters: a list of H modes (default: empty)
    :param non_scalar_outputs: a list of O modes (default: empty)
    :return: a TT tensor of size (2^N) x (I^H). Hyperparameter modes preserve their size; non-scalar output modes disappear (Sobol indices are weighted-averaged across them); remaining modes become size 2 (usual Sobol TT encoding)

    Example:

    ```
    t = tr.core.random_tt(shape=[10, 11, 12, 13], ranks=3)
    st = tr.core.general_sobol_tt(t, hyperparameters=[1], non_scalar_outputs=[3])  # st has size 2 x 11 x 2
    ```

    """

    N = t.d
    hyperparameters = np.array(hyperparameters)
    non_scalar_outputs = np.array(non_scalar_outputs)
    assert np.all(0 <= hyperparameters)
    assert np.all(hyperparameters < N)
    assert np.all(0 <= non_scalar_outputs)
    assert np.all(non_scalar_outputs < N)
    assert not (set(hyperparameters) & set(non_scalar_outputs))

    ws = copy.copy(t.n)
    ws[list(hyperparameters)] = 1
    wst = windowed_sobol_tt(t, ws=ws, mode='valid', normalize=True, non_scalar_outputs=non_scalar_outputs, **kwargs)[0]
    cores = tt.vector.to_list(wst.tt)
    # We remove now singleton dimensions
    for n in np.where(wst.n > 1)[0]:
        cores[n] = cores[n][:, :cores[n].shape[1]//2, :]
    return tt.vector.from_list(cores)
