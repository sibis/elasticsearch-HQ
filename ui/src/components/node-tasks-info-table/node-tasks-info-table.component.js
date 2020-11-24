import template from './node-tasks-info-table.template.html';
import controller from './node-tasks-info-table.controller';

const nodeTasksInfoTableComponent = {
  bindings: {
    info: '<'
  },
  template,
  controller,
  controllerAs: 'nodeTasksInfoTableCtrl'
};

export default nodeTasksInfoTableComponent;
