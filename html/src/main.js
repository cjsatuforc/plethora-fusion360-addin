import Vue from 'vue'
import App from './App.vue'
import router from './router'
import Spinner from 'vue-simple-spinner'
import Dropdown from 'bp-vuejs-dropdown'

Vue.prototype.$eventBus = new Vue()

Vue.config.productionTip = false

Vue.component('vue-simple-spinner', Spinner)
Vue.component('dropdown', Dropdown)

var vue = new Vue({
  el: '#app',
  router,
  render: h => h(App),
  methods: {
    emitFusion360Message(action, data) {
      var json = JSON.parse(data);
      this.$eventBus.$emit(action, json);
    }
  }
})

window.fusionJavaScriptHandler = {
  handle: function(action, data) {
      vue.emitFusion360Message(action, data);

      // Build up JSON return string.
      var result = {};
      result.status = 'OK';
      var response = JSON.stringify(result);
      return response;
  }
};
