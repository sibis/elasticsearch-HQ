import template from './index-metric-segment.template.html';
import controller from './index-metric-segment.controller';

const indexMetricSegmentComponent = {
  bindings: {
    stats: '<',
    summary: '<'
  },
  template,
  controller,
  controllerAs: 'indexMetricSegmentCtrl'
};

export default indexMetricSegmentComponent;
