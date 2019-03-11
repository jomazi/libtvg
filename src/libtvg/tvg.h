/*
 * Time-varying graph library
 *
 * Copyright (c) 2018-2019 Sebastian Lackner
 */

#ifndef _TVG_H_
#define _TVG_H_

#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

#include "list.h"

#define TVG_FLAGS_NONZERO   0x00000001  /* weights are always nonzero */
#define TVG_FLAGS_POSITIVE  0x00000002  /* weights are always positive */
#define TVG_FLAGS_DIRECTED  0x00000004  /* edges are directed */
#define TVG_FLAGS_STREAMING 0x00000008  /* streaming mode */

struct entry1
{
    uint64_t index;
    float    weight;
};

struct bucket1
{
    uint64_t    num_entries;
    uint64_t    max_entries;
    struct entry1 *entries;
    uint64_t    hint;
};

struct vector_ops;

struct vector
{
    int         refcount;
    uint32_t    flags;
    uint64_t    revision;
    float       eps;

    /* private: */
    const struct vector_ops *ops;
    uint32_t    bits;
    struct bucket1 *buckets;
    uint64_t    optimize;
};

struct entry2
{
    uint64_t    source;
    uint64_t    target;
    float       weight;
};

struct bucket2
{
    uint64_t    num_entries;
    uint64_t    max_entries;
    struct entry2 *entries;
    uint64_t    hint;
};

struct graph_ops;

struct graph
{
    int         refcount;
    uint32_t    flags;
    uint64_t    revision;
    float       eps;
    float       ts;

    /* private: */
    struct tvg *tvg;         /* NULL for disconnected graphs */
    struct list entry;

    const struct graph_ops *ops;
    uint32_t    bits_source; /* 0...31 */
    uint32_t    bits_target; /* 0...31 */
    struct bucket2 *buckets;
    uint64_t    optimize;

    struct graph *delta;
    float       delta_mul;
};

struct tvg
{
    int         refcount;
    uint32_t    flags;

    /* private: */
    struct list graphs;
};

struct source
{
    struct list entry;
    struct list todo_entry;
    struct graph *graph;
    uint64_t    revision;
};

struct window_ops;

struct window
{
    int         refcount;
    float       eps;
    float       ts;

    /* private: */
    struct tvg *tvg;
    const struct window_ops *ops;
    float       window_l;
    float       window_r;
    float       weight;
    float       log_beta;
    struct list sources;
    struct graph *result;
};

struct bfs_entry
{
    double   weight;
    uint32_t count;
    uint64_t from;
    uint64_t to;
};

#define _UNIQUE_VARIABLE3(a, b) (a ## b)
#define _UNIQUE_VARIABLE2(a, b) _UNIQUE_VARIABLE3(a, b)
#define _UNIQUE_VARIABLE(a) _UNIQUE_VARIABLE2(a, __COUNTER__)

/* bucket1 macros */

static inline struct entry1 *__bucket1_for_each_entry(struct bucket1 *bucket, struct entry1 **entry)
{
    *entry = &bucket->entries[0];
    return &bucket->entries[bucket->num_entries];
}

#define _BUCKET1_FOR_EACH_ENTRY(_bucket, _entry, _end_entry) \
    for (struct entry1 *(_end_entry) = __bucket1_for_each_entry((_bucket), &(_entry)); \
         (_entry) != (_end_entry); (_entry)++)

#define BUCKET1_FOR_EACH_ENTRY(_bucket, _entry) \
    _BUCKET1_FOR_EACH_ENTRY((_bucket), (_entry), _UNIQUE_VARIABLE(__end_entry_))

static inline struct entry1 *__bucket1_for_each_entry_rev(struct bucket1 *bucket, struct entry1 **entry)
{
    *entry = &bucket->entries[bucket->num_entries];
    return &bucket->entries[0];
}

#define _BUCKET1_FOR_EACH_ENTRY_REV(_bucket, _entry, _end_entry) \
    for (struct entry1 *(_end_entry) = __bucket1_for_each_entry_rev((_bucket), &(_entry)); \
         (_entry)-- != (_end_entry);)

#define BUCKET1_FOR_EACH_ENTRY_REV(_bucket, _entry) \
    _BUCKET1_FOR_EACH_ENTRY_REV((_bucket), (_entry), _UNIQUE_VARIABLE(__end_entry_))

