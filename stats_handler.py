from elastichq.service import IndicesService, ClusterService
from elastichq.model import ClusterDTO

from elastichq.api.clusters import dbConnect
from datetime import datetime

import psycopg2
import redis

def persist_elastic_search():
    clusters = ClusterService().get_clusters()
    schema = ClusterDTO(many=True)
    result = schema.dump(clusters)

    

    for cluster in result.data:

        #establishing the connection

        # conn = psycopg2.connect(
        #     database="postgres", user='postgres', password='password', host='127.0.0.1', port= '5432'
        # )
        # conn.autocommit = True
        conn = dbConnect()
        cursor = conn.cursor()

        cluster_info = ClusterService().get_cluster_summary(cluster['cluster_name'])
        query = '''
        INSERT INTO cluster
            (
                name, nodes_count, indices_count, status, 
                documents, size, active_shards, unassigned_shards, initializing_shards, 
                relocating_shards, created_at
            )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())
        ON CONFLICT (name) DO NOTHING RETURNING id;
        '''
        data = (
            cluster_info['cluster_name'], cluster_info['number_of_nodes'], cluster_info['indices_count'], cluster_info['status'], 
            cluster_info['number_of_documents'], cluster_info['indices_size_in_bytes'],
            cluster_info['active_shards'], cluster_info['unassigned_shards'], cluster_info['initializing_shards'],
            cluster_info['relocating_shards'],
            )  
        cluster_name = cluster['cluster_name']
        cursor.execute(query, data)
        cursor.execute('''SELECT id from cluster where name=%s''', (cluster_info['cluster_name'],))

        #Fetching 1st row from the table
        cluster_id = cursor.fetchone()[0]
        
        # cluster.execute(query, data)
        res = IndicesService().get_indices_stats(cluster['cluster_name'], None)
        for name, val in res['indices'].items():
            value = IndicesService().get_indices_stats(cluster['cluster_name'], name)
            query = '''
                INSERT INTO index
                    (
                        cluster_id, name, docs, size, cache_size, created_at
                    )
                VALUES (%s, %s, %s, %s, %s, now())
                ON CONFLICT (name) DO NOTHING RETURNING id;
            '''
            data = (
                cluster_id, name, value['indices'][name]['primaries']['docs']['count'], 
                value['indices'][name]['primaries']['store']['size_in_bytes'], value['indices'][name]['primaries']['query_cache']['memory_size_in_bytes'],
            )
            cursor.execute(query, data)
            cursor.execute('''SELECT id from index where name=%s and cluster_id=%s''', (name, cluster_id,))
            result = cursor.fetchone()
            index_id = result[0]
            r = redis.Redis(host='localhost', port=6379, decode_responses=True)
            cons_name = cluster_name+":"+name
            prev_rate = str(r.get(cons_name))
            prev_rate = prev_rate.split(":")

            query = '''
                INSERT INTO index_stats
                    (
                        index_id, documents_size, total_documents, deleted_documents, query_total, query_total_in_ms,
                        fetch_total, fetch_total_in_ms, index_rate, search_rate, search_latency, flush_operations, 
                        index_total, index_time_in_ms, delete_index_total, created_at
                    )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now());
            '''
            data = (
                index_id, value['indices'][name]['primaries']['store']['size_in_bytes'], value['indices'][name]['primaries']['docs']['count'], 
                value['indices'][name]['primaries']['docs']['deleted'], value['indices'][name]['primaries']['search']['query_total'],value['indices'][name]['primaries']['search']['query_time_in_millis'],
                value['indices'][name]['primaries']['search']['fetch_total'],value['indices'][name]['primaries']['search']['fetch_time_in_millis'], float(prev_rate[0]), float(prev_rate[1]), float(prev_rate[2]),
                value['indices'][name]['primaries']['flush']['total'], value['indices'][name]['primaries']['indexing']['index_total'], value['indices'][name]['primaries']['indexing']['index_time_in_millis'],
                value['indices'][name]['primaries']['indexing']['delete_total'],
            )
            cursor.execute(query, data)
        conn.close()
