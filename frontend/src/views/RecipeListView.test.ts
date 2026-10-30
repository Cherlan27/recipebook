import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import RecipeListView from './RecipeListView.vue'
import { routes } from '../router'

function stubFetch(response: Partial<Response> | Error) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      response instanceof Error ? Promise.reject(response) : Promise.resolve(response as Response),
    ),
  )
}

function stubRecipes(recipes: unknown[]) {
  stubFetch({ ok: true, status: 200, json: () => Promise.resolve(recipes) })
}

async function mountOverview() {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push('/')
  await router.isReady()
  const wrapper = mount(RecipeListView, { global: { plugins: [router] } })
  await flushPromises()
  return { wrapper, router }
}

const recipe = (id: number, nr: number, name: string, rest: object = {}) => ({
  id,
  nr,
  name,
  effort: null,
  time_minutes: null,
  kid_friendly: null,
  tags: [],
  ...rest,
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RecipeListView', () => {
  it('shows the recipes in the returned order with nr and name', async () => {
    stubRecipes([recipe(1, 3, 'Soup'), recipe(2, 7, 'Pasta'), recipe(3, 12, 'Curry')])

    const { wrapper } = await mountOverview()

    const entries = wrapper.findAll('li')
    expect(entries.map((entry) => entry.text())).toEqual([
      expect.stringMatching(/3.*Soup/),
      expect.stringMatching(/7.*Pasta/),
      expect.stringMatching(/12.*Curry/),
    ])
  })

  it('shows effort, time, kid-friendliness and tags of a recipe that has them', async () => {
    stubRecipes([
      recipe(1, 3, 'Soup', {
        effort: 2,
        time_minutes: 25,
        kid_friendly: 'with_adjustments',
        tags: ['Pasta', 'Quick'],
      }),
    ])

    const { wrapper } = await mountOverview()

    const text = wrapper.find('li').text()
    expect(text).toContain('Effort')
    expect(text).toContain('25 min')
    expect(text).toContain('with adjustments')
    expect(text).toContain('Pasta')
    expect(text).toContain('Quick')
  })

  it('hides empty fields and their labels', async () => {
    stubRecipes([recipe(1, 3, 'Soup')])

    const { wrapper } = await mountOverview()

    const text = wrapper.find('li').text()
    expect(text).not.toContain('Effort')
    expect(text).not.toContain('min')
    expect(text).not.toContain('Kid-friendly')
  })

  it('links each recipe to its detail view by id', async () => {
    stubRecipes([recipe(5, 12, 'Pasta')])

    const { wrapper, router } = await mountOverview()
    await wrapper.find('a').trigger('click')
    await flushPromises()

    expect(router.currentRoute.value.fullPath).toBe('/recipes/5')
  })

  it('shows a hint and no entries when there are no recipes', async () => {
    stubRecipes([])

    const { wrapper } = await mountOverview()

    expect(wrapper.text()).toContain('No recipes yet')
    expect(wrapper.findAll('li')).toHaveLength(0)
  })

  it('shows a backend-unreachable hint on a network error, not the empty-database hint', async () => {
    stubFetch(new TypeError('Failed to fetch'))

    const { wrapper } = await mountOverview()

    expect(wrapper.text()).toContain('backend is not reachable')
    expect(wrapper.text()).not.toContain('No recipes yet')
  })
})
