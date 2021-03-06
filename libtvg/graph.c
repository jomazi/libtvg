/*
 * Time-varying graph library
 * Graph functions.
 *
 * Copyright (c) 2018-2019 Sebastian Lackner
 */

#include <float.h>

#include "internal.h"

#define FILE_TAG     0x47475654U /* "TVGG" */
#define FILE_VERSION 0x00000001U

struct file_header
{
    uint32_t tag;
    uint32_t version;
    uint32_t flags;
    uint32_t bits_source;
    uint32_t bits_target;
};

/* graph_debug relies on that */
C_ASSERT(sizeof(long long unsigned int) == sizeof(uint64_t));

/* graph_load_binary relies on that */
C_ASSERT(sizeof(struct file_header) == 20);
C_ASSERT(sizeof(((struct bucket2 *)0)->num_entries) == 8);
C_ASSERT(sizeof(struct entry2) == 24);

struct graph *alloc_graph(uint32_t flags)
{
    static const uint32_t bits_source = 0;
    static const uint32_t bits_target = 0;
    struct graph *graph;
    struct bucket2 *buckets;
    uint64_t i, num_buckets;

    if (flags & ~(TVG_FLAGS_POSITIVE |
                  TVG_FLAGS_DIRECTED))
        return NULL;

    num_buckets = 1ULL << (bits_source + bits_target);
    if (!(buckets = malloc(sizeof(*buckets) * num_buckets)))
        return NULL;

    for (i = 0; i < num_buckets; i++)
        init_bucket2(&buckets[i]);

    if (!(graph = malloc(sizeof(*graph))))
    {
        free(buckets);
        return NULL;
    }

    graph->refcount    = 1;
    graph->flags       = flags;
    graph->revision    = 0;
    graph->ts          = 0.0;
    objectid_init(&graph->objectid);
    graph->nodes       = NULL;
    graph->query       = NULL;
    graph->tvg         = NULL;
    graph->cache       = 0;
    list_init(&graph->cache_entry);
    graph->bits_source = bits_source;
    graph->bits_target = bits_target;
    graph->buckets     = buckets;
    graph->optimize    = 0;

    /* set a proper 'optimize' value */
    graph_optimize(graph);
    return graph;
}

struct graph *grab_graph(struct graph *graph)
{
    if (graph) __sync_fetch_and_add(&graph->refcount, 1);
    return graph;
}

void free_graph(struct graph *graph)
{
    uint64_t i, num_buckets;

    if (!graph) return;
    if (__sync_sub_and_fetch(&graph->refcount, 1)) return;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);
    for (i = 0; i < num_buckets; i++)
        free_bucket2(&graph->buckets[i]);

    /* When the last reference is dropped the graph should no longer
     * be associated with a time-varying-graph object. Triggering this
     * assertion means that 'free_graph' was called too often. */
    assert(!graph->tvg);
    assert(!graph->cache);

    free_vector(graph->nodes);
    free_query(graph->query);
    free(graph->buckets);
    free(graph);
}

void unlink_graph(struct graph *graph)
{
    struct graph *other_graph;
    struct tvg *tvg;
    int cache;

    if (!graph || !(tvg = graph->tvg))
        return;

    if ((cache = (graph->cache != 0)))  /* we have to reload later */
    {
        graph->flags |= (TVG_FLAGS_LOAD_NEXT | TVG_FLAGS_LOAD_PREV);
        list_remove(&graph->cache_entry);
        tvg->graph_cache_used -= graph->cache;
        graph->cache = 0;
    }

    if (graph->flags & TVG_FLAGS_LOAD_NEXT)
    {
        other_graph = AVL_PREV(graph, &tvg->graphs, struct graph, entry);
        if (other_graph) other_graph->flags |= TVG_FLAGS_LOAD_NEXT;
    }
    if (graph->flags & TVG_FLAGS_LOAD_PREV)
    {
        other_graph = AVL_NEXT(graph, &tvg->graphs, struct graph, entry);
        if (other_graph) other_graph->flags |= TVG_FLAGS_LOAD_PREV;
    }

    avl_remove(&graph->entry);
    graph->tvg = NULL;
    graph->flags &= ~TVG_FLAGS_READONLY;  /* allow changes */

    if (!cache)
        tvg_invalidate_queries(tvg, graph->ts, graph->ts);

    free_graph(graph);
}

