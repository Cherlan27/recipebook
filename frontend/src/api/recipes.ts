export type KidFriendly = 'yes' | 'with_adjustments' | 'no'

export interface RecipeListItem {
  id: number
  nr: number
  name: string
  effort: number | null
  time_minutes: number | null
  kid_friendly: KidFriendly | null
  tags: string[]
}

export interface RecipeDetail extends RecipeListItem {
  servings: number | null
  ingredients: string | null
  steps: string | null
  created_at: string
  updated_at: string
}

export class NotFoundError extends Error {}

export class BackendUnavailableError extends Error {}

async function getJson<T>(url: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(url)
  } catch {
    throw new BackendUnavailableError('The backend is not reachable')
  }
  if (response.status === 404) throw new NotFoundError(`Not found: ${url}`)
  if (!response.ok) throw new BackendUnavailableError(`The backend answered ${response.status}`)
  return response.json() as Promise<T>
}

export function fetchRecipes(): Promise<RecipeListItem[]> {
  return getJson('/api/recipes')
}

export function fetchRecipe(id: number): Promise<RecipeDetail> {
  return getJson(`/api/recipes/${id}`)
}
