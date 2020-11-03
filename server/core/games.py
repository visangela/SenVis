"""
TT recipes for cooperative game theory metrics and applications

They all take TT cooperative games as their input. A TT game is
a 2^N TT that encodes a game (N, v) where N is a set of players
(each player gets a TT core) and v is the characteristic function,
mapping each subset of {1, ..., N} to a real number
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
import scipy as sp
import tt

import ttrecipes as tr


def group_shapley(game, eps=1e-6, verbose=False, **kwargs):
    """
    Given a game, builds a tensor that maps each tuple to its "group Shapley value", i.e. the Shapley value resulting from calling that tuple a single player and leaving everyone else unchanged ("externality-free")

    References:
    - Flores et al., "The Shapley Group Value"
    - Skibski et al., "A Graphical Representation for Games in Partition Function Form"

    """

    N = game.d

    def fun(Xs):
        tcard = np.sum(Xs == 1, axis=1)
        ccard = np.sum(Xs == 2, axis=1)
        return sp.misc.factorial(N - tcard - ccard) * sp.misc.factorial(tcard) / sp.misc.factorial(N - ccard + 1)

    # TODO use direct handcrafted automaton
    ws = tr.core.cross(ticks_list=[np.arange(3)]*N, fun=fun, eps=eps, verbose=verbose, **kwargs)
    ws = tt.vector.from_list([core[:, [0, 1, 2, 2], :] for core in tt.vector.to_list(ws)])

    cores = [core[:, [0, 1, 0, 1], :] for core in tt.vector.to_list(game)]
    game = tt.vector.from_list(cores)

    t = tt.multifuncrs2([game, ws], lambda x: x[:, 0]*x[:, 1], eps=eps, verb=verbose, **kwargs)

    add = tt.vector.from_list([core[:, [0, 1, 3], :] for core in tt.vector.to_list(t)])
    sub = tt.vector.from_list([core[:, [0, 1, 2], :] for core in tt.vector.to_list(t)])
    t = add-sub

    t = tt.vector.from_list([np.concatenate([np.sum(core[:, 0:2, :], axis=1, keepdims=True), core[:, 2:3, :]], axis=1) for core in tt.vector.to_list(t)])
    return t.round(eps=0)


def banzhaf_power_indices(st, threshold=0.5, eps=1e-6, verbose=False, **kwargs):
    """
    Compute all N Banzhaf values for a 2^N tensor: for each n-th variable, it is the proportion of all swing votes in which it is the key vote (i.e. tuples whose closed value exceeds a given threshold). The value of a coalition is its closed value

    :param st: a Sobol TT
    :param threshold: real between 0 and 1 that defines the majority (default: 0.5)
    :param eps: default is 1e-6
    :return: a vector with the N Banzhaf values

    """

    N = st.d
    threshold *= tr.core.sum(st)
    cst = tr.core.to_lower(st)
    cst_masked = tt.multifuncrs2([cst], lambda x: x >= threshold, eps=eps, verb=verbose, **kwargs)

    result = np.empty(N)
    for i in range(N):
        idx1 = [slice(None)] * N
        idx1[i] = 1
        idx2 = [slice(None)] * N
        idx2[i] = 0
        result[i] = tr.core.sum(cst_masked[idx1] * (tt.ones(cst_masked[idx2].n) - cst_masked[idx2]))
    return result/np.sum(result)


def check_constant_sum(game, eps=1e-10):
    """
    Check if v(S) + v(N\S) == v(N) for all S contained in N

    :param game:
    :param eps:
    :return: True or False

    """

    N = game.d
    vN = game[[1]*N]
    residual = vN*tt.ones([2]*N) - (game + tr.core.complement(game))
    return np.abs(tt.vector.norm(residual) / tt.vector.norm(game)) < eps


def check_monotone(game, eps=1e-10):
    """
    Check if a game is monotone. If not, return two tuples S and T such that S is contained in T and the value of S exceeds T by the largest margin

    :param game:
    :param eps:
    :return: two lists (S, T)

    """

    T = tt.vector.from_list([core[:, [0, 1, 1], :] for core in tt.vector.to_list(game)])
    S = tt.vector.from_list([core[:, [0, 1, 0], :] for core in tt.vector.to_list(game)])
    residual = tt.vector.round(T - S, eps=eps)
    # If the game is monotone, the residual is always positive (unless it's a cost game)
    val, point = tr.core.minimize(residual)
    S = np.atleast_1d(np.where(point == 1)[0])
    T = np.union1d(S, np.atleast_1d(np.where(point == 2)[0]))
    if val / tt.vector.norm(game) <= eps:
        return True
    else:
        return S, T


def check_superadditive(game, is_cost_game=False, eps=1e-10):
    """
    Check if a game is superadditive. If not, return two tuples with the greatest excess: their value sum minus their union's value
    """

    sign = -is_cost_game*2 + 1
    part1 = tt.vector.from_list([core[:, [0, 0, 1], :] for core in tt.vector.to_list(game)])
    part2 = tt.vector.from_list([core[:, [0, 1, 0], :] for core in tt.vector.to_list(game)])
    union = tt.vector.from_list([core[:, [0, 1, 1], :] for core in tt.vector.to_list(game)])
    residual = tt.vector.round(union - (part1 + part2), eps=eps)
    # If the game is superadditive, the residual is always positive (unless it's a cost game)
    val, point = tr.core.minimize(residual*sign)
    S = np.atleast_1d(np.where(point == 2)[0])
    T = np.atleast_1d(np.where(point == 1)[0])
    if val / tt.vector.norm(game) * sign >= -eps:
        return True
    else:
        return S, T


def check_convex(game, is_cost_game=False, eps=1e-10):
    """
    Check if a game is convex. If not, return two tuples whose value sum minus intersection value is higher than their union's value
    """

    sign = -is_cost_game*2 + 1
    part1 = tt.vector.from_list([core[:, [0, 0, 1, 1], :] for core in tt.vector.to_list(game)])
    part2 = tt.vector.from_list([core[:, [0, 1, 0, 1], :] for core in tt.vector.to_list(game)])
    intersection = tt.vector.from_list([core[:, [0, 0, 0, 1], :] for core in tt.vector.to_list(game)])
    union = tt.vector.from_list([core[:, [0, 1, 1, 1], :] for core in tt.vector.to_list(game)])
    residual = tt.vector.round(union + intersection - (part1 + part2), eps=eps)
    # If the game is convex, the residual is always positive (unless it's a cost game)
    val, point = tr.core.minimize(residual*sign)
    S = np.atleast_1d(np.where(np.logical_or(point == 2, point == 3))[0])
    T = np.atleast_1d(np.where(np.logical_or(point == 1, point == 3))[0])
    if val / tt.vector.norm(game) * sign >= -eps:
        return True
    else:
        return S, T


def check_core(game, payoff, is_cost_game=False, eps=1e-10):
    """
    Check if a payoff vector is in a game's core. If not, find a coalition with the smallest excess (i.e. whose participants are the happiest)

    Reference: https://www.cs.ubc.ca/~kevinlb/teaching/cs532l%20-%202007-8/lectures/lect23.pdf

    :param game: an N-dimensional game TT
    :param payoff: N values
    :return: True if `payoff` is in the core of `game`. Otherwise, returns the coalition that deviates the largest

    """

    sign = -is_cost_game*2 + 1
    cores = []
    for p in payoff:
        core = np.repeat(np.eye(2)[:, np.newaxis, :], 2, axis=1)
        core[1, 1, 0] = p
        cores.append(core)
    cores[0] = cores[0][1:2, :, :]
    cores[-1] = cores[-1][:, :, 0:1]
    t = tt.vector.from_list(cores)
    residual = (t - game).round(eps)
    val, point = tr.core.minimize(residual*sign)
    if val / tt.vector.norm(game) * sign >= -eps:
        return True
    else:
        return point


def veto_players(game, eps=1e-10):
    """
    Return all veto players, sorted. Veto player means that all coalitions without it have 0 value

    :param game:
    :param eps:
    :return: a vector of integers between 0 and N-1

    """

    N = game.d
    norm = tt.vector.norm(game)
    players = []
    for n in range(N):
        idx = [slice(None)]*N
        idx[n] = 0
        if tt.vector.norm(game[idx]) / norm < eps:
            players.append(n)
    return np.array(players)


def zero_players(game, eps=1e-10):
    """
    Return all zero players, sorted. A zero player adds zero value to every coalition
    :param game:
    :param eps:
    :return: a vector of integers between 0 and N-1

    """

    N = game.d
    norm = tt.vector.norm(game)
    players = []
    t = tt.vector.from_list([np.concatenate([core[:, [0, 1], :], core[:, [1], :] - core[:, [0], :]], axis=1) for core in tt.vector.to_list(game)])
    for n in range(N):
        idx = [slice(0, 2)]*N
        idx[n] = [2]
        if tt.vector.norm(t[idx]) / norm < eps:
            players.append(n)
    return np.array(players)


def inessential_players(game, eps=1e-10):
    """
    Return all inessential players, sorted. An inessential player n adds v(n) to every coalition

    :param game:
    :param eps:
    :return: a vector of integers between 0 and N-1

    """

    N = game.d
    norm = tt.vector.norm(game)
    players = []
    t = tt.vector.from_list([np.concatenate([core[:, [0, 1], :], core[:, [1], :] - core[:, [0], :]], axis=1) for core in tt.vector.to_list(game)])
    for n in range(N):
        idx = [slice(0, 2)]*N
        idx[n] = [2]
        tidx = t[idx]
        if tt.vector.norm(tidx - tr.core.set_choose(game, n)*tt.ones(tidx.n)) / norm < eps:
            players.append(n)
    return np.array(players)


def harsanyi_dividends(game):
    """
    Create a 2^N tensor that stores the Harsanyi dividend for every possible coalition (Harsanyi, 1963)
    Related to A. Owen's trick to compute the Shapley values from Sobol indices

    http://www.wifa.uni-leipzig.de/fileadmin/user_upload/itvwl-vwl/MIKRO/Lehre/CGT-applications/acgt_2010_07_09.pdf

    :param game: a 2^N TT
    :return: a 2^N TT

    """

    return tr.core.from_lower(game)
