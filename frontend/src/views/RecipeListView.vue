<script setup lang="ts">
import { ref } from 'vue'
import { BackendUnavailableError, fetchRecipes, type RecipeListItem } from '../api/recipes'
import { kidFriendlyLabel } from '../kidFriendlyLabel'

const recipes = ref<RecipeListItem[] | null>(null)
const backendUnavailable = ref(false)

fetchRecipes()
  .then((list) => {
    recipes.value = list
  })
  .catch((error) => {
    if (!(error instanceof BackendUnavailableError)) throw error
    backendUnavailable.value = true
  })
</script>

<template>
  <main>
    <h1>Recipes</h1>
    <p v-if="backendUnavailable">The backend is not reachable. Try again later.</p>
    <p v-else-if="recipes?.length === 0">No recipes yet.</p>
    <ul v-else-if="recipes">
      <li v-for="recipe in recipes" :key="recipe.id">
        <RouterLink :to="`/recipes/${recipe.id}`">{{ recipe.nr }} {{ recipe.name }}</RouterLink>
        <span v-if="recipe.effort !== null"> Effort {{ recipe.effort }}/3</span>
        <span v-if="recipe.time_minutes !== null"> {{ recipe.time_minutes }} min</span>
        <span v-if="recipe.kid_friendly !== null">
          Kid-friendly: {{ kidFriendlyLabel(recipe.kid_friendly) }}
        </span>
        <span v-for="tag in recipe.tags" :key="tag"> {{ tag }}</span>
      </li>
    </ul>
  </main>
</template>