struct graph *graph_duplicate(struct graph *source)
{
    struct bucket2 *buckets;
    uint64_t i, num_buckets;
    struct graph *graph;

    num_buckets = 1ULL << (source->bits_source + source->bits_target);
    if (!(buckets = malloc(sizeof(*buckets) * num_buckets)))
        return NULL;

    for (i = 0; i < num_buckets; i++)
    {
        if (!init_bucket2_from(&buckets[i], &source->buckets[i]))
        {
            while (i--)
                free_bucket2(&buckets[i]);

            return NULL;
        }
    }

    if (!(graph = malloc(sizeof(*graph))))
    {
        for (i = 0; i < num_buckets; i++)
            free_bucket2(&buckets[i]);

        free(buckets);
        return NULL;
    }

    graph->refcount    = 1;
    graph->flags       = source->flags & ~(TVG_FLAGS_LOAD_NEXT |
                                           TVG_FLAGS_LOAD_PREV |
                                           TVG_FLAGS_READONLY);
    graph->revision    = source->revision;
    graph->ts          = source->ts;
    graph->objectid    = source->objectid;
    graph->nodes       = grab_vector(source->nodes);  /* readonly */
    graph->query       = NULL;
    graph->tvg         = NULL;
    graph->cache       = 0;
    list_init(&graph->cache_entry);
    graph->bits_source = source->bits_source;
    graph->bits_target = source->bits_target;
    graph->buckets     = buckets;
    graph->optimize    = source->optimize;
    return graph;
}

void graph_refresh_cache(struct graph *graph)
{
    if (!graph->cache) return;
    assert(graph->tvg != NULL);
    list_remove(&graph->cache_entry);
    list_add_tail(&graph->tvg->graph_cache, &graph->cache_entry);
}

void graph_debug(struct graph *graph)
{
    struct entry2 *edge;
    char objectid_str[32];

    objectid_to_str(&graph->objectid, objectid_str);
    fprintf(stderr, "Graph %p (ts %llu, objectid %s, revision %llu)\n", graph,
            (long long unsigned int)graph->ts, objectid_str,
            (long long unsigned int)graph->revision);

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        fprintf(stderr, "A[%llu, %llu] = %f\n", (long long unsigned int)edge->source,
                                                (long long unsigned int)edge->target, edge->weight);
    }
}

uint64_t graph_memory_usage(struct graph *graph)
{
    uint64_t i, num_buckets;
    struct bucket2 *bucket;
    uint64_t size = sizeof(*graph);

    /* In the following, we underestimate the memory usage a bit, since
     * we do not take into account the heap structure itself. */

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);
    size += sizeof(*bucket) * num_buckets;

    for (i = 0; i < num_buckets; i++)
    {
        bucket = &graph->buckets[i];
        size += sizeof(bucket->entries) * bucket->max_entries;
    }

    if (graph->nodes)
        size += vector_memory_usage(graph->nodes);

    return size;
}

struct graph *prev_graph(struct graph *graph)
{
    struct tvg *tvg;

    if (!graph || !(tvg = graph->tvg))
        return NULL;

    /* Ensure that the user has one additional reference. */
    assert(__sync_fetch_and_add(&graph->refcount, 0) >= 2);

    if (graph->flags & TVG_FLAGS_LOAD_PREV)
        tvg_load_prev_graph(tvg, graph);

    graph = AVL_PREV(graph, &tvg->graphs, struct graph, entry);
    if (!graph)
        return NULL;

    assert(graph->tvg == tvg);
    graph_refresh_cache(graph);
    return grab_graph(graph);
}

struct graph *next_graph(struct graph *graph)
{
    struct tvg *tvg;

    if (!graph || !(tvg = graph->tvg))
        return NULL;

    /* Ensure that the user has one additional reference. */
    assert(__sync_fetch_and_add(&graph->refcount, 0) >= 2);

    if (graph->flags & TVG_FLAGS_LOAD_NEXT)
        tvg_load_next_graph(tvg, graph);

    graph = AVL_NEXT(graph, &tvg->graphs, struct graph, entry);
    if (!graph)
        return NULL;