struct _bucket1_iter2
{
    struct entry1 *entry1;
    struct entry1 *entry2;
    struct entry1 *end_entry1;
    struct entry1 *end_entry2;
};

static inline struct _bucket1_iter2 __bucket1_for_each_entry2(struct bucket1 *bucket1, struct bucket1 *bucket2)
{
    struct _bucket1_iter2 iter;

    iter.end_entry1 = __bucket1_for_each_entry(bucket1, &iter.entry1);
    iter.end_entry2 = __bucket1_for_each_entry(bucket2, &iter.entry2);

    return iter;
}

static inline int __bucket1_next_entry2(struct _bucket1_iter2 *iter, struct entry1 **entry1, struct entry1 **entry2)
{
    if (iter->entry1 != iter->end_entry1)
    {
        if (iter->entry2 != iter->end_entry2)
        {
            if (iter->entry1->index < iter->entry2->index)
            {
                *entry1 = iter->entry1++;
                *entry2 = NULL;
            }
            else if (iter->entry1->index > iter->entry2->index)
            {
                *entry1 = NULL;
                *entry2 = iter->entry2++;
            }
            else
            {
                *entry1 = iter->entry1++;
                *entry2 = iter->entry2++;
            }
            return 1;
        }
        else
        {
            *entry1 = iter->entry1++;
            *entry2 = NULL;
            return 1;
        }
    }
    else
    {
        if (iter->entry2 != iter->end_entry2)
        {
            *entry1 = NULL;
            *entry2 = iter->entry2++;
            return 1;
        }
        else
        {
            return 0;
        }
    }
}

#define _BUCKET1_FOR_EACH_ENTRY2(_bucket1, _entry1, _bucket2, _entry2, _iter) \
    for (struct _bucket1_iter2 (_iter) = __bucket1_for_each_entry2((_bucket1), (_bucket2)); \
         __bucket1_next_entry2(&(_iter), &(_entry1), &(_entry2));)

#define BUCKET1_FOR_EACH_ENTRY2(_bucket1, _entry1, _bucket2, _entry2) \
    _BUCKET1_FOR_EACH_ENTRY2((_bucket1), (_entry1), (_bucket2), (_entry2), _UNIQUE_VARIABLE(__iter_))

static inline struct _bucket1_iter2 __bucket1_for_each_entry_rev2(struct bucket1 *bucket1, struct bucket1 *bucket2)
{
    struct _bucket1_iter2 iter;

    iter.end_entry1 = __bucket1_for_each_entry_rev(bucket1, &iter.entry1);
    iter.end_entry2 = __bucket1_for_each_entry_rev(bucket2, &iter.entry2);

    return iter;
}

static inline int __bucket1_prev_entry2(struct _bucket1_iter2 *iter, struct entry1 **entry1, struct entry1 **entry2)
{
    if (iter->entry1 != iter->end_entry1)
    {
        if (iter->entry2 != iter->end_entry2)
        {
            struct entry1 *prev_entry1 = &iter->entry1[-1];
            struct entry1 *prev_entry2 = &iter->entry2[-1];
            if (prev_entry1->index < prev_entry2->index)
            {
                *entry1 = NULL;
                *entry2 = --iter->entry2;
            }
            else if (prev_entry1->index > prev_entry2->index)
            {
                *entry1 = --iter->entry1;
                *entry2 = NULL;
            }
            else
            {
                *entry1 = --iter->entry1;
                *entry2 = --iter->entry2;
            }
            return 1;
        }
        else
        {
            *entry1 = --iter->entry1;
            *entry2 = NULL;
            return 1;
        }
    }
    else
    {
        if (iter->entry2 != iter->end_entry2)
        {
            *entry1 = NULL;
            *entry2 = --iter->entry2;
            return 1;
        }
        else
        {
            return 0;
        }
    }
}

#define _BUCKET1_FOR_EACH_ENTRY_REV2(_bucket1, _entry1, _bucket2, _entry2, _iter) \
    for (struct _bucket1_iter2 (_iter) = __bucket1_for_each_entry_rev2((_bucket1), (_bucket2)); \
         __bucket1_prev_entry2(&(_iter), &(_entry1), &(_entry2));)

