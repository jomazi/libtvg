/*
 * Time-varying graph library
 * Metric functions.
 *
 * Copyright (c) 2019 Sebastian Lackner
 */

#include "tvg.h"
#include "internal.h"

struct edge_stability
{
    struct list entry;
    uint64_t source;
    uint64_t target;
    float    value1;
    float    value2;
};

struct node_stability
{
    struct list entry;
    uint64_t index;
    float    value1;
    float    value2;
};

static int _sort_edge_stability(const void *a, const void *b, void *userdata)
{
    const struct edge_stability *sa = a, *sb = b;
    int res;

    if ((res = COMPARE(sa->value1, sb->value1))) return res;
    return COMPARE(sa->value2, sb->value2);
}

static int _sort_node_stability(const void *a, const void *b, void *userdata)
{
    const struct node_stability *sa = a, *sb = b;
    int res;

    if ((res = COMPARE(sa->value1, sb->value1))) return res;
    return COMPARE(sa->value2, sb->value2);
}

struct graph *metric_edge_stability_pareto(struct graph **graphs, uint64_t num_graphs,
                                           struct graph *override_mean, float base)
{
    struct edge_stability *next_stability;
    struct edge_stability *stability;
    struct edge_stability *best;
    struct array *array = NULL;
    struct graph *result;
    uint32_t graph_flags;
    struct entry2 *edge;
    float sum2, temp;
    float weight = 1.0;
    struct list queue;
    float mean;
    uint64_t i;
    int ret = 0;

    if (!num_graphs)
        return NULL;

    graph_flags = graphs[0]->flags & TVG_FLAGS_DIRECTED;
    for (i = 1; i < num_graphs; i++)
    {
        if ((graph_flags ^ graphs[i]->flags) & TVG_FLAGS_DIRECTED)
            return NULL;
    }

    if (!(result = alloc_graph(graph_flags)))
        return NULL;

    for (i = 0; i < num_graphs; i++)
    {
        if (!graph_add_graph(result, graphs[i], 1.0))
            goto error;
    }

    if (!graph_mul_const(result, 1.0 / num_graphs))
        goto error;

    if (!(array = alloc_array(sizeof(struct edge_stability))))
        goto error;

    GRAPH_FOR_EACH_EDGE(override_mean ? override_mean : result, edge)
    {
        mean = override_mean ? graph_get_edge(result, edge->source, edge->target) : edge->weight;
        sum2 = 0.0;
        for (i = 0; i < num_graphs; i++)
        {
            temp = graph_get_edge(graphs[i], edge->source, edge->target) - mean;
            sum2 += temp * temp;
        }

        if (!(stability = array_append_empty(array)))
            goto error;

        stability->source = edge->source;
        stability->target = edge->target;
        stability->value1 = -edge->weight;
        stability->value2 = sum2; /* actually sqrt(sum2 / (num_graphs - 1)); */
    }

    free_graph(result);
    if (!(result = alloc_graph(graph_flags | TVG_FLAGS_POSITIVE)))
        goto error;

    array_sort(array, _sort_edge_stability, NULL);

    list_init(&queue);
    for (i = 0; (stability = (struct edge_stability *)array_ptr(array, i)); i++)
    {
        list_add_tail(&queue, &stability->entry);
    }

    while (!list_empty(&queue))
    {
        best = NULL;

        LIST_FOR_EACH_SAFE(stability, next_stability, &queue, struct edge_stability, entry)
        {
            if (!best || stability->value2 < best->value2 ||
                (stability->value1 == best->value1 && stability->value2 == best->value2))
            {
                if (!graph_set_edge(result, stability->source, stability->target, weight))
                    goto error;

                list_remove(&stability->entry);
                best = stability;
            }
        }

        if (base == 0.0)
            weight += 1.0;
        else
            weight *= base;
    }

    ret = 1;

error:
    if (!ret)
    {
        free_graph(result);
        result = NULL;
    }
    free_array(array);
    return result;
}

struct vector *metric_node_stability_pareto(struct vector **vectors, uint64_t num_vectors,
                                            struct vector *override_mean, float base)
{
    struct node_stability *next_stability;
    struct node_stability *stability;
    struct node_stability *best;
    struct array *array = NULL;
    struct vector *result;
    struct entry1 *entry;
    float sum2, temp;
    float weight = 1.0;
    struct list queue;
    float mean;
    uint64_t i;
    int ret = 0;

    if (!num_vectors)
        return NULL;

    if (!(result = alloc_vector(0)))
        return NULL;

    for (i = 0; i < num_vectors; i++)
    {
        if (!vector_add_vector(result, vectors[i], 1.0))
            goto error;
    }

    if (!vector_mul_const(result, 1.0 / num_vectors))
        goto error;

    if (!(array = alloc_array(sizeof(struct node_stability))))
        goto error;

    VECTOR_FOR_EACH_ENTRY(override_mean ? override_mean : result, entry)
    {
        mean = override_mean ? vector_get_entry(result, entry->index) : entry->weight;
        sum2 = 0.0;
        for (i = 0; i < num_vectors; i++)
        {
            temp = vector_get_entry(vectors[i], entry->index) - mean;
            sum2 += temp * temp;
        }

        if (!(stability = array_append_empty(array)))
            goto error;

        stability->index  = entry->index;
        stability->value1 = -entry->weight;
        stability->value2 = sum2; /* actually sqrt(sum2 / (num_vectors - 1)); */
    }

    free_vector(result);
    if (!(result = alloc_vector(TVG_FLAGS_POSITIVE)))
        goto error;

    array_sort(array, _sort_node_stability, NULL);

    list_init(&queue);
    for (i = 0; (stability = (struct node_stability *)array_ptr(array, i)); i++)
    {
        list_add_tail(&queue, &stability->entry);
    }

    while (!list_empty(&queue))
    {
        best = NULL;

        LIST_FOR_EACH_SAFE(stability, next_stability, &queue, struct node_stability, entry)
        {
            if (!best || stability->value2 < best->value2 ||
                (stability->value1 == best->value1 && stability->value2 == best->value2))
            {
                if (!vector_set_entry(result, stability->index, weight))
                    goto error;

                list_remove(&stability->entry);
                best = stability;
            }
        }

        if (base == 0.0)
            weight += 1.0;
        else
            weight *= base;
    }

    ret = 1;

error:
    if (!ret)
    {
        free_vector(result);
        result = NULL;
    }
    free_array(array);
    return result;
}
