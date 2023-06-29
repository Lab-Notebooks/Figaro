"""Module for library"""

import os
import re
import dill
import itertools
import joblib
import tqdm
import multiprocessing


def available_cpu_count():
    """Number of available virtual or physical CPUs on this system, i.e.
    user/real as output by time(1) when called with an optimally scaling
    userspace-only program"""

    # cpuset
    # cpuset may restrict the number of *available* processors
    try:
        m = re.search(r"(?m)^Cpus_allowed:\s*(.*)$", open("/proc/self/status").read())
        if m:
            res = bin(int(m.group(1).replace(",", ""), 16)).count("1")
            if res > 0:
                return res
    except IOError:
        pass


def filelist_from_item(item, path_from_root):
    """
    Arguments
    ---------
    item		: boxsdk item object
    path_from_root	: path from folder root
    """
    item = dill.loads(item)

    if hasattr(item, "get_items"):
        return filelist_from_folder(item, os.path.join(path_from_root, item.name))
    else:
        return (path_from_root, item.name, item.object_id)


def filelist_from_folder(folder, path_from_root=""):
    """
    Arguments
    ---------
    folder		: boxsdk folder object
    path_from_root	: path from folder root
    """

    itemlist = [item for item in folder.get_items()]

    num_procs = min(multiprocessing.cpu_count(), len(itemlist))

    if num_procs == 1:

        filelist = [
            filelist_from_item(dill.dumps(item), path_from_root) for item in itemlist
        ]

    else:

        with joblib.parallel_backend(n_jobs=num_procs, backend="loky"):
            filelist = joblib.Parallel(batch_size="auto")(
                joblib.delayed(filelist_from_item)(dill.dumps(item), path_from_root)
                for item in itemlist
            )

    filelist = list(itertools.chain.from_iterable(filelist))
    return filelist
