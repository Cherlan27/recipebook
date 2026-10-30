import { describe, it, expect, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import App from './App.vue'
import { routes } from './router'

vi.mock('./api/recipes', async (importOriginal) => ({
  ...(await importOriginal<typeof import('./api/recipes')>()),
  fetchRecipes: () => Promise.resolve([]),
}))

describe('App', () => {
  it('renders the view of the current route', async () => {
    const router = createRouter({ history: createMemoryHistory(), routes })
    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, { global: { plugins: [router] } })
    await flushPromises()

    expect(wrapper.html()).not.toBe('')
    expect(router.currentRoute.value.name).toBe('recipe-list')
  })
})