#define BUCKET1_FOR_EACH_ENTRY_REV2(_bucket1, _entry1, _bucket2, _entry2) \
    _BUCKET1_FOR_EACH_ENTRY_REV2((_bucket1), (_entry1), (_bucket2), (_entry2), _UNIQUE_VARIABLE(__iter_))

/* bucket2 macros */

static inline struct entry2 *__bucket2_for_each_entry(struct bucket2 *bucket, struct entry2 **entry)
{
    *entry = &bucket->entries[0];
    return &bucket->entries[bucket->num_entries];
}

#define _BUCKET2_FOR_EACH_ENTRY(_bucket, _entry, _end_entry) \
    for (struct entry2 *(_end_entry) = __bucket2_for_each_entry((_bucket), &(_entry)); \
         (_entry) != (_end_entry); (_entry)++)

#define BUCKET2_FOR_EACH_ENTRY(_bucket, _entry) \
    _BUCKET2_FOR_EACH_ENTRY((_bucket), (_entry), _UNIQUE_VARIABLE(__end_entry_))

static inline struct entry2 *__bucket2_for_each_entry_rev(struct bucket2 *bucket, struct entry2 **entry)
{
    *entry = &bucket->entries[bucket->num_entries];
    return &bucket->entries[0];
}

#define _BUCKET2_FOR_EACH_ENTRY_REV(_bucket, _entry, _end_entry) \
    for (struct entry2 *(_end_entry) = __bucket2_for_each_entry_rev((_bucket), &(_entry)); \
         (_entry)-- != (_end_entry);)

#define BUCKET2_FOR_EACH_ENTRY_REV(_bucket, _entry) \
    _BUCKET2_FOR_EACH_ENTRY_REV((_bucket), (_entry), _UNIQUE_VARIABLE(__end_entry_))

struct _bucket2_iter2
{
    struct entry2 *entry1;
    struct entry2 *entry2;
    struct entry2 *end_entry1;
    struct entry2 *end_entry2;
};

static inline struct _bucket2_iter2 __bucket2_for_each_entry2(struct bucket2 *bucket1, struct bucket2 *bucket2)
{
    struct _bucket2_iter2 iter;

    iter.end_entry1 = __bucket2_for_each_entry(bucket1, &iter.entry1);
    iter.end_entry2 = __bucket2_for_each_entry(bucket2, &iter.entry2);

    return iter;
}

static inline int __bucket2_next_entry2(struct _bucket2_iter2 *iter, struct entry2 **entry1, struct entry2 **entry2)
{
    if (iter->entry1 != iter->end_entry1)
    {
        if (iter->entry2 != iter->end_entry2)
        {
            if (iter->entry1->target < iter->entry2->target)
            {
                *entry1 = iter->entry1++;
                *entry2 = NULL;
            }
            else if (iter->entry1->target > iter->entry2->target)
            {
                *entry1 = NULL;
                *entry2 = iter->entry2++;
            }
            else if (iter->entry1->source < iter->entry2->source)
            {
                *entry1 = iter->entry1++;
                *entry2 = NULL;
            }
            else if (iter->entry1->source > iter->entry2->source)
            {
                *entry1 = NULL;
                *entry2 = iter->entry2++;
            }
            else
            {
                *entry1 = iter->entry1++;
                *entry2 = iter->entry2++;
            }
            return 1;
        }
        else
        {
            *entry1 = iter->entry1++;
            *entry2 = NULL;
            return 1;
        }
    }
    else
    {
        if (iter->entry2 != iter->end_entry2)
        {
            *entry1 = NULL;
            *entry2 = iter->entry2++;
            return 1;
        }
        else
        {
            return 0;
        }
    }
}

#define _BUCKET2_FOR_EACH_ENTRY2(_bucket1, _entry1, _bucket2, _entry2, _iter) \
    for (struct _bucket2_iter2 (_iter) = __bucket2_for_each_entry2((_bucket1), (_bucket2)); \
         __bucket2_next_entry2(&(_iter), &(_entry1), &(_entry2));)

#define BUCKET2_FOR_EACH_ENTRY2(_bucket1, _entry1, _bucket2, _entry2) \
    _BUCKET2_FOR_EACH_ENTRY2((_bucket1), (_entry1), (_bucket2), (_entry2), _UNIQUE_VARIABLE(__iter_))

