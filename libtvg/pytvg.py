#!/usr/bin/python3
from ctypes import cdll
from ctypes import cast
from ctypes import c_int, c_int64
from ctypes import c_uint, c_uint64
from ctypes import c_float, c_double
from ctypes import c_void_p, c_char_p
from ctypes import Structure
from ctypes import POINTER
from ctypes import CFUNCTYPE
from ctypes import addressof
from ctypes.util import find_library
import collections
import functools
import weakref
import numpy as np
import numpy.ctypeslib as npc
import math
import sys
import os

libname = "libtvg.dylib" if sys.platform == "darwin" else "libtvg.so"
filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), libname)
lib = cdll.LoadLibrary(filename)
libc = cdll.LoadLibrary(find_library('c'))

class c_vector(Structure):
    _fields_ = [("refcount", c_int),
                ("flags", c_uint),
                ("revision", c_uint64),
                ("eps", c_float)]

class c_graph(Structure):
    _fields_ = [("refcount", c_int),
                ("flags",    c_uint),
                ("revision", c_uint64),
                ("eps",      c_float),
                ("ts",       c_uint64),
                ("id",       c_uint64)]

class c_tvg(Structure):
    _fields_ = [("refcount", c_int),
                ("flags",    c_uint)]

class c_window(Structure):
    _fields_ = [("refcount", c_int),
                ("eps",      c_float),
                ("ts",       c_uint64)]

class c_mongodb_config(Structure):
    _fields_ = [("uri",          c_char_p),
                ("database",     c_char_p),
                ("col_articles", c_char_p),
                ("article_id",   c_char_p),
                ("article_time", c_char_p),
                ("col_entities", c_char_p),
                ("entity_doc",   c_char_p),
                ("entity_sen",   c_char_p),
                ("entity_ent",   c_char_p),
                ("max_distance", c_uint)]

class c_mongodb(Structure):
    _fields_ = [("refcount", c_int)]

class c_bfs_entry(Structure):
    _fields_ = [("weight",    c_double),
                ("count",     c_uint64),
                ("edge_from", c_uint64),
                ("edge_to",   c_uint64)]

# Hacky: we need optional ndpointer parameters at some places.
def or_null(t):
    class wrap:
        def from_param(cls, obj):
            if obj is None: return None
            return t.from_param(obj)
    return wrap()

c_double_p       = POINTER(c_double)
c_vector_p       = POINTER(c_vector)
c_graph_p        = POINTER(c_graph)
c_tvg_p          = POINTER(c_tvg)
c_window_p       = POINTER(c_window)
c_mongodb_config_p = POINTER(c_mongodb_config)
c_mongodb_p      = POINTER(c_mongodb)
c_bfs_entry_p    = POINTER(c_bfs_entry)
c_bfs_callback_p = CFUNCTYPE(c_int, c_graph_p, c_bfs_entry_p, c_void_p)

# vector functions

lib.alloc_vector.argtypes = ()
lib.alloc_vector.restype = c_vector_p

lib.free_vector.argtypes = (c_vector_p,)

lib.vector_set_eps.argtypes = (c_vector_p, c_float)

lib.vector_empty.argtypes = (c_vector_p,)
lib.vector_empty.restype = c_int

lib.vector_has_entry.argtypes = (c_vector_p, c_uint64)
lib.vector_has_entry.restype = c_int

lib.vector_get_entry.argtypes = (c_vector_p, c_uint64)
lib.vector_get_entry.restype = c_float

lib.vector_get_entries.argtypes = (c_vector_p, or_null(npc.ndpointer(dtype=np.uint64)), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.vector_get_entries.restype = c_uint64

lib.vector_set_entry.argtypes = (c_vector_p, c_uint64, c_float)
lib.vector_set_entry.restype = c_int

lib.vector_set_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), npc.ndpointer(dtype=np.float32), c_uint64)
lib.vector_set_entries.restype = c_int

lib.vector_add_entry.argtypes = (c_vector_p, c_uint64, c_float)
lib.vector_add_entry.restype = c_int

lib.vector_add_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), npc.ndpointer(dtype=np.float32), c_uint64)
lib.vector_add_entries.restype = c_int

lib.vector_sub_entry.argtypes = (c_vector_p, c_uint64, c_float)
lib.vector_sub_entry.restype = c_int

lib.vector_sub_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), npc.ndpointer(dtype=np.float32), c_uint64)
lib.vector_sub_entries.restype = c_int

lib.vector_del_entry.argtypes = (c_vector_p, c_uint64)

lib.vector_del_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), c_uint64)

lib.vector_mul_const.argtypes = (c_vector_p, c_float)

lib.vector_norm.argtypes = (c_vector_p,)
lib.vector_norm.restype = c_double

lib.vector_mul_vector.argtypes = (c_vector_p, c_vector_p)
lib.vector_mul_vector.restype = c_double

# graph functions

lib.alloc_graph.argtypes = (c_uint,)
lib.alloc_graph.restype = c_graph_p

lib.free_graph.argtypes = (c_graph_p,)

lib.unlink_graph.argtypes = (c_graph_p,)

lib.graph_memory_usage.argtypes = (c_graph_p,)
lib.graph_memory_usage.restype = c_uint64

lib.prev_graph.argtypes = (c_graph_p,)
lib.prev_graph.restype = c_graph_p

lib.next_graph.argtypes = (c_graph_p,)
lib.next_graph.restype = c_graph_p

lib.graph_enable_delta.argtypes = (c_graph_p,)
lib.graph_enable_delta.restype = c_int

lib.graph_disable_delta.argtypes = (c_graph_p,)

lib.graph_get_delta.argtypes = (c_graph_p, POINTER(c_float))
lib.graph_get_delta.restype = c_graph_p

lib.graph_set_eps.argtypes = (c_graph_p, c_float)

lib.graph_empty.argtypes = (c_graph_p,)
lib.graph_empty.restype = c_int

lib.graph_has_edge.argtypes = (c_graph_p, c_uint64, c_uint64)
lib.graph_has_edge.restype = c_int

lib.graph_get_edge.argtypes = (c_graph_p, c_uint64, c_uint64)
lib.graph_get_edge.restype = c_float

lib.graph_get_edges.argtypes = (c_graph_p, or_null(npc.ndpointer(dtype=np.uint64)), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.graph_get_edges.restype = c_uint64

lib.graph_get_adjacent_edges.argtypes = (c_graph_p, c_uint64, or_null(npc.ndpointer(dtype=np.uint64)), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.graph_get_adjacent_edges.restype = c_uint64

lib.graph_set_edge.argtypes = (c_graph_p, c_uint64, c_uint64, c_float)
lib.graph_set_edge.restype = c_int

lib.graph_set_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), npc.ndpointer(dtype=np.float32), c_uint64)
lib.graph_set_edges.restype = c_int

lib.graph_add_edge.argtypes = (c_graph_p, c_uint64, c_uint64, c_float)
lib.graph_add_edge.restype = c_int

lib.graph_add_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), npc.ndpointer(dtype=np.float32), c_uint64)
lib.graph_add_edges.restype = c_int

lib.graph_add_graph.argtypes = (c_graph_p, c_graph_p, c_float)
lib.graph_add_graph.restype = c_int

lib.graph_sub_edge.argtypes = (c_graph_p, c_uint64, c_uint64, c_float)
lib.graph_sub_edge.restype = c_int

lib.graph_sub_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), npc.ndpointer(dtype=np.float32), c_uint64)
lib.graph_sub_edges.restype = c_int

lib.graph_sub_graph.argtypes = (c_graph_p, c_graph_p, c_float)
lib.graph_sub_graph.restype = c_int

lib.graph_del_edge.argtypes = (c_graph_p, c_uint64, c_uint64)

lib.graph_del_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), c_uint64)

lib.graph_mul_const.argtypes = (c_graph_p, c_float)

lib.graph_mul_vector.argtypes = (c_graph_p, c_vector_p)
lib.graph_mul_vector.restype = c_vector_p

lib.graph_in_degrees.argtypes = (c_graph_p,)
lib.graph_in_degrees.restype = c_vector_p

lib.graph_in_weights.argtypes = (c_graph_p,)
lib.graph_in_weights.restype = c_vector_p

lib.graph_out_degrees.argtypes = (c_graph_p,)
lib.graph_out_degrees.restype = c_vector_p

lib.graph_out_weights.argtypes = (c_graph_p,)
lib.graph_out_weights.restype = c_vector_p

lib.graph_degree_anomalies.argtypes = (c_graph_p,)
lib.graph_degree_anomalies.restype = c_vector_p

lib.graph_weight_anomalies.argtypes = (c_graph_p,)
lib.graph_weight_anomalies.restype = c_vector_p

lib.graph_power_iteration.argtypes = (c_graph_p, c_uint, c_double_p)
lib.graph_power_iteration.restype = c_vector_p

lib.graph_bfs.argtypes = (c_graph_p, c_uint64, c_int, c_bfs_callback_p, c_void_p)
lib.graph_bfs.restype = c_int

# tvg functions

lib.alloc_tvg.argtypes = (c_uint,)
lib.alloc_tvg.restype = c_tvg_p

lib.free_tvg.argtypes = (c_tvg_p,)

lib.tvg_link_graph.argtypes = (c_tvg_p, c_graph_p, c_uint64)
lib.tvg_link_graph.restype = c_int

lib.tvg_alloc_graph.argtypes = (c_tvg_p, c_uint64)
lib.tvg_alloc_graph.restype = c_graph_p

lib.tvg_load_graphs_from_file.argtypes = (c_tvg_p, c_char_p)
lib.tvg_load_graphs_from_file.restype = c_int

lib.tvg_enable_mongodb_sync.argtypes = (c_tvg_p, c_mongodb_p, c_uint64, c_uint64)
lib.tvg_enable_mongodb_sync.restype = c_int

lib.tvg_disable_mongodb_sync.argtypes = (c_tvg_p,)

lib.tvg_alloc_window_rect.argtypes = (c_tvg_p, c_int64, c_int64)
lib.tvg_alloc_window_rect.restype = c_window_p

lib.tvg_alloc_window_decay.argtypes = (c_tvg_p, c_int64, c_float)
lib.tvg_alloc_window_decay.restype = c_window_p