    assert(graph->tvg == tvg);
    graph_refresh_cache(graph);
    return grab_graph(graph);
}

int graph_inc_bits_target(struct graph *graph)
{
    struct bucket2 *buckets;
    uint64_t i, num_buckets;
    uint64_t mask = 1ULL << graph->bits_target;

    if (graph->bits_target >= 31)
        return 0;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);
    if (!(buckets = realloc(graph->buckets, sizeof(*buckets) * 2 * num_buckets)))
        return 0;

    graph->buckets = buckets;

    for (i = 0; i < num_buckets; i++)
    {
        init_bucket2(&buckets[i + num_buckets]);
        if (!bucket2_split(&buckets[i], &buckets[i + num_buckets], 0, mask))
        {
            /* FIXME: Error handling is mostly untested. */

            while (i--)
            {
                bucket2_merge(&buckets[i], &buckets[i + num_buckets]);
                free_bucket2(&buckets[i + num_buckets]);
            }

            if ((buckets = realloc(graph->buckets, sizeof(*buckets) * num_buckets)))
                graph->buckets = buckets;

            return 0;
        }
    }

    for (i = 0; i < 2 * num_buckets; i++)
        bucket2_compress(&buckets[i]);

    graph->bits_target++;
    return 1;
}

int graph_dec_bits_target(struct graph *graph)
{
    struct bucket2 *buckets;
    uint64_t i, num_buckets;
    uint64_t mask = 1ULL << (graph->bits_target - 1);

    if (!graph->bits_target)
        return 0;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target - 1);
    buckets = graph->buckets;

    for (i = 0; i < num_buckets; i++)
    {
        if (!bucket2_merge(&buckets[i], &buckets[i + num_buckets]))
        {
            /* FIXME: Error handling is mostly untested. */

            while (i--)
                bucket2_split(&buckets[i], &buckets[i + num_buckets], 0, mask);

            return 0;
        }
    }

    for (i = 0; i < num_buckets; i++)
    {
        bucket2_compress(&buckets[i]);
        free_bucket2(&buckets[i + num_buckets]);
    }

    if ((buckets = realloc(graph->buckets, sizeof(*buckets) * num_buckets)))
        graph->buckets = buckets;

    graph->bits_target--;
    return 1;
}

int graph_inc_bits_source(struct graph *graph)
{
    uint64_t num_source, num_target;
    struct bucket2 *buckets;
    uint64_t i, j, num_buckets;
    uint64_t mask = 1ULL << graph->bits_source;

    if (graph->bits_source >= 31)
        return 0;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);
    num_source  = 1ULL << graph->bits_source;
    num_target  = 1ULL << graph->bits_target;
    if (!(buckets = realloc(graph->buckets, sizeof(*buckets) * 2 * num_buckets)))
        return 0;

    graph->buckets = buckets;

    for (i = num_target; i--;)
    {
        memmove(&buckets[i * 2 * num_source], &buckets[i * num_source],
                sizeof(*buckets) * num_source);
    }

    for (i = 0; i < 2 * num_buckets; i += 2 * num_source)
    for (j = 0; j < num_source; j++)
    {
        init_bucket2(&buckets[i + j + num_source]);
        if (!bucket2_split(&buckets[i + j], &buckets[i + j + num_source], mask, 0))
        {
            /* FIXME: Error handling is mostly untested. */

            for (;;)
            {
                while (j--)
                {
                    bucket2_merge(&buckets[i + j], &buckets[i + j + num_source]);
                    free_bucket2(&buckets[i + j + num_source]);
                }
                if (!i) break;
                i -= 2 * num_source;
                j = num_source;
            }

            for (i = 0; i < num_target; i++)
            {
                memmove(&buckets[i * num_source], &buckets[i * 2 * num_source],
                        sizeof(*buckets) * num_source);
            }

            if ((buckets = realloc(graph->buckets, sizeof(*buckets) * num_buckets)))
                graph->buckets = buckets;

            return 0;
        }
    }

    for (i = 0; i < 2 * num_buckets; i++)
        bucket2_compress(&buckets[i]);

    graph->bits_source++;
    return 1;
}

