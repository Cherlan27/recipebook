import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter, createWebHashHistory } from 'vue-router'
import { router, routes } from './router'

describe('routes', () => {
  it('resolves / to the overview', () => {
    const memoryRouter = createRouter({ history: createMemoryHistory(), routes })

    expect(memoryRouter.resolve('/').name).toBe('recipe-list')
  })

  it('resolves /recipes/:id to the detail view with the id as parameter', () => {
    const memoryRouter = createRouter({ history: createMemoryHistory(), routes })
    const resolved = memoryRouter.resolve('/recipes/5')

    expect(resolved.name).toBe('recipe-detail')
    expect(resolved.params.id).toBe('5')
  })

  it('puts the route in the URL hash', () => {
    const hashRouter = createRouter({ history: createWebHashHistory(), routes })

    expect(hashRouter.resolve('/recipes/5').href).toBe('#/recipes/5')
    expect(router.options.history.base).toBe('/#')
  })
})
