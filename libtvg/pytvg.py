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
import itertools
import warnings
import weakref
import numpy as np
import numpy.ctypeslib as npc
import struct
import math
import sys
import os

libname = "libtvg.dylib" if sys.platform == "darwin" else "libtvg.so"
filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), libname)
lib = cdll.LoadLibrary(filename)
libc = cdll.LoadLibrary(find_library('c'))

LIBTVG_API_VERSION  = 0x00000007

TVG_FLAGS_NONZERO   = 0x00000001
TVG_FLAGS_POSITIVE  = 0x00000002
TVG_FLAGS_DIRECTED  = 0x00000004
TVG_FLAGS_STREAMING = 0x00000008

TVG_FLAGS_LOAD_NEXT = 0x00010000
TVG_FLAGS_LOAD_PREV = 0x00020000

OBJECTID_NONE   = 0
OBJECTID_INT    = 1
OBJECTID_OID    = 2

class c_objectid(Structure):
    _fields_ = [("lo",       c_uint64),
                ("hi",       c_uint),
                ("type",     c_uint)]

class c_vector(Structure):
    _fields_ = [("refcount", c_uint64),
                ("flags",    c_uint),
                ("revision", c_uint64),
                ("eps",      c_float)]

class c_graph(Structure):
    _fields_ = [("refcount", c_uint64),
                ("flags",    c_uint),
                ("revision", c_uint64),
                ("eps",      c_float),
                ("ts",       c_uint64),
                ("objectid", c_objectid)]

class c_node(Structure):
    _fields_ = [("refcount", c_uint64),
                ("index",    c_uint64)]

class c_tvg(Structure):
    _fields_ = [("refcount", c_uint64),
                ("flags",    c_uint)]

class c_metric(Structure):
    _fields_ = [("refcount", c_uint64)]

class c_window(Structure):
    _fields_ = [("refcount", c_uint64),
                ("ts",       c_uint64),
                ("window_l", c_int64),
                ("window_r", c_int64)]

class c_mongodb_config(Structure):
    _fields_ = [("uri",          c_char_p),
                ("database",     c_char_p),
                ("col_articles", c_char_p),
                ("article_id",   c_char_p),
                ("article_time", c_char_p),
                ("filter_key",   c_char_p),
                ("filter_value", c_char_p),
                ("col_entities", c_char_p),
                ("entity_doc",   c_char_p),
                ("entity_sen",   c_char_p),
                ("entity_ent",   c_char_p),
                ("use_pool",     c_int),
                ("load_nodes",   c_int),
                ("sum_weights",  c_int),
                ("max_distance", c_uint64)]

class c_mongodb(Structure):
    _fields_ = [("refcount", c_uint64)]

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
c_objectid_p     = POINTER(c_objectid)
c_vector_p       = POINTER(c_vector)
c_graph_p        = POINTER(c_graph)
c_node_p         = POINTER(c_node)
c_tvg_p          = POINTER(c_tvg)
c_metric_p       = POINTER(c_metric)
c_window_p       = POINTER(c_window)
c_mongodb_config_p = POINTER(c_mongodb_config)
c_mongodb_p      = POINTER(c_mongodb)
c_bfs_entry_p    = POINTER(c_bfs_entry)
c_bfs_callback_p = CFUNCTYPE(c_int, c_graph_p, c_bfs_entry_p, c_void_p)

# init function

lib.init_libtvg.argtypes = (c_uint64,)
lib.init_libtvg.restype = c_int

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

lib.vector_set_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.vector_set_entries.restype = c_int

lib.vector_add_entry.argtypes = (c_vector_p, c_uint64, c_float)
lib.vector_add_entry.restype = c_int

lib.vector_add_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.vector_add_entries.restype = c_int

lib.vector_sub_entry.argtypes = (c_vector_p, c_uint64, c_float)
lib.vector_sub_entry.restype = c_int

lib.vector_sub_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.vector_sub_entries.restype = c_int

lib.vector_del_entry.argtypes = (c_vector_p, c_uint64)

lib.vector_del_entries.argtypes = (c_vector_p, npc.ndpointer(dtype=np.uint64), c_uint64)

lib.vector_mul_const.argtypes = (c_vector_p, c_float)

lib.vector_norm.argtypes = (c_vector_p,)
lib.vector_norm.restype = c_double

lib.vector_mul_vector.argtypes = (c_vector_p, c_vector_p)
lib.vector_mul_vector.restype = c_double

lib.vector_sub_vector_norm.argtypes = (c_vector_p, c_vector_p)
lib.vector_sub_vector_norm.restype = c_double

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

lib.graph_set_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.graph_set_edges.restype = c_int

lib.graph_add_edge.argtypes = (c_graph_p, c_uint64, c_uint64, c_float)
lib.graph_add_edge.restype = c_int

lib.graph_add_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
lib.graph_add_edges.restype = c_int

lib.graph_add_graph.argtypes = (c_graph_p, c_graph_p, c_float)
lib.graph_add_graph.restype = c_int

lib.graph_sub_edge.argtypes = (c_graph_p, c_uint64, c_uint64, c_float)
lib.graph_sub_edge.restype = c_int

lib.graph_sub_edges.argtypes = (c_graph_p, npc.ndpointer(dtype=np.uint64), or_null(npc.ndpointer(dtype=np.float32)), c_uint64)
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

lib.graph_power_iteration.argtypes = (c_graph_p, c_vector_p, c_uint, c_double, c_double_p)
lib.graph_power_iteration.restype = c_vector_p

lib.graph_filter_nodes.argtypes = (c_graph_p, c_vector_p)
lib.graph_filter_nodes.restype = c_graph_p

lib.graph_bfs.argtypes = (c_graph_p, c_uint64, c_int, c_bfs_callback_p, c_void_p)
lib.graph_bfs.restype = c_int

# node functions

lib.alloc_node.argtypes = ()
lib.alloc_node.restype = c_node_p

lib.free_node.argtypes = (c_node_p,)

lib.unlink_node.argtypes = (c_node_p,)

lib.node_set_attribute.argtypes = (c_node_p, c_char_p, c_char_p)
lib.node_set_attribute.restype = c_int

lib.node_get_attribute.argtypes = (c_node_p, c_char_p)
lib.node_get_attribute.restype = c_char_p

lib.node_get_attributes.argtypes = (c_node_p,)
lib.node_get_attributes.restype = POINTER(c_char_p)

# tvg functions

lib.alloc_tvg.argtypes = (c_uint,)
lib.alloc_tvg.restype = c_tvg_p

lib.free_tvg.argtypes = (c_tvg_p,)

lib.tvg_memory_usage.argtypes = (c_tvg_p,)
lib.tvg_memory_usage.restype = c_uint64

lib.tvg_link_graph.argtypes = (c_tvg_p, c_graph_p, c_uint64)
lib.tvg_link_graph.restype = c_int

lib.tvg_alloc_graph.argtypes = (c_tvg_p, c_uint64)
lib.tvg_alloc_graph.restype = c_graph_p

lib.tvg_set_primary_key.argtypes = (c_tvg_p, c_char_p)
lib.tvg_set_primary_key.restype = c_int

lib.tvg_link_node.argtypes = (c_tvg_p, c_node_p, POINTER(c_node_p), c_uint64)
lib.tvg_link_node.restype = c_int

lib.tvg_get_node_by_index.argtypes = (c_tvg_p, c_uint64)
lib.tvg_get_node_by_index.restype = c_node_p

lib.tvg_get_node_by_primary_key.argtypes = (c_tvg_p, c_node_p)
lib.tvg_get_node_by_primary_key.restype = c_node_p

lib.tvg_load_graphs_from_file.argtypes = (c_tvg_p, c_char_p)
lib.tvg_load_graphs_from_file.restype = c_int

lib.tvg_load_nodes_from_file.argtypes = (c_tvg_p, c_char_p)
lib.tvg_load_nodes_from_file.restype = c_int

lib.tvg_enable_mongodb_sync.argtypes = (c_tvg_p, c_mongodb_p, c_uint64, c_uint64)
lib.tvg_enable_mongodb_sync.restype = c_int

lib.tvg_disable_mongodb_sync.argtypes = (c_tvg_p,)

lib.tvg_lookup_graph_ge.argtypes = (c_tvg_p, c_uint64)
lib.tvg_lookup_graph_ge.restype = c_graph_p

lib.tvg_lookup_graph_le.argtypes = (c_tvg_p, c_uint64)
lib.tvg_lookup_graph_le.restype = c_graph_p

lib.tvg_lookup_graph_near.argtypes = (c_tvg_p, c_uint64)
lib.tvg_lookup_graph_near.restype = c_graph_p

lib.tvg_compress.argtypes = (c_tvg_p, c_uint64, c_uint64)
lib.tvg_compress.restype = c_int

# window functions

lib.tvg_alloc_window.argtypes = (c_tvg_p, c_int64, c_int64)
lib.tvg_alloc_window.restype = c_window_p

lib.free_window.argtypes = (c_window_p,)

lib.window_reset.argtypes = (c_window_p,)

lib.window_update.argtypes = (c_window_p, c_uint64)
lib.window_update.restype = c_int

lib.window_get_sources.argtypes = (c_window_p, POINTER(c_graph_p), c_uint64)
lib.window_get_sources.restype = c_uint64

# Metric functions

lib.window_alloc_metric_sum_edges.argtypes = (c_window_p, c_float)
lib.window_alloc_metric_sum_edges.restype = c_metric_p

lib.metric_sum_edges_get_eps.argtypes = (c_metric_p,)
lib.metric_sum_edges_get_eps.restype = c_float

lib.metric_sum_edges_get_result.argtypes = (c_metric_p,)
lib.metric_sum_edges_get_result.restype = c_graph_p

lib.window_alloc_metric_sum_edges_exp.argtypes = (c_window_p, c_float, c_float, c_float)
lib.window_alloc_metric_sum_edges_exp.restype = c_metric_p

lib.metric_sum_edges_exp_get_weight.argtypes = (c_metric_p,)
lib.metric_sum_edges_exp_get_weight.restype = c_float

lib.metric_sum_edges_exp_get_log_beta.argtypes = (c_metric_p,)
lib.metric_sum_edges_exp_get_log_beta.restype = c_float

lib.metric_sum_edges_exp_get_eps.argtypes = (c_metric_p,)
lib.metric_sum_edges_exp_get_eps.restype = c_float

lib.metric_sum_edges_exp_get_result.argtypes = (c_metric_p,)
lib.metric_sum_edges_exp_get_result.restype = c_graph_p

lib.window_alloc_metric_count_edges.argtypes = (c_window_p,)
lib.window_alloc_metric_count_edges.restype = c_metric_p

lib.metric_count_edges_get_result.argtypes = (c_metric_p,)
lib.metric_count_edges_get_result.restype = c_graph_p

lib.window_alloc_metric_count_nodes.argtypes = (c_window_p,)
lib.window_alloc_metric_count_nodes.restype = c_metric_p

lib.metric_count_nodes_get_result.argtypes = (c_metric_p,)
lib.metric_count_nodes_get_result.restype = c_vector_p

lib.free_metric.argtypes = (c_metric_p,)

lib.metric_reset.argtypes = (c_metric_p,)

lib.metric_get_window.argtypes = (c_metric_p,)
lib.metric_get_window.restype = c_graph_p

# MongoDB functions

lib.alloc_mongodb.argtypes = (c_mongodb_config_p,)
lib.alloc_mongodb.restype = c_mongodb_p

lib.free_mongodb.argtypes = (c_mongodb_p,)

lib.mongodb_load_graph.argtypes = (c_tvg_p, c_mongodb_p, c_objectid_p, c_uint)
lib.mongodb_load_graph.restype = c_graph_p