int graph_dec_bits_source(struct graph *graph)
{
    uint64_t num_source, num_target;
    uint64_t i, j, num_buckets;
    struct bucket2 *buckets;
    uint64_t mask = 1ULL << (graph->bits_source - 1);

    if (!graph->bits_source)
        return 0;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target - 1);
    num_source  = 1ULL << (graph->bits_source - 1);
    num_target  = 1ULL << graph->bits_target;
    buckets = graph->buckets;

    for (i = 0; i < 2 * num_buckets; i += 2 * num_source)
    for (j = 0; j < num_source; j++)
    {
        if (!bucket2_merge(&buckets[i + j], &buckets[i + j + num_source]))
        {
            /* FIXME: Error handling is mostly untested. */

            for (;;)
            {
                while (j--)
                    bucket2_split(&buckets[i + j], &buckets[i + j + num_source], mask, 0);
                if (!i) break;
                i -= 2 * num_source;
                j = num_source;
            }

            return 0;
        }
    }

    for (i = 0; i < 2 * num_buckets; i += 2 * num_source)
    for (j = 0; j < num_source; j++)
    {
        bucket2_compress(&buckets[i + j]);
        free_bucket2(&buckets[i + j + num_source]);
    }

    for (i = 0; i < num_target; i++)
    {
        memmove(&buckets[i * num_source], &buckets[i * 2 * num_source],
               sizeof(*buckets) * num_source);
    }

    if ((buckets = realloc(graph->buckets, sizeof(*buckets) * num_buckets)))
        graph->buckets = buckets;

    graph->bits_source--;
    return 1;
}

void graph_optimize(struct graph *graph)
{
    uint64_t i, num_buckets;
    uint64_t num_edges;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);

    num_edges = 0;
    for (i = 0; i < num_buckets; i++)
        num_edges += bucket2_num_entries(&graph->buckets[i]);

    /* Adjust the number of buckets if the graph is getting too dense.
     * For now, we prefer source bits over target bits. */

    if (num_edges >= num_buckets * 256)
    {
        while (num_edges >= num_buckets * 64)
        {
            if (graph->bits_source <= graph->bits_target)
            {
                if (!graph_inc_bits_source(graph)) goto error;
                num_buckets *= 2;
            }
            else
            {
                if (!graph_inc_bits_target(graph)) goto error;
                num_buckets *= 2;
            }
        }
    }

    if (num_buckets >= 2 && num_edges < num_buckets * 16)
    {
        while (num_buckets >= 2 && num_edges < num_buckets * 64)
        {
            if (graph->bits_source <= graph->bits_target)
            {
                if (!graph_dec_bits_target(graph)) goto error;
                num_buckets /= 2;
            }
            else
            {
                if (!graph_dec_bits_source(graph)) goto error;
                num_buckets /= 2;
            }
        }
    }

    graph->optimize = MIN(num_buckets * 256 - num_edges, num_edges - num_buckets * 16);
    graph->optimize = MAX(graph->optimize, 256ULL);
    if (!(graph->flags & TVG_FLAGS_DIRECTED)) graph->optimize /= 2;
    return;

error:
    fprintf(stderr, "%s: Failed to optimize graph, trying again later.\n", __func__);
    graph->optimize = 1024;
}

int graph_empty(struct graph *graph)
{
    struct entry2 *edge;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        return 0;
    }

    return 1;
}

uint64_t graph_num_edges(struct graph *graph)
{
    uint64_t i, num_buckets;
    uint64_t num_edges = 0;
    struct entry2 *edge;
    uint64_t mask;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);

    if (graph->flags & TVG_FLAGS_DIRECTED)
    {
        for (i = 0; i < num_buckets; i++)
            num_edges += bucket2_num_entries(&graph->buckets[i]);
        return num_edges;
    }

    if (graph->bits_source > graph->bits_target)
        mask = (1ULL << graph->bits_target) - 1;
    else
        mask = (1ULL << graph->bits_source) - 1;

    for (i = 0; i < num_buckets; i++)
    {
        if (((i >> graph->bits_source) ^ i) & mask)  /* non-diagonal */
        {
            num_edges += bucket2_num_entries(&graph->buckets[i]);
            continue;
        }

        BUCKET2_FOR_EACH_ENTRY(&graph->buckets[i], edge)
        {
            if (edge->target >= edge->source)
                num_edges += 2;
        }
    }

    assert(!(num_edges & 1));
    num_edges /= 2;
    return num_edges;
}

