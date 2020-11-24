import angular from 'angular';
import nodeNetworkStatsTable from './node-network-stats-table.component';

export default angular.module('eshq.nodeNetworkStatsTable', [])
  .component('eshqNodeNetworkStatsTable', nodeNetworkStatsTable)
  .name;
