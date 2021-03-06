/*
 * Time-varying graph library
 * Breath-first search functions.
 *
 * Copyright (c) 2017-2018 Sebastian Lackner
 */

#include "internal.h"

static int _sort_bfs_entry_by_weight(const void *a, const void *b, void *userdata)
{
    const struct bfs_entry *ba = a, *bb = b;
    return COMPARE(ba->weight, bb->weight);
}

static int _sort_bfs_entry_by_count(const void *a, const void *b, void *userdata)
{
    const struct bfs_entry *ba = a, *bb = b;
    return COMPARE(ba->count, bb->count);
}

int graph_bfs(struct graph *graph, uint64_t source, int use_weights, int (*callback)(struct graph *graph,
              const struct bfs_entry *entry, void *userdata), void *userdata)
{
    struct bfs_entry entry, new_entry;
    struct vector *visited;
    struct minheap *queue;
    struct entry2 *edge;
    int ret = 0;

    if (!(visited = alloc_vector(0)))
        return 0;

    if (!(queue = alloc_minheap(sizeof(struct bfs_entry), use_weights ?
          _sort_bfs_entry_by_weight : _sort_bfs_entry_by_count, NULL)))
    {
        free_vector(visited);
        return 0;
    }

    new_entry.weight = 0.0;
    new_entry.count  = 0;
    new_entry.from   = ~0ULL;
    new_entry.to     = source;

    if (!minheap_push(queue, &new_entry))
    {
        fprintf(stderr, "%s: Out of memory!\n", __func__);
        goto done;
    }

    while (minheap_pop(queue, &entry))
    {
        source = entry.to;

        if (vector_has_entry(visited, source))
            continue;
        if ((ret = callback(graph, &entry, userdata)))
        {
            /* 0: continue, 1: success, -1: error */
            ret = (ret > 0);
            goto done;
        }
        if (!vector_set_entry(visited, source, 1))
        {
            fprintf(stderr, "%s: Out of memory!\n", __func__);
            goto done;
        }

        GRAPH_FOR_EACH_ADJACENT_EDGE(graph, source, edge)
        {
            assert(edge->source == source);
            if (vector_has_entry(visited, edge->target))
                continue;

            new_entry.weight = entry.weight + edge->weight;
            new_entry.count  = entry.count + 1;
            new_entry.from   = source;
            new_entry.to     = edge->target;

            if (!minheap_push(queue, &new_entry))
            {
                fprintf(stderr, "%s: Out of memory!\n", __func__);
                goto done;
            }
        }
    }

    ret = 1;

done:
    free_minheap(queue);
    free_vector(visited);
    return ret;
}

struct bfs_distance_context
{
    uint64_t end;
    struct bfs_entry entry;
};

static int _bfs_distance_callback(struct graph *graph, const struct bfs_entry *entry, void *userdata)
{
    struct bfs_distance_context *context = userdata;
    if (entry->to != context->end) return 0;
    context->entry = *entry;
    return 1;
}

uint64_t graph_get_distance_count(struct graph *graph, uint64_t source, uint64_t end)
{
    struct bfs_distance_context context;
    context.end = end;
    context.entry.count = ~0ULL;

    /* FIXME: Distinguish unreachable node and out-of-memory error */
    graph_bfs(graph, source, 0, _bfs_distance_callback, &context);
    return context.entry.count;
}

double graph_get_distance_weight(struct graph *graph, uint64_t source, uint64_t end)
{
    struct bfs_distance_context context;
    context.end = end;
    context.entry.weight = INFINITY;

    /* FIXME: Distinguish unreachable node and out-of-memory error */
    graph_bfs(graph, source, 1, _bfs_distance_callback, &context);
    return context.entry.weight;
}

struct bfs_all_distances_count_context
{
    struct vector *counts;
    uint64_t max_count;
};

static int _bfs_all_distances_count_callback(struct graph *graph, const struct bfs_entry *entry, void *userdata)
{
    struct bfs_all_distances_count_context *context = userdata;
    if (entry->count > context->max_count) return 1;
    if (!vector_set_entry(context->counts, entry->to, entry->count)) return -1;
    return 0;
}