uint64_t graph_get_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t max_edges)
{
    uint64_t count = 0;
    struct entry2 *edge;

    if (!max_edges || (!indices && !weights))
        return graph_num_edges(graph);

    /* For undirected graph, the GRAPH_FOR_EACH_EDGE macro will
     * automatically skip edges in the reverse direction */

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        if (count++ >= max_edges) continue;
        if (indices)
        {
            *indices++ = edge->source;
            *indices++ = edge->target;
        }
        if (weights)
        {
            *weights++ = edge->weight;
        }
    }

    return count;
}

struct vector *graph_get_nodes(struct graph *graph)
{
    struct vector *nodes;
    struct entry2 *edge;

    /* For graphs loaded from a MongoDB, return the occurrence
     * vector instead of computing the nodes dynamically. */
    if (graph->nodes)
    {
        if (!graph->revision)
            return grab_vector(graph->nodes);

        free_vector(graph->nodes);
        graph->nodes = NULL;
    }

    if (!(nodes = alloc_vector(0)))
        return NULL;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        if (!vector_add_entry(nodes, edge->source, 1))
        {
            free_vector(nodes);
            return NULL;
        }
        if (!vector_add_entry(nodes, edge->target, 1))
        {
            free_vector(nodes);
            return NULL;
        }
    }

    nodes->flags |= TVG_FLAGS_READONLY;  /* block changes */
    return nodes;
}

static int _sort_entry2_by_weight(const void *a, const void *b, void *userdata)
{
    const struct entry2 *ba = a, *bb = b;
    return -COMPARE(ba->weight, bb->weight);
}

uint64_t graph_get_top_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t max_edges)
{
    struct minheap *queue;
    struct entry2 *edge;
    struct entry2 new_edge;
    float weight;
    uint64_t count = 0;

    if (!max_edges)
        return 0;

    if (!(queue = alloc_minheap(sizeof(struct entry2), _sort_entry2_by_weight, NULL)))
        return 0;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        if (!minheap_push(queue, edge))
        {
            fprintf(stderr, "%s: Out of memory\n", __func__);
            free_minheap(queue);
            return 0;
        }
    }

    assert(max_edges >= 1);
    while (minheap_pop(queue, &new_edge))
    {
        if (indices)
        {
            *indices++ = new_edge.source;
            *indices++ = new_edge.target;
        }
        if (weights)
        {
            *weights++ = new_edge.weight;
        }
        if (++count == max_edges)
        {
            /* Count how many other edges have the same weight. */
            weight = new_edge.weight;
            while (minheap_pop(queue, &new_edge))
            {
                if (new_edge.weight != weight) break;
                count++;
            }
            break;
        }
    }

    free_minheap(queue);
    return count;
}

uint64_t graph_get_adjacent_edges(struct graph *graph, uint64_t source, uint64_t *indices, float *weights, uint64_t max_edges)
{
    uint64_t count = 0;
    struct entry2 *edge;

    GRAPH_FOR_EACH_ADJACENT_EDGE(graph, source, edge)
    {
        if (count++ >= max_edges) continue;
        if (indices)
        {
            assert(edge->source == source);
            *indices++ = edge->target;
        }
        if (weights)
        {
            *weights++ = edge->weight;
        }
    }

    return count;
}

int graph_set_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t num_edges)
{
    if (weights)
    {
        while (num_edges--)
        {
            if (!graph_set_edge(graph, indices[0], indices[1], weights[0]))
                return 0;

            indices += 2;
            weights++;
        }
    }
    else
    {
        while (num_edges--)
        {
            if (!graph_set_edge(graph, indices[0], indices[1], 1.0f))
                return 0;

            indices += 2;
        }
    }

    return 1;
}

int graph_add_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t num_edges)
{
    if (weights)
    {
        while (num_edges--)
        {
            if (!graph_add_edge(graph, indices[0], indices[1], weights[0]))
                return 0;

            indices += 2;
            weights++;
        }
    }
    else
    {
        while (num_edges--)
        {
            if (!graph_add_edge(graph, indices[0], indices[1], 1.0f))
                return 0;

            indices += 2;
        }
    }

    return 1;
}

