import { afterEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createMemoryHistory, createRouter } from 'vue-router'
import RecipeDetailView from './RecipeDetailView.vue'
import { routes } from '../router'

function stubFetch(response: Partial<Response> | Error) {
  vi.stubGlobal(
    'fetch',
    vi.fn(() =>
      response instanceof Error ? Promise.reject(response) : Promise.resolve(response as Response),
    ),
  )
}

function stubRecipe(recipe: unknown) {
  stubFetch({ ok: true, status: 200, json: () => Promise.resolve(recipe) })
}

async function mountDetail(id = 5) {
  const router = createRouter({ history: createMemoryHistory(), routes })
  await router.push(`/recipes/${id}`)
  await router.isReady()
  const wrapper = mount(RecipeDetailView, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

const minimalRecipe = {
  id: 5,
  nr: 12,
  name: 'Bread',
  effort: null,
  time_minutes: null,
  servings: null,
  kid_friendly: null,
  ingredients: null,
  steps: null,
  tags: [],
  created_at: '2026-10-01T10:00:00',
  updated_at: '2026-10-01T10:00:00',
}

const fullRecipe = {
  ...minimalRecipe,
  name: 'Pasta',
  effort: 2,
  time_minutes: 25,
  servings: 4,
  kid_friendly: 'yes',
  ingredients: '200 g Pasta\n1 Onion',
  steps: 'Boil water\nCook pasta',
  tags: ['Pasta', 'Quick'],
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('RecipeDetailView', () => {
  it('requests the recipe of the route id', async () => {
    stubRecipe(fullRecipe)

    await mountDetail(5)

    expect(fetch).toHaveBeenCalledWith('/api/recipes/5')
  })

  it('shows all fields of a recipe with all fields filled', async () => {
    stubRecipe(fullRecipe)

    const wrapper = await mountDetail()

    const text = wrapper.text()
    expect(text).toContain('12')
    expect(text).toContain('Pasta')
    expect(text).toContain('Effort')
    expect(text).toContain('25 min')
    expect(text).toContain('4 servings')
    expect(text).toContain('Kid-friendly: yes')
    expect(text).toContain('Quick')
    expect(text).toContain('200 g Pasta')
    expect(text).toContain('Cook pasta')
  })

  it('shows only nr and name, and no labels, for a recipe with only the required fields', async () => {
    stubRecipe(minimalRecipe)

    const wrapper = await mountDetail()

    const text = wrapper.text()
    expect(text).toContain('12')
    expect(text).toContain('Bread')
    expect(text).not.toContain('Effort')
    expect(text).not.toContain('min')
    expect(text).not.toContain('servings')
    expect(text).not.toContain('Kid-friendly')
    expect(text).not.toContain('Tags')
    expect(text).not.toContain('Ingredients')
    expect(text).not.toContain('Steps')
  })

  it('shows ingredients as a bulleted list and steps as a numbered list, one entry per non-empty line', async () => {
    stubRecipe({
      ...minimalRecipe,
      ingredients: '200 g Pasta\n\n1 Onion\n',
      steps: 'Boil water\r\n  \r\nCook pasta',
    })

    const wrapper = await mountDetail()

    const ingredients = wrapper.findAll('ul > li').map((item) => item.text())
    const steps = wrapper.findAll('ol > li').map((item) => item.text())
    expect(ingredients).toEqual(['200 g Pasta', '1 Onion'])
    expect(steps).toEqual(['Boil water', 'Cook pasta'])
  })

  it('shows a not-found hint with a link to the overview for an unknown recipe', async () => {
    stubFetch({ ok: false, status: 404 })

    const wrapper = await mountDetail(999)

    expect(wrapper.text()).toContain('Recipe not found')
    expect(wrapper.find('a').attributes('href')).toBe('/')
  })

  it('shows a backend-unreachable hint when the backend answers with 500', async () => {
    stubFetch({ ok: false, status: 500 })

    const wrapper = await mountDetail()

    expect(wrapper.text()).toContain('backend is not reachable')
    expect(wrapper.text()).not.toContain('Recipe not found')
  })
})