static inline struct _bucket2_iter2 __bucket2_for_each_entry_rev2(struct bucket2 *bucket1, struct bucket2 *bucket2)
{
    struct _bucket2_iter2 iter;

    iter.end_entry1 = __bucket2_for_each_entry_rev(bucket1, &iter.entry1);
    iter.end_entry2 = __bucket2_for_each_entry_rev(bucket2, &iter.entry2);

    return iter;
}

static inline int __bucket2_prev_entry2(struct _bucket2_iter2 *iter, struct entry2 **entry1, struct entry2 **entry2)
{
    if (iter->entry1 != iter->end_entry1)
    {
        if (iter->entry2 != iter->end_entry2)
        {
            struct entry2 *prev_entry1 = &iter->entry1[-1];
            struct entry2 *prev_entry2 = &iter->entry2[-1];
            if (prev_entry1->target < prev_entry2->target)
            {
                *entry1 = NULL;
                *entry2 = --iter->entry2;
            }
            else if (prev_entry1->target > prev_entry2->target)
            {
                *entry1 = --iter->entry1;
                *entry2 = NULL;
            }
            else if (prev_entry1->source < prev_entry2->source)
            {
                *entry1 = NULL;
                *entry2 = --iter->entry2;
            }
            else if (prev_entry1->source > prev_entry2->source)
            {
                *entry1 = --iter->entry1;
                *entry2 = NULL;
            }
            else
            {
                *entry1 = --iter->entry1;
                *entry2 = --iter->entry2;
            }
            return 1;
        }
        else
        {
            *entry1 = --iter->entry1;
            *entry2 = NULL;
            return 1;
        }
    }
    else
    {
        if (iter->entry2 != iter->end_entry2)
        {
            *entry1 = NULL;
            *entry2 = --iter->entry2;
            return 1;
        }
        else
        {
            return 0;
        }
    }
}

#define _BUCKET2_FOR_EACH_ENTRY_REV2(_bucket1, _entry1, _bucket2, _entry2, _iter) \
    for (struct _bucket2_iter2 (_iter) = __bucket2_for_each_entry_rev2((_bucket1), (_bucket2)); \
         __bucket2_prev_entry2(&(_iter), &(_entry1), &(_entry2));)

#define BUCKET2_FOR_EACH_ENTRY_REV2(_bucket1, _entry1, _bucket2, _entry2) \
    _BUCKET2_FOR_EACH_ENTRY_REV2((_bucket1), (_entry1), (_bucket2), (_entry2), _UNIQUE_VARIABLE(__iter_))

/* bucket1 + bucket2 macros */

struct _bucket21_iter
{
    struct entry2 *entry2;
    struct entry1 *entry1;
    struct entry2 *end_entry2;
    struct entry1 *end_entry1;
};

static inline struct _bucket21_iter __bucket21_for_each_entry(struct bucket2 *bucket2, struct bucket1 *bucket1)
{
    struct _bucket21_iter iter;

    iter.end_entry2 = __bucket2_for_each_entry(bucket2, &iter.entry2);
    iter.end_entry1 = __bucket1_for_each_entry(bucket1, &iter.entry1);

    return iter;
}

static inline int __bucket21_next_entry(struct _bucket21_iter *iter, struct entry2 **entry2, struct entry1 **entry1)
{
    if (iter->entry2 == iter->end_entry2)
        return 0;

    while (iter->entry1 != iter->end_entry1)
    {
        if (iter->entry1->index < iter->entry2->target)
        {
            iter->entry1++;
            continue;  /* skip entry1 */
        }
        else if (iter->entry1->index > iter->entry2->target)
        {
            *entry2 = iter->entry2++;
            *entry1 = NULL;
        }
        else
        {
            *entry2 = iter->entry2++;
            *entry1 = iter->entry1;
        }
        return 1;
    }

    *entry2 = iter->entry2++;
    *entry1 = NULL;
    return 1;
}

#define _BUCKET21_FOR_EACH_ENTRY(_bucket2, _entry2, _bucket1, _entry1, _iter) \
    for (struct _bucket21_iter (_iter) = __bucket21_for_each_entry((_bucket2), (_bucket1)); \
         __bucket21_next_entry(&(_iter), &(_entry2), &(_entry1));)

/* NOTE: This macro primarily iterates over bucket2: Entries in
 * bucket1 without corresponding entry in bucket2 are skipped! */