int graph_add_graph(struct graph *out, struct graph *graph, float weight)
{
    struct entry2 *edge;

    if ((out->flags ^ graph->flags) & TVG_FLAGS_DIRECTED)
        return 0;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        if (!graph_add_edge(out, edge->source, edge->target, edge->weight * weight))
            return 0;
    }

    /* graph_add_edge already updated the revision */
    return 1;
}

int graph_sub_edge(struct graph *graph, uint64_t source, uint64_t target, float weight)
{
    return graph_add_edge(graph, source, target, -weight);
}

int graph_sub_edges(struct graph *graph, uint64_t *indices, float *weights, uint64_t num_edges)
{
    if (weights)
    {
        while (num_edges--)
        {
            if (!graph_add_edge(graph, indices[0], indices[1], -weights[0]))
                return 0;

            indices += 2;
            weights++;
        }
    }
    else
    {
        while (num_edges--)
        {
            if (!graph_add_edge(graph, indices[0], indices[1], -1.0f))
                return 0;

            indices += 2;
        }
    }

    return 1;
}

int graph_sub_graph(struct graph *out, struct graph *graph, float weight)
{
    return graph_add_graph(out, graph, -weight);
}

int graph_del_edges(struct graph *graph, uint64_t *indices, uint64_t num_edges)
{
    while (num_edges--)
    {
        if (!graph_del_edge(graph, indices[0], indices[1]))
            return 0;

        indices += 2;
    }

    return 1;
}

struct vector *graph_mul_vector(const struct graph *graph, const struct vector *vector)
{
    struct vector *out;
    struct entry1 *entry;
    struct entry2 *edge;

    /* FIXME: Appropriate flags? */
    if (!(out = alloc_vector(0)))
        return NULL;

    GRAPH_VECTOR_FOR_EACH_EDGE(graph, edge, vector, entry)
    {
        if (!entry) continue;
        if (!vector_add_entry(out, edge->source, edge->weight * entry->weight))
        {
            free_vector(out);
            return NULL;
        }
    }

    return out;
}

struct vector *graph_in_degrees(const struct graph *graph)
{
    struct vector *vector;
    struct entry2 *edge;

    /* FIXME: Appropriate flags? */
    if (!(vector = alloc_vector(0)))
        return NULL;

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (!vector_add_entry(vector, edge->target, 1.0))
        {
            free_vector(vector);
            return NULL;
        }
    }

    return vector;
}

struct vector *graph_in_weights(const struct graph *graph)
{
    struct vector *vector;
    struct entry2 *edge;

    /* FIXME: Appropriate flags? */
    if (!(vector = alloc_vector(0)))
        return NULL;

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (!vector_add_entry(vector, edge->target, edge->weight))
        {
            free_vector(vector);
            return NULL;
        }
    }

    return vector;
}

struct vector *graph_out_degrees(const struct graph *graph)
{
    struct vector *vector;
    struct entry2 *edge;

    /* FIXME: Appropriate flags? */
    if (!(vector = alloc_vector(0)))
        return NULL;

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (!vector_add_entry(vector, edge->source, 1.0))
        {
            free_vector(vector);
            return NULL;
        }
    }

    return vector;
}

struct vector *graph_out_weights(const struct graph *graph)
{
    struct vector *vector;
    struct entry2 *edge;

    /* FIXME: Appropriate flags? */
    if (!(vector = alloc_vector(0)))
        return NULL;

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (!vector_add_entry(vector, edge->source, edge->weight))
        {
            free_vector(vector);
            return NULL;
        }
    }

    return vector;
}

struct vector *graph_degree_anomalies(const struct graph *graph)
{
    struct vector *vector, *temp;
    struct entry1 *entry;
    struct entry2 *edge;

    if (!(vector = graph_out_degrees(graph)))
        return NULL;

    if (!(temp = alloc_vector(0)))
    {
        free_vector(vector);
        return NULL;
    }

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (!vector_add_entry(temp, edge->source, vector_get_entry(vector, edge->target)))
        {
            free_vector(vector);
            free_vector(temp);
            return NULL;
        }
    }

    VECTOR_FOR_EACH_ENTRY(vector, entry)
    {
        entry->weight -= vector_get_entry(temp, entry->index) / entry->weight;
    }

    free_vector(temp);
    return vector;
}

