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
            goto done;
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