struct vector *graph_get_all_distances_count(struct graph *graph, uint64_t source, uint64_t max_count)
{
    struct bfs_all_distances_count_context context;

    context.max_count = max_count;
    if (!(context.counts = alloc_vector(0)))
        return NULL;

    if (!graph_bfs(graph, source, 0, _bfs_all_distances_count_callback, &context))
    {
        free_vector(context.counts);
        return NULL;
    }

    return context.counts;
}

struct bfs_all_distances_weight_context
{
    struct vector *weights;
    double max_weight;
};

static int _bfs_all_distances_weight_callback(struct graph *graph, const struct bfs_entry *entry, void *userdata)
{
    struct bfs_all_distances_weight_context *context = userdata;
    if (entry->weight > context->max_weight) return 1;
    if (!vector_set_entry(context->weights, entry->to, entry->weight)) return -1;
    return 0;
}

struct vector *graph_get_all_distances_weight(struct graph *graph, uint64_t source, double max_weight)
{
    struct bfs_all_distances_weight_context context;

    context.max_weight = max_weight;
    if (!(context.weights = alloc_vector(0)))
        return NULL;

    if (!graph_bfs(graph, source, 1, _bfs_all_distances_weight_callback, &context))
    {
        free_vector(context.weights);
        return NULL;
    }

    return context.weights;
}

struct bfs_all_distances_graph_context
{
    int use_weights;
    uint64_t start;
    struct graph *distances;
};

static int _bfs_all_distances_graph_callback(struct graph *graph, const struct bfs_entry *entry, void *userdata)
{
    struct bfs_all_distances_graph_context *context = userdata;
    if (entry->to == context->start) return 0;  /* skip diagonal */
    if (!graph_add_edge(context->distances, context->start, entry->to,
                        context->use_weights ? entry->weight : entry->count)) return -1;
    return 0;
}

struct graph *graph_get_all_distances_graph(struct graph *graph, int use_weights)
{
    struct bfs_all_distances_graph_context context;
    struct vector *nodes;
    struct entry1 *entry;

    if (!(nodes = graph_get_nodes(graph)))
        return NULL;

    context.use_weights = use_weights;
    if (!(context.distances = alloc_graph(TVG_FLAGS_DIRECTED)))
    {
        free_vector(nodes);
        return NULL;
    }

    VECTOR_FOR_EACH_ENTRY(nodes, entry)
    {
        context.start = entry->index;
        if (!graph_bfs(graph, entry->index, use_weights, _bfs_all_distances_graph_callback, &context))
        {
            free_graph(context.distances);
            free_vector(nodes);
            return NULL;
        }
    }

    free_vector(nodes);
    return context.distances;
}

struct bfs_components_context
{
    struct vector *components;
    uint64_t identifier;
};

static int _bfs_components_callback(struct graph *graph, const struct bfs_entry *entry, void *userdata)
{
    struct bfs_components_context *context = userdata;
    if (!vector_set_entry(context->components, entry->to, context->identifier)) return -1;
    return 0;
}

struct vector *graph_get_connected_components(struct graph *graph)
{
    struct bfs_components_context context;
    struct vector *nodes;
    struct entry1 *entry;

    if (graph->flags & TVG_FLAGS_DIRECTED)
    {
        fprintf(stderr, "%s: Directed graphs not supported\n", __func__);
        return NULL;
    }

    if (!(nodes = graph_get_nodes(graph)))
        return NULL;

    context.identifier = 0;
    if (!(context.components = alloc_vector(0)))
    {
        free_vector(nodes);
        return NULL;
    }

    VECTOR_FOR_EACH_ENTRY(nodes, entry)
    {
        if (vector_has_entry(context.components, entry->index)) continue;
        if (!graph_bfs(graph, entry->index, 0, _bfs_components_callback, &context))
        {
            free_vector(context.components);
            free_vector(nodes);
            return NULL;
        }
        context.identifier++;
    }

    free_vector(nodes);
    return context.components;
}
