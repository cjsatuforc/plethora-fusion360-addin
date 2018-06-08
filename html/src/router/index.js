import Vue from 'vue'
import Router from 'vue-router'
import LogIn from '@/components/LogIn'
import Analyze from '@/components/Analyze'

Vue.use(Router)

export default new Router({
  routes: [
    {
        path: '/',
        redirect: {
            name: "login"
        }
    },
    {
        path: "/login",
        name: "login",
        component: LogIn
    },
    {
        path: "/analyze",
        name: "analyze",
        component: Analyze
    }
]
})