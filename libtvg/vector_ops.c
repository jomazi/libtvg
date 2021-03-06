/*
 * Time-varying graph library
 * Vector functions.
 *
 * Copyright (c) 2018-2019 Sebastian Lackner
 */

#include "internal.h"

static inline struct bucket1 *_vector_get_bucket(struct vector *vector, uint64_t index)
{
    uint32_t i = (uint32_t)(index & ((1ULL << vector->bits) - 1));
    return &vector->buckets[i];
}

static inline struct entry1 *_vector_get_entry(struct vector *vector, uint64_t index, int allocate)
{
    struct bucket1 *bucket = _vector_get_bucket(vector, index);
    return bucket1_get_entry(bucket, index, allocate);
}

int vector_has_entry(struct vector *vector, uint64_t index)
{
    return _vector_get_entry(vector, index, 0) != NULL;
}

float vector_get_entry(struct vector *vector, uint64_t index)
{
    struct entry1 *entry;

    if (!(entry = _vector_get_entry(vector, index, 0)))
        return 0.0;

    return entry->weight;
}

int vector_clear(struct vector *vector)
{
    uint64_t i, num_buckets;

    if (UNLIKELY(vector->flags & TVG_FLAGS_READONLY))
        return 0;

    num_buckets = 1ULL << vector->bits;
    for (i = 0; i < num_buckets; i++)
        bucket1_clear(&vector->buckets[i]);

    vector->revision++;
    if (!--vector->optimize)
        vector_optimize(vector);

    return 1;
}

int vector_set_entry(struct vector *vector, uint64_t index, float weight)
{
    struct entry1 *entry;

    if (UNLIKELY(vector->flags & TVG_FLAGS_READONLY))
        return 0;

    if (!(entry = _vector_get_entry(vector, index, 1)))
        return 0;

    entry->weight = weight;

    vector->revision++;
    if (!--vector->optimize)
        vector_optimize(vector);

    return 1;
}

int vector_add_entry(struct vector *vector, uint64_t index, float weight)
{
    struct entry1 *entry;

    if (UNLIKELY(vector->flags & TVG_FLAGS_READONLY))
        return 0;

    if (!(entry = _vector_get_entry(vector, index, 1)))
        return 0;

    entry->weight += weight;

    vector->revision++;
    if (!--vector->optimize)
        vector_optimize(vector);

    return 1;
}

int vector_del_entry(struct vector *vector, uint64_t index)
{
    struct bucket1 *bucket;
    struct entry1 *entry;

    if (UNLIKELY(vector->flags & TVG_FLAGS_READONLY))
        return 0;

    bucket = _vector_get_bucket(vector, index);
    if (!(entry = bucket1_get_entry(bucket, index, 0)))
        return 1;

    bucket1_del_entry(bucket, entry);

    vector->revision++;
    if (!--vector->optimize)
        vector_optimize(vector);

    return 1;
}

int vector_mul_const(struct vector *vector, float constant)
{
    struct entry1 *entry;

    if (UNLIKELY(vector->flags & TVG_FLAGS_READONLY))
        return 0;

    if (constant == 1.0)
        return 1;

    VECTOR_FOR_EACH_ENTRY(vector, entry)
    {
        entry->weight *= constant;
    }

    vector->revision++;
    return 1;
}

int vector_del_small(struct vector *vector, float eps)
{
    struct bucket1 *bucket;
    struct entry1 *entry, *out;
    uint64_t i, num_buckets;

    if (UNLIKELY(vector->flags & TVG_FLAGS_READONLY))
        return 0;

    eps = fabs(eps);  /* ensure eps is positive */
    num_buckets = 1ULL << vector->bits;
    for (i = 0; i < num_buckets; i++)
    {
        bucket = &vector->buckets[i];
        out = &bucket->entries[0];

        if (vector->flags & TVG_FLAGS_POSITIVE)
        {
            BUCKET1_FOR_EACH_ENTRY(bucket, entry)
            {
                if (entry->weight <= eps) continue;
                if (out != entry) *out = *entry;
                out++;
            }
        }
        else
        {
            BUCKET1_FOR_EACH_ENTRY(bucket, entry)
            {
                if (fabs(entry->weight) <= eps) continue;
                if (out != entry) *out = *entry;
                out++;
            }
        }

        bucket->num_entries = (uint64_t)(out - &bucket->entries[0]);
        assert(bucket->num_entries <= bucket->max_entries);
    }

    vector->revision++;
    /* FIXME: Trigger vector_optimize? */
    return 1;
}
