import { afterEach, describe, expect, it, vi } from 'vitest'
import { BackendUnavailableError, NotFoundError, fetchRecipe, fetchRecipes } from './recipes'

function stubFetch(response: Partial<Response> | Error) {
  const fetchMock = vi.fn(() =>
    response instanceof Error ? Promise.reject(response) : Promise.resolve(response as Response),
  )
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('fetchRecipes', () => {
  it('requests the relative list URL and returns the parsed list', async () => {
    const list = [{ id: 1, nr: 3, name: 'Soup' }]
    const fetchMock = stubFetch({ ok: true, status: 200, json: () => Promise.resolve(list) })

    await expect(fetchRecipes()).resolves.toEqual(list)
    expect(fetchMock).toHaveBeenCalledWith('/api/recipes')
  })

  it('throws BackendUnavailableError on a network error', async () => {
    stubFetch(new TypeError('Failed to fetch'))

    await expect(fetchRecipes()).rejects.toBeInstanceOf(BackendUnavailableError)
  })

  it('throws BackendUnavailableError on a 5xx status', async () => {
    stubFetch({ ok: false, status: 503 })

    await expect(fetchRecipes()).rejects.toBeInstanceOf(BackendUnavailableError)
  })
})

describe('fetchRecipe', () => {
  it('requests the relative detail URL and returns the parsed recipe', async () => {
    const recipe = { id: 5, nr: 12, name: 'Pasta' }
    const fetchMock = stubFetch({ ok: true, status: 200, json: () => Promise.resolve(recipe) })

    await expect(fetchRecipe(5)).resolves.toEqual(recipe)
    expect(fetchMock).toHaveBeenCalledWith('/api/recipes/5')
  })

  it('throws NotFoundError on 404', async () => {
    stubFetch({ ok: false, status: 404 })

    await expect(fetchRecipe(999)).rejects.toBeInstanceOf(NotFoundError)
  })

  it('throws BackendUnavailableError on a network error', async () => {
    stubFetch(new TypeError('Failed to fetch'))

    await expect(fetchRecipe(5)).rejects.toBeInstanceOf(BackendUnavailableError)
  })

  it('throws BackendUnavailableError on a 5xx status', async () => {
    stubFetch({ ok: false, status: 500 })

    await expect(fetchRecipe(5)).rejects.toBeInstanceOf(BackendUnavailableError)
  })
  it('throws NotFoundError on 422, which the backend answers for an invalid id', async () => {
    stubFetch({ ok: false, status: 422 })

    await expect(fetchRecipe(5)).rejects.toBeInstanceOf(NotFoundError)
  })

  it('does not report another 4xx status as an unreachable backend', async () => {
    stubFetch({ ok: false, status: 400 })

    const error = await fetchRecipe(5).catch((caught) => caught)

    expect(error).toBeInstanceOf(Error)
    expect(error).not.toBeInstanceOf(BackendUnavailableError)
  })
})
