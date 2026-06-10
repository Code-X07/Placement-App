import store  from './store.js'
import router from './router.js'
import NavBar from './components/shared/NavBar.js'

new Vue({
  el: '#app',
  store,
  router,
  components: { NavBar },
  template: `
    <div>
      <NavBar v-if="$store.getters.isLoggedIn" />
      <div class="container mt-4">
        <router-view />
      </div>
    </div>
  `,
})