#define BUCKET21_FOR_EACH_ENTRY(_bucket2, _entry2, _bucket1, _entry1) \
    _BUCKET21_FOR_EACH_ENTRY((_bucket2), (_entry2), (_bucket1), (_entry1), _UNIQUE_VARIABLE(__iter_))

/* vector macros */

struct _vector_iter
{
    const struct vector *vector;
    uint64_t       index;
    uint64_t       end_index;
    struct entry1 *entry;
    struct entry1 *end_entry;
};

static inline struct _vector_iter __vector_for_each_entry(const struct vector *vector)
{
    struct _vector_iter iter;

    iter.vector    = vector;
    iter.index     = 0;
    iter.end_index = 1ULL << vector->bits;
    iter.end_entry = __bucket1_for_each_entry(&vector->buckets[iter.index], &iter.entry);

    return iter;
}

static inline int __vector_next_entry(struct _vector_iter *iter, struct entry1 **entry)
{
    if (iter->index >= iter->end_index)
        return 0;

    for (;;)
    {
        if (iter->entry != iter->end_entry)
        {
            *entry = iter->entry++;
            return 1;
        }
        iter->index++;

        if (iter->index >= iter->end_index)
            break;

        iter->end_entry = __bucket1_for_each_entry(&iter->vector->buckets[iter->index], &iter->entry);
    }

    return 0;
}

#define _VECTOR_FOR_EACH_ENTRY(_graph, _edge, _iter) \
    for (struct _vector_iter (_iter) = __vector_for_each_entry((_graph)); __vector_next_entry(&(_iter), &(_edge));)

/* NOTE: Due to the internal bucket structure there is no guarantee about the sort order! */
#define VECTOR_FOR_EACH_ENTRY(_graph, _edge) \
    _VECTOR_FOR_EACH_ENTRY((_graph), (_edge), _UNIQUE_VARIABLE(__iter_))

/* graph macros */

struct _graph_iter
{
    const struct graph *graph;
    uint64_t       index;
    uint64_t       end_index;
    struct entry2 *edge;
    struct entry2 *end_edge;
};

static inline struct _graph_iter __graph_for_each_edge(const struct graph *graph)
{
    struct _graph_iter iter;

    iter.graph     = graph;
    iter.index     = 0;
    iter.end_index = 1ULL << (graph->bits_source + graph->bits_target);
    iter.end_edge  = __bucket2_for_each_entry(&graph->buckets[iter.index], &iter.edge);

    return iter;
}

static inline int __graph_next_directed_edge(struct _graph_iter *iter, struct entry2 **edge)
{
    if (iter->index >= iter->end_index)
        return 0;

    for (;;)
    {
        if (iter->edge != iter->end_edge)
        {
            *edge = iter->edge++;
            return 1;
        }
        iter->index++;

        if (iter->index >= iter->end_index)
            break;

        iter->end_edge = __bucket2_for_each_entry(&iter->graph->buckets[iter->index], &iter->edge);
    }

    return 0;
}

#define _GRAPH_FOR_EACH_DIRECTED_EDGE(_graph, _edge, _iter) \
    for (struct _graph_iter (_iter) = __graph_for_each_edge((_graph)); __graph_next_directed_edge(&(_iter), &(_edge));)

/* NOTE: Due to the internal bucket structure there is no guarantee about the sort order! */
#define GRAPH_FOR_EACH_DIRECTED_EDGE(_graph, _edge) \
    _GRAPH_FOR_EACH_DIRECTED_EDGE((_graph), (_edge), _UNIQUE_VARIABLE(__iter_))

static inline int __graph_next_undirected_edge(struct _graph_iter *iter, struct entry2 **edge)
{
    if (iter->index >= iter->end_index)
        return 0;

    for (;;)
    {
        for (; iter->edge != iter->end_edge; iter->edge++)
        {
            if (iter->edge->target >= iter->edge->source)
            {
                *edge = iter->edge++;
                return 1;
            }
        }
        iter->index++;

        if (iter->index >= iter->end_index)
            break;

        iter->end_edge = __bucket2_for_each_entry(&iter->graph->buckets[iter->index], &iter->edge);
    }

    return 0;
}