lib.tvg_alloc_window_smooth.argtypes = (c_tvg_p, c_int64, c_float)
lib.tvg_alloc_window_smooth.restype = c_window_p

lib.tvg_lookup_graph_ge.argtypes = (c_tvg_p, c_uint64)
lib.tvg_lookup_graph_ge.restype = c_graph_p

lib.tvg_lookup_graph_le.argtypes = (c_tvg_p, c_uint64)
lib.tvg_lookup_graph_le.restype = c_graph_p

lib.tvg_lookup_graph_near.argtypes = (c_tvg_p, c_uint64)
lib.tvg_lookup_graph_near.restype = c_graph_p

lib.tvg_compress.argtypes = (c_tvg_p, c_uint64, c_uint64)
lib.tvg_compress.restype = c_int

# window functions

lib.free_window.argtypes = (c_window_p,)

lib.window_set_eps.argtypes = (c_window_p, c_float)

lib.window_clear.argtypes = (c_window_p,)

lib.window_update.argtypes = (c_window_p, c_uint64)
lib.window_update.restype = c_graph_p

# MongoDB functions

lib.alloc_mongodb.argtypes = (c_mongodb_config_p,)
lib.alloc_mongodb.restype = c_mongodb_p

lib.free_mongodb.argtypes = (c_mongodb_p,)

lib.mongodb_load_graph.argtypes = (c_mongodb_p, c_uint64, c_uint)
lib.mongodb_load_graph.restype = c_graph_p

lib.tvg_load_graphs_from_mongodb.argtypes = (c_tvg_p, c_mongodb_p)
lib.tvg_load_graphs_from_mongodb.restype = c_int

# libc functions

libc.free.argtypes = (c_void_p,)

TVG_FLAGS_NONZERO   = 0x00000001
TVG_FLAGS_POSITIVE  = 0x00000002
TVG_FLAGS_DIRECTED  = 0x00000004
TVG_FLAGS_STREAMING = 0x00000008

TVG_FLAGS_LOAD_NEXT = 0x00010000
TVG_FLAGS_LOAD_PREV = 0x00020000

# The 'cacheable' decorator can be used on Vector and Graph objects to cache the result
# of a function call as long as the underlying vector/graph has not changed. This is
# ensured by storing and comparing the revision number embedded in the object header.
def cacheable(func):
    cache = weakref.WeakKeyDictionary()
    @functools.wraps(func)
    def wrapper(self, drop_cache=False):
        try:
            old_revision, result = cache[self]
        except KeyError:
            old_revision, result = (None, None)
        new_revision = self._obj.contents.revision
        if old_revision != new_revision or drop_cache:
            result = func(self) # FIXME: Support *args, **kwargs.
            cache[self] = (new_revision, result)
        return result
    return wrapper

class Labels(object):
    def __init__(self):
        self._id2label = {}
        self._label2id = collections.defaultdict(list)

    @staticmethod
    def load(filename, *args, **kwargs):
        labels = Labels(*args, **kwargs)
        with open(filename) as fp:
            for line in fp:
                line = line.rstrip()
                if line == "": continue
                if line.startswith("#"): continue
                if line.startswith(";"): continue
                values = line.split("\t", 1)
                labels[int(values[0])] = values[1]
        return labels

    def __getitem__(self, index):
        return self._id2label[index]

    def __setitem__(self, index, label):
        if index in self._id2label:
            del self[index]

        self._id2label[index] = label
        self._label2id[label].append(index)

    def __delitem__(self, index):
        try:
            label = self._id2label[index]
        except KeyError:
            return
        self._label2id[label].remove(index)
        del self._id2label[index]

    def __len__(self):
        return len(self._id2label)

    def lookup(self, label):
        return self._label2id[label]

