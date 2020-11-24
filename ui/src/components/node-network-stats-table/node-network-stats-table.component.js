import template from './node-network-stats-table.template.html';
import controller from './node-network-stats-table.controller';

const nodeNetworkStatsTableComponent = {
  bindings: {
    info: '<'
  },
  template,
  controller,
  controllerAs: 'nodeNetworkStatsTableCtrl'
};

export default nodeNetworkStatsTableComponent;