#define _GRAPH_FOR_EACH_UNDIRECTED_EDGE(_graph, _edge, _iter) \
    for (struct _graph_iter (_iter) = __graph_for_each_edge((_graph)); __graph_next_undirected_edge(&(_iter), &(_edge));)

/* NOTE: Due to the internal bucket structure there is no guarantee about the sort order! */
#define GRAPH_FOR_EACH_UNDIRECTED_EDGE(_graph, _edge) \
    _GRAPH_FOR_EACH_UNDIRECTED_EDGE((_graph), (_edge), _UNIQUE_VARIABLE(__iter_))

static inline int __graph_next_edge(struct _graph_iter *iter, struct entry2 **edge)
{
    if (iter->graph->flags & TVG_FLAGS_DIRECTED)
        return __graph_next_directed_edge(iter, edge);
    else
        return __graph_next_undirected_edge(iter, edge);
}

#define _GRAPH_FOR_EACH_EDGE(_graph, _edge, _iter) \
    for (struct _graph_iter (_iter) = __graph_for_each_edge((_graph)); __graph_next_edge(&(_iter), &(_edge));)

/* NOTE: Due to the internal bucket structure there is no guarantee about the sort order! */
#define GRAPH_FOR_EACH_EDGE(_graph, _edge) \
    _GRAPH_FOR_EACH_EDGE((_graph), (_edge), _UNIQUE_VARIABLE(__iter_))

struct _graph_adjacent_iter
{
    const struct graph *graph;
    uint64_t       index;
    uint64_t       end_index;
    struct entry2 *edge;
    struct entry2 *end_edge;
    uint64_t       source;
};


static inline struct _graph_adjacent_iter __graph_for_each_adjacent_edge(const struct graph *graph, uint64_t source)
{
    struct _graph_adjacent_iter iter;

    iter.graph     = graph;
    iter.index     = source & ((1ULL << graph->bits_source) - 1);
    iter.end_index = 1ULL << (graph->bits_source + graph->bits_target);
    iter.end_edge  = __bucket2_for_each_entry(&graph->buckets[iter.index], &iter.edge);
    iter.source    = source;

    return iter;
}

static inline int __graph_next_adjacent_edge(struct _graph_adjacent_iter *iter, struct entry2 **edge)
{
    if (iter->index >= iter->end_index)
        return 0;

    for (;;)
    {
        for (; iter->edge != iter->end_edge; iter->edge++)
        {
            if (iter->edge->source == iter->source)
            {
                *edge = iter->edge++;
                return 1;
            }
        }
        iter->index += (1ULL << iter->graph->bits_source);

        if (iter->index >= iter->end_index)
            break;

        iter->end_edge = __bucket2_for_each_entry(&iter->graph->buckets[iter->index], &iter->edge);
    }

    return 0;
}

#define _GRAPH_FOR_EACH_ADJACENT_EDGE(_graph, _source, _edge, _iter) \
    for (struct _graph_adjacent_iter (_iter) = __graph_for_each_adjacent_edge((_graph), (_source)); \
         __graph_next_adjacent_edge(&(_iter), &(_edge));)

/* NOTE: Due to the internal bucket structure there is no guarantee about the sort order! */
#define GRAPH_FOR_EACH_ADJACENT_EDGE(_graph, _source, _edge) \
    _GRAPH_FOR_EACH_ADJACENT_EDGE((_graph), (_source), (_edge), _UNIQUE_VARIABLE(__iter_))

/* vector functions */

struct vector *alloc_vector(uint32_t flags);
struct vector *grab_vector(struct vector *vector);
void free_vector(struct vector *vector);

int vector_inc_bits(struct vector *vector);
int vector_dec_bits(struct vector *vector);
void vector_optimize(struct vector *vector);

void vector_set_eps(struct vector *vector, float eps);

int vector_empty(struct vector *vector);

int vector_has_entry(struct vector *vector, uint64_t index);

float vector_get_entry(struct vector *vector, uint64_t index);
uint64_t vector_get_entries(struct vector *vector, uint64_t *indices, float *weights, uint64_t max_edges);

int vector_set_entry(struct vector *vector, uint64_t index, float weight);
int vector_set_entries(struct vector *vector, uint64_t *indices, float *weights, uint64_t num_entries);

int vector_add_entry(struct vector *vector, uint64_t index, float weight);
int vector_add_entries(struct vector *vector, uint64_t *indices, float *weights, uint64_t num_entries);