class Vector(object):
    def __init__(self, nonzero=False, positive=False, obj=None):
        if obj is None:
            flags = 0
            flags |= (TVG_FLAGS_NONZERO  if nonzero  else 0)
            flags |= (TVG_FLAGS_POSITIVE if positive else 0)
            obj = lib.alloc_vector(flags)

        self._obj = obj
        if not obj:
            raise MemoryError

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_vector(self._obj)

    @cacheable
    def __repr__(self):
        max_entries = 10
        indices = np.empty(shape=(max_entries,), dtype=np.uint64,  order='C')
        weights = np.empty(shape=(max_entries,), dtype=np.float32, order='C')
        num_entries = lib.vector_get_entries(self._obj, indices, weights, max_entries)

        out = []
        for i in range(min(num_entries, max_entries)):
            out.append("%d: %f" % (indices[i], weights[i]))
        if num_entries > max_entries:
            out.append("...")

        return "Vector({%s})" % ", ".join(out)

    @property
    def flags(self):
        return self._obj.contents.flags

    @property
    def revision(self):
        return self._obj.contents.revision

    @property
    def eps(self):
        return self._obj.contents.eps

    @eps.setter
    def eps(self, value):
        lib.vector_set_eps(self._obj, value)

    @cacheable
    def empty(self):
        return lib.vector_empty(self._obj)

    def has_entry(self, index):
        return lib.vector_has_entry(self._obj, index)

    def __getitem__(self, index):
        return lib.vector_get_entry(self._obj, index)

    def entries(self, ret_indices=True, ret_weights=True):
        num_entries = 100 # FIXME: Arbitrary limit.
        while True:
            max_entries = num_entries
            indices = np.empty(shape=(max_entries,), dtype=np.uint64,  order='C') if ret_indices else None
            weights = np.empty(shape=(max_entries,), dtype=np.float32, order='C') if ret_weights else None
            num_entries = lib.vector_get_entries(self._obj, indices, weights, max_entries)
            if num_entries <= max_entries:
                break

        if indices is not None:
            indices.resize((num_entries,), refcheck=False)
        if weights is not None:
            weights.resize((num_entries,), refcheck=False)

        return indices, weights

    @property
    @cacheable
    def num_entries(self):
        return lib.vector_get_entries(self._obj, None, None, 0)

    def __len__(self):
        return self.num_entries

    def __setitem__(self, index, weight):
        res = lib.vector_set_entry(self._obj, index, weight)
        if not res:
            raise MemoryError

    def set_entries(self, indices, weights):
        indices = np.asarray(indices, dtype=np.uint64)
        weights = np.asarray(weights, dtype=np.float32)

        if indices.size == 0 and weights.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 1:
            raise ValueError("indices array does not have correct dimensions")
        if len(weights.shape) != 1:
            raise ValueError("weights array does not have correct dimensions")
        if indices.shape[0] != weights.shape[0]:
            raise ValueError("indices/weights arrays have different length")

        res = lib.vector_set_entries(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def add_entry(self, index, weight):
        res = lib.vector_add_entry(self._obj, index, weight)
        if not res:
            raise MemoryError

    def add_entries(self, indices, weights):
        indices = np.asarray(indices, dtype=np.uint64)
        weights = np.asarray(weights, dtype=np.float32)

        if indices.size == 0 and weights.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 1:
            raise ValueError("indices array does not have correct dimensions")
        if len(weights.shape) != 1:
            raise ValueError("weights array does not have correct dimensions")
        if indices.shape[0] != weights.shape[0]:
            raise ValueError("indices/weights arrays have different length")

        res = lib.vector_add_entries(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def sub_entry(self, index, weight):
        res = lib.vector_sub_entry(self._obj, index, weight)
        if not res:
            raise MemoryError

    def sub_entries(self, indices, weights):
        indices = np.asarray(indices, dtype=np.uint64)
        weights = np.asarray(weights, dtype=np.float32)

        if indices.size == 0 and weights.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 1:
            raise ValueError("indices array does not have correct dimensions")
        if len(weights.shape) != 1:
            raise ValueError("weights array does not have correct dimensions")
        if indices.shape[0] != weights.shape[0]:
            raise ValueError("indices/weights arrays have different length")

        res = lib.vector_sub_entries(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def __delitem__(self, index):
        lib.vector_del_entry(self._obj, index)

    def del_entries(self, indices):
        indices = np.asarray(indices, dtype=np.uint64)

        if indices.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 1:
            raise ValueError("indices array does not have correct dimensions")

        lib.vector_del_entries(self._obj, indices, indices.shape[0])

    def mul_const(self, constant):
        lib.vector_mul_const(self._obj, constant)

    @cacheable
    def norm(self):
        return lib.vector_norm(self._obj)

    def mul_vector(self, other):
        # FIXME: Check type of 'other'.
        return lib.vector_mul_vector(self._obj, other._obj)

class Graph(object):
    def __init__(self, nonzero=False, positive=False, directed=False, obj=None):
        if obj is None:
            flags = 0
            flags |= (TVG_FLAGS_NONZERO  if nonzero  else 0)
            flags |= (TVG_FLAGS_POSITIVE if positive else 0)
            flags |= (TVG_FLAGS_DIRECTED if directed else 0)
            obj = lib.alloc_graph(flags)

        self._obj = obj
        if not obj:
            raise MemoryError

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_graph(self._obj)

    @cacheable
    def __repr__(self):
        max_edges = 10
        indices = np.empty(shape=(max_edges, 2), dtype=np.uint64,  order='C')
        weights = np.empty(shape=(max_edges,),   dtype=np.float32, order='C')
        num_edges = lib.graph_get_edges(self._obj, indices, weights, max_edges)

        out = []
        for i in range(min(num_edges, max_edges)):
            out.append("(%d, %d): %f" % (indices[i][0], indices[i][1], weights[i]))
        if num_edges > max_edges:
            out.append("...")

        return "Graph({%s})" % ", ".join(out)

    @property
    def flags(self):
        return self._obj.contents.flags

    @property
    def revision(self):
        return self._obj.contents.revision

    @property
    def eps(self):
        return self._obj.contents.eps

    @eps.setter
    def eps(self, value):
        lib.graph_set_eps(self._obj, value)

    @property
    def ts(self):
        return self._obj.contents.ts

    @property
    def id(self):
        return self._obj.contents.id

    @staticmethod
    def load_from_file(filename, nonzero=False, positive=False, directed=False):
        raise NotImplementedError

    @staticmethod
    def load_from_mongodb(mongodb, id, nonzero=False, positive=False, directed=False):
        flags = 0
        flags |= (TVG_FLAGS_NONZERO  if nonzero  else 0)
        flags |= (TVG_FLAGS_POSITIVE if positive else 0)
        flags |= (TVG_FLAGS_DIRECTED if directed else 0)
        obj = lib.mongodb_load_graph(mongodb._obj, id, flags)
        return Graph(obj=obj) if obj else None

    def unlink(self):
        lib.unlink_graph(self._obj)

    @property
    @cacheable
    def memory_usage(self):
        return lib.graph_memory_usage(self._obj)

    @property
    def next(self):
        obj = lib.next_graph(self._obj)
        return Graph(obj=obj) if obj else None

    @property
    def prev(self):
        obj = lib.prev_graph(self._obj)
        return Graph(obj=obj) if obj else None

    def enable_delta(self):
        res = lib.graph_enable_delta(self._obj)
        if not res:
            raise MemoryError

    def disable_delta(self):
        lib.graph_disable_delta(self._obj)

    def get_delta(self):
        mul = c_float()
        obj = lib.graph_get_delta(self._obj, mul)
        if not obj:
            return (None, None)
        return Graph(obj=obj), mul.value

    @cacheable
    def empty(self):
        return lib.graph_empty(self._obj)

    def has_edge(self, indices):
        (source, target) = indices
        return lib.graph_has_edge(self._obj, source, target)

    def __getitem__(self, indices):
        (source, target) = indices
        return lib.graph_get_edge(self._obj, source, target)

    def edges(self, ret_indices=True, ret_weights=True):
        num_edges = 100 # FIXME: Arbitrary limit.
        while True:
            max_edges = num_edges
            indices = np.empty(shape=(max_edges, 2), dtype=np.uint64,  order='C') if ret_indices else None
            weights = np.empty(shape=(max_edges,),   dtype=np.float32, order='C') if ret_weights else None
            num_edges = lib.graph_get_edges(self._obj, indices, weights, max_edges)
            if num_edges <= max_edges:
                break

        if indices is not None:
            indices.resize((num_edges, 2), refcheck=False)
        if weights is not None:
            weights.resize((num_edges,), refcheck=False)

        return indices, weights

    @property
    @cacheable
    def num_edges(self):
        return lib.graph_get_edges(self._obj, None, None, 0)

    def nodes(self):
        # Nodes are always implicit: A node exists when it is used as edge source or target.
        # FIXME: Add a C library helper?
        indices, _ = self.edges(ret_weights=False)
        return np.unique(indices)

    @property
    @cacheable
    def num_nodes(self):
        return len(self.nodes())

    def adjacent_edges(self, source, ret_indices=True, ret_weights=True):
        num_edges = 100 # FIXME: Arbitrary limit.
        while True:
            max_edges = num_edges
            indices = np.empty(shape=(max_edges,), dtype=np.uint64,  order='C') if ret_indices else None
            weights = np.empty(shape=(max_edges,), dtype=np.float32, order='C') if ret_weights else None
            num_edges = lib.graph_get_adjacent_edges(self._obj, source, indices, weights, max_edges)
            if num_edges <= max_edges:
                break

        if indices is not None:
            indices.resize((num_edges,), refcheck=False)
        if weights is not None:
            weights.resize((num_edges,), refcheck=False)

        return indices, weights

    def num_adjacent_edges(self, source):
        return lib.graph_get_adjacent_edges(self._obj, source, None, None, 0)

    def __len__(self):
        return self.num_edges

    def __setitem__(self, indices, weight):
        (source, target) = indices
        res = lib.graph_set_edge(self._obj, source, target, weight)
        if not res:
            raise MemoryError

    def set_edges(self, indices, weights):
        indices = np.asarray(indices, dtype=np.uint64)
        weights = np.asarray(weights, dtype=np.float32)

        if indices.size == 0 and weights.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 2 or indices.shape[1] != 2:
            raise ValueError("indices array does not have correct dimensions")
        if len(weights.shape) != 1:
            raise ValueError("weights array does not have correct dimensions")
        if indices.shape[0] != weights.shape[0]:
            raise ValueError("indices/weights arrays have different length")

        res = lib.graph_set_edges(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def add_edge(self, indices, weight):
        (source, target) = indices
        res = lib.graph_add_edge(self._obj, source, target, weight)
        if not res:
            raise MemoryError

    def add_edges(self, indices, weights):
        indices = np.asarray(indices, dtype=np.uint64)
        weights = np.asarray(weights, dtype=np.float32)

        if indices.size == 0 and weights.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 2 or indices.shape[1] != 2:
            raise ValueError("indices array does not have correct dimensions")
        if len(weights.shape) != 1:
            raise ValueError("weights array does not have correct dimensions")
        if indices.shape[0] != weights.shape[0]:
            raise ValueError("indices/weights arrays have different length")

        res = lib.graph_add_edges(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def sub_edge(self, indices, weight):
        (source, target) = indices
        res = lib.graph_sub_edge(self._obj, source, target, weight)
        if not res:
            raise MemoryError

    def sub_edges(self, indices, weights):
        indices = np.asarray(indices, dtype=np.uint64)
        weights = np.asarray(weights, dtype=np.float32)

        if indices.size == 0 and weights.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 2 or indices.shape[1] != 2:
            raise ValueError("indices array does not have correct dimensions")
        if len(weights.shape) != 1:
            raise ValueError("weights array does not have correct dimensions")
        if indices.shape[0] != weights.shape[0]:
            raise ValueError("indices/weights arrays have different length")

        res = lib.graph_sub_edges(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def __delitem__(self, indices):
        (source, target) = indices
        lib.graph_del_edge(self._obj, source, target)

    def del_edges(self, indices):
        indices = np.asarray(indices, dtype=np.uint64)

        if indices.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 2 or indices.shape[1] != 2:
            raise ValueError("indices array does not have correct dimensions")

        lib.graph_del_edges(self._obj, indices, indices.shape[0])

    def mul_const(self, constant):
        lib.graph_mul_const(self._obj, constant)

    def mul_vector(self, other):
        # FIXME: Check type of 'other'.
        return Vector(obj=lib.graph_mul_vector(self._obj, other._obj))

    def in_degrees(self):
        return Vector(obj=lib.graph_in_degrees(self._obj))

    def in_weights(self):
        return Vector(obj=lib.graph_in_weights(self._obj))

    def out_degrees(self):
        return Vector(obj=lib.graph_out_degrees(self._obj))

    def out_weights(self):
        return Vector(obj=lib.graph_out_weights(self._obj))

    def degree_anomalies(self):
        return Vector(obj=lib.graph_degree_anomalies(self._obj))

    def weight_anomalies(self):
        return Vector(obj=lib.graph_weight_anomalies(self._obj))

    def power_iteration(self, num_iterations=0, ret_eigenvalue=True):
        eigenvalue = c_double() if ret_eigenvalue else None
        vector = Vector(obj=lib.graph_power_iteration(self._obj, num_iterations, eigenvalue))
        if eigenvalue is not None:
            eigenvalue = eigenvalue.value
        return vector, eigenvalue

    def bfs_count(self, source, max_count=0xffffffffffffffff):
        result = []

        def wrapper(graph, entry, userdata):
            if entry.contents.count > max_count:
                return 1

            entry = entry.contents
            edge_from = entry.edge_from if entry.edge_from != 0xffffffffffffffff else None
            result.append((entry.weight, entry.count, edge_from, entry.edge_to))
            return 0

        res = lib.graph_bfs(self._obj, source, 0, c_bfs_callback_p(wrapper), None)
        if not res:
            raise RuntimeError

        return result

    def bfs_weight(self, source, max_weight=np.inf):
        result = []

        def wrapper(graph, entry, userdata):
            if entry.contents.weight > max_weight:
                return 1

            entry = entry.contents
            edge_from = entry.edge_from if entry.edge_from != 0xffffffffffffffff else None
            result.append((entry.weight, entry.count, edge_from, entry.edge_to))
            return 0

        res = lib.graph_bfs(self._obj, source, 1, c_bfs_callback_p(wrapper), None)
        if not res:
            raise RuntimeError

        return result

    def encode_visjs(self, node_attributes=None):
        if node_attributes is None:
            node_attributes = lambda i: {}

        nodes = []
        edges = []

        for i in self.nodes():
            nodes.append({'id': i, **node_attributes(i)})

        delta, mul = self.get_delta()
        if delta is None:
            indices, weights = self.edges()
            for i, w in zip(indices, weights):
                edges.append({'id': "%d-%d" % (i[0], i[1]), 'from': i[0], 'to': i[1], 'value': w})

            return {'cmd': 'network_set', 'nodes': nodes, 'edges': edges}

        deleted_nodes = set()
        deleted_edges = []

        indices, weights = delta.edges()
        for i, w in zip(indices, weights):
            if w > 0.0:
                edges.append({'id': "%d-%d" % (i[0], i[1]), 'from': i[0], 'to': i[1], 'value': w})
                continue
            deleted_edges.append({'id': "%d-%d" % (i[0], i[1])})
            if self.num_adjacent_edges(i[0]) == 0:
                deleted_nodes.add(i[0])
            if self.num_adjacent_edges(i[1]) == 0:
                deleted_nodes.add(i[1])

        deleted_nodes = [{'id': x} for x in deleted_nodes]
        return {'cmd': 'network_update', 'mul':mul,
                'nodes': nodes, 'deleted_nodes': deleted_nodes,
                'edges': edges, 'deleted_edges': deleted_edges}

class GraphIter(object):
    def __init__(self, graph):
        self._graph = graph

    def __next__(self):
        if not self._graph:
            raise StopIteration

        result = self._graph
        self._graph = result.next
        return result

class GraphIterReversed(object):
    def __init__(self, graph):
        self._graph = graph

    def __iter__(self):
        return self

    def __next__(self):
        if not self._graph:
            raise StopIteration

        result = self._graph
        self._graph = result.prev
        return result

class TVG(object):
    def __init__(self, nonzero=False, positive=False, directed=False, streaming=False, obj=None):
        if obj is None:
            flags = 0
            flags |= (TVG_FLAGS_NONZERO  if nonzero  else 0)
            flags |= (TVG_FLAGS_POSITIVE if positive else 0)
            flags |= (TVG_FLAGS_DIRECTED if directed else 0)
            flags |= (TVG_FLAGS_STREAMING if streaming else 0)
            obj = lib.alloc_tvg(flags)

        self._obj = obj
        if not obj:
            raise MemoryError

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_tvg(self._obj)

    @property
    def flags(self):
        return self._obj.contents.flags

    def link(self, graph, ts):
        res = lib.tvg_link_graph(self._obj, graph._obj, ts)
        if not res:
            raise RuntimeError

    def Graph(self, ts):
        return Graph(obj=lib.tvg_alloc_graph(self._obj, ts))

    @staticmethod
    def load(source, *args, **kwargs):
        tvg = TVG(*args, **kwargs)
        if isinstance(source, MongoDB):
            tvg.load_from_mongodb(source)
        else:
            tvg.load_from_file(source)
        return tvg

    def load_from_file(self, filename):
        res = lib.tvg_load_graphs_from_file(self._obj, filename.encode("utf-8"))
        if not res:
            raise IOError

    def load_from_mongodb(self, mongodb):
        res = lib.tvg_load_graphs_from_mongodb(self._obj, mongodb._obj)
        if not res:
            raise IOError

    def enable_mongodb_sync(self, mongodb, batch_size=0, cache_size=0):
        res = lib.tvg_enable_mongodb_sync(self._obj, mongodb._obj, batch_size, cache_size)
        if not res:
            raise IOError

    def disable_mongodb_sync(self):
        lib.tvg_disable_mongodb_sync(self._obj)

    def __iter__(self):
        return GraphIter(self.lookup_ge())

    def __reversed__(self):
        return GraphIterReversed(self.lookup_le())

    def WindowRect(self, window_l, window_r):
        return Window(obj=lib.tvg_alloc_window_rect(self._obj, window_l, window_r))

    def WindowDecay(self, window, beta=None, log_beta=None):
        if np.isinf(window):
            window = 0x7fffffffffffffff
        if log_beta is None:
            log_beta = math.log(beta)
        return Window(obj=lib.tvg_alloc_window_decay(self._obj, window, log_beta))

    def WindowSmooth(self, window, beta=None, log_beta=None):
        if np.isinf(window):
            window = 0x7fffffffffffffff
        if log_beta is None:
            log_beta = math.log(beta)
        return Window(obj=lib.tvg_alloc_window_smooth(self._obj, window, log_beta))

    def lookup_ge(self, ts=0):
        if isinstance(ts, float):
            ts = math.ceil(ts)
        obj = lib.tvg_lookup_graph_ge(self._obj, ts)
        return Graph(obj=obj) if obj else None

    def lookup_le(self, ts=0xffffffffffffffff):
        if isinstance(ts, float):
            ts = int(ts)
        obj = lib.tvg_lookup_graph_le(self._obj, ts)
        return Graph(obj=obj) if obj else None

    def lookup_near(self, ts):
        if isinstance(ts, float):
            ts = int(ts + 0.5)
        obj = lib.tvg_lookup_graph_near(self._obj, ts)
        return Graph(obj=obj) if obj else None

    def compress(self, step, offset=0):
        if np.isinf(step):
            step = 0
        res = lib.tvg_compress(self._obj, step, offset)
        if not res:
            raise MemoryError

class Window(object):
    def __init__(self, obj=None):
        if obj is None:
            raise NotImplementedError

        self._obj = obj
        if not obj:
            raise MemoryError

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_window(self._obj)

    @property
    def eps(self):
        return self._obj.contents.eps

    @eps.setter
    def eps(self, value):
        lib.window_set_eps(self._obj, value)

    @property
    def ts(self):
        return self._obj.contents.ts

    def clear(self):
        lib.window_clear(self._obj)

    def update(self, ts):
        return Graph(obj=lib.window_update(self._obj, ts))

class MongoDB(object):
    def __init__(self, uri, database, col_articles, article_id, article_time,
                 col_entities, entity_doc, entity_sen, entity_ent, max_distance, obj=None):
        if obj is None:
            config = c_mongodb_config()
            config.uri          = uri.encode("utf-8")
            config.database     = database.encode("utf-8")
            config.col_articles = col_articles.encode("utf-8")
            config.article_id   = article_id.encode("utf-8")
            config.article_time = article_time.encode("utf-8")
            config.col_entities = col_entities.encode("utf-8")
            config.entity_doc   = entity_doc.encode("utf-8")
            config.entity_sen   = entity_sen.encode("utf-8")
            config.entity_ent   = entity_ent.encode("utf-8")
            config.max_distance = max_distance
            obj = lib.alloc_mongodb(config)

        self._obj = obj
        if not obj:
            raise MemoryError

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_mongodb(self._obj)

if __name__ == '__main__':
    import datetime
    import unittest
    import mockupdb

    class LabelsTests(unittest.TestCase):
        def test_map(self):
            l = Labels()

            l[0] = "A"
            l[1] = "B"
            l[2] = "C"
            l[3] = "A"
            l[4] = "C"

            self.assertEqual(len(l), 5)
            self.assertEqual(l[0], "A")
            self.assertEqual(l[1], "B")
            self.assertEqual(l[2], "C")
            self.assertEqual(l[3], "A")
            self.assertEqual(l[4], "C")
            with self.assertRaises(KeyError):
                dummy = l[5]
            indices = l.lookup("A")
            self.assertEqual(indices, [0, 3])
            indices = l.lookup("B")
            self.assertEqual(indices, [1])
            indices = l.lookup("C")
            self.assertEqual(indices, [2, 4])
            indices = l.lookup("D")
            self.assertEqual(indices, [])

            l[0] = "D"

            self.assertEqual(len(l), 5)
            self.assertEqual(l[0], "D")
            indices = l.lookup("A")
            self.assertEqual(indices, [3])
            indices = l.lookup("D")
            self.assertEqual(indices, [0])

            del l[0]

            self.assertEqual(len(l), 4)
            with self.assertRaises(KeyError):
                dummy = l[0]
            indices = l.lookup("D")
            self.assertEqual(indices, [])

            del l

        def test_load(self):
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.labels")
            l = Labels.load(filename)

            self.assertEqual(len(l), 2491)

            self.assertEqual(l[1], "polic")
            self.assertEqual(l[362462], "Jay Wright (basketball)")
            with self.assertRaises(KeyError):
                dummy = l[5]

            indices = l.lookup("polic")
            self.assertEqual(indices, [1])
            indices = l.lookup("Jay Wright (basketball)")
            self.assertEqual(indices, [362462])
            indices = l.lookup("should-not-exist")
            self.assertEqual(indices, [])

            del l

    class VectorTests(unittest.TestCase):
        def test_add_entry(self):
            v = Vector()
            self.assertTrue(v.empty())
            self.assertTrue(v.empty(drop_cache=True))
            revisions = [v.revision]

            for i in range(10):
                v[i] = i * i

            self.assertFalse(v.empty())
            self.assertNotIn(v.revision, revisions)
            revisions.append(v.revision)

            self.assertEqual(v.norm(), math.sqrt(15333.0))
            self.assertEqual(v.norm(drop_cache=True), math.sqrt(15333.0))
            self.assertEqual(v.mul_vector(v), 15333.0)

            for i in range(10):
                self.assertTrue(v.has_entry(i))
                self.assertEqual(v[i], i * i)
                v.add_entry(i, 1.0)
                self.assertEqual(v[i], i * i + 1)
                v.sub_entry(i, 1.0)
                self.assertEqual(v[i], i * i)

            self.assertNotIn(v.revision, revisions)
            revisions.append(v.revision)

            v.mul_const(2.0)

            self.assertNotIn(v.revision, revisions)
            revisions.append(v.revision)

            for i in range(10):
                self.assertTrue(v.has_entry(i))
                self.assertEqual(v[i], 2.0 * i * i)
                del v[i]
                self.assertFalse(v.has_entry(i))
                self.assertEqual(v[i], 0.0)

            self.assertTrue(v.empty())
            self.assertNotIn(v.revision, revisions)
            del v

        def test_batch(self):
            test_indices = np.array([0, 1, 2])
            test_weights = np.array([1.0, 2.0, 3.0])

            v = Vector()
            self.assertEqual(v.flags, 0)

            v.add_entries([], [])
            v.add_entries(test_indices, test_weights)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [1.0, 2.0, 3.0])

            self.assertEqual(v.num_entries, 3)
            self.assertEqual(len(v), 3)

            indices, _ = v.entries(ret_weights=False)
            self.assertEqual(indices.tolist(), [0, 1, 2])

            _, weights = v.entries(ret_indices=False)
            self.assertEqual(weights.tolist(), [1.0, 2.0, 3.0])

            v.add_entries([], [])
            v.add_entries(test_indices, test_weights)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [2.0, 4.0, 6.0])

            v.sub_entries([], [])
            v.sub_entries(test_indices, -test_weights)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [3.0, 6.0, 9.0])

            v.set_entries([], [])
            v.set_entries(test_indices, test_weights)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [1.0, 2.0, 3.0])

            v.del_entries([])
            v.del_entries(test_indices)
            self.assertEqual(v.entries()[0].tolist(), [])
            self.assertEqual(v.num_entries, 0)
            self.assertEqual(len(v), 0)

            for i in range(1000):
                v.add_entry(i, 1.0)
            indices, _ = v.entries(ret_weights=False)
            indices = list(indices)
            for i in range(1000):
                self.assertIn(i, indices)
                indices.remove(i)
            self.assertEqual(len(indices), 0)
            self.assertEqual(v.num_entries, 1000)
            self.assertEqual(len(v), 1000)

            del v

        def test_flags(self):
            v = Vector()
            self.assertEqual(v.flags, 0)
            v[0] = 0.0
            self.assertTrue(v.has_entry(0))
            v.add_entry(0, 1.0)
            self.assertEqual(v[0], 1.0)
            v.add_entry(0, -1.0)
            self.assertTrue(v.has_entry(0))
            self.assertEqual(v[0], 0.0)
            v.sub_entry(0, 1.0)
            self.assertEqual(v[0], -1.0)
            v.sub_entry(0, -1.0)
            self.assertTrue(v.has_entry(0))
            self.assertEqual(v[0], 0.0)
            del v

            v = Vector(nonzero=True)
            self.assertEqual(v.flags, TVG_FLAGS_NONZERO)
            self.assertEqual(v.eps, 0.0)
            v[0] = 0.0
            self.assertFalse(v.has_entry(0))
            v.add_entry(0, 1.0)
            self.assertEqual(v[0], 1.0)
            v.add_entry(0, -0.75)
            self.assertEqual(v[0], 0.25)
            v.add_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, 1.0)
            self.assertEqual(v[0], -1.0)
            v.sub_entry(0, -0.75)
            self.assertEqual(v[0], -0.25)
            v.sub_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            del v

            v = Vector(nonzero=True)
            v.eps = 0.5
            self.assertEqual(v.flags, TVG_FLAGS_NONZERO)
            self.assertEqual(v.eps, 0.5)
            v[0] = 0.0
            self.assertFalse(v.has_entry(0))
            v.add_entry(0, 1.0)
            self.assertEqual(v[0], 1.0)
            v.add_entry(0, -0.25)
            self.assertEqual(v[0], 0.75)
            v.add_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, 1.0)
            self.assertEqual(v[0], -1.0)
            v.sub_entry(0, -0.25)
            self.assertEqual(v[0], -0.75)
            v.sub_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            del v

            v = Vector(positive=True)
            self.assertEqual(v.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(v.eps, 0.0)
            v[0] = 0.0
            self.assertFalse(v.has_entry(0))
            v.add_entry(0, 1.0)
            self.assertEqual(v[0], 1.0)
            v.add_entry(0, -0.75)
            self.assertEqual(v[0], 0.25)
            v.add_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, 1.0)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, -0.25)
            self.assertEqual(v[0], 0.25)
            del v

            v = Vector(positive=True)
            v.eps = 0.5
            self.assertEqual(v.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(v.eps, 0.5)
            v[0] = 0.0
            self.assertFalse(v.has_entry(0))
            v.add_entry(0, 1.0)
            self.assertEqual(v[0], 1.0)
            v.add_entry(0, -0.25)
            self.assertEqual(v[0], 0.75)
            v.add_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, 1.0)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, -0.25)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, -0.5)
            self.assertFalse(v.has_entry(0))
            v.sub_entry(0, -0.75)
            self.assertEqual(v[0], 0.75)
            del v

        def test_mul_const(self):
            v = Vector()
            v[0] = 1.0
            v.mul_const(-1.0)
            self.assertEqual(v[0], -1.0)
            v.mul_const(0.0)
            self.assertTrue(v.has_entry(0))
            self.assertEqual(v[0], 0.0)
            del v

            v = Vector(nonzero=True)
            v[0] = 1.0
            v.mul_const(-1.0)
            self.assertEqual(v[0], -1.0)
            v.mul_const(0.0)
            self.assertFalse(v.has_entry(0))
            del v

            v = Vector(positive=True)
            v[0] = 1.0
            v.mul_const(-1.0)
            self.assertFalse(v.has_entry(0))
            del v

            v = Vector(positive=True)
            v[0] = 1.0
            for i in range(200):
                v.mul_const(0.5)
                if not v.has_entry(0):
                    break
            else:
                self.assertTrue(False)

        def test_repr(self):
            v = Vector()
            self.assertEqual(repr(v), "Vector({})")
            for i in range(10):
                v[i] = 1.0
            expected = "Vector({0: X, 1: X, 2: X, 3: X, 4: X, 5: X, 6: X, 7: X, 8: X, 9: X})"
            self.assertEqual(repr(v).replace("1.000000", "X"), expected)
            v[10] = 2.0
            expected = "Vector({0: X, 1: X, 2: X, 3: X, 4: X, 5: X, 6: X, 7: X, 8: X, 9: X, ...})"
            self.assertEqual(repr(v).replace("1.000000", "X"), expected)
            del v

    class GraphTests(unittest.TestCase):
        def test_add_edge(self):
            g = Graph(directed=True)
            self.assertTrue(g.empty())
            self.assertTrue(g.empty(drop_cache=True))
            revisions = [g.revision]
            mem = g.memory_usage

            for i in range(100):
                s, t = i//10, i%10
                g[s, t] = i

            self.assertFalse(g.empty())
            self.assertNotIn(g.revision, revisions)
            self.assertGreater(g.memory_usage, mem)
            revisions.append(g.revision)

            for i in range(100):
                s, t = i//10, i%10
                self.assertTrue(i == 0 or g.has_edge((s, t)))
                self.assertEqual(g[s, t], i)
                g.add_edge((s, t), 1.0)
                self.assertEqual(g[s, t], i + 1)
                g.sub_edge((s, t), 1.0)
                self.assertEqual(g[s, t], i)

            self.assertNotIn(g.revision, revisions)
            revisions.append(g.revision)

            g.mul_const(2.0)

            self.assertNotIn(g.revision, revisions)
            revisions.append(g.revision)

            for i in range(100):
                s, t = i//10, i%10
                self.assertTrue(i == 0 or g.has_edge((s, t)))
                self.assertEqual(g[s, t], 2.0 * i)
                del g[s, t]
                self.assertFalse(g.has_edge((s, t)))
                self.assertEqual(g[s, t], 0.0)

            self.assertTrue(g.empty())
            self.assertNotIn(g.revision, revisions)
            del g

        def test_power_iteration(self):
            g = Graph(directed=True)
            g[0, 0] = 0.5
            g[0, 1] = 0.5
            g[1, 0] = 0.2
            g[1, 1] = 0.8
            v, e = g.power_iteration()
            self.assertTrue(abs(e - 1.0) < 1e-7)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-7)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-7)
            del v
            v, _ = g.power_iteration(ret_eigenvalue=False)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-7)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-7)
            del v

            g.mul_const(-1)

            v, e = g.power_iteration()
            self.assertTrue(abs(e + 1.0) < 1e-7)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-7)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-7)
            del v
            v, _ = g.power_iteration(ret_eigenvalue=False)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-7)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-7)
            del v

            del g

        def test_batch(self):
            test_indices = np.array([[0, 1], [1, 2], [2, 0]])
            test_weights = np.array([1.0, 2.0, 3.0])

            g = Graph(directed=True)
            self.assertEqual(g.flags, TVG_FLAGS_DIRECTED)

            g.add_edges([], [])
            g.add_edges(test_indices, test_weights)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [3.0, 1.0, 2.0])
            self.assertEqual(g.num_edges, 3)
            self.assertEqual(len(g), 3)
            self.assertEqual(g.nodes().tolist(), [0, 1, 2])
            self.assertEqual(g.num_nodes, 3)

            indices, _ = g.edges(ret_weights=False)
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])

            _, weights = g.edges(ret_indices=False)
            self.assertEqual(weights.tolist(), [3.0, 1.0, 2.0])

            for i in range(3):
                indices, weights = g.adjacent_edges(i)
                self.assertEqual(indices.tolist(), [(i + 1) % 3])
                self.assertEqual(weights.tolist(), [i + 1.0])

                indices, _ = g.adjacent_edges(i, ret_weights=False)
                self.assertEqual(indices.tolist(), [(i + 1) % 3])

                _, weights = g.adjacent_edges(i, ret_indices=False)
                self.assertEqual(weights.tolist(), [i + 1.0])

            g.add_edges([], [])
            g.add_edges(test_indices, test_weights)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [6.0, 2.0, 4.0])

            g.sub_edges([], [])
            g.sub_edges(test_indices, -test_weights)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [9.0, 3.0, 6.0])

            g.set_edges([], [])
            g.set_edges(test_indices, test_weights)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [3.0, 1.0, 2.0])

            g.del_edges([])
            g.del_edges(test_indices)
            self.assertEqual(g.edges()[0].tolist(), [])
            self.assertEqual(g.num_edges, 0)
            self.assertEqual(len(g), 0)
            self.assertEqual(g.nodes().tolist(), [])
            self.assertEqual(g.num_nodes, 0)

            for i in range(1000):
                g.add_edge((i, i + 1), 1.0)
            indices, _ = g.edges(ret_weights=False)
            indices = [tuple(x) for x in indices]
            for i in range(1000):
                self.assertIn((i, i + 1), indices)
                indices.remove((i, i + 1))
            self.assertEqual(len(indices), 0)
            self.assertEqual(g.num_edges, 1000)
            self.assertEqual(len(g), 1000)

            del g

        def test_directed(self):
            g = Graph(directed=True)
            g[1, 1] = 2.0
            g[1, 2] = 1.0
            self.assertEqual(g[1, 1], 2.0)
            self.assertEqual(g[1, 2], 1.0)
            self.assertEqual(g[2, 1], 0.0)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[1, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [2.0, 1.0])
            self.assertEqual(g.num_edges, 2)
            self.assertEqual(g.nodes().tolist(), [1, 2])
            self.assertEqual(g.num_nodes, 2)
            del g

        def test_undirected(self):
            g = Graph(directed=False)
            g[1, 1] = 2.0
            g[1, 2] = 1.0
            self.assertEqual(g[1, 1], 2.0)
            self.assertEqual(g[1, 2], 1.0)
            self.assertEqual(g[2, 1], 1.0)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[1, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [2.0, 1.0])
            self.assertEqual(g.num_edges, 2)
            self.assertEqual(g.nodes().tolist(), [1, 2])
            self.assertEqual(g.num_nodes, 2)
            del g

        def test_flags(self):
            g = Graph()
            self.assertEqual(g.flags, 0)
            g[0, 0] = 0.0
            self.assertTrue(g.has_edge((0, 0)))
            g.add_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], 1.0)
            g.add_edge((0, 0), -1.0)
            self.assertTrue(g.has_edge((0, 0)))
            self.assertEqual(g[0, 0], 0.0)
            g.sub_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], -1.0)
            g.sub_edge((0, 0), -1.0)
            self.assertTrue(g.has_edge((0, 0)))
            self.assertEqual(g[0, 0], 0.0)
            del g

            g = Graph(nonzero=True)
            self.assertEqual(g.flags, TVG_FLAGS_NONZERO)
            self.assertEqual(g.eps, 0.0)
            g[0, 0] = 0.0
            self.assertFalse(g.has_edge((0, 0)))
            g.add_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], 1.0)
            g.add_edge((0, 0), -0.75)
            self.assertEqual(g[0, 0], 0.25)
            g.add_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], -1.0)
            g.sub_edge((0, 0), -0.75)
            self.assertEqual(g[0, 0], -0.25)
            g.sub_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            del g

            g = Graph(nonzero=True)
            g.eps = 0.5
            self.assertEqual(g.flags, TVG_FLAGS_NONZERO)
            self.assertEqual(g.eps, 0.5)
            g[0, 0] = 0.0
            self.assertFalse(g.has_edge((0, 0)))
            g.add_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], 1.0)
            g.add_edge((0, 0), -0.25)
            self.assertEqual(g[0, 0], 0.75)
            g.add_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], -1.0)
            g.sub_edge((0, 0), -0.25)
            self.assertEqual(g[0, 0], -0.75)
            g.sub_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            del g

            g = Graph(positive=True)
            self.assertEqual(g.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g.eps, 0.0)
            g[0, 0] = 0.0
            self.assertFalse(g.has_edge((0, 0)))
            g.add_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], 1.0)
            g.add_edge((0, 0), -0.75)
            self.assertEqual(g[0, 0], 0.25)
            g.add_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), 1.0)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), -0.25)
            self.assertEqual(g[0, 0], 0.25)
            del g

            g = Graph(positive=True)
            g.eps = 0.5
            self.assertEqual(g.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g.eps, 0.5)
            g[0, 0] = 0.0
            self.assertFalse(g.has_edge((0, 0)))
            g.add_edge((0, 0), 1.0)
            self.assertEqual(g[0, 0], 1.0)
            g.add_edge((0, 0), -0.25)
            self.assertEqual(g[0, 0], 0.75)
            g.add_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), 1.0)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), -0.25)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), -0.5)
            self.assertFalse(g.has_edge((0, 0)))
            g.sub_edge((0, 0), -0.75)
            self.assertEqual(g[0, 0], 0.75)
            del g

        def test_bfs(self):
            g = Graph(directed=True)
            g[0, 1] = 1.0
            g[1, 2] = 1.0
            g[2, 3] = 1.0
            g[3, 4] = 1.5
            g[2, 4] = 1.5

            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[0, 1], [1, 2], [2, 3], [2, 4], [3, 4]])
            self.assertEqual(weights.tolist(), [1.0, 1.0, 1.0, 1.5, 1.5])

            results = g.bfs_count(0, max_count=2)
            self.assertEqual(results, [(0.0, 0, None, 0), (1.0, 1, 0, 1), (2.0, 2, 1, 2)])
            results = g.bfs_count(0)
            self.assertEqual(results, [(0.0, 0, None, 0), (1.0, 1, 0, 1), (2.0, 2, 1, 2), (3.0, 3, 2, 3), (3.5, 3, 2, 4)])

            results = g.bfs_weight(0, max_weight=2.0)
            self.assertEqual(results, [(0.0, 0, None, 0), (1.0, 1, 0, 1), (2.0, 2, 1, 2)])
            results = g.bfs_weight(0)
            self.assertEqual(results, [(0.0, 0, None, 0), (1.0, 1, 0, 1), (2.0, 2, 1, 2), (3.0, 3, 2, 3), (3.5, 3, 2, 4)])

            del g

        def test_mul_const(self):
            g = Graph()
            g[0, 0] = 1.0
            g.mul_const(-1.0)
            self.assertEqual(g[0, 0], -1.0)
            g.mul_const(0.0)
            self.assertTrue(g.has_edge((0, 0)))
            self.assertEqual(g[0, 0], 0.0)
            del g

            g = Graph(nonzero=True)
            g[0, 0] = 1.0
            g.mul_const(-1.0)
            self.assertEqual(g[0, 0], -1.0)
            g.mul_const(0.0)
            self.assertFalse(g.has_edge((0, 0)))
            del g

            g = Graph(positive=True)
            g[0, 0] = 1.0
            g.mul_const(-1.0)
            self.assertFalse(g.has_edge((0, 0)))
            del g

            g = Graph(positive=True)
            g[0, 0] = 1.0
            for i in range(200):
                g.mul_const(0.5)
                if not g.has_edge((0, 0)):
                    break
            else:
                self.assertTrue(False)

        def test_delta(self):
            g = Graph()
            g[0, 0] = 1.0
            g[0, 1] = 2.0
            g[0, 2] = 3.0
            g.enable_delta()
            del g[0, 0]
            g[0, 1] = 3.0
            g.mul_const(2.0)
            d, m = g.get_delta()
            self.assertNotEqual(d, None)
            self.assertEqual(m, 2.0)
            indices, weights = d.edges()
            self.assertEqual(indices.tolist(), [[0, 0], [0, 1]])
            self.assertEqual(weights.tolist(), [0.0, 6.0])
            g.disable_delta()
            d, m = g.get_delta()
            self.assertEqual(d, None)
            self.assertEqual(m, None)
            del g

            g = Graph(directed=True)
            g[0, 0] = 1.0
            g[0, 1] = 2.0
            g[0, 2] = 3.0
            g.enable_delta()
            del g[0, 0]
            g[0, 1] = 3.0
            g.mul_const(2.0)
            d, m = g.get_delta()
            self.assertNotEqual(d, None)
            self.assertEqual(m, 2.0)
            indices, weights = d.edges()
            self.assertEqual(indices.tolist(), [[0, 0], [0, 1]])
            self.assertEqual(weights.tolist(), [0.0, 6.0])
            g.disable_delta()
            d, m = g.get_delta()
            self.assertEqual(d, None)
            self.assertEqual(m, None)
            del g

        def test_weights(self):
            g = Graph(directed=True)
            g[0, 0] = 1.0
            g[0, 1] = 2.0
            g[1, 0] = 3.0

            d = g.in_degrees()
            indices, weights = d.entries()
            self.assertEqual(indices.tolist(), [0, 1])
            self.assertEqual(weights.tolist(), [2.0, 1.0])
            d = g.in_weights()
            indices, weights = d.entries()
            self.assertEqual(indices.tolist(), [0, 1])
            self.assertEqual(weights.tolist(), [4.0, 2.0])

            d = g.out_degrees()
            indices, weights = d.entries()
            self.assertEqual(indices.tolist(), [0, 1])
            self.assertEqual(weights.tolist(), [2.0, 1.0])
            d = g.out_weights()
            indices, weights = d.entries()
            self.assertEqual(indices.tolist(), [0, 1])
            self.assertEqual(weights.tolist(), [3.0, 3.0])
            del g

        def test_anomalies(self):
            g = Graph(directed=False)

            a = g.degree_anomalies()
            indices, weights = a.entries()
            self.assertEqual(indices.tolist(), [])
            self.assertEqual(weights.tolist(), [])
            a = g.weight_anomalies()
            indices, weights = a.entries()
            self.assertEqual(indices.tolist(), [])
            self.assertEqual(weights.tolist(), [])

            c = 0
            for i in range(5):
                for j in range(i + 1):
                    if c % 3 != 0: g[i, j] = c
                    c += 1

            a = g.degree_anomalies()
            indices, weights = a.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2, 3, 4])
            self.assertEqual(weights.tolist(), [-2.5, 1.5999999046325684, -0.6666667461395264, -1.0, 0.5])
            a = g.weight_anomalies()
            indices, weights = a.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2, 3, 4])
            self.assertEqual(weights.tolist(), [-34.90909194946289,-9.119998931884766, -7.0588226318359375,
                                                -5.392856597900391, 18.39583396911621])
            del g

        def test_repr(self):
            g = Graph()
            self.assertEqual(repr(g), "Graph({})")
            for i in range(10):
                g[1, i] = 1.0
            expected = "Graph({(0, 1): X, (1, 1): X, (1, 2): X, (1, 3): X, (1, 4): X, (1, 5): X, (1, 6): X, (1, 7): X, (1, 8): X, (1, 9): X})"
            self.assertEqual(repr(g).replace("1.000000", "X"), expected)
            g[1, 10] = 2.0
            expected = "Graph({(0, 1): X, (1, 1): X, (1, 2): X, (1, 3): X, (1, 4): X, (1, 5): X, (1, 6): X, (1, 7): X, (1, 8): X, (1, 9): X, ...})"
            self.assertEqual(repr(g).replace("1.000000", "X"), expected)
            del g

    class TVGTests(unittest.TestCase):
        def test_lookup(self):
            tvg = TVG(positive=True)
            self.assertEqual(tvg.flags, TVG_FLAGS_POSITIVE)

            g1 = tvg.Graph(100)
            self.assertEqual(g1.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g1.ts, 100)
            g2 = tvg.Graph(200)
            self.assertEqual(g2.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g2.ts, 200)
            g3 = tvg.Graph(300)
            self.assertEqual(g3.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g3.ts, 300)

            g = tvg.lookup_le(50)
            self.assertEqual(g, None)
            g = tvg.lookup_ge(50)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))

            g = tvg.lookup_le(150)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))
            g = tvg.lookup_ge(150)
            self.assertEqual(addressof(g._obj.contents), addressof(g2._obj.contents))

            g = tvg.lookup_le(250)
            self.assertEqual(addressof(g._obj.contents), addressof(g2._obj.contents))
            g = tvg.lookup_ge(250)
            self.assertEqual(addressof(g._obj.contents), addressof(g3._obj.contents))

            g = tvg.lookup_le(350)
            self.assertEqual(addressof(g._obj.contents), addressof(g3._obj.contents))
            g = tvg.lookup_ge(350)
            self.assertEqual(g, None)

            g = tvg.lookup_near(149)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))
            g = tvg.lookup_near(151)
            self.assertEqual(addressof(g._obj.contents), addressof(g2._obj.contents))

            # For backwards compatibility, we still allow passing float values.

            g = tvg.lookup_ge(100.0)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))
            g = tvg.lookup_ge(100.01)
            self.assertEqual(addressof(g._obj.contents), addressof(g2._obj.contents))

            g = tvg.lookup_le(200.0)
            self.assertEqual(addressof(g._obj.contents), addressof(g2._obj.contents))
            g = tvg.lookup_le(199.99)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))

            g = tvg.lookup_near(149.49)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))
            g = tvg.lookup_near(150.51)
            self.assertEqual(addressof(g._obj.contents), addressof(g2._obj.contents))

            del tvg

        def test_link(self):
            tvg = TVG()
            g1 = Graph()
            g2 = Graph(directed=True)

            tvg.link(g1, 10)
            with self.assertRaises(RuntimeError):
                tvg.link(g1, 20)
            with self.assertRaises(RuntimeError):
                tvg.link(g2, 20)

            g = tvg.lookup_near(10)
            self.assertEqual(g.ts, 10)
            self.assertEqual(addressof(g._obj.contents), addressof(g1._obj.contents))
            del tvg

        def test_compress(self):
            source = np.random.rand(100)

            tvg = TVG(positive=True)

            for t, s in enumerate(source):
                g = tvg.Graph(t)
                g[0, 0] = s

            tvg.compress(step=5, offset=100)

            t = 0
            for g in tvg:
                self.assertEqual(g.ts, t)
                self.assertTrue(abs(g[0, 0] - np.sum(source[t:t+5])) < 1e-6)
                t += 5

            del tvg

        def test_load(self):
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.graph")
            tvg = TVG.load(filename)

            timestamps = []
            edges = []
            for g in tvg:
                self.assertEqual(g.revision, 0)
                timestamps.append(g.ts)
                edges.append(g.num_edges)

            self.assertEqual(timestamps, [      0,  130000,  141000,  164000,  176000,  272000,  376000,  465000,  666000,  682000,  696000,
                                           770000,  848000, 1217000, 1236000, 1257000, 1266000, 1431000, 1515000, 1539000, 1579000, 1626000,
                                          1763000, 1803000, 1834000, 1920000, 1967000, 2021000, 2188000, 2405000, 2482000, 2542000, 2551000,
                                          2583000, 2591000, 2604000, 2620000, 2830000, 2852000, 2957000, 3008000])

            self.assertEqual(edges, [155, 45, 1250, 90, 178, 85, 367, 98, 18, 528, 158, 201, 267, 214, 613, 567, 1, 137, 532, 59, 184,
                                     40, 99, 285, 326, 140, 173, 315, 211, 120, 19, 137, 170, 42, 135, 348, 168, 132, 147, 218, 321])

            g = tvg.lookup_near(141000)
            self.assertTrue(abs(g[6842, 249977] - 0.367879) < 1e-7)

            g = tvg.lookup_near(1257000)
            self.assertTrue(abs(g[1291, 3529] - 1.013476) < 1e-7)

            g = tvg.lookup_near(2604000)
            self.assertTrue(abs(g[121, 1154] - 3.000000) < 1e-7)

            tvg.compress(step=600000)

            timestamps = []
            edges = []
            for g in tvg:
                timestamps.append(g.ts)
                edges.append(g.num_edges)

            self.assertEqual(timestamps, [0, 600000, 1200000, 1800000, 2400000, 3000000])
            self.assertEqual(edges, [2226, 1172, 2446, 1448, 1632, 321])

            timestamps = []
            edges = []
            for g in reversed(tvg):
                timestamps.append(g.ts)
                edges.append(g.num_edges)

            self.assertEqual(timestamps, [3000000, 2400000, 1800000, 1200000, 600000, 0])
            self.assertEqual(edges, [321, 1632, 1448, 2446, 1172, 2226])

            tvg.compress(step=np.inf, offset=100000)

            timestamps = []
            edges = []
            for g in tvg:
                timestamps.append(g.ts)
                edges.append(g.num_edges)

            self.assertEqual(timestamps, [100000])
            self.assertEqual(edges, [9097])

            del tvg

    class WindowTests(unittest.TestCase):
        def test_rect(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[0, 1] = 2.0
            g = tvg.Graph(300)
            g[0, 2] = 3.0

            with self.assertRaises(MemoryError):
                tvg.WindowRect(0, 0)
            with self.assertRaises(MemoryError):
                tvg.WindowRect(1, 0)

            window = tvg.WindowRect(-50, 50)

            g = window.update(100)
            self.assertEqual(window.ts, 100)
            self.assertEqual(g[0, 0], 1.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 0.0)

            g = window.update(200)
            self.assertEqual(window.ts, 200)
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 2.0)
            self.assertEqual(g[0, 2], 0.0)

            g = window.update(300)
            self.assertEqual(window.ts, 300)
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 3.0)

            # Clearing the window should not modify the last output graph.
            window.clear()
            g2 = window.update(100)
            self.assertEqual(window.ts, 100)

            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 3.0)

            self.assertEqual(g2[0, 0], 1.0)
            self.assertEqual(g2[0, 1], 0.0)
            self.assertEqual(g2[0, 2], 0.0)

            del window
            del tvg

        def test_rect_streaming(self):
            tvg = TVG(positive=True, streaming=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[0, 1] = 2.0
            g = tvg.Graph(300)
            g[0, 2] = 3.0

            window = tvg.WindowRect(-50, 50)

            g = window.update(100)
            self.assertEqual(window.ts, 100)
            self.assertEqual(g[0, 0], 1.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 0.0)
            d, m = g.get_delta()
            self.assertEqual(d, None)
            self.assertEqual(m, None)

            g = window.update(200)
            self.assertEqual(window.ts, 200)
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 2.0)
            self.assertEqual(g[0, 2], 0.0)
            d, m = g.get_delta()
            self.assertNotEqual(d, None)
            self.assertEqual(m, 1.0)
            indices, weights = d.edges()
            self.assertEqual(indices.tolist(), [[0, 0], [0, 1]])
            self.assertEqual(weights.tolist(), [0.0, 2.0])

            g = window.update(300)
            self.assertEqual(window.ts, 300)
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 3.0)
            d, m = g.get_delta()
            self.assertNotEqual(d, None)
            self.assertEqual(m, 1.0)
            indices, weights = d.edges()
            self.assertEqual(indices.tolist(), [[0, 1], [0, 2]])
            self.assertEqual(weights.tolist(), [0.0, 3.0])

            # Clearing the window should not modify the last output graph.
            window.clear()
            g2 = window.update(100)
            self.assertEqual(window.ts, 100)

            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 3.0)

            self.assertEqual(d[0, 0], 0.0)
            self.assertEqual(d[0, 1], 0.0)
            self.assertEqual(d[0, 2], 3.0)

            self.assertEqual(g2[0, 0], 1.0)
            self.assertEqual(g2[0, 1], 0.0)
            self.assertEqual(g2[0, 2], 0.0)

            del window
            del tvg

        def test_decay_precision(self):
            tvg = TVG(positive=True)
            beta = 0.3

            g = tvg.Graph(0)
            g[0, 0] = 1.0

            with self.assertRaises(MemoryError):
                tvg.WindowDecay(0, beta)
            with self.assertRaises(MemoryError):
                tvg.WindowDecay(-1, beta)

            window = tvg.WindowDecay(np.inf, beta)

            g = window.update(100)
            self.assertTrue(abs(g[0, 0] - math.pow(beta, 100.0)) < 1e-7)

            g = window.update(0)
            self.assertTrue(abs(g[0, 0] - 1.0) < 1e-7)

            del window
            del g

        def test_smooth(self):
            source = np.random.rand(100)
            beta = 0.3

            tvg = TVG(positive=True)

            for t, s in enumerate(source):
                g = tvg.Graph(t)
                g[0, 0] = s

            with self.assertRaises(MemoryError):
                tvg.WindowSmooth(0, beta)
            with self.assertRaises(MemoryError):
                tvg.WindowSmooth(-1, beta)

            window = tvg.WindowSmooth(np.inf, beta)
            expected = 0.0
            for t, s in enumerate(source):
                g = window.update(t)
                self.assertEqual(window.ts, t)
                expected = beta * expected + (1.0 - beta) * s
                self.assertTrue(abs(g[0, 0] - expected) < 1e-6)
            del window

            window = tvg.WindowSmooth(np.inf, log_beta=math.log(beta))
            expected = 0.0
            for t, s in enumerate(source):
                g = window.update(t)
                self.assertEqual(window.ts, t)
                expected = beta * expected + (1.0 - beta) * s
                self.assertTrue(abs(g[0, 0] - expected) < 1e-6)
            del window
            del tvg

        def test_smooth_streaming(self):
            source = np.random.rand(100)
            beta = 0.3

            tvg = TVG(positive=True, streaming=True)

            for t, s in enumerate(source):
                g = tvg.Graph(t)
                g[0, 0] = s
                if (t % 10) == 0:
                    g[0, 1] = 1.0

            window = tvg.WindowSmooth(np.inf, beta)
            expected = 0.0
            for t, s in enumerate(source):
                g = window.update(t)
                self.assertEqual(window.ts, t)
                expected = beta * expected + (1.0 - beta) * s
                self.assertTrue(abs(g[0, 0] - expected) < 1e-6)
                d, m = g.get_delta()
                if t == 0:
                    self.assertEqual(d, None)
                    self.assertEqual(m, None)
                    continue

                self.assertNotEqual(d, None)
                self.assertTrue(abs(m - beta) < 1e-6)
                indices, weights = d.edges()
                if (t % 10) == 0:
                    self.assertEqual(indices.tolist(), [[0, 0], [0, 1]])
                    self.assertEqual(weights.tolist(), [g[0, 0], g[0, 1]])
                else:
                    self.assertEqual(indices.tolist(), [[0, 0]])
                    self.assertEqual(weights.tolist(), [g[0, 0]])

            del window
            del tvg

        def test_encode_visjs(self):
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.graph")
            tvg = TVG.load(filename, positive=True, streaming=True)
            window = tvg.WindowDecay(600000, log_beta=np.log(0.93)/1000)
            window.eps = 1e-6

            ts = tvg.lookup_ge().ts
            last_ts = tvg.lookup_le().ts + 600000.0

            client_graph = None
            client_nodes = set()

            while ts < last_ts:
                graph = window.update(ts)
                visjs = graph.encode_visjs()

                if visjs['cmd'] == 'network_set':
                    client_nodes = set([node['id'] for node in visjs['nodes']])
                    client_graph = Graph()
                    for edge in visjs['edges']:
                        self.assertEqual(edge['id'], "%d-%d" % (edge['from'], edge['to']))
                        client_graph[edge['from'], edge['to']] = edge['value']

                elif visjs['cmd'] == 'network_update':
                    for edge in visjs['deleted_edges']:
                        edge_from, edge_to = map(int, edge['id'].split("-"))
                        del client_graph[edge_from, edge_to]
                    for node in visjs['deleted_nodes']:
                        try:
                            client_nodes.remove(node['id'])
                        except KeyError:
                            pass # FIXME: Why can this happen?
                    client_graph.mul_const(visjs['mul'])
                    for node in visjs['nodes']:
                        client_nodes.add(node['id'])
                    for edge in visjs['edges']:
                        self.assertEqual(edge['id'], "%d-%d" % (edge['from'], edge['to']))
                        client_graph[edge['from'], edge['to']] = edge['value']

                else:
                    self.assertTrue(False)

                self.assertEqual(client_nodes, set(graph.nodes()))
                self.assertEqual(client_nodes, set(client_graph.nodes()))

                indices, weights = client_graph.edges()
                index_to_weight = {}
                for i, w in zip(indices, weights):
                    index_to_weight[tuple(i)] = w

                indices, weights = graph.edges()
                for i, w in zip(indices, weights):
                    i = tuple(i)
                    self.assertIn(i, index_to_weight)
                    self.assertTrue(abs(index_to_weight[i] - w) < 1e-7)
                    del index_to_weight[i]

                self.assertEqual(len(index_to_weight), 0)
                ts += 50000

    class MongoDBTests(unittest.TestCase):
        def setUp(self):
            self.s = mockupdb.MockupDB()
            self.s.run()

            future = mockupdb.go(MongoDB, self.s.uri, "database", "col_articles",
                                 "_id", "time", "col_entities", "doc", "sen", "ent", 5)

            request = self.s.receives("isMaster")
            request.replies({'ok': 1, 'maxWireVersion': 5})

            request = self.s.receives("ping")
            request.replies({'ok': 1})

            self.db = future()

        def tearDown(self):
            self.s.stop()

        def load_from_occurrences(self, occurrences):
            future = mockupdb.go(Graph.load_from_mongodb, self.db, 1337)

            request = self.s.receives()
            self.assertEqual(request["find"], "col_entities")
            self.assertEqual(request["filter"], {'doc': 1337})
            self.assertEqual(request["sort"], {'sen': 1})
            request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            return future()

        def test_invalid(self):
            with self.assertRaises(MemoryError):
                MongoDB("http://localhost", "database", "col_articles",
                        "_id", "time", "col_entities", "doc", "sen", "ent", 5)

        def test_selfloop(self):
            occurrences = []
            for i in range(10):
                occurrences.append({'sen': i, 'ent': 1})
                occurrences.append({'sen': i, 'ent': 1})
            g = self.load_from_occurrences(occurrences)
            self.assertEqual(g.num_edges, 0)

        def test_max_distance(self):
            for i in range(10):
                occurrences = [{'sen': 1,     'ent': 1},
                               {'sen': 1 + i, 'ent': 2},
                               {              'ent': 1}, # no sen
                               {'sen': 1              }] # no ent
                g = self.load_from_occurrences(occurrences)
                if i <= 5:
                    self.assertEqual(g.num_edges, 1)
                    self.assertTrue(abs(g[1, 2]/math.exp(-i) - 1.0) < 1e-7)
                else:
                    self.assertEqual(g.num_edges, 0)

        def test_weight_sum(self):
            for i in range(10):
                occurrences = [{'sen': 1,     'ent': 1    },
                               {'sen': 1,     'ent': "Q1" },
                               {'sen': 1 + i, 'ent': 2    },
                               {              'ent': 1    }, # no sen
                               {'sen': 1                  }] # no ent
                g = self.load_from_occurrences(occurrences)
                if i <= 5:
                    self.assertEqual(g.num_edges, 1)
                    self.assertTrue(abs(g[1, 2]/(2.0 * math.exp(-i)) - 1.0) < 1e-7)
                else:
                    self.assertEqual(g.num_edges, 0)

        def test_load(self):
            future = mockupdb.go(TVG.load, self.db)

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', 1), ('_id', 1)]))
            documents = [{'_id': 10, 'time': datetime.datetime.utcfromtimestamp(1546300800)},
                         {'_id': 11, 'time': datetime.datetime.utcfromtimestamp(1546387200)},
                         {'_id': 12, 'time': datetime.datetime.utcfromtimestamp(1546473600)},
                         {           'time': datetime.datetime.utcfromtimestamp(1546560000)}, # no id
                         {'_id': 14                                                        }] # no time
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            for i in range(3):
                request = self.s.receives()
                self.assertEqual(request["find"], "col_entities")
                self.assertEqual(request["filter"], {'doc': 10 + i})
                self.assertEqual(request["sort"], {'sen': 1})
                occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 2 + i}]
                request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            tvg = future()
            for i, g in enumerate(tvg):
                self.assertEqual(g.revision, 0)
                self.assertEqual(g.ts, 1546300800000 + i * 86400000)
                self.assertEqual(g[1, 2 + i], 1.0)
            del tvg

        def test_sync(self):
            tvg = TVG()
            tvg.enable_mongodb_sync(self.db, batch_size=2, cache_size=0x8000) # 32 kB cache

            future = mockupdb.go(tvg.lookup_ge, 0)

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {'time': {'$gte': datetime.datetime.utcfromtimestamp(0)}})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', 1), ('_id', 1)]))
            self.assertEqual(request["limit"], 2)
            documents = [{'_id': 10, 'time': datetime.datetime.utcfromtimestamp(1546300800)},
                         {'_id': 11, 'time': datetime.datetime.utcfromtimestamp(1546387200)}]
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            for i in range(2):
                request = self.s.receives()
                self.assertEqual(request["find"], "col_entities")
                self.assertEqual(request["filter"], {'doc': 10 + i})
                self.assertEqual(request["sort"], {'sen': 1})
                occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 2 + i}]
                request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            g = future()
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, 0)
            self.assertEqual(g.ts, 1546300800000)
            self.assertEqual(g[1, 2], 1.0)

            g = g.next
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546387200000)
            self.assertEqual(g[1, 3], 1.0)

            future = mockupdb.go(getattr, g, 'next')

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {"$or": [{"time": {"$gt": datetime.datetime.utcfromtimestamp(1546387200)}},
                                                         {"time": datetime.datetime.utcfromtimestamp(1546387200), "_id": {"$gt": 11}}]})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', 1), ('_id', 1)]))
            self.assertEqual(request["limit"], 2)
            documents = [{'_id': 12, 'time': datetime.datetime.utcfromtimestamp(1546473600)},
                         {'_id': 13, 'time': datetime.datetime.utcfromtimestamp(1546560000)}]
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            for i in range(2):
                request = self.s.receives()
                self.assertEqual(request["find"], "col_entities")
                self.assertEqual(request["filter"], {'doc': 12 + i})
                self.assertEqual(request["sort"], {'sen': 1})
                occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 4 + i}]
                request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            g = future()
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, 0)
            self.assertEqual(g.ts, 1546473600000)
            self.assertEqual(g[1, 4], 1.0)

            g = g.next
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546560000000)
            self.assertEqual(g[1, 5], 1.0)

            future = mockupdb.go(tvg.lookup_le, 1546732800000)

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {'time': {'$lte': datetime.datetime.utcfromtimestamp(1546732800)}})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', -1), ('_id', -1)]))
            self.assertEqual(request["limit"], 2)
            documents = [{'_id': 15, 'time': datetime.datetime.utcfromtimestamp(1546732800)},
                         {'_id': 14, 'time': datetime.datetime.utcfromtimestamp(1546646400)}]
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            for i in range(2):
                request = self.s.receives()
                self.assertEqual(request["find"], "col_entities")
                self.assertEqual(request["filter"], {'doc': 15 - i})
                self.assertEqual(request["sort"], {'sen': 1})
                occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 7 - i}]
                request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            g = future()
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546732800000)
            self.assertEqual(g[1, 7], 1.0)

            g = g.prev
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_PREV)
            self.assertEqual(g.ts, 1546646400000)
            self.assertEqual(g[1, 6], 1.0)

            future = mockupdb.go(getattr, g, 'prev')

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {"$or": [{"time": {"$lt": datetime.datetime.utcfromtimestamp(1546646400)}},
                                                         {"time": datetime.datetime.utcfromtimestamp(1546646400), "_id": {"$lt": 14}}]})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', -1), ('_id', -1)]))
            self.assertEqual(request["limit"], 2)
            documents = [{'_id': 13, 'time': datetime.datetime.utcfromtimestamp(1546560000)},
                         {'_id': 12, 'time': datetime.datetime.utcfromtimestamp(1546473600)}]
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            g = future()
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, 0)
            self.assertEqual(g.ts, 1546560000000)
            self.assertEqual(g[1, 5], 1.0)

            g = tvg.lookup_ge(1546732800000)
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546732800000)
            self.assertEqual(g[1, 7], 1.0)

            future = mockupdb.go(getattr, g, 'next')

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {"$or": [{"time": {"$gt": datetime.datetime.utcfromtimestamp(1546732800)}},
                                                         {"time": datetime.datetime.utcfromtimestamp(1546732800), "_id": {"$gt": 15}}]})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', 1), ('_id', 1)]))
            self.assertEqual(request["limit"], 2)
            documents = []
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            g = future()
            self.assertEqual(g, None)

            for i, g in enumerate(tvg):
                self.assertEqual(g.revision, 0)
                self.assertEqual(g.flags, 0)
                self.assertEqual(g.ts, 1546300800000 + i * 86400000)
                self.assertEqual(g[1, 2 + i], 1.0)

            tvg.disable_mongodb_sync()
            del tvg

    # Run the unit tests
    unittest.main()
