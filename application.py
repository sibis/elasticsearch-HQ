# import argparse
import logging.config
import optparse
import os
import threading

from elastichq import create_app
from elastichq.globals import socketio
from elastichq.utils import find_config
from elastichq.service import IndicesService, ClusterService
from elastichq.model import ClusterDTO

from stats_handler import persist_elastic_search

import schedule
import time
import redis

default_host = '0.0.0.0'
default_port = 5000
default_debug = False
default_enable_ssl = False
default_ca_certs = None
default_verify_certs = True
default_client_key = None
default_client_cert = None
default_url = 'https://admin:admin@localhost:9200'
is_gunicorn = "gunicorn" in os.environ.get("SERVER_SOFTWARE", "")
default_redisurl = 'redis://redis:6379'

application = create_app() 

# set default url, override with env for docker
application.config['DEFAULT_URL'] = os.environ.get('HQ_DEFAULT_URL', default_url)
application.config['ENABLE_SSL'] = os.environ.get('HQ_ENABLE_SSL', default_enable_ssl)
application.config['CA_CERTS'] = os.environ.get('HQ_CA_CERTS', default_ca_certs)
application.config['VERIFY_CERTS'] = os.environ.get('HQ_VERIFY_CERTS', default_verify_certs)
application.config['DEBUG'] = os.environ.get('HQ_DEBUG', default_debug)
application.config['CLIENT_KEY'] = os.environ.get('CLIENT_KEY', default_client_key)
application.config['CLIENT_CERT'] = os.environ.get('CLIENT_CERT', default_client_cert)

if os.environ.get('HQ_DEBUG') == 'True':
    config = find_config('logger_debug.json')
    logging.config.dictConfig(config)

def job():
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
   
    clusters = ClusterService().get_clusters()
    schema = ClusterDTO(many=True)
    result = schema.dump(clusters)
    for cluster in result.data:
        res = IndicesService().get_indices_stats(cluster['cluster_name'], None)
        for name, val in res['indices'].items():
            cons_name = 'prev:'+cluster['cluster_name']+':'+name
            ongoing_name = cluster['cluster_name']+':'+name

            prev_rate = str(r.get(cons_name))
            prev_rate = prev_rate.split(":")
            try:
                prev_search_latency = (float(val['total']['search']['query_total']/val['total']['search']['query_time_in_millis']) - float(prev_rate[2])) / 60
            except ZeroDivisionError:
                prev_search_latency = 0
            # format - index_total : search_total : search_time/search_count
            result = str(val['total']['indexing']['index_total'])+':'+str(val['total']['search']['query_total'])+':'+str(prev_search_latency)
            if r.get(cons_name) is None:
                r.set(cons_name, result)
            else:
                prev_rate = str(r.get(cons_name))
                r.set(cons_name, result)
                
                prev_rate = prev_rate.split(":")
                current_index_rate = (float(val['total']['indexing']['index_total']) - float(prev_rate[0])) / 60
                current_search_total = (float(val['total']['search']['query_total']) - float(prev_rate[1])) / 60
                try:
                    current_search_latency = ((float(val['total']['search']['query_total'])/float(val['total']['search']['query_time_in_millis'])) - float(prev_rate[2])) / 60
                except ZeroDivisionError:
                    current_search_latency = 0
                # derivative of the total search time by the derivative of the total search count - search latency
                ongoing_result = str(current_index_rate)+':'+str(current_search_total)+':'+str(current_search_latency)
                r.set(ongoing_name, ongoing_result)
                


def start_scheduler():
    schedule.every(10).minutes.do(job)
    schedule.every(15).minute.do(persist_elastic_search)
    while True:
        schedule.run_pending()
        time.sleep(1)
    
if __name__ == '__main__':
    #start_scheduler()
    download_thread = threading.Thread(target=start_scheduler, name="Downloader", args="")
    download_thread.start()

    # Set up the command-line options
    parser = optparse.OptionParser()
    parser.add_option("-H", "--host",
                      help="Hostname of the Flask app " + \
                           "[default %s]" % default_host,
                      default=default_host)
    parser.add_option("-P", "--port",
                      help="Port for the Flask app " + \
                           "[default %s]" % default_port,
                      default=default_port)
    parser.add_option("-d", "--debug",
                      action="store_true", dest="debug", default=default_debug,
                      help=optparse.SUPPRESS_HELP)
    parser.add_option("-u", "--url", default=default_url)
    parser.add_option("-s", "--enable-ssl",
                      action="store_true", default=default_enable_ssl)
    parser.add_option("-c", "--ca-certs", default=default_ca_certs,
                      help='Required when --use-ssl is set. ' + \
                           'Path to CA file or directory [default %s]' % default_ca_certs)
    parser.add_option("-v", "--verify_certs", default=default_verify_certs,
                      help='Set to False when using self-signed certs.')
    parser.add_option("-x", "--client_cert", default=default_client_cert,
                      help='Set to path of the client cert file.')
    parser.add_option("-X", "--client_key", default=default_client_key,
                      help='Set to path of the client key file.')

    options, _ = parser.parse_args()

    application.config['DEFAULT_URL'] = os.environ.get('HQ_DEFAULT_URL', options.url)
    application.config['ENABLE_SSL'] = os.environ.get('HQ_ENABLE_SSL', options.enable_ssl)
    application.config['CA_CERTS'] = os.environ.get('HQ_CA_CERTS', options.ca_certs)
    application.config['VERIFY_CERTS'] = os.environ.get('HQ_VERIFY_CERTS', options.verify_certs)
    application.config['CLIENT_KEY'] = os.environ.get('CLIENT_KEY', options.client_key)
    application.config['CLIENT_CERT'] = os.environ.get('CLIENT_CERT', options.client_cert)

    if is_gunicorn:
        if options.debug:
            config = find_config('logger_debug.json')
            logging.config.dictConfig(config)

        # we set reloader False so gunicorn doesn't call two instances of all the Flask init functions.
        socketio.run(application, host=options.host, port=options.port, debug=options.debug, use_reloader=False)
    else:
        if options.debug:
            config = find_config('logger_debug.json')
            logging.config.dictConfig(config)
        socketio.run(application, host=options.host, port=options.port, debug=options.debug)