lib.tvg_load_graphs_from_mongodb.argtypes = (c_tvg_p, c_mongodb_p)
lib.tvg_load_graphs_from_mongodb.restype = c_int

# libc functions

libc.free.argtypes = (c_void_p,)

# Before proceeding with any other function calls, first make sure that the library
# is compatible. This is especially important since there is no stable API yet.

if not lib.init_libtvg(LIBTVG_API_VERSION):
    raise RuntimeError("Incompatible %s library! Try to run 'make'." % libname)

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

# The 'libtvgobject' decorator should be used for classes corresponding to objects in
# the libtvg library. It ensures that there is at most one Python object corresponding
# to each libtvg object.
def libtvgobject(klass):
    cache = weakref.WeakValueDictionary()
    @functools.wraps(klass, assigned=('__name__', '__module__'), updated=())
    class wrapper(klass):
        __doc__ = klass.__doc__
        def __new__(cls, *args, obj=None, **kwargs):
            if obj:
                try:
                    return cache[addressof(obj.contents)]._get_obj()
                except KeyError:
                    pass
            result = klass(*args, obj=obj, **kwargs)
            result.__class__ = cls
            cache[addressof(result._obj.contents)] = result
            return result
        def __init__(self, *args, **kwargs):
            pass
    return wrapper

@libtvgobject
class Vector(object):
    """
    This object represents a vector of arbitrary / infinite dimension. To achieve that,
    it only stores entries that are explicitly set, and assumes that all other entries
    of the vector are zero. Internally, it uses hashing to map indices to buckets,
    that are stored in contiguous blocks of memory and in sorted order for faster access.

    # Arguments
    nonzero: Enforce that all entries must be non-zero.
    positive: Enforce that all entries must be positive.
    """

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

    def _get_obj(self):
        lib.free_vector(self._obj)
        return self

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
        """
        Return the current revision of the vector object. This value is incremented
        whenever the vector is changed. It is also used by the @cacheable decorator
        to check the cache validity.
        """
        return self._obj.contents.revision

    @property
    def eps(self):
        """
        Get/set the current value of epsilon. This is used to determine whether an
        entry is equal to zero. Whenever |x| < eps, it is treated as zero.
        """
        return self._obj.contents.eps

    @eps.setter
    def eps(self, value):
        lib.vector_set_eps(self._obj, value)

    @cacheable
    def empty(self):
        """ Check if a vector is empty, i.e., if it does not have any entries. """
        return lib.vector_empty(self._obj)

    def has_entry(self, index):
        """ Check if a vector has an entry with index `index`. """
        return lib.vector_has_entry(self._obj, index)

    def __getitem__(self, index):
        """ Return entry `index` of the vector, or 0 if it doesn't exist. """
        return lib.vector_get_entry(self._obj, index)

    def entries(self, ret_indices=True, ret_weights=True):
        """
        Return all indices and/or weights of a vector.

        # Arguments
        ret_indices: Return indices, otherwise None.
        ret_weights: Return weights, otherwise None.

        # Returns
        `(indices, weights)`
        """

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
        """ Return the number of entries of a vector. """
        return lib.vector_get_entries(self._obj, None, None, 0)

    def __len__(self):
        """ Return the number of entries of a vector. """
        return self.num_entries

    def __setitem__(self, index, weight):
        """ Set the entry with index `index` of a vector to `weight`. """
        res = lib.vector_set_entry(self._obj, index, weight)
        if not res:
            raise MemoryError

    def set_entries(self, indices, weights=None):
        """
        Short-cut to set multiple entries of a vector.
        If weights is None the elements are set to 1.

        # Arguments
        indices: List of indices (list or 1d numpy array).
        weights: List of weights to set (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if weights is not None:
            weights = np.asarray(weights, dtype=np.float32)

            if indices.size == 0 and weights.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 1:
                raise ValueError("indices array does not have correct dimensions")
            if len(weights.shape) != 1:
                raise ValueError("weights array does not have correct dimensions")
            if indices.shape[0] != weights.shape[0]:
                raise ValueError("indices/weights arrays have different length")

        else:
            if indices.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 1:
                raise ValueError("indices array does not have correct dimensions")

        res = lib.vector_set_entries(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def add_entry(self, index, weight):
        """ Add weight `weight` to the entry with index `index`. """
        res = lib.vector_add_entry(self._obj, index, weight)
        if not res:
            raise MemoryError

    def add_entries(self, indices, weights=None):
        """
        Short-cut to update multiple entries of a vector by adding values.
        If weights is None the elements are set to 1.

        # Arguments
        indices: List of indices (list or 1d numpy array).
        weights: List of weights to add (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if weights is not None:
            weights = np.asarray(weights, dtype=np.float32)

            if indices.size == 0 and weights.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 1:
                raise ValueError("indices array does not have correct dimensions")
            if len(weights.shape) != 1:
                raise ValueError("weights array does not have correct dimensions")
            if indices.shape[0] != weights.shape[0]:
                raise ValueError("indices/weights arrays have different length")

        else:
            if indices.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 1:
                raise ValueError("indices array does not have correct dimensions")

        res = lib.vector_add_entries(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def sub_entry(self, index, weight):
        """ Subtract weight `weight` from the entry with index `index`. """
        res = lib.vector_sub_entry(self._obj, index, weight)
        if not res:
            raise MemoryError

    def sub_entries(self, indices, weights=None):
        """
        Short-cut to update multiple entries of a vector by subtracting values.
        If weights is None the elements are set to 1.

        # Arguments
        indices: List of indices (list or 1d numpy array).
        weights: List of weights to subtract (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if weights is not None:
            weights = np.asarray(weights, dtype=np.float32)

            if indices.size == 0 and weights.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 1:
                raise ValueError("indices array does not have correct dimensions")
            if len(weights.shape) != 1:
                raise ValueError("weights array does not have correct dimensions")
            if indices.shape[0] != weights.shape[0]:
                raise ValueError("indices/weights arrays have different length")

        else:
            if indices.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 1:
                raise ValueError("indices array does not have correct dimensions")

        res = lib.vector_sub_entries(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def __delitem__(self, index):
        """ Delete entry `index` from the vector or do nothing if it doesn't exist. """
        lib.vector_del_entry(self._obj, index)

    def del_entries(self, indices):
        """
        Short-cut to delete multiple entries from a vector.

        # Arguments
        indices: List of indices (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if indices.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 1:
            raise ValueError("indices array does not have correct dimensions")

        lib.vector_del_entries(self._obj, indices, indices.shape[0])

    def mul_const(self, constant):
        """ Perform inplace element-wise multiplication of the vector with `constant`. """
        lib.vector_mul_const(self._obj, constant)

    @cacheable
    def norm(self):
        """ Return the L2 norm of the vector. """
        return lib.vector_norm(self._obj)

    def mul_vector(self, other):
        """ Compute the scalar product of the current vector with a second vector `other`. """
        # FIXME: Check type of 'other'.
        return lib.vector_mul_vector(self._obj, other._obj)

    def sub_vector_norm(self, other):
        """ Compute L2 norm of (self - other). """
        return lib.vector_sub_vector_norm(self._obj, other._obj)

    def as_dict(self):
        """ Return a dictionary containing all vector entries. """
        return dict(zip(*self.entries()))

@libtvgobject
class Graph(object):
    """
    This object represents a graph of arbitrary / infinite dimension. To achieve that,
    it only stores edges that are explicitly set, and assumes that all other edges
    of the graph have a weight of zero. Internally, it uses hashing to map source and
    target indices to buckets, that are stored in contiguous blocks of memory and in
    sorted order for faster access.

    # Arguments
    nonzero: Enforce that all entries must be non-zero.
    positive: Enforce that all entries must be positive.
    directed: Create a directed graph.
    """

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

    def _get_obj(self):
        lib.free_graph(self._obj)
        return self

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
        """
        Return the current revision of the graph object. This value is incremented
        whenever the graph is changed. It is also used by the @cacheable decorator
        to check the cache validity.
        """
        return self._obj.contents.revision

    @property
    def eps(self):
        """
        Get/set the current value of epsilon. This is used to determine whether an
        entry is equal to zero. Whenever |x| < eps, it is treated as zero.
        """
        return self._obj.contents.eps

    @eps.setter
    def eps(self, value):
        lib.graph_set_eps(self._obj, value)

    @property
    def ts(self):
        """
        Get the timestamp associated with this graph object. This only applies to
        objects that are part of a time-varying graph.
        """
        return self._obj.contents.ts

    @property
    def id(self):
        """
        Get the ID associated with this graph object. This only applies to objects
        loaded from an external data source, e.g., from a MongoDB.
        """
        return self._obj.contents.id

    @staticmethod
    def load_from_file(filename, nonzero=False, positive=False, directed=False):
        raise NotImplementedError

    @staticmethod
    def load_from_mongodb(mongodb, id, nonzero=False, positive=False, directed=False):
        """
        Load a single graph from a MongoDB database.

        # Arguments
        id: Identifier (numeric or objectid) of the document to load
        nonzero: Enforce that all entries must be non-zero.
        positive: Enforce that all entries must be positive.
        directed: Create a directed graph.
        """

        objectid = c_objectid()

        if isinstance(id, int):
            objectid.lo = id
            objectid.hi = 0
            objectid.type = OBJECTID_INT

        elif isinstance(id, bytes) and len(id) == 12:
            hi, lo = struct.unpack(">IQ", id)
            objectid.lo = lo
            objectid.hi = hi
            objectid.type = OBJECTID_OID

        elif isinstance(id, str) and len(id) == 24:
            hi, lo = struct.unpack(">IQ", bytes.fromhex(id))
            objectid.lo = lo
            objectid.hi = hi
            objectid.type = OBJECTID_OID

        else:
            raise ValueError("Objectid is not valid")

        flags = 0
        flags |= (TVG_FLAGS_NONZERO  if nonzero  else 0)
        flags |= (TVG_FLAGS_POSITIVE if positive else 0)
        flags |= (TVG_FLAGS_DIRECTED if directed else 0)

        obj = lib.mongodb_load_graph(None, mongodb._obj, objectid, flags)
        return Graph(obj=obj) if obj else None

    def unlink(self):
        """ Unlink a graph from the TVG object. """
        lib.unlink_graph(self._obj)

    @property
    @cacheable
    def memory_usage(self):
        """ Return the memory usage currently associated with the graph. """
        return lib.graph_memory_usage(self._obj)

    @property
    def next(self):
        """ Return the (chronologically) next graph object. """
        obj = lib.next_graph(self._obj)
        return Graph(obj=obj) if obj else None

    @property
    def prev(self):
        """ Return the (chronologically) previous graph object. """
        obj = lib.prev_graph(self._obj)
        return Graph(obj=obj) if obj else None

    @cacheable
    def empty(self):
        """ Check if the graph is empty, i.e., it does not have any edges. """
        return lib.graph_empty(self._obj)

    def has_edge(self, indices):
        """ Check if the graph has edge `(source, target)`. """
        (source, target) = indices
        return lib.graph_has_edge(self._obj, source, target)

    def __getitem__(self, indices):
        """ Return the weight of edge `(source, target)`. """
        (source, target) = indices
        return lib.graph_get_edge(self._obj, source, target)

    def edges(self, ret_indices=True, ret_weights=True):
        """
        Return all indices and/or weights of a graph.

        # Arguments
        ret_indices: Return indices consisting of (source, target), otherwise None.
        ret_weights: Return weights, otherwise None.

        # Returns
        `(indices, weights)`
        """

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
        """ Return the number of edges of a graph. """
        return lib.graph_get_edges(self._obj, None, None, 0)

    def nodes(self):
        """
        Return a list of all nodes. A node is considered present, when it is connected
        to at least one other node (either as a source or target).
        """

        # FIXME: Add a C library helper?
        indices, _ = self.edges(ret_weights=False)
        return np.unique(indices)

    @property
    @cacheable
    def num_nodes(self):
        """ Return the number of nodes of a graph. """
        return len(self.nodes())

    def adjacent_edges(self, source, ret_indices=True, ret_weights=True):
        """
        Return information about all edges adjacent to a given source edge.

        # Arguments
        source: Index of the source node.
        ret_indices: Return target indices, otherwise None.
        ret_weights: Return weights, otherwise None.

        # Returns
        `(indices, weights)`
        """

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
        """ Return the number of adjacent edges to a given `source` node, i.e., the node degree. """
        return lib.graph_get_adjacent_edges(self._obj, source, None, None, 0)

    def __len__(self):
        """ Return the number of edges of a graph. """
        return self.num_edges

    def __setitem__(self, indices, weight):
        """ Set edge `(source, target)` of a graph to `weight`."""
        (source, target) = indices
        res = lib.graph_set_edge(self._obj, source, target, weight)
        if not res:
            raise MemoryError

    def set_edges(self, indices, weights=None):
        """
        Short-cut to set multiple edges in a graph.
        If weights is None the elements are set to 1.

        # Arguments
        indices: List of indices (list of tuples or 2d numpy array).
        weights: List of weights to set (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if weights is not None:
            weights = np.asarray(weights, dtype=np.float32)

            if indices.size == 0 and weights.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 2 or indices.shape[1] != 2:
                raise ValueError("indices array does not have correct dimensions")
            if len(weights.shape) != 1:
                raise ValueError("weights array does not have correct dimensions")
            if indices.shape[0] != weights.shape[0]:
                raise ValueError("indices/weights arrays have different length")

        else:
            if indices.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 2 or indices.shape[1] != 2:
                raise ValueError("indices array does not have correct dimensions")

        res = lib.graph_set_edges(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def add_edge(self, indices, weight):
        """ Add weight `weight` to edge `(source, target)`. """
        (source, target) = indices
        res = lib.graph_add_edge(self._obj, source, target, weight)
        if not res:
            raise MemoryError

    def add_edges(self, indices, weights=None):
        """
        Short-cut to update multiple edges of a graph by adding values.
        If weights is None the elements are set to 1.

        # Arguments
        indices: List of indices (list of tuples or 2d numpy array).
        weights: List of weights to set (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if weights is not None:
            weights = np.asarray(weights, dtype=np.float32)

            if indices.size == 0 and weights.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 2 or indices.shape[1] != 2:
                raise ValueError("indices array does not have correct dimensions")
            if len(weights.shape) != 1:
                raise ValueError("weights array does not have correct dimensions")
            if indices.shape[0] != weights.shape[0]:
                raise ValueError("indices/weights arrays have different length")
        else:
            if indices.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 2 or indices.shape[1] != 2:
                raise ValueError("indices array does not have correct dimensions")

        res = lib.graph_add_edges(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def sub_edge(self, indices, weight):
        """ Subtract weight `weight` from edge `(source, target)`. """
        (source, target) = indices
        res = lib.graph_sub_edge(self._obj, source, target, weight)
        if not res:
            raise MemoryError

    def sub_edges(self, indices, weights=None):
        """
        Short-cut to update multiple edges of a graph by subtracting values.
        If weights is None the elements are set to 1.

        # Arguments
        indices: List of indices (list of tuples or 2d numpy array).
        weights: List of weights to set (list or 1d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if weights is not None:
            weights = np.asarray(weights, dtype=np.float32)

            if indices.size == 0 and weights.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 2 or indices.shape[1] != 2:
                raise ValueError("indices array does not have correct dimensions")
            if len(weights.shape) != 1:
                raise ValueError("weights array does not have correct dimensions")
            if indices.shape[0] != weights.shape[0]:
                raise ValueError("indices/weights arrays have different length")

        else:
            if indices.size == 0:
                return # nothing to do for empty array
            if len(indices.shape) != 2 or indices.shape[1] != 2:
                raise ValueError("indices array does not have correct dimensions")

        res = lib.graph_sub_edges(self._obj, indices, weights, indices.shape[0])
        if not res:
            raise MemoryError

    def __delitem__(self, indices):
        """ Delete edge `(source, target)` from the graph or do nothing if it doesn't exist. """
        (source, target) = indices
        lib.graph_del_edge(self._obj, source, target)

    def del_edges(self, indices):
        """
        Short-cut to delete multiple edges from a graph.

        # Arguments
        indices: List of indices (list of tuples or 2d numpy array).
        """

        indices = np.asarray(indices, dtype=np.uint64)

        if indices.size == 0:
            return # nothing to do for empty array
        if len(indices.shape) != 2 or indices.shape[1] != 2:
            raise ValueError("indices array does not have correct dimensions")

        lib.graph_del_edges(self._obj, indices, indices.shape[0])

    def mul_const(self, constant):
        """ Perform inplace element-wise multiplication of all graph edges with `constant`. """
        lib.graph_mul_const(self._obj, constant)

    def mul_vector(self, other):
        """ Compute the matrix-vector product of the graph with vector `other`. """
        # FIXME: Check type of 'other'.
        return Vector(obj=lib.graph_mul_vector(self._obj, other._obj))

    def in_degrees(self):
        """ Compute and return a vector of in-degrees. """
        return Vector(obj=lib.graph_in_degrees(self._obj))

    def in_weights(self):
        """ Compute and return a vector of in-weights. """
        return Vector(obj=lib.graph_in_weights(self._obj))

    def out_degrees(self):
        """ Compute and return a vector of out-degrees. """
        return Vector(obj=lib.graph_out_degrees(self._obj))

    def out_weights(self):
        """ Compute and return a vector of out-weights. """
        return Vector(obj=lib.graph_out_weights(self._obj))

    def degree_anomalies(self):
        """ Compute and return a vector of degree anomalies. """
        return Vector(obj=lib.graph_degree_anomalies(self._obj))

    def weight_anomalies(self):
        """ Compute and return a vector of weight anomalies. """
        return Vector(obj=lib.graph_weight_anomalies(self._obj))

    def power_iteration(self, initial_guess=None, num_iterations=0, tolerance=None, ret_eigenvalue=True):
        """
        Compute and return the eigenvector (and optionally the eigenvalue).

        # Arguments
        initial_guess: Initial guess for the solver.
        num_iterations: Number of iterations.
        tolerance: Desired tolerance.
        ret_eigenvalue: Also return the eigenvalue. This requires one more iteration.

        # Returns
        `(eigenvector, eigenvalue)`
        """

        if tolerance is None:
            tolerance = 0.0

        eigenvalue = c_double() if ret_eigenvalue else None
        initial_guess = initial_guess._obj if initial_guess is not None else None
        vector = Vector(obj=lib.graph_power_iteration(self._obj, initial_guess, num_iterations, tolerance, eigenvalue))
        if eigenvalue is not None:
            eigenvalue = eigenvalue.value
        return vector, eigenvalue

    def filter_nodes(self, nodes):
        """
        Create a subgraph by only keeping edges, where at least one node is
        part of the subset specified by the `nodes` parameter.

        # Arguments
        nodes: Vector or list of nodes to preserve

        # Returns
        Resulting graph.
        """

        if not isinstance(nodes, Vector):
            vector = Vector()
            vector.set_entries(nodes)
            nodes = vector

        return Graph(obj=lib.graph_filter_nodes(self._obj, nodes._obj))

    def bfs_count(self, source, max_count=None):
        """
        Perform a breadth-first search in the graph, starting from node `source`.
        In this version, the order is based solely on the number of links.

        # Arguments
        source: Index of the source node.
        max_count: Maximum depth.

        # Returns
        List of tuples `(weight, count, edge_from, edge_to)`.
        """

        result = []

        if max_count is None:
            max_count = 0xffffffffffffffff

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
        """
        Perform a breadth-first search in the graph, starting from node `source`.
        In this version, the order is based on the sum of the weights.

        # Arguments
        source: Index of the source node.
        max_weight: Maximum weight.

        # Returns
        List of tuples `(weight, count, edge_from, edge_to)`.
        """

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
        """
        Encode a graph as a Python dictionary for parsing with visjs.

        # Arguments
        node_attributes: Function to query node attributes.

        # Returns
        Dictionary containing the following key-value pairs:

        cmd: Either `"network_set"` for full updates, or `"network_update"` for partial updates.
        nodes: List of nodes (with ids and custom attributes).
        edges: List of edges (with ids and weights).
        deleted_nodes: List of deleted node ids (only for `cmd = "network_update"`).
        deleted_edges: List of deleted edge ids (only for `cmd = "network_update"`).
        """

        if node_attributes is None:
            node_attributes = lambda i: {}

        nodes = []
        edges = []

        for i in self.nodes():
            nodes.append({'id': i, **node_attributes(i)})

        indices, weights = self.edges()
        for i, w in zip(indices, weights):
            edges.append({'id': "%d-%d" % (i[0], i[1]), 'from': i[0], 'to': i[1], 'value': w})

        return {'cmd': 'network_set', 'nodes': nodes, 'edges': edges}

    def as_dict(self):
        """ Return a dictionary containing all graph edges. """
        indices, weights = self.edges()
        return dict([((i[0], i[1]), w) for i, w in zip(indices, weights)])

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

@libtvgobject
class Node(object):
    """
    This object represents a node. Since nodes are implicit in our model, they
    should only have static attributes that do not depend on the timestamp.
    For now, both node attribute keys and values are limited to the string type -
    in the future this might be extended to other data types. Attributes related
    to the primary key (that uniquely identify a node in the context of a time-
    varying-graph) must be set before both objects are linked. All other attributes
    can be set at any time.

    # Arguments
    **kwargs: Key-value pairs of type string to assign to the node.
    """

    def __init__(self, obj=None, **kwargs):
        if obj is None:
            obj = lib.alloc_node()

        self._obj = obj
        if not obj:
            raise MemoryError

        for k, v in kwargs.items():
            self[k] = v

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_node(self._obj)

    def _get_obj(self):
        lib.free_node(self._obj)
        return self

    @property
    def index(self):
        """ Return the index of the node. """
        return self._obj.contents.index

    @property
    def text(self):
        """ Short-cut to return the 'text' attribute of a node. """
        return self["text"]

    def unlink(self):
        """
        Unlink the node from the time-varying graph. The node itself stays valid,
        but it is no longer returned for any `node_by_index` or `node_by_primary_key`
        call.
        """

        lib.unlink_node(self._obj)

    def __setitem__(self, key, value):
        """ Set the node attribute `key` to `value`. Both key and value must have the type string. """
        res = lib.node_set_attribute(self._obj, key.encode("utf-8"), value.encode("utf-8"))
        if not res:
            raise KeyError

    def __getitem__(self, key):
        """ Return the node attribute for `key`. """
        value = lib.node_get_attribute(self._obj, key.encode("utf-8"))
        if not value:
            raise KeyError
        return value.decode("utf-8")

    def as_dict(self):
        """ Return a dictionary containing all node attributes. """
        ptr = lib.node_get_attributes(self._obj)
        if not ptr:
            raise MemoryError

        data = {}
        for i in itertools.count(step=2):
            if not ptr[i]: break
            key = ptr[i].decode("utf-8")
            value = ptr[i + 1].decode("utf-8")
            data[key] = value

        libc.free(ptr)
        return data

@libtvgobject
class TVG(object):
    """
    This object represents a time-varying graph.

    # Arguments
    nonzero: Enforce that all entries must be non-zero.
    positive: Enforce that all entries must be positive.
    directed: Create a directed time-varying graph.
    streaming: Support for streaming / differential updates.
    primary_key: List or semicolon separated string of attributes.
    """

    def __init__(self, nonzero=False, positive=False, directed=False, streaming=False, primary_key=None, obj=None):
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

        if primary_key:
            self.set_primary_key(primary_key)

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_tvg(self._obj)

    def _get_obj(self):
        lib.free_tvg(self._obj)
        return self

    @property
    def flags(self):
        return self._obj.contents.flags

    @property
    def memory_usage(self):
        """ Return the memory usage currently associated with the TVG. """
        return lib.tvg_memory_usage(self._obj)

    def link_graph(self, graph, ts):
        """
        Link a graph to the time-varying-graph object.

        # Arguments
        graph: The graph to link.
        ts: Time-stamp of the graph (as uint64, typically UNIX timestamp in milliseconds).
        """
        res = lib.tvg_link_graph(self._obj, graph._obj, ts)
        if not res:
            raise RuntimeError

    def Graph(self, ts):
        """ Create a new graph associated with the time-varying-graph object. """
        return Graph(obj=lib.tvg_alloc_graph(self._obj, ts))

    def set_primary_key(self, key):
        """
        Set or update the primary key used to distinguish graph nodes. The key can
        consist of one or multiple attributes, and is used to identify a node
        (especially, when loading from an external source, that does not use integer
        identifiers).

        # Arguments
        key: List or semicolon separated string of attributes.
        """

        if isinstance(key, list):
            key = ";".join(key)
        res = lib.tvg_set_primary_key(self._obj, key.encode("utf-8"))
        if not res:
            raise RuntimeError

    def link_node(self, node, index=None):
        """
        Link a node to the time-varying-graph object.

        # Arguments
        node: The node to link.
        index: Index to assign to the node, or `None` if the next empty index should be used.
        """

        if index is None:
            index = 0xffffffffffffffff

        res = lib.tvg_link_node(self._obj, node._obj, None, index)
        if not res:
            raise RuntimeError

    def Node(self, **kwargs):
        """
        Create a new node assicated with the graph. Note that all primary key attributes
        must be set immediately during construction, it is not possible to change them later.

        # Arguments
        **kwargs: Key-value pairs of type string to assign to the node.
        """

        node = Node(**kwargs)

        obj = c_node_p()
        res = lib.tvg_link_node(self._obj, node._obj, obj, 0xffffffffffffffff)
        if not res:
            del node
            if not obj:
                raise RuntimeError
            node = Node(obj=obj)

        return node

    def node_by_index(self, index):
        """
        Lookup a node by index.

        # Arguments
        index: Index of the node.

        # Returns
        Node object.
        """

        obj = lib.tvg_get_node_by_index(self._obj, index)
        if not obj:
            raise KeyError
        return Node(obj=obj)

    def node_by_primary_key(self, **kwargs):
        """
        Lookup a node by its primary key. This must match the primary key set with
        `set_primary_key` (currently, a time-varying graph can only have one key).

        # Arguments
        **kwargs: Key-value pairs of the primary key.

        # Returns
        Node object.
        """

        primary_key = Node(**kwargs)
        obj = lib.tvg_get_node_by_primary_key(self._obj, primary_key._obj)
        del primary_key
        if not obj:
            raise KeyError
        return Node(obj=obj)

    def node_by_text(self, text):
        """ Lookup a node by its text (assumes that `text` is the primary key). """
        return self.node_by_primary_key(text=text)

    @staticmethod
    def load(source, nodes=None, *args, **kwargs):
        """
        Load a time-varying-graph from an external data source.

        # Arguments
        source: Data source to load (currently either a file path, or a MongoDB object).
        nodes: Secondary data source to load node attributes (must be a file path).
        *args, **kwargs: Arguments passed through to the `TVG()` constructor.
        """

        tvg = TVG(*args, **kwargs)
        if isinstance(source, MongoDB):
            tvg.load_graphs_from_mongodb(source)
        else:
            tvg.load_graphs_from_file(source)
        if nodes:
            tvg.load_nodes_from_file(nodes)
        return tvg

    def load_graphs_from_file(self, filename):
        """ Load a time-varying-graph (i.e., a collection of graphs) from a file. """
        res = lib.tvg_load_graphs_from_file(self._obj, filename.encode("utf-8"))
        if not res:
            raise IOError

    def load_nodes_from_file(self, filename):
        """ Load node attributes from a file. """
        res = lib.tvg_load_nodes_from_file(self._obj, filename.encode("utf-8"))
        if not res:
            raise IOError

    def load_graphs_from_mongodb(self, mongodb):
        """ Load a time-varying-graph (i.e., multiple graphs) from a MongoDB. """
        res = lib.tvg_load_graphs_from_mongodb(self._obj, mongodb._obj)
        if not res:
            raise IOError

    def enable_mongodb_sync(self, mongodb, batch_size=0, cache_size=0):
        """
        Enable synchronization with a MongoDB server. Whenever more data is needed
        (e.g., querying the previous or next graph, or looking up graphs in a certain
        range), requests are sent to the database. Each request loads up to
        `batch_size` graphs. The total amount of data kept in memory can be controlled
        with the `cache_size` parameter.

        # Arguments
        mongodb: MongoDB object.
        batch_size: Maximum number of graphs to load in a single request.
        cache_size: Maximum size of the cache (in bytes).
        """

        res = lib.tvg_enable_mongodb_sync(self._obj, mongodb._obj, batch_size, cache_size)
        if not res:
            raise IOError

    def disable_mongodb_sync(self):
        """ Disable synchronization with a MongoDB server. """
        lib.tvg_disable_mongodb_sync(self._obj)

    def __iter__(self):
        """ Iterates through all graphs of a time-varying-graph object. """
        return GraphIter(self.lookup_ge())

    def __reversed__(self):
        """ Iterates (in reverse order) through all graphs of a time-varying graph object. """
        return GraphIterReversed(self.lookup_le())

    def Window(self, window_l, window_r):
        """
        Create a new sliding window to aggregate data in a specific range around a
        fixed timestmap. Only graphs in [ts + window_l, ts + window_r] are
        considered.

        # Arguments
        window_l: Left boundary of the interval, relative to the timestamp.
        window_r: Right boundary of the interval, relative to the timestamp.
        """

        if window_l < 0 and np.isinf(window_l):
            window_l = -0x8000000000000000
        if window_r > 0 and np.isinf(window_r):
            window_r =  0x7fffffffffffffff
        return Window(obj=lib.tvg_alloc_window(self._obj, window_l, window_r))

    def WindowSumEdges(self, window_l, window_r, eps=0.0):
        """
        Create a new rectangular filter window to aggregate data in a specific range
        around a fixed timestamp. Only graphs in [ts + window_l, ts + window_r] are
        considered.

        # Arguments
        window_l: Left boundary of the interval, relative to the timestamp.
        window_r: Right boundary of the interval, relative to the timestamp.
        """

        window = self.Window(window_l, window_r)
        return window.SumEdges(eps=eps)

    def WindowSumEdgesExp(self, window, beta=None, log_beta=None, eps=0.0):
        """
        Create a new exponential decay window to aggregate data in a specific range
        around a fixed timestamp. Only graphs in [ts - window, window] are considered.

        # Arguments
        window: Amount of data in the past to consider.
        beta: Exponential decay constant.
        """

        window = self.Window(-window, 0)
        return window.SumEdgesExp(beta=beta, log_beta=log_beta, eps=eps)

    def WindowSumEdgesExpNorm(self, window, beta=None, log_beta=None, eps=0.0):
        """
        Create a new exponential smoothing window to aggregate data in a specific range
        around a fixed timestamp. Only graphs in [ts - window, window] are considered.

        # Arguments
        window: Amount of data in the past to consider.
        beta: Exponential decay constant.
        """

        window = self.Window(-window, 0)
        return window.SumEdgesExpNorm(beta=beta, log_beta=log_beta, eps=eps)

    def WindowCountEdges(self, window_l, window_r):
        """
        Create a new rectangular filter window to count edges in a specific range
        around a fixed timestamp. Only graphs in [ts + window_l, ts + window_r] are
        considered.

        # Arguments
        window_l: Left boundary of the interval, relative to the timestamp.
        window_r: Right boundary of the interval, relative to the timestamp.
        """

        window = self.Window(window_l, window_r)
        return window.CountEdges()

    def WindowCountNodes(self, window_l, window_r):
        """
        Create a new rectangular filter window to count nodes in a specific range
        around a fixed timestamp. Only graphs in [ts + window_l, ts + window_r] are
        considered.

        # Arguments
        window_l: Left boundary of the interval, relative to the timestamp.
        window_r: Right boundary of the interval, relative to the timestamp.
        """

        window = self.Window(window_l, window_r)
        return window.CountNodes()

    def lookup_ge(self, ts=0):
        """ Search for the first graph with timestamps `>= ts`. """
        if isinstance(ts, float):
            ts = math.ceil(ts)
        obj = lib.tvg_lookup_graph_ge(self._obj, ts)
        return Graph(obj=obj) if obj else None

    def lookup_le(self, ts=0xffffffffffffffff):
        """ Search for the last graph with timestamps `<= ts`. """
        if isinstance(ts, float):
            ts = int(ts)
        obj = lib.tvg_lookup_graph_le(self._obj, ts)
        return Graph(obj=obj) if obj else None

    def lookup_near(self, ts):
        """ Search for a graph with a timestamp close to `ts`. """
        if isinstance(ts, float):
            ts = int(ts + 0.5)
        obj = lib.tvg_lookup_graph_near(self._obj, ts)
        return Graph(obj=obj) if obj else None

    def compress(self, step, offset=0):
        """ Compress the graph by aggregating timestamps differing by at most `step`. """
        if step > 0 and np.isinf(step):
            step = 0
        res = lib.tvg_compress(self._obj, step, offset)
        if not res:
            raise MemoryError

@libtvgobject
class Metric(object):
    def __init__(self, obj=None):
        if obj is None:
            raise NotImplementedError

        self._obj = obj
        if not obj:
            raise MemoryError

        self._window = Window(obj=lib.metric_get_window(self._obj))

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_metric(self._obj)

    def _get_obj(self):
        lib.free_metric(self._obj)
        return self

    @property
    def window(self):
        """ Get the associated window. """
        return self._window

    @property
    def ts(self):
        """ Return the current timestamp of the window. """
        return self._window.ts

    @property
    def width(self):
        """ Return the width of the window. """
        return self._window.width

    @property
    def result(self):
        return None

    def reset(self):
        """ Clear all additional data associated with the metric. """
        lib.metric_reset(self._obj)

    def update(self, ts):
        """ Move the sliding window to a new timestamp. """
        self._window.update(ts)
        return self.result

    def sources(self):
        """ Return all graphs of the current window. """
        return self._window.sources()

class MetricGraph(Metric):
    def sample_eigenvectors(self, ts, sample_width, sample_steps=9, tolerance=None):
        """
        Iterative power iteration algorithm to track eigenvectors of a graph over time.
        Collection of eigenvectors starts at t = (ts - sample_width) and continues up
        to t = ts. Each entry of the returned dictionary contains sample_steps values
        collected at equidistant time steps.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.
        tolerance: Tolerance for the power_iteration algorithm.

        # Returns
        Dictionary containing lists of collected values for each node.
        """

        eigenvector = None
        result = collections.defaultdict(list)

        for step, ts in enumerate(np.linspace(ts - sample_width, ts, sample_steps)):
            graph = self.update(int(ts))
            eigenvector, _ = graph.power_iteration(initial_guess=eigenvector, tolerance=tolerance,
                                                   ret_eigenvalue=False)

            indices, weights = eigenvector.entries()
            for i, w in zip(indices, weights):
                result[i] += [0.0] * (step - len(result[i]))
                result[i].append(w)

        for i in result.keys():
            result[i] += [0.0] * (sample_steps - len(result[i]))

        return result

    def sample_edges(self, ts, sample_width, sample_steps=9):
        """
        Collect edges starting at t = (ts - sample_width) and continue up to t = ts.
        Each entry of the returned dictionary contains sample_steps value collected
        at equidistant time steps.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.

        # Returns
        Dictionary containing lists of collected values for each edge.
        """

        result = collections.defaultdict(list)

        for step, ts in enumerate(np.linspace(ts - sample_width, ts, sample_steps)):
            graph = self.update(int(ts))

            indices, weights = graph.edges()
            for i, w in zip(indices, weights):
                i = tuple(i)
                result[i] += [0.0] * (step - len(result[i]))
                result[i].append(w)

        for i in result.keys():
            result[i] += [0.0] * (sample_steps - len(result[i]))

        return result

    def metric_entropy(self, ts, sample_width, sample_steps=9, tolerance=None, num_bins=50):
        """
        Rate the importance / interestingness of individual nodes by their entropy.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.
        tolerance: Tolerance for the power_iteration algorithm.
        num_bins: Number of bins used to create the entropy model.

        # Returns
        Dictionary containing the metric for each node.
        """

        values = self.sample_eigenvectors(ts, sample_width, sample_steps=sample_steps, tolerance=tolerance)

        data = []
        for i in values.keys():
            data += values[i]

        prob, bin_edges = np.histogram(data, bins=num_bins)
        prob = np.array(prob, dtype=float) / np.sum(prob)
        entropy = (- np.ma.log(prob) * prob).filled(0)

        @np.vectorize
        def to_entropy(x):
            index = np.searchsorted(bin_edges, x)
            if index >= 1: index -= 1
            return entropy[index]

        result = {}
        for i in values.keys():
            result[i] = np.sum(to_entropy(values[i]))

        return result

    def metric_entropy_local(self, ts, sample_width, sample_steps=9, tolerance=None, num_bins=50):
        """
        Like metric_entropy(), but train a separate model for each time step.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.
        tolerance: Tolerance for the power_iteration algorithm.
        num_bins: Number of bins used to create the entropy model.

        # Returns
        Dictionary containing the metric for each node.
        """

        values = self.sample_eigenvectors(ts, sample_width, sample_steps=sample_steps, tolerance=tolerance)

        result = collections.defaultdict(float)
        for j in range(sample_steps):

            data = []
            for i in values.keys():
                data.append(values[i][j])

            prob, bin_edges = np.histogram(data, bins=num_bins)
            prob = np.array(prob, dtype=float) / np.sum(prob)
            entropy = (- np.ma.log(prob) * prob).filled(0)

            def to_entropy(x):
                index = np.searchsorted(bin_edges, x)
                if index >= 1: index -= 1
                return entropy[index]

            for i in values.keys():
                result[i] += to_entropy(values[i][j])

        return result

    def metric_entropy_2d(self, ts, sample_width, sample_steps=9, tolerance=None, num_bins=50):
        """
        Like metric_entropy(), but train a 2-dimensional model for entropy estimations.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.
        tolerance: Tolerance for the power_iteration algorithm.
        num_bins: Number of bins used to create the entropy model.

        # Returns
        Dictionary containing the metric for each node.
        """

        values = self.sample_eigenvectors(ts, sample_width, sample_steps=sample_steps, tolerance=tolerance)

        data_x = []
        data_y = []
        for i in values.keys():
            data_x += values[i][:-1]
            data_y += values[i][1:]

        prob, bin_edges_x, bin_edges_y = np.histogram2d(data_x, data_y, bins=num_bins)

        prob = np.array(prob, dtype=float) / np.sum(prob)
        entropy = (- np.ma.log(prob) * prob).filled(0)

        @np.vectorize
        def to_entropy(x, y):
            index_x = np.searchsorted(bin_edges_x, x)
            index_y = np.searchsorted(bin_edges_y, y)
            if index_x >= 1: index_x -= 1
            if index_y >= 1: index_y -= 1
            return entropy[index_x, index_y]

        result = {}
        for i in values.keys():
            result[i] = np.sum(to_entropy(values[i][:-1], values[i][1:]))

        return result

    def metric_trend(self, ts, sample_width, sample_steps=9, tolerance=None):
        """
        Rate the importance / interestingness of individual nodes by their trend.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.
        tolerance: Tolerance for the power_iteration algorithm.

        # Returns
        Dictionary containing the metric for each node.
        """

        values = self.sample_eigenvectors(ts, sample_width, sample_steps=sample_steps, tolerance=tolerance)

        A = np.zeros((sample_steps, 2))
        A[:, 0] = 1.0
        A[:, 1] = range(A.shape[0])

        kwargs = {}
        if np.lib.NumpyVersion(np.__version__) >= '1.14.0':
            kwargs['rcond'] = None

        result = {}
        for i in values.keys():
            result[i] = np.linalg.lstsq(A, values[i], **kwargs)[0][1]

        return result

    def metric_stability(self, ts, sample_width, sample_steps=9, tolerance=None):
        """
        Rate the stability of individual nodes by ranking their average and standard deviation.

        # Arguments
        ts: Timestamp of the window.
        sample_width: Width of the region to collect samples.
        sample_steps: Number of values to collect.
        tolerance: Tolerance for the power_iteration algorithm.

        # Returns
        Dictionary containing the metric for each node.
        """

        values = self.sample_eigenvectors(ts, sample_width, sample_steps=sample_steps, tolerance=tolerance)

        nodes = []
        costs = []
        for i in values.keys():
            nodes.append(i)
            costs.append([-np.mean(values[i]), np.std(values[i])])

        nodes = np.array(nodes)
        costs = np.array(costs)
        rank = 1.0

        result = {}
        while len(nodes):
            front = np.ones(costs.shape[0], dtype=bool)
            for i, c in enumerate(costs):
                if front[i]:
                    front[front] = np.any(costs[front] < c, axis=1)
                    front[i] = True

            for i in np.where(front)[0]:
                result[nodes[i]] = rank

            nodes = nodes[~front]
            costs = costs[~front]
            rank += 1.0

        return result

class MetricSumEdges(MetricGraph):
    @property
    def eps(self):
        """ Get the epsilon parameter. """
        return lib.metric_sum_edges_get_eps(self._obj)

    @property
    def result(self):
        """ Get the current graph based on the rectangle window. """
        return Graph(obj=lib.metric_sum_edges_get_result(self._obj))

class MetricSumEdgesExp(MetricGraph):
    @property
    def weight(self):
        """ Get the weight parameter. """
        return lib.metric_sum_edges_exp_get_weight(self._obj)

    @property
    def log_beta(self):
        """ Get the log_beta parameter. """
        return lib.metric_sum_edges_exp_get_log_beta(self._obj)

    @property
    def eps(self):
        """ Get the epsilon parameter. """
        return lib.metric_sum_edges_exp_get_eps(self._obj)

    @property
    def result(self):
        """ Get the current graph based on the exponential decay window. """
        return Graph(obj=lib.metric_sum_edges_exp_get_result(self._obj))

class MetricCountEdges(MetricGraph):
    @property
    def result(self):
        """ Get the current graph base on edge counts. """
        return Graph(obj=lib.metric_count_edges_get_result(self._obj))

class MetricCountNodes(MetricGraph):
    @property
    def result(self):
        """ Get the current graph base on node counts. """
        return Vector(obj=lib.metric_count_nodes_get_result(self._obj))

@libtvgobject
class Window(object):
    """
    This object represents a sliding window, which can be used to extract and aggregate
    data in a specific timeframe. Once the object has been created, most parameters can
    not be changed anymore. Only the timestamp can be changed.
    """

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

    def _get_obj(self):
        lib.free_window(self._obj)
        return self

    @property
    def ts(self):
        """ Return the current timestamp of the window. """
        return self._obj.contents.ts

    @property
    def width(self):
        """ Return the width of the window. """
        return self._obj.contents.window_r - self._obj.contents.window_l

    def SumEdges(self, eps=0.0):
        """ Create a new rectangular filter metric. """
        return MetricSumEdges(obj=lib.window_alloc_metric_sum_edges(self._obj, eps))

    def SumEdgesExp(self, weight=1.0, beta=None, log_beta=None, eps=0.0):
        """
        Create a new exponential decay metric.

        # Arguments
        beta: Exponential decay constant.
        """

        if log_beta is None:
            log_beta = math.log(beta)
        return MetricSumEdgesExp(obj=lib.window_alloc_metric_sum_edges_exp(self._obj, weight, log_beta, eps))

    def SumEdgesExpNorm(self, beta=None, log_beta=None, eps=0.0):
        """
        Create a new exponential smoothing metric.

        # Arguments
        beta: Exponential decay constant.
        """

        if log_beta is None:
            log_beta = math.log(beta)
        return self.SumEdgesExp(weight=-np.expm1(log_beta), log_beta=log_beta, eps=eps)

    def CountEdges(self):
        """ Create a new edge count metric. """
        return MetricCountEdges(obj=lib.window_alloc_metric_count_edges(self._obj))

    def CountNodes(self):
        """ Create a new node count metric. """
        return MetricCountNodes(obj=lib.window_alloc_metric_count_nodes(self._obj))

    def reset(self):
        """"
        Clear all additional data associated with the window, and force a full recompute
        when the `update` function is used the next time.
        """

        lib.window_reset(self._obj)

    def update(self, ts):
        """
        Move the sliding window to a new timestamp. Whenever possible, the previous state
        will be reused to speed up the computation. For rectangular windows, for example,
        it is sufficient to add data points that are moved into the interval, and to remove
        data points that are now outside of the interval. For exponential windows, it is
        also necessary to perform a multiplication of the full graph.

        # Arguments
        ts: New timestamp of the window.
        """

        res = lib.window_update(self._obj, ts)
        if not res:
            raise MemoryError

    def sources(self):
        """ Return all graphs of the current window. """

        num_sources = 100 # FIXME: Arbitrary limit.
        while True:
            max_sources = num_sources
            graphs = (c_graph_p * max_sources)()
            num_sources = lib.window_get_sources(self._obj, graphs, max_sources)
            if num_sources <= max_sources:
                break
            for obj in graphs:
                lib.free_graph(obj)
            graphs = None

        if graphs is not None:
            graphs = [Graph(obj=obj) for obj in graphs[:num_sources]]

        return graphs

@libtvgobject
class MongoDB(object):
    """
    This object represents a MongoDB connection.

    # Arguments
    uri: URI to identify the MongoDB server, e.g., mongodb://localhost.
    database: Name of the database.

    col_articles: Name of the articles collection.
    article_id: Name of the article ID key.
    article_time: Name of the article time key.

    filter_key: Filter articles by comparing the value of a given key.
    filter_value: Expected value of filter key.

    col_entities: Name of the entities collection.
    entity_doc: Name of the entity doc key.
    entity_sen: Name of the entity sen key.
    entity_ent: Name(s) of the entity ent key, e.g., attr1;attr2;attr3.

    use_pool: Use a connection pool to access MongoDB.
    load_nodes: Load node attributes.
    sum_weights: Compute edge weights as the sum of co-occurrence weights.

    max_distance: Maximum distance of mentions.
    """

    def __init__(self, uri, database, col_articles, article_id, article_time,
                 col_entities, entity_doc, entity_sen, entity_ent, use_pool=True,
                 load_nodes=False, sum_weights=True, max_distance=None, filter_key=None,
                 filter_value=None, use_objectids=None, obj=None):
        if obj is None:
            config = c_mongodb_config()
            config.uri           = uri.encode("utf-8")
            config.database      = database.encode("utf-8")
            config.col_articles  = col_articles.encode("utf-8")
            config.article_id    = article_id.encode("utf-8")
            config.article_time  = article_time.encode("utf-8")
            config.filter_key    = filter_key.encode("utf-8")   if filter_key   is not None else None
            config.filter_value  = filter_value.encode("utf-8") if filter_value is not None else None
            config.col_entities  = col_entities.encode("utf-8")
            config.entity_doc    = entity_doc.encode("utf-8")
            config.entity_sen    = entity_sen.encode("utf-8")
            config.entity_ent    = entity_ent.encode("utf-8")
            config.use_pool      = use_pool
            config.load_nodes    = load_nodes
            config.sum_weights   = sum_weights
            config.max_distance  = max_distance if max_distance is not None else 0xffffffffffffffff
            obj = lib.alloc_mongodb(config)

        self._obj = obj
        if not obj:
            raise MemoryError

    def __del__(self):
        if lib is None:
            return
        if self._obj:
            lib.free_mongodb(self._obj)

    def _get_obj(self):
        lib.free_mongodb(self._obj)
        return self

if __name__ == '__main__':
    import datetime
    import unittest
    import mockupdb
    import tempfile
    import bson
    import gc

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

            v.add_entries([])
            v.add_entries(test_indices)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [3.0, 5.0, 7.0])

            v.sub_entries([], [])
            v.sub_entries(test_indices, -test_weights)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [4.0, 7.0, 10.0])

            v.sub_entries([])
            v.sub_entries(test_indices)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [3.0, 6.0, 9.0])

            v.set_entries([], [])
            v.set_entries(test_indices, test_weights)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [1.0, 2.0, 3.0])

            v.set_entries([])
            v.set_entries(test_indices)
            indices, weights = v.entries()
            self.assertEqual(indices.tolist(), [0, 1, 2])
            self.assertEqual(weights.tolist(), [1.0, 1.0, 1.0])

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

        def test_sub_vector_norm(self):
            v = Vector()
            v[0] = 2.0

            w = Vector()
            w[0] = 5.0
            w[1] = 4.0

            self.assertEqual(v.sub_vector_norm(v), 0.0)
            self.assertEqual(w.sub_vector_norm(w), 0.0)
            self.assertEqual(v.sub_vector_norm(w), 5.0)
            self.assertEqual(w.sub_vector_norm(v), 5.0)

            del v
            del w

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

        def test_as_dict(self):
            v = Vector()
            for i in range(10):
                v[i] = i * i

            result = v.as_dict()
            self.assertEqual(result, {0: 0.0, 1: 1.0, 2: 4.0, 3: 9.0, 4: 16.0,
                                      5: 25.0, 6: 36.0, 7: 49.0, 8: 64.0, 9: 81.0})
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
            v, _ = g.power_iteration(tolerance=1e-3)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-3)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-3)
            del v
            w = Vector()
            w[0] = 1.0 / math.sqrt(2)
            w[1] = 1.0 / math.sqrt(2)
            v, _ = g.power_iteration(initial_guess=w, num_iterations=1)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-7)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-7)
            del v
            del w

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
            v, _ = g.power_iteration(tolerance=1e-3)
            self.assertTrue(abs(v[0] - 1.0 / math.sqrt(2)) < 1e-3)
            self.assertTrue(abs(v[1] - 1.0 / math.sqrt(2)) < 1e-3)
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

            g.add_edges([])
            g.add_edges(test_indices)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [7.0, 3.0, 5.0])

            g.sub_edges([], [])
            g.sub_edges(test_indices, -test_weights)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [10.0, 4.0, 7.0])

            g.sub_edges([])
            g.sub_edges(test_indices)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [9.0, 3.0, 6.0])

            g.set_edges([], [])
            g.set_edges(test_indices, test_weights)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [3.0, 1.0, 2.0])

            g.set_edges([])
            g.set_edges(test_indices)
            indices, weights = g.edges()
            self.assertEqual(indices.tolist(), [[2, 0], [0, 1], [1, 2]])
            self.assertEqual(weights.tolist(), [1.0, 1.0, 1.0])

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

        def test_filter_nodes(self):
            g = Graph(directed=True)
            g[0, 1] = 1.0
            g[1, 2] = 2.0
            g[2, 3] = 3.0
            g[3, 4] = 4.0
            g[2, 4] = 5.0

            h = g.filter_nodes([1, 2, 3])
            indices, weights = h.edges()
            self.assertEqual(indices.tolist(), [[1, 2], [2, 3]])
            self.assertEqual(weights.tolist(), [2.0, 3.0])

            del g
            del h

        def test_as_dict(self):
            g = Graph(directed=True)
            for i in range(100):
                s, t = i//10, i%10
                g[s, t] = i

            result = g.as_dict()
            self.assertEqual(len(result), 100)
            for i in range(100):
                s, t = i//10, i%10
                self.assertEqual(result[s, t], i)
            del g

    class TVGTests(unittest.TestCase):
        def test_lookup(self):
            tvg = TVG(positive=True)
            self.assertEqual(tvg.flags, TVG_FLAGS_POSITIVE)
            mem = tvg.memory_usage

            g1 = tvg.Graph(100)
            self.assertEqual(g1.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g1.ts, 100)
            g2 = tvg.Graph(200)
            self.assertEqual(g2.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g2.ts, 200)
            g3 = tvg.Graph(300)
            self.assertEqual(g3.flags, TVG_FLAGS_NONZERO | TVG_FLAGS_POSITIVE)
            self.assertEqual(g3.ts, 300)
            self.assertGreater(tvg.memory_usage, mem)

            g = tvg.lookup_le(50)
            self.assertEqual(g, None)
            g = tvg.lookup_ge(50)
            self.assertEqual(g, g1)

            g = tvg.lookup_le(150)
            self.assertEqual(g, g1)
            g = tvg.lookup_ge(150)
            self.assertEqual(g, g2)

            g = tvg.lookup_le(250)
            self.assertEqual(g, g2)
            g = tvg.lookup_ge(250)
            self.assertEqual(g, g3)

            g = tvg.lookup_le(350)
            self.assertEqual(g, g3)
            g = tvg.lookup_ge(350)
            self.assertEqual(g, None)

            g = tvg.lookup_near(149)
            self.assertEqual(g, g1)
            g = tvg.lookup_near(151)
            self.assertEqual(g, g2)

            # For backwards compatibility, we still allow passing float values.

            g = tvg.lookup_ge(100.0)
            self.assertEqual(g, g1)
            g = tvg.lookup_ge(100.01)
            self.assertEqual(g, g2)

            g = tvg.lookup_le(200.0)
            self.assertEqual(g, g2)
            g = tvg.lookup_le(199.99)
            self.assertEqual(g, g1)

            g = tvg.lookup_near(149.49)
            self.assertEqual(g, g1)
            g = tvg.lookup_near(150.51)
            self.assertEqual(g, g2)

            del tvg

        def test_link(self):
            tvg = TVG()
            g1 = Graph()
            g2 = Graph(directed=True)

            tvg.link_graph(g1, 10)
            with self.assertRaises(RuntimeError):
                tvg.link_graph(g1, 20)
            with self.assertRaises(RuntimeError):
                tvg.link_graph(g2, 20)

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
            filename_graphs = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.graph")
            filename_nodes = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.nodes")
            tvg = TVG.load(filename_graphs, nodes=filename_nodes)
            tvg.set_primary_key(["a", "b", "c"])
            tvg.set_primary_key(["text"])

            l = tvg.node_by_index(1)
            self.assertEqual(l.text, "polic")
            l = tvg.node_by_index(362462)
            self.assertEqual(l.text, "Jay Wright (basketball)")
            with self.assertRaises(KeyError):
                tvg.node_by_index(5)

            l = tvg.node_by_text("polic")
            self.assertEqual(l.index, 1)
            l = tvg.node_by_text("Jay Wright (basketball)")
            self.assertEqual(l.index, 362462)
            with self.assertRaises(KeyError):
                tvg.node_by_text("should-not-exist")

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

        def test_load_crlf(self):
            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.graph")
            with open(filename, "rb") as fp:
                content = fp.read()

            temp_graph = tempfile.NamedTemporaryFile()
            temp_graph.write(content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
            temp_graph.flush()

            filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../datasets/example/example-tvg.nodes")
            with open(filename, "rb") as fp:
                content = fp.read()

            temp_nodes = tempfile.NamedTemporaryFile()
            temp_nodes.write(content.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
            temp_nodes.flush()

            tvg = TVG.load(temp_graph.name, nodes=temp_nodes.name, primary_key=["text"])

            temp_graph.close()
            temp_nodes.close()

            l = tvg.node_by_index(1)
            self.assertEqual(l.text, "polic")
            l = tvg.node_by_index(362462)
            self.assertEqual(l.text, "Jay Wright (basketball)")
            with self.assertRaises(KeyError):
                tvg.node_by_index(5)

            l = tvg.node_by_text("polic")
            self.assertEqual(l.index, 1)
            l = tvg.node_by_text("Jay Wright (basketball)")
            self.assertEqual(l.index, 362462)
            with self.assertRaises(KeyError):
                tvg.node_by_text("should-not-exist")

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

            del tvg

        def test_nodes(self):
            tvg = TVG()
            tvg.set_primary_key("text")

            l = tvg.Node(text="A", other="sample text")
            self.assertEqual(l.index, 0)
            self.assertEqual(l.text, "A")
            l = tvg.Node(text="B")
            self.assertEqual(l.index, 1)
            self.assertEqual(l.text, "B")
            l = tvg.Node(text="C")
            self.assertEqual(l.index, 2)
            self.assertEqual(l.text, "C")
            l = tvg.Node(text="D")
            self.assertEqual(l.index, 3)
            self.assertEqual(l.text, "D")

            l = tvg.Node(text="A")
            self.assertEqual(l.index, 0)
            self.assertEqual(l.text, "A")
            self.assertEqual(l['other'], "sample text")

            l = tvg.node_by_index(1)
            self.assertEqual(l.index, 1)
            self.assertEqual(l.text, "B")

            with self.assertRaises(KeyError):
                tvg.node_by_index(4)

            l = tvg.node_by_text("C")
            self.assertEqual(l.index, 2)
            self.assertEqual(l.text, "C")

            with self.assertRaises(KeyError):
                tvg.node_by_text("E")

            l.unlink()

            with self.assertRaises(KeyError):
                tvg.node_by_index(2)

            with self.assertRaises(KeyError):
                tvg.node_by_text("C")

            l = Node(text="Z")
            tvg.link_node(l, 4)
            self.assertEqual(l.index, 4)
            self.assertEqual(l.text, "Z")

            l = tvg.node_by_index(4)
            self.assertEqual(l.index, 4)
            self.assertEqual(l.text, "Z")

            l = tvg.node_by_text("Z")
            self.assertEqual(l.index, 4)
            self.assertEqual(l.text, "Z")

            l = Node(text="Z")
            self.assertEqual(l.index, 0xffffffffffffffff)
            with self.assertRaises(RuntimeError):
                tvg.link_node(l)
            self.assertEqual(l.index, 0xffffffffffffffff)

            del tvg

        def test_node_attrs(self):
            tvg = TVG()
            tvg.set_primary_key("text")

            l = tvg.Node(text="sample text")
            self.assertEqual(l.as_dict(), {'text': "sample text"})

            with self.assertRaises(KeyError):
                l["text"] = "other text"

            l["attr1"] = "sample attr1"
            l["attr2"] = "sample attr2"
            l["attr3"] = "sample attr3"
            self.assertEqual(l.as_dict(), {'text': "sample text",
                                           'attr1': "sample attr1",
                                           'attr2': "sample attr2",
                                           'attr3': "sample attr3"})

            l["attr1"] = "other attr1"
            self.assertEqual(l.as_dict(), {'text': "sample text",
                                           'attr1': "other attr1",
                                           'attr2': "sample attr2",
                                           'attr3': "sample attr3"})

            tvg.set_primary_key(["text", "attr1"])
            with self.assertRaises(KeyError):
                l["attr1"] = "sample attr1"

            del tvg

    class WindowTests(unittest.TestCase):
        def test_sum_edges(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[0, 1] = 2.0
            g = tvg.Graph(300)
            g[0, 2] = 3.0

            with self.assertRaises(MemoryError):
                tvg.WindowSumEdges(0, 0)
            with self.assertRaises(MemoryError):
                tvg.WindowSumEdges(1, 0)

            window = tvg.WindowSumEdges(-50, 50, eps=0.5)
            self.assertEqual(window.width, 100)
            self.assertEqual(window.eps, 0.5)

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
            window.reset()
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

        def test_sum_edges_exp_precision(self):
            tvg = TVG(positive=True)
            beta = 0.3

            g = tvg.Graph(0)
            g[0, 0] = 1.0

            with self.assertRaises(MemoryError):
                tvg.WindowSumEdgesExp(0, beta)
            with self.assertRaises(MemoryError):
                tvg.WindowSumEdgesExp(-1, beta)

            window = tvg.WindowSumEdgesExp(np.inf, beta)
            self.assertEqual(window.weight, 1.0)
            self.assertTrue(abs(window.log_beta - np.log(beta)) < 1e-7)
            self.assertEqual(window.eps, 0.0)

            g = window.update(100)
            self.assertTrue(abs(g[0, 0] - math.pow(beta, 100.0)) < 1e-7)

            g = window.update(0)
            self.assertTrue(abs(g[0, 0] - 1.0) < 1e-7)

            del window
            del g

        def test_sum_edges_exp_norm(self):
            source = np.random.rand(100)
            beta = 0.3

            tvg = TVG(positive=True)

            for t, s in enumerate(source):
                g = tvg.Graph(t)
                g[0, 0] = s

            with self.assertRaises(MemoryError):
                tvg.WindowSumEdgesExpNorm(0, beta)
            with self.assertRaises(MemoryError):
                tvg.WindowSumEdgesExpNorm(-1, beta)

            window = tvg.WindowSumEdgesExpNorm(np.inf, beta)
            self.assertTrue(abs(window.weight + np.expm1(np.log(beta))) < 1e-7)
            self.assertTrue(abs(window.log_beta - np.log(beta)) < 1e-7)
            self.assertEqual(window.eps, 0.0)

            expected = 0.0
            for t, s in enumerate(source):
                g = window.update(t)
                self.assertEqual(window.ts, t)
                expected = beta * expected + (1.0 - beta) * s
                self.assertTrue(abs(g[0, 0] - expected) < 1e-6)
            del window

            window = tvg.WindowSumEdgesExpNorm(np.inf, log_beta=math.log(beta))
            self.assertTrue(abs(window.weight + np.expm1(np.log(beta))) < 1e-7)
            self.assertTrue(abs(window.log_beta - np.log(beta)) < 1e-7)
            self.assertEqual(window.eps, 0.0)

            expected = 0.0
            for t, s in enumerate(source):
                g = window.update(t)
                self.assertEqual(window.ts, t)
                expected = beta * expected + (1.0 - beta) * s
                self.assertTrue(abs(g[0, 0] - expected) < 1e-6)
            del window
            del tvg

        def test_count_edges(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[0, 1] = 2.0
            g = tvg.Graph(300)
            g[0, 2] = 3.0

            with self.assertRaises(MemoryError):
                tvg.WindowCountEdges(0, 0)
            with self.assertRaises(MemoryError):
                tvg.WindowCountEdges(1, 0)

            window = tvg.WindowCountEdges(-50, 50)
            self.assertEqual(window.width, 100)

            g = window.update(100)
            self.assertEqual(window.ts, 100)
            self.assertEqual(g[0, 0], 1.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 0.0)

            g = window.update(200)
            self.assertEqual(window.ts, 200)
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 1.0)
            self.assertEqual(g[0, 2], 0.0)

            g = window.update(300)
            self.assertEqual(window.ts, 300)
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 1.0)

            # Clearing the window should not modify the last output graph.
            window.reset()
            g2 = window.update(100)
            self.assertEqual(window.ts, 100)

            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 1.0)

            self.assertEqual(g2[0, 0], 1.0)
            self.assertEqual(g2[0, 1], 0.0)
            self.assertEqual(g2[0, 2], 0.0)

            del window
            del tvg

        def test_count_nodes(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[0, 1] = 2.0
            g[1, 2] = 2.0
            g = tvg.Graph(300)
            g[0, 2] = 3.0

            with self.assertRaises(MemoryError):
                tvg.WindowCountNodes(0, 0)
            with self.assertRaises(MemoryError):
                tvg.WindowCountNodes(1, 0)

            window = tvg.WindowCountNodes(-50, 50)
            self.assertEqual(window.width, 100)

            v = window.update(100)
            self.assertEqual(window.ts, 100)
            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 0.0)
            self.assertEqual(v[2], 0.0)

            v = window.update(200)
            self.assertEqual(window.ts, 200)
            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 1.0)
            self.assertEqual(v[2], 1.0)

            v = window.update(300)
            self.assertEqual(window.ts, 300)
            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 0.0)
            self.assertEqual(v[2], 1.0)

            # Clearing the window should not modify the last output graph.
            window.reset()
            v2 = window.update(100)
            self.assertEqual(window.ts, 100)

            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 0.0)
            self.assertEqual(v[2], 1.0)

            self.assertEqual(v2[0], 1.0)
            self.assertEqual(v2[1], 0.0)
            self.assertEqual(v2[2], 0.0)

            del window
            del tvg

        def test_multi(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[0, 1] = 2.0
            g[1, 2] = 2.0
            g = tvg.Graph(300)
            g[0, 2] = 3.0

            window = tvg.Window(-50, 50)
            self.assertEqual(window.width, 100)
            metric_edges = window.CountEdges()
            metric_nodes = window.CountNodes()

            window.update(100)
            self.assertEqual(window.ts, 100)

            g = metric_edges.result
            self.assertEqual(g[0, 0], 1.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 0.0)

            v = metric_nodes.result
            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 0.0)
            self.assertEqual(v[2], 0.0)

            window.update(200)
            self.assertEqual(window.ts, 200)

            g = metric_edges.result
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 1.0)
            self.assertEqual(g[0, 2], 0.0)

            v = metric_nodes.result
            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 1.0)
            self.assertEqual(v[2], 1.0)

            window.update(300)
            self.assertEqual(window.ts, 300)

            g = metric_edges.result
            self.assertEqual(g[0, 0], 0.0)
            self.assertEqual(g[0, 1], 0.0)
            self.assertEqual(g[0, 2], 1.0)

            v = metric_nodes.result
            self.assertEqual(v[0], 1.0)
            self.assertEqual(v[1], 0.0)
            self.assertEqual(v[2], 1.0)

            del window
            del tvg

        def test_sample_eigenvectors(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.sample_eigenvectors(300, sample_width=200, sample_steps=3)
            self.assertEqual(len(values), 3)
            self.assertEqual(values[0], [1.0, 0.0, 0.0])
            self.assertEqual(values[1], [0.0, 1.0, 0.0])
            self.assertEqual(values[2], [0.0, 0.0, 1.0])

            del window
            del tvg

        def test_sample_edges(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.sample_edges(300, sample_width=200, sample_steps=3)
            self.assertEqual(len(values), 3)
            self.assertEqual(values[0, 0], [1.0, 0.0, 0.0])
            self.assertEqual(values[1, 1], [0.0, 2.0, 0.0])
            self.assertEqual(values[2, 2], [0.0, 0.0, 3.0])

            del window
            del tvg

        def test_metric_entropy(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = g[0, 1] = g[0, 2] = 1.0
            g[1, 1] = g[1, 2] = 1.0
            g[2, 2] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = g[1, 2] = 2.0
            g[2, 2] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.metric_entropy(300, sample_width=200, sample_steps=3, num_bins=6)
            P = np.array([3, 0, 0, 3, 2, 1]) / 9.0
            self.assertEqual(len(values), 3)
            self.assertEqual(values[0], - np.log(P[3]) * P[3] - np.log(P[0]) * P[0] - np.log(P[0]) * P[0])
            self.assertEqual(values[1], - np.log(P[3]) * P[3] - np.log(P[4]) * P[4] - np.log(P[0]) * P[0])
            self.assertEqual(values[2], - np.log(P[3]) * P[3] - np.log(P[4]) * P[4] - np.log(P[5]) * P[5])

            del window
            del tvg

        def test_metric_entropy_local(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = g[0, 1] = g[0, 2] = 1.0
            g[1, 1] = g[1, 2] = 1.0
            g[2, 2] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = g[1, 2] = 2.0
            g[2, 2] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.metric_entropy_local(300, sample_width=200, sample_steps=3, num_bins=2)
            P0 = 1.0
            P1 = np.array([1, 2]) / 3.0
            P2 = np.array([2, 1]) / 3.0
            self.assertEqual(len(values), 3)
            self.assertEqual(values[0], - np.log(P0) * P0 - np.log(P1[0]) * P1[0] - np.log(P2[0]) * P2[0])
            self.assertEqual(values[1], - np.log(P0) * P0 - np.log(P1[1]) * P1[1] - np.log(P2[0]) * P2[0])
            self.assertEqual(values[2], - np.log(P0) * P0 - np.log(P1[1]) * P1[1] - np.log(P2[1]) * P2[1])

            del window
            del tvg

        def test_metric_2d(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = g[0, 1] = g[0, 2] = 1.0
            g[1, 1] = g[1, 2] = 1.0
            g[2, 2] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = g[1, 2] = 2.0
            g[2, 2] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.metric_entropy_2d(300, sample_width=200, sample_steps=3, num_bins=2)
            P = np.array([[1, 0], [2, 3]]) / 6.0
            self.assertEqual(len(values), 3)
            self.assertEqual(values[0], - np.log(P[1, 0]) * P[1, 0] - np.log(P[0, 0]) * P[0, 0])
            self.assertEqual(values[1], - np.log(P[1, 1]) * P[1, 1] - np.log(P[1, 0]) * P[1, 0])
            self.assertEqual(values[2], - np.log(P[1, 1]) * P[1, 1] - np.log(P[1, 1]) * P[1, 1])

            del window
            del tvg

        def test_metric_trend(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = g[0, 1] = g[0, 2] = 1.0
            g[1, 1] = g[1, 2] = 1.0
            g[2, 2] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = g[1, 2] = 2.0
            g[2, 2] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.metric_trend(300, sample_width=200, sample_steps=3)
            self.assertEqual(len(values), 3)
            self.assertTrue(abs(values[0] + 0.288675129) < 1e-7)
            self.assertTrue(abs(values[1] + 0.288675129) < 1e-7)
            self.assertTrue(abs(values[2] - 0.211324870) < 1e-7)

            del window
            del tvg

        def test_metric_stability(self):
            tvg = TVG(positive=True)

            g = tvg.Graph(100)
            g[0, 0] = g[0, 1] = g[0, 2] = 1.0
            g[1, 1] = g[1, 2] = 1.0
            g[2, 2] = 1.0
            g = tvg.Graph(200)
            g[1, 1] = g[1, 2] = 2.0
            g[2, 2] = 2.0
            g = tvg.Graph(300)
            g[2, 2] = 3.0

            window = tvg.WindowSumEdges(-50, 50)
            self.assertEqual(window.width, 100)

            values = window.metric_stability(300, sample_width=200, sample_steps=3)
            self.assertEqual(len(values), 3)
            self.assertEqual(values[2], 1.0)
            self.assertEqual(values[0], 2.0)
            self.assertEqual(values[1], 2.0)

            del window
            del tvg

        def test_sources(self):
            tvg = TVG(positive=True)

            for t in range(50):
                g = tvg.Graph(t)
                g[t, t] = 1.0

            window = tvg.WindowSumEdges(-1000, 0)
            self.assertEqual(window.width, 1000)

            g = window.update(999)
            for t in range(50):
                self.assertEqual(g[t, t], 1.0)
            self.assertEqual(g[50, 50], 0.0)

            graphs = window.sources()
            self.assertEqual(len(graphs), 50)
            for t, g in enumerate(graphs):
                self.assertEqual(g.ts, t)
                self.assertEqual(g[t, t], 1.0)

            for t in range(50, 500):
                g = tvg.Graph(t)
                g[t, t] = 1.0

            g = window.update(999)
            for t in range(500):
                self.assertEqual(g[t, t], 1.0)
            self.assertEqual(g[500, 500], 0.0)

            graphs = window.sources()
            self.assertEqual(len(graphs), 500)
            for t, g in enumerate(graphs):
                self.assertEqual(g.ts, t)
                self.assertEqual(g[t, t], 1.0)

            del tvg

    class MongoDBTests(unittest.TestCase):
        def MongoDB(self, *args, **kwargs):
            future = mockupdb.go(MongoDB, *args, **kwargs)

            request = self.s.receives("isMaster")
            request.replies({'ok': 1, 'maxWireVersion': 5})

            request = self.s.receives("ping")
            request.replies({'ok': 1})

            return future()

        def setUp(self):
            self.s = mockupdb.MockupDB()
            self.s.run()

            self.db = self.MongoDB(self.s.uri, "database", "col_articles",
                                   "_id", "time", "col_entities", "doc", "sen", "ent",
                                   use_pool=False, max_distance=5, filter_key="fkey",
                                   filter_value="fvalue")

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
                        "_id", "time", "col_entities", "doc", "sen", "ent")

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
                               {'sen': 1 + i, 'ent': 2    },
                               {              'ent': 1    }, # no sen
                               {'sen': 1                  }] # no ent
                g = self.load_from_occurrences(occurrences)
                if i <= 5:
                    self.assertEqual(g.num_edges, 1)
                    self.assertTrue(abs(g[1, 2]/math.exp(-i) - 1.0) < 1e-7)
                else:
                    self.assertEqual(g.num_edges, 0)

        def test_load(self):
            future = mockupdb.go(TVG.load, self.db, primary_key="dummy")

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {'fkey': 'fvalue'})
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
            self.assertEqual(request["filter"], {'time': {'$gte': datetime.datetime.utcfromtimestamp(0)},
                                                 'fkey': 'fvalue'})
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
                                                         {"time": datetime.datetime.utcfromtimestamp(1546387200), "_id": {"$gt": 11}}],
                                                 'fkey': 'fvalue'})
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
            self.assertEqual(request["filter"], {'time': {'$lte': datetime.datetime.utcfromtimestamp(1546732800)},
                                                 'fkey': 'fvalue'})
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
                                                         {"time": datetime.datetime.utcfromtimestamp(1546646400), "_id": {"$lt": 14}}],
                                                 'fkey': 'fvalue'})
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
                                                         {"time": datetime.datetime.utcfromtimestamp(1546732800), "_id": {"$gt": 15}}],
                                                 'fkey': 'fvalue'})
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

        def test_streaming(self):
            tvg = TVG(streaming=True)
            tvg.enable_mongodb_sync(self.db, batch_size=2, cache_size=0x8000) # 32 kB cache

            future = mockupdb.go(tvg.lookup_le)

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {'fkey': 'fvalue'})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', -1), ('_id', -1)]))
            self.assertEqual(request["limit"], 2)
            documents = [{'_id': 11, 'time': datetime.datetime.utcfromtimestamp(1546387200)},
                         {'_id': 10, 'time': datetime.datetime.utcfromtimestamp(1546300800)}]
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            for i in range(2):
                request = self.s.receives()
                self.assertEqual(request["find"], "col_entities")
                self.assertEqual(request["filter"], {'doc': 11 - i})
                self.assertEqual(request["sort"], {'sen': 1})
                occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 3 - i}]
                request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            g = future()
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546387200000)
            self.assertEqual(g[1, 3], 1.0)

            g = g.prev
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_PREV)
            self.assertEqual(g.ts, 1546300800000)
            self.assertEqual(g[1, 2], 1.0)

            future = mockupdb.go(tvg.lookup_le)

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {'fkey': 'fvalue'})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', -1), ('_id', -1)]))
            self.assertEqual(request["limit"], 2)
            documents = [{'_id': 12, 'time': datetime.datetime.utcfromtimestamp(1546473600)},
                         {'_id': 11, 'time': datetime.datetime.utcfromtimestamp(1546387200)}]
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            request = self.s.receives()
            self.assertEqual(request["find"], "col_entities")
            self.assertEqual(request["filter"], {'doc': 12})
            self.assertEqual(request["sort"], {'sen': 1})
            occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 4}]
            request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            g = future()
            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546473600000)
            self.assertEqual(g[1, 4], 1.0)

            g2 = g.prev
            self.assertEqual(g2.revision, 0)
            self.assertEqual(g2.flags, 0)
            self.assertEqual(g2.ts, 1546387200000)
            self.assertEqual(g2[1, 3], 1.0)

            future = mockupdb.go(getattr, g, 'next')

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {"$or": [{"time": {"$gt": datetime.datetime.utcfromtimestamp(1546473600)}},
                                                         {"time": datetime.datetime.utcfromtimestamp(1546473600), "_id": {"$gt": 12}}],
                                                 'fkey': 'fvalue'})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', 1), ('_id', 1)]))
            self.assertEqual(request["limit"], 2)
            documents = []
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            g2 = future()
            self.assertEqual(g2, None)

            self.assertEqual(g.revision, 0)
            self.assertEqual(g.flags, TVG_FLAGS_LOAD_NEXT)
            self.assertEqual(g.ts, 1546473600000)
            self.assertEqual(g[1, 4], 1.0)

            tvg.disable_mongodb_sync()
            del tvg

        def test_objectid(self):
            self.db = self.MongoDB(self.s.uri, "database", "col_articles",
                                   "_id", "time", "col_entities", "doc", "sen", "ent",
                                   use_pool=False, max_distance=5)

            future = mockupdb.go(TVG.load, self.db, primary_key="dummy")

            request = self.s.receives()
            self.assertEqual(request["find"], "col_articles")
            self.assertEqual(request["filter"], {})
            self.assertEqual(request["sort"], collections.OrderedDict([('time', 1), ('_id', 1)]))
            documents = [{'_id': bson.ObjectId('123456781234567812345678'),
                          'time': datetime.datetime.utcfromtimestamp(1546300800)},
                         {'_id': bson.ObjectId('123456781234567812345679'),
                          'time': datetime.datetime.utcfromtimestamp(1546387200)},
                         {'_id': bson.ObjectId('12345678123456781234567a'),
                          'time': datetime.datetime.utcfromtimestamp(1546473600)},
                         {'time': datetime.datetime.utcfromtimestamp(1546560000)}, # no id
                         {'_id': bson.ObjectId('12345678123456781234567c')}]       # no time
            request.replies({'cursor': {'id': 0, 'firstBatch': documents}})

            for i in range(3):
                request = self.s.receives()
                self.assertEqual(request["find"], "col_entities")
                self.assertEqual(request["filter"], {'doc': [bson.ObjectId('123456781234567812345678'),
                                                             bson.ObjectId('123456781234567812345679'),
                                                             bson.ObjectId('12345678123456781234567a')][i]})
                self.assertEqual(request["sort"], {'sen': 1})
                occurrences = [{'sen': 1, 'ent': 1}, {'sen': 1, 'ent': 2 + i}]
                request.replies({'cursor': {'id': 0, 'firstBatch': occurrences}})

            tvg = future()
            for i, g in enumerate(tvg):
                self.assertEqual(g.revision, 0)
                self.assertEqual(g.ts, 1546300800000 + i * 86400000)
                self.assertEqual(g[1, 2 + i], 1.0)
            del tvg

            future = mockupdb.go(Graph.load_from_mongodb, self.db, '112233445566778899aabbcc')

            request = self.s.receives()
            self.assertEqual(request["find"], "col_entities")
            self.assertEqual(request["filter"], {'doc': bson.ObjectId('112233445566778899aabbcc')})
            self.assertEqual(request["sort"], {'sen': 1})
            request.replies({'cursor': {'id': 0, 'firstBatch': []}})

            g = future()
            self.assertTrue(isinstance(g, Graph))
            del g

            future = mockupdb.go(Graph.load_from_mongodb, self.db, b'\x11\x22\x33\x44\x55\x66\x77\x88\x99\xaa\xbb\xcc')

            request = self.s.receives()
            self.assertEqual(request["find"], "col_entities")
            self.assertEqual(request["filter"], {'doc': bson.ObjectId('112233445566778899aabbcc')})
            self.assertEqual(request["sort"], {'sen': 1})
            request.replies({'cursor': {'id': 0, 'firstBatch': []}})

            g = future()
            self.assertTrue(isinstance(g, Graph))
            del g

        def test_max_distance(self):
            occurrences = [{'sen': 0, 'ent': 1 },
                           {'sen': 0x7fffffffffffffff, 'ent': 2 }]

            g = self.load_from_occurrences(occurrences)
            self.assertFalse(g.has_edge((1, 2)))
            del g

            self.db = self.MongoDB(self.s.uri, "database", "col_articles",
                                   "_id", "time", "col_entities", "doc", "sen", "ent",
                                   use_pool=False, max_distance=None)

            g = self.load_from_occurrences(occurrences)
            self.assertTrue(g.has_edge((1, 2)))
            self.assertEqual(g[1, 2], 0.0)
            del g

        def test_sum_weights(self):
            occurrences1 = [{'sen': 1, 'ent': 1},
                            {'sen': 2, 'ent': 2},
                            {'sen': 4, 'ent': 1}]

            occurrences2 = [{'sen': 1, 'ent': 1},
                            {'sen': 3, 'ent': 2},
                            {'sen': 4, 'ent': 1}]

            g = self.load_from_occurrences(occurrences1)
            self.assertTrue(abs(g[1, 2]/(math.exp(-1.0) + np.exp(-2.0)) - 1.0) < 1e-7)
            del g

            g = self.load_from_occurrences(occurrences1)
            self.assertTrue(abs(g[1, 2]/(math.exp(-1.0) + np.exp(-2.0)) - 1.0) < 1e-7)
            del g

            self.db = self.MongoDB(self.s.uri, "database", "col_articles",
                                   "_id", "time", "col_entities", "doc", "sen", "ent",
                                   use_pool=False, sum_weights=False)

            g = self.load_from_occurrences(occurrences1)
            self.assertTrue(abs(g[1, 2]/math.exp(-1.0) - 1.0) < 1e-7)
            del g

            g = self.load_from_occurrences(occurrences2)
            self.assertTrue(abs(g[1, 2]/math.exp(-1.0) - 1.0) < 1e-7)
            del g

    # Run the unit tests
    unittest.main()
    gc.collect()