struct vector *graph_weight_anomalies(const struct graph *graph)
{
    struct vector *vector, *temp;
    struct entry1 *entry;
    struct entry2 *edge;

    if (!(vector = graph_out_weights(graph)))
        return NULL;

    if (!(temp = alloc_vector(0)))
    {
        free_vector(vector);
        return NULL;
    }

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (!vector_add_entry(temp, edge->source, edge->weight * vector_get_entry(vector, edge->target)))
        {
            free_vector(vector);
            free_vector(temp);
            return NULL;
        }
    }

    VECTOR_FOR_EACH_ENTRY(vector, entry)
    {
        entry->weight -= vector_get_entry(temp, entry->index) / entry->weight;
    }

    free_vector(temp);
    return vector;
}

double graph_sum_weights(const struct graph *graph)
{
    struct entry2 *edge;
    double sum = 0.0;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        sum += edge->weight;
    }

    return sum;
}

struct vector *graph_power_iteration(const struct graph *graph, struct vector *initial_guess,
                                     uint32_t num_iterations, double tolerance, double *ret_eigenvalue)
{
    struct random_pool pool;
    struct vector *vector;
    struct vector *temp;
    struct entry2 *edge;
    float value;

    if (!num_iterations)
        num_iterations = 100;

    /* FIXME: Appropriate flags? */
    if (!(vector = alloc_vector(0)))
        return NULL;

    random_pool_init(&pool);

    GRAPH_FOR_EACH_DIRECTED_EDGE(graph, edge)
    {
        if (vector_has_entry(vector, edge->target)) continue;
        if (!initial_guess || !(value = vector_get_entry(initial_guess, edge->target)))
            value = random_pool_float(&pool);
        if (!vector_add_entry(vector, edge->target, value))
        {
            free_vector(vector);
            return NULL;
        }
    }

    while (num_iterations--)
    {
        if (!(temp = graph_mul_vector(graph, vector)))
        {
            free_vector(vector);
            return NULL;
        }

        if (!vector_mul_const(temp, (float)(1.0 / vector_norm(temp))))
        {
            free_vector(vector);
            free_vector(temp);
            return NULL;
        }

        if (tolerance > 0.0 && vector_sub_vector_norm(vector, temp) <= tolerance)
            num_iterations = 0;

        free_vector(vector);
        vector = temp;
    }

    if (ret_eigenvalue)
    {
        if (!(temp = graph_mul_vector(graph, vector)))
        {
            free_vector(vector);
            return NULL;
        }
        *ret_eigenvalue = vector_mul_vector(vector, temp);
        free_vector(temp);
    }

    return vector;
}

struct graph *graph_filter_nodes(const struct graph *graph, struct vector *nodes)
{
    uint32_t graph_flags;
    struct entry2 *edge;
    struct graph *out;

    graph_flags = graph->flags & (TVG_FLAGS_POSITIVE |
                                  TVG_FLAGS_DIRECTED);


    if (!(out = alloc_graph(graph_flags)))
        return NULL;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        if (!vector_has_entry(nodes, edge->source)) continue;
        if (!vector_has_entry(nodes, edge->target)) continue;

        if (!graph_set_edge(out, edge->source, edge->target, edge->weight))
        {
            free_graph(out);
            return NULL;
        }
    }

    return out;
}

struct graph *graph_normalize(const struct graph *graph)
{
    struct vector *out_weights;
    struct vector *in_weights;
    struct graph *result;
    uint32_t graph_flags;
    struct entry2 *edge;
    float weight;
    int ret = 0;

    if (!(out_weights = graph_out_weights(graph)))
        return NULL;

    if (!(graph->flags & TVG_FLAGS_DIRECTED))
        in_weights = grab_vector(out_weights);
    else if (!(in_weights = graph_in_weights(graph)))
    {
        free_vector(out_weights);
        return NULL;
    }

    graph_flags = graph->flags & TVG_FLAGS_DIRECTED;
    if (!(result = alloc_graph(graph_flags)))
        goto error;

