import { createRouter, createWebHashHistory } from 'vue-router'
import CollectionsPage from '../views/CollectionsPage.vue'
import DocumentsPage from '../views/DocumentsPage.vue'
import ChatPage from '../views/ChatPage.vue'
import ParamsPage from '../views/ParamsPage.vue'

const routes = [
  { path: '/', redirect: '/collections' },
  { path: '/collections', name: 'collections', component: CollectionsPage },
  { path: '/documents', name: 'documents', component: DocumentsPage },
  { path: '/chat', name: 'chat', component: ChatPage },
  { path: '/params', name: 'params', component: ParamsPage },
]

export default createRouter({
  history: createWebHashHistory(),
  routes,
})
