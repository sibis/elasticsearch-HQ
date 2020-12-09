import template from './index-metric-search.template.html';
import controller from './index-metric-search.controller';

const indexMetricSearchComponent = {
  bindings: {
    stats: '<',
    summary: '<',
    index_rate: '<',
    search_rate: '<',
    search_latency: '<'
  },
  template,
  controller,
  controllerAs: 'indexMetricSearchCtrl'
};

export default indexMetricSearchComponent;
