import { createRouter, createWebHashHistory, type RouteRecordRaw } from 'vue-router'
import RecipeDetailView from './views/RecipeDetailView.vue'
import RecipeListView from './views/RecipeListView.vue'

// Hash mode: the server only ever sees "/", so deep links work with the static mount (ADR-9).
export const routes: RouteRecordRaw[] = [
  { path: '/', name: 'recipe-list', component: RecipeListView },
  { path: '/recipes/:id', name: 'recipe-detail', component: RecipeDetailView },
]

export const router = createRouter({ history: createWebHashHistory(), routes })