int vector_sub_entry(struct vector *vector, uint64_t index, float weight);
int vector_sub_entries(struct vector *vector, uint64_t *indices, float *weights, uint64_t num_entries);

void vector_del_entry(struct vector *vector, uint64_t index);
void vector_del_entries(struct vector *vector, uint64_t *indices, uint64_t num_entries);

void vector_mul_const(struct vector *vector, float constant);
double vector_norm(const struct vector *vector);
double vector_mul_vector(const struct vector *vector1, /* const */ struct vector *vector2);

/* graph functions */

struct graph *alloc_graph(uint32_t flags);
struct graph *grab_graph(struct graph *graph);
void free_graph(struct graph *graph);
void unlink_graph(struct graph *graph);

struct graph *prev_graph(struct graph *graph);
struct graph *next_graph(struct graph *graph);

int graph_enable_delta(struct graph *graph);
void graph_disable_delta(struct graph *graph);
struct graph *graph_get_delta(struct graph *graph, float *mul);

void graph_debug(struct graph *graph);

int graph_inc_bits_target(struct graph *graph);
int graph_dec_bits_target(struct graph *graph);
int graph_inc_bits_source(struct graph *graph);
int graph_dec_bits_source(struct graph *graph);
void graph_optimize(struct graph *graph);

void graph_set_eps(struct graph *graph, float eps);

int graph_empty(struct graph *graph);

int graph_has_edge(struct graph *graph, uint64_t source, uint64_t target);

float graph_get_edge(struct graph *graph, uint64_t source, uint64_t target);
uint64_t graph_get_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t max_edges);
uint64_t graph_get_adjacent_edges(struct graph *graph, uint64_t source, uint64_t *indices, float *weights, uint64_t max_edges);

int graph_set_edge(struct graph *graph, uint64_t source, uint64_t target, float weight);
int graph_set_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t num_edges);

int graph_add_edge(struct graph *graph, uint64_t source, uint64_t target, float weight);
int graph_add_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t num_edges);
int graph_add_graph(struct graph *out, struct graph *graph, float weight);

int graph_sub_edge(struct graph *graph, uint64_t source, uint64_t target, float weight);
int graph_sub_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t num_edges);
int graph_sub_graph(struct graph *out, struct graph *graph, float weight);

void graph_del_edge(struct graph *graph, uint64_t source, uint64_t target);
void graph_del_edges(struct graph *graph, uint64_t *indices, uint64_t num_edges);

void graph_mul_const(struct graph *graph, float constant);
struct vector *graph_mul_vector(const struct graph *graph, /* const */ struct vector *vector);
struct vector *graph_power_iteration(const struct graph *graph, uint32_t num_iterations, double *eigenvalue_out);

int graph_bfs(struct graph *g, uint64_t source, int use_weights, int (*callback)(struct graph *,
              struct bfs_entry *, void *), void *userdata);

/* tvg functions */

struct tvg *alloc_tvg(uint32_t flags);
struct tvg *grab_tvg(struct tvg *tvg);
void free_tvg(struct tvg *tvg);

struct graph *tvg_alloc_graph(struct tvg *tvg, float ts);

int tvg_load_graphs(struct tvg *tvg, const char *filename);

struct window *tvg_alloc_window_rect(struct tvg *tvg, float window_l, float window_r);
struct window *tvg_alloc_window_decay(struct tvg *tvg, float window, float log_beta);
struct window *tvg_alloc_window_smooth(struct tvg *tvg, float window, float log_beta);

struct graph *tvg_lookup_graph_ge(struct tvg *tvg, float ts);
struct graph *tvg_lookup_graph_le(struct tvg *tvg, float ts);
struct graph *tvg_lookup_graph_near(struct tvg *tvg, float ts);

int tvg_compress(struct tvg *tvg, float step, float offset);

struct graph *tvg_extract(struct tvg *tvg, float ts, float (*weight_func)(struct graph *,
                          float, void *), void *userdata);

/* window functions */

/* alloc_window not exported */
struct window *grab_window(struct window *window);
void free_window(struct window *window);
void window_set_eps(struct window *window, float eps);
void window_clear(struct window *window);
struct graph *window_update(struct window *window, float ts);
struct graph *window_get_delta(struct window *window, float *mul);

#endif /* _TVG_H_ */