    GRAPH_FOR_EACH_EDGE(graph, edge)
    {
        weight = vector_get_entry(out_weights, edge->source) *
                 vector_get_entry(in_weights,  edge->target);
        if (!graph_add_edge(result, edge->source, edge->target, edge->weight / weight))
            goto error;
    }

    ret = 1;

error:
    if (!ret)
    {
        free_graph(result);
        result = NULL;
    }
    free_vector(in_weights);
    free_vector(out_weights);
    return result;
}

int graph_save_binary(struct graph *graph, const char *filename)
{
    struct file_header header;
    struct bucket2 *bucket;
    uint64_t i, num_buckets;
    FILE *fp;
    int ret = 0;

    if (!(fp = fopen(filename, "wb")))
    {
        fprintf(stderr, "%s: Failed to create file '%s'\n", __func__, filename);
        return 0;
    }

    header.tag         = FILE_TAG;
    header.version     = FILE_VERSION;
    header.flags       = graph->flags & ~(TVG_FLAGS_LOAD_NEXT |
                                          TVG_FLAGS_LOAD_PREV |
                                          TVG_FLAGS_READONLY);
    header.bits_source = graph->bits_source;
    header.bits_target = graph->bits_target;

    if (fwrite(&header, sizeof(header), 1, fp) != 1)
        goto error;

    num_buckets = 1ULL << (graph->bits_source + graph->bits_target);
    for (i = 0; i < num_buckets; i++)
    {
        bucket = &graph->buckets[i];
        if (fwrite(&bucket->num_entries, sizeof(bucket->num_entries), 1, fp) != 1)
            goto error;
        if (!bucket->num_entries)
            continue;  /* nothing to save */
        if (fwrite(bucket->entries, sizeof(*bucket->entries), bucket->num_entries, fp) != bucket->num_entries)
            goto error;
    }

    /* Saving successful. */
    ret = 1;

error:
    fclose(fp);
    return ret;
}

struct graph *graph_load_binary(const char *filename)
{
    struct file_header header;
    uint64_t i, num_buckets;
    uint64_t num_entries;
    struct bucket2 *bucket;
    struct graph *result = NULL;
    FILE *fp;
    int ret = 0;

    if (!(fp = fopen(filename, "rb")))
    {
        fprintf(stderr, "%s: File '%s' not found\n", __func__, filename);
        return NULL;
    }

    if (fread(&header, sizeof(header), 1, fp) != 1)
        goto error;

    if (header.tag != FILE_TAG)
    {
        fprintf(stderr, "%s: Expected tag %08x, got %08x\n", __func__, FILE_TAG, header.tag);
        goto error;
    }
    if (header.version != FILE_VERSION)
    {
        fprintf(stderr, "%s: Expected version %08x, got %08x\n", __func__, FILE_VERSION, header.version);
        goto error;
    }
    if (header.bits_source > 31 || header.bits_target > 31)
    {
        fprintf(stderr, "%s: Graph is too large to load into memory\n", __func__);
        goto error;
    }

    if (!(result = alloc_graph(header.flags)))
        goto error;

    num_buckets = 1ULL << (header.bits_source + header.bits_target);
    if (!(bucket = malloc(sizeof(*bucket) * num_buckets)))
        goto error;

    for (i = 0; i < num_buckets; i++)
        init_bucket2(&bucket[i]);

    free(result->buckets);  /* buckets have no references */
    result->bits_source = header.bits_source;
    result->bits_target = header.bits_target;
    result->buckets     = bucket;

    for (i = 0; i < num_buckets; i++)
    {
        bucket = &result->buckets[i];
        if (fread(&num_entries, sizeof(num_entries), 1, fp) != 1)
            goto error;
        if (!num_entries)
            continue;  /* nothing to load */
        if (!bucket2_reserve(bucket, num_entries))
            goto error;
        if (fread(bucket->entries, sizeof(*bucket->entries), num_entries, fp) != num_entries)
            goto error;
        bucket->num_entries = num_entries;
    }

    /* Loading successful. */
    ret = 1;

error:
    if (!ret)
    {
        free_graph(result);
        result = NULL;
    }
    fclose(fp);
    return result;
}
