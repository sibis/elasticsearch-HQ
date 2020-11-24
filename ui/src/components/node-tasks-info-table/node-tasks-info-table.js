import angular from 'angular';
import nodeTasksInfoTable from './node-tasks-info-table.component';

export default angular.module('eshq.nodeTasksInfoTable', [])
  .component('eshqNodeTasksInfoTable', nodeTasksInfoTable)
  .name;
