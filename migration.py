# import psycopg2

# try:
#     conn = psycopg2.connect(database = "projetofinal", user = "postgres", password = "admin", host = "localhost", port = "5432")
# except:
#     print("I am unable to connect to the database") 

# cur = conn.cursor()
# try:
#     cur.execute("CREATE TABLE test (id serial PRIMARY KEY, num integer, data varchar);")
# except:
#     print("I can't drop our test database!")

# conn.commit() # <--- makes sure the change is shown in the database
# conn.close()
# cur.close()

import psycopg2

#establishing the connection
conn = psycopg2.connect(
   database="elastic_HQ", user='elastichq_admin', password='elasticHQ@321', host='127.0.0.1', port= '5432'
)
conn.autocommit = True

#Creating a cursor object using the cursor() method
cursor = conn.cursor()

#Preparing query to create a database
cluster_sql = '''
CREATE TABLE IF NOT EXISTS cluster (
    id SERIAL PRIMARY KEY,
    nodes_count INT,
    indices_count INT,
    status VARCHAR(255),
    name VARCHAR(255) UNIQUE,
    documents INT,
    size INT,
    active_shards INT,
    unassigned_shards INT,
    initializing_shards INT,
    relocating_shards INT,
    created_at TIMESTAMP
);
''';

#Creating a database
cursor.execute(cluster_sql)
print("Cluster table created successfully........")

node_sql = '''
CREATE TABLE IF NOT EXISTS node (
    id SERIAL PRIMARY KEY,
    cluster_id INT REFERENCES cluster(id),
    name VARCHAR(255),
    address VARCHAR(255),
    master BOOLEAN NOT NULL DEFAULT FALSE,
    data BOOLEAN NOT NULL DEFAULT FALSE,
    heap_used VARCHAR(255),
    free_space VARCHAR(255),
    created_at TIMESTAMP
);
''';

#Creating a database
cursor.execute(node_sql)
print("Node table created successfully........")

node_sql = '''
CREATE TABLE IF NOT EXISTS index (
    id SERIAL PRIMARY KEY UNIQUE,
    cluster_id INT REFERENCES cluster(id),
    name VARCHAR(255) UNIQUE,
    docs INT,
    shard INT,
    replicas INT,
    size INT,
    cache_size INT,
    created_at TIMESTAMP
);
''';

#Creating a database
cursor.execute(node_sql)
print("Index table created successfully........")

index_stats_sql = '''
CREATE TABLE IF NOT EXISTS index_stats (
    id SERIAL PRIMARY KEY,
    index_id INT REFERENCES index(id),
    documents_size INT,
    total_documents INT,
    deleted_documents INT,
    query_total INT,
    query_total_in_ms INT,
    fetch_total INT,
    fetch_total_in_ms INT,
    index_rate float8, 
    search_rate float8,
    search_latency float8,
    flush_operations INT,
    index_total INT,
    index_time_in_ms INT,
    delete_index_total INT,
    created_at TIMESTAMP
);
''';

#Creating a database
cursor.execute(index_stats_sql)
print("Index stats table created successfully........")

#Closing the connection
conn.close()