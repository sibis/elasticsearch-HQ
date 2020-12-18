"""
.. module:: clusters

.. moduleauthor:: Roy Russo <royrusso@gmail.com>
"""

from flask import request, current_app
from flask_restful import Resource
from requests.exceptions import ConnectionError

from elastichq.model import ClusterDTO
from . import api
from ..common.api_response import APIResponse
from ..common.exceptions import BadRequest, request_wrapper
from ..common.status_codes import HTTP_Status
from ..service import ClusterService, ConnectionNotAuthorized, ConnectionService

import psycopg2, json

class ClusterConnection(Resource):
    """
    Manages cluster connection pool.
    """

    @request_wrapper
    def post(self):
        """

        Creates a connection to a given host/port. Accepts a JSON POST BODY. This will add the connection, if it doesn't already
        exist, to the pool of connections and save the details in the database.

        .. :quickref: ClusterConnection; Creates a connection to the cluster.

        **Example request**:

        .. sourcecode:: http

          POST /api/clusters/_connect/ HTTP/1.1
          Accept: application/json

        .. code-block:: json

            {
                "ip": "127.0.0.1",
                "port": "9200",
                "use_ssl": false
            }

        **Request Structure**

          - *(dict) --*

            - **ip** *(string) --* IP address or host name
            - **port** *(string) --* ES REST API port
            - **use_ssl** *(boolean) --* Whether to use HTTPS or not.

        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 201
          Content-Type: application/json

        .. code-block:: json

            {
              "data": [
                {
                  "cluster_name": "",
                  "cluster_ip": "",
                  "cluster_port": "9200",
                  "cluster_scheme": "http",
                  "cluster_connected": true,
                  "cluster_host": "http://10.0.0.0:9200",
                  "cluster_version": "2.3.5"
                }
              ],
              "status_code": 200,
              "message": null,
              "response_time": 92
            }


        **Response Structure**

          - *(dict) --*

            - **cluster_name** *(string) --* cluster name
            - **cluster_ip** *(string) --* IP or host
            - **cluster_port** *(string) --*
            - **cluster_scheme** *(string) --*
            - **cluster_connected** *(boolean) --* Whether there was a successful connection.
            - **cluster_host** *(string) --* The complete connection url
            - **cluster_version** *(string) --* Elasticsearch version


        :reqheader Accept: application/json
        :resheader Content-Type: application/json
        :status 201: connection created
        :status 400: bad request
        :status 500: server error
        """
        json_data = request.get_json(force=True)
        params = request.values.to_dict()
        params.update(json_data)

        if params.get('ip', None) is None:
            raise BadRequest(message='Missing required parameters.')

        scheme = 'http'
        if params.get('use_ssl', False) is True:
            scheme = 'https'

        try:
            enable_ssl = current_app.config.get('ENABLE_SSL', False)
            ca_certs = current_app.config.get('CA_CERTS', None)
            verify_certs = current_app.config.get('VERIFY_CERTS', None)
            client_key = current_app.config.get('CLIENT_KEY', None)
            client_cert = current_app.config.get('CLIENT_CERT', None)

            print(client_key)
            print(client_cert)
            response = ConnectionService().create_connection(ip=params['ip'], port=params.get('port', "9200"),
                                                             scheme=scheme, username=params.get('username', None),
                                                             password=params.get('password', None),
                                                             fail_on_exception=True,
                                                             enable_ssl=enable_ssl, ca_certs=ca_certs,
                                                             verify_certs=verify_certs,
                                                             client_key=client_key,
                                                             client_cert=client_cert)

            schema = ClusterDTO(many=False)
            result = schema.dump(response)
            return APIResponse(result.data, HTTP_Status.CREATED, None)
        except ConnectionNotAuthorized as cna:
            return APIResponse([], HTTP_Status.UNAUTHORIZED, None)
        except ConnectionError as ce:
            return APIResponse([], HTTP_Status.NOT_FOUND, None)

    @request_wrapper
    def delete(self, cluster_name):
        """
        Deletes a connection from the connection pool and the database, by cluster name.

        :note: This method does NOT delete your Elasticsearch Cluster, just the connection from HQ to it.

        **Example request**:

        .. sourcecode:: http

          DELETE /clusters/_connect/<CLUSTER_NAME> HTTP/1.1
          Accept: application/json

        :type cluster_name: string
        :param cluster_name: Name of cluster connection to remove.
        :returns: List of active clusters.

        :status 200: Ok
        :status 400: bad request
        :status 500: server error
        """
        response = ConnectionService().delete_connection(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


class ClusterList(Resource):
    """
    Retrieves a list of all active and inactive cluster connections.
    """

    @request_wrapper
    def get(self):
        """Returns a collection of clusters.


        **Example request**:

        .. sourcecode:: http

          GET /api/clusters/ HTTP/1.1
          Accept: application/json

        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json

        .. code-block:: json

            {
                "status_code": 200,
                "response_time": 1648,
                "message": null,
                "data": [
                    {
                        "cluster_name": "",
                        "cluster_ip": "",
                        "cluster_port": "9200",
                        "cluster_scheme": "http",
                        "cluster_connected": true,
                        "cluster_host": "http://10.0.0.0:9200",
                        "cluster_version": "2.3.5",
                        "cluster_health": {  }
                    }
                ]
            }

        **Response Structure**

          - *(dict) --*

            - **cluster_name** *(string) --* cluster name
            - **cluster_ip** *(string) --* IP or host
            - **cluster_port** *(string) --*
            - **cluster_scheme** *(string) --*
            - **cluster_connected** *(boolean) --* Whether there was a successful connection.
            - **cluster_host** *(string) --* The complete connection url
            - **cluster_version** *(string) --* Elasticsearch version

        :resheader Content-Type: application/json
        :status 200: OK
        :status 500: server error
        """
        response = ClusterService().get_clusters()

        schema = ClusterDTO(many=True)
        result = schema.dump(response)
        return APIResponse(result.data, HTTP_Status.OK, None)


class ClusterHealth(Resource):
    """
    Wrapper around the Cluster health API https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-health.html
    """

    @request_wrapper
    def get(self, cluster_name):
        """
        Returns cluster health for one cluster


        **Example request**:

        .. sourcecode:: http

          GET /api/clusters/<cluster_name>/_health HTTP/1.1

        :type cluster_name: string
        :param cluster_name: Name of cluster

        **Example response**:

        .. sourcecode:: http

          HTTP/1.1 200 OK
          Vary: Accept
          Content-Type: application/json

        .. code-block:: json

            {
                "status_code": 200,
                "data": [
                    {
                        "active_primary_shards": 10,
                        "relocating_shards": 0,
                        "cluster_name": "es_v2",
                        "active_shards": 10,
                        "task_max_waiting_in_queue_millis": 0,
                        "number_of_pending_tasks": 0,
                        "timed_out": false,
                        "number_of_nodes": 1,
                        "unassigned_shards": 10,
                        "number_of_in_flight_fetch": 0,
                        "initializing_shards": 0,
                        "delayed_unassigned_shards": 0,
                        "active_shards_percent_as_number": 50,
                        "status": "yellow",
                        "number_of_data_nodes": 1
                    }
                ],
                "response_time": 38,
                "message": null
            }


        :resheader Content-Type: application/json
        :status 200: OK
        :status 500: server error
        """
        response = ClusterService().get_cluster_health(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


class ClusterState(Resource):

    @request_wrapper
    def get(self, cluster_name):
        """
        Wrapper around https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-state.html
        """
        response = ClusterService().get_cluster_state(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


class ClusterSummary(Resource):
    """
    Brief summary for a given cluster name
    """

    @request_wrapper
    def get(self, cluster_name):
        """
        Given a cluster_name, returns summary information from several ES Cluster APIs.

        :param cluster_name:
        :return:
        """
        response = ClusterService().get_cluster_summary(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


class ClusterStats(Resource):
    @request_wrapper
    def get(self, cluster_name):
        """
        Wrapper around https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster-stats.html
        :param cluster_name:
        :return:
        """
        response = ClusterService().get_cluster_stats(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


class ClusterPendingTasks(Resource):
    @request_wrapper
    def get(self, cluster_name):
        response = ClusterService().get_cluster_pending_tasks(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


class ClusterSettings(Resource):

    @request_wrapper
    def get(self, cluster_name):
        response = ClusterService().get_cluster_settings(cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)

    @request_wrapper
    def put(self, cluster_name):
        json_data = request.get_json(force=True)
        response = ClusterService().put_cluster_settings(json_data, cluster_name)
        return APIResponse(response, HTTP_Status.OK, None)


def dbConnect():
    conn = psycopg2.connect(
            database="postgres", user='postgres', password='password', host='127.0.0.1', port= '5432'
        )
    conn.autocommit = True
    return conn

class PersistentClusterInformation(Resource):

    @request_wrapper
    def get(self):
        conn = dbConnect()
        cursor = conn.cursor()
        cursor.execute('''SELECT * from cluster''')
        clusters = cursor.fetchall()
        conn.close()

        res = []
        
        for row in clusters:
            val = {}
            val['id'] = row[0]
            val['name'] = row[4]
            val['status'] = row[3]
            val['nodes_count'] = row[1]
            val['indices_count'] = row[2]
            val['documents'] = row[5]
            val['size'] = row[6]
            res.append(val)
        rngData = json.dumps(res, sort_keys = True, default = str)
        return APIResponse(rngData, HTTP_Status.OK, None)


class PersistentIndexInformation(Resource):

    @request_wrapper
    def get(self, cluster_id):
        conn = dbConnect()
        cursor = conn.cursor()
        cursor.execute('''SELECT * from index where cluster_id=%s''', (cluster_id,))
        clusters = cursor.fetchall()
        conn.close()
        res = []
        for row in clusters:
            val = {}
            val['id'] = row[0]
            val['name'] = row[2]
            val['docs'] = row[3]
            val['size'] = row[6]
            val['cache_size'] = row[7]
            val['created_at'] = row[8]
            res.append(val)
        rngData = json.dumps(res, sort_keys = True, default = str)
        return APIResponse(rngData, HTTP_Status.OK, None)


class PersistentIndexStatsInformation(Resource):

    @request_wrapper
    def get(self, index_id):
        date = request.args.get('date')
        conn = dbConnect()
        cursor = conn.cursor()
        cursor.execute('''SELECT * from index_stats where index_id=%s and created_at < %s ORDER BY created_at DESC LIMIT 1;''', (index_id,date,))
        clusters = cursor.fetchall()
        conn.close()
        res = []
        for row in clusters:
            val = {}
            val['documents_size'] = row[2]
            val['total_docs'] = row[3]
            val['deleted_docs'] = row[4]
            val['query_total'] = row[5]
            val['query_time_in_ms'] = row[6]
            val['fetch_total'] = row[7]
            val['fetch_time_in_ms'] = row[8]
            val['index_rate'] = row[9]
            val['search_rate'] = row[10]
            val['search_latency'] = row[11]
            res.append(val)
        rngData = json.dumps(res, sort_keys = True, default = str)
        return APIResponse(rngData, HTTP_Status.OK, None)


api.add_resource(ClusterConnection, '/clusters/_connect', '/clusters/<string:cluster_name>/_connect',
                 endpoint='clusters', methods=['POST', 'DELETE'])
api.add_resource(ClusterList, '/clusters', endpoint='clusters_list', methods=['GET'])
api.add_resource(ClusterStats, '/clusters/<string:cluster_name>/_stats', endpoint='clusters_stats', methods=['GET'])
api.add_resource(ClusterHealth, '/clusters/<string:cluster_name>/_health', endpoint='clusters_health', methods=['GET'])
api.add_resource(ClusterSummary, '/clusters/<string:cluster_name>/_summary', endpoint='clusters_summary',
                 methods=['GET'])
api.add_resource(ClusterState, '/clusters/<string:cluster_name>/_state', endpoint='clusters_state', methods=['GET'])
api.add_resource(ClusterPendingTasks, '/clusters/<string:cluster_name>/_pending_tasks',
                 endpoint='clusters_pending_tasks', methods=['GET'])
api.add_resource(ClusterSettings, '/clusters/<string:cluster_name>/_settings', endpoint='clusters_settings',
                 methods=['GET', 'PUT'])

api.add_resource(PersistentClusterInformation, '/persistent/clusters', endpoint='persistent_clusters_list', methods=['GET'])
api.add_resource(PersistentIndexInformation, '/persistent/cluster/<int:cluster_id>/indices', endpoint='persistent_index_list', methods=['GET'])
api.add_resource(PersistentIndexStatsInformation, '/persistent/index/<int:index_id>/stats', endpoint='persistent_index_statss', methods=['GET'])


# http://localhost:5000/api/persistent/clusters
# http://localhost:5000/api/persistent/cluster/1/indices
# http://localhost:5000/api/persistent/index/1/stats?date=2020-12-17