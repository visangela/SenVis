import json
import tntorch as tn
import torch
import itertools
import time
import numpy as np

models = __import__('models')
dircov = __import__('dircov')

digit = 4


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#                    handle post request and generate order and tensor
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def functional(case):
    calling = getattr(models, "get_" + case)
    function_local, axes = calling()
    return function_local, axes

def data_processing(function_local, axes):
    N = len(axes)

    domains = [axes[n]['domain'] for n in range(N)]
    tick_num = 64
    domain = []
    for n in range(N):
        domain.append(torch.linspace(domains[n][0], domains[n][1], tick_num))

    t = tn.cross(function=function_local, domain=domain, function_arg='matrix', max_iter=10)

    para = [axes[n]['name'] for n in range(N)]

    return N, t, para


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# generate the index for all the subsets of the given set, used for indexing in visualization
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def combination_data(N, nfix, para, listvariable=None):
    n = nfix if nfix < N else N
    if listvariable is None:
        listvariable = list(range(1, N + 1))

    sett = []
    setsInOrder = {}

    for i in range(n):
        setOrder = i + 1
        setsInOrder[setOrder] = {}
        setnow = list(itertools.combinations(listvariable, setOrder))

        setsInOrder[setOrder] = setnow
    sett.append(setsInOrder)

    setAll = {'order': n, "name": para, "sets": sett}

    return json.dumps(setAll)


def data_prereading(N, nfix, t, listvariable=None):
    start = time.time()
    dc = dircov.DirectionalCovariance(t)  # positive or negative of the sobol indices

    n = nfix if nfix < N else N
    if listvariable is None:
        listvariable = list(range(1, N + 1))

    inputorder = len(listvariable)
    # ========= compute all the sobol indices in one loop =============
    sobolAll = []
    sobolsetInOrder = {}
    for i in range(n):
        setOrder = i + 1
        sobolsetInOrder[setOrder] = {}
        setnow = list(itertools.combinations(listvariable, setOrder))
        len_setnow = len(setnow)  # like C(2,5) = 10

        sobolset = {
            'dc': [],
            'sobol': [],
            'closed': [],
            'total': [],
            'super': []
        }

        for j in range(len_setnow):
            # split setnow and get every single element in setnow, then apply the logic
            vindex = setnow[j]
            dc_p = dc.index(list(map(lambda x: x - 1, list(vindex))))
            union_set = tn.any(N, which=list(map(lambda x: x - 1, list(vindex))))
            inter_set = tn.all(N, which=list(map(lambda x: x - 1, list(vindex))))

            sobol_p = tn.sobol(t, mask=tn.only(inter_set)).tolist()
            sobol_p = round(sobol_p, digit)

            sobol_c = tn.sobol(t, mask=tn.only(union_set)).tolist()
            sobol_c = round(sobol_c, digit)

            sobol_t = tn.sobol(t, union_set).tolist()
            sobol_t = round(sobol_t, digit)

            sobol_s = tn.sobol(t, inter_set).tolist()
            sobol_s = round(sobol_s, digit)

            # sobols[i] = [sobol_p, sobol_c, sobol_t, sobol_s]
            sobolset['dc'].append(dc_p)
            sobolset['sobol'].append(sobol_p)
            sobolset['closed'].append(sobol_c)
            sobolset['total'].append(sobol_t)
            sobolset['super'].append(sobol_s)

        sobolsetInOrder[setOrder].update(sobolset)

    sobolAll.append(sobolsetInOrder)

    sobolJson = {'order': N, 'od': n, 'chosenorder': inputorder, 'nodes': sobolAll}
    print('computing this index took only {:g}s'.format(time.time() - start))
    return json.dumps(sobolJson)


# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# ============ generate all the four sobol indices values =============
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
def data_reading(N, nfix, t, listvariable=None):
    start = time.time()
    dc = dircov.DirectionalCovariance(t)

    n = nfix if nfix < N else N
    if listvariable is None:
        listvariable = list(range(1, N + 1))

    inputorder = len(listvariable)
    # ========= compute all the sobol indices in one loop =============
    sobolAll = []
    relativeAll = []
    sobolsetInOrder = {}
    relativeInOrder = {}

    for i in range(n):
        setOrder = i + 1
        sobolsetInOrder[setOrder] = {}
        relativeInOrder[setOrder] = {}
        setnow = list(itertools.combinations(listvariable, setOrder))
        len_setnow = len(setnow)

        sobolset = {
            'dc': [],
            'sobol': [],
            'closed': [],
            'total': [],
            'super': []
        }

        for j in range(len_setnow):
            # split setnow and get every single element in setnow, then apply the logic
            vindex = setnow[j]
            dc_p = dc.index(list(map(lambda x: x - 1, list(vindex))))
            union_set = tn.any(N, which=list(map(lambda x: x - 1, list(vindex))))
            inter_set = tn.all(N, which=list(map(lambda x: x - 1, list(vindex))))

            sobol_p = tn.sobol(t, mask=tn.only(inter_set)).tolist()
            sobol_p = round(sobol_p, digit)

            sobol_c = tn.sobol(t, mask=tn.only(union_set)).tolist()
            sobol_c = round(sobol_c, digit)

            sobol_t = tn.sobol(t, union_set).tolist()
            sobol_t = round(sobol_t, digit)

            sobol_s = tn.sobol(t, inter_set).tolist()
            sobol_s = round(sobol_s, digit)

            # sobols[i] = [sobol_p, sobol_c, sobol_t, sobol_s]
            sobolset['dc'].append(dc_p)
            sobolset['sobol'].append(sobol_p)
            sobolset['closed'].append(sobol_c)
            sobolset['total'].append(sobol_t)
            sobolset['super'].append(sobol_s)

        # tn.sobol(t, x & (y | z)) / tn.sobol(t, y | z); or tn.sobol(t, (x | y) & z) / tn.sobol(t, z)
        # get relative importance values
        setfull = list(itertools.combinations(listvariable, setOrder))
        len_setfull = len(setfull)
        relativeOrders = []
        for j in range(len_setfull):
            vindex = setfull[j]
            temp = listvariable
            for m in range(len(vindex)):
                vrest = np.delete(temp, list(temp).index(vindex[m]))
                temp = vrest
            inter_set = tn.any(N, which=list(map(lambda x: x - 1, list(vindex))))
            relative_index = []
            for k in range(len(vrest)):
                rela = []
                dnmset = list(itertools.combinations(vrest, k + 1))
                for m in range(len(dnmset)):
                    dnm_union = tn.any(N, which=list(map(lambda x: x - 1, list(dnmset[m]))))

                    nm_sobol = tn.sobol(t, (inter_set & dnm_union))
                    dnm_sobol = tn.sobol(t, dnm_union)

                    rela_temp = (nm_sobol / dnm_sobol).tolist()
                    rela_temp = round(rela_temp, digit)

                    rela.append(rela_temp)
                relative_index.append(rela)
            relativeOrders.append(relative_index)

        sobolsetInOrder[setOrder].update(sobolset)
        relativeInOrder[setOrder] = relativeOrders
    sobolAll.append(sobolsetInOrder)
    relativeAll.append(relativeInOrder)

    sobolJson = {'order': N, 'od': n, 'chosenorder': inputorder, 'nodes': sobolAll, 'relatives': relativeAll}
    print('computing this index took only {:g}s'.format(time.time() - start))

    return json.dumps(sobolJson)

