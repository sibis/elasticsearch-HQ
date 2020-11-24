import template from './index-metric-merge.template.html';
import controller from './index-metric-merge.controller';

const indexMetricMergeComponent = {
  bindings: {
    stats: '<',
    summary: '<'
  },
  template,
  controller,
  controllerAs: 'indexMetricMergeCtrl'
};

export default indexMetricMergeComponent;
