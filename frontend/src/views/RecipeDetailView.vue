<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import {
  BackendUnavailableError,
  NotFoundError,
  fetchRecipe,
  type RecipeDetail,
} from '../api/recipes'
import { kidFriendlyLabel } from '../kidFriendlyLabel'
import { toLines } from '../toLines'

const recipe = ref<RecipeDetail | null>(null)
const ingredients = computed(() => toLines(recipe.value?.ingredients ?? null))
const steps = computed(() => toLines(recipe.value?.steps ?? null))
const notFound = ref(false)
const backendUnavailable = ref(false)

fetchRecipe(Number(useRoute().params.id))
  .then((loaded) => {
    recipe.value = loaded
  })
  .catch((error) => {
    if (error instanceof NotFoundError) notFound.value = true
    else if (error instanceof BackendUnavailableError) backendUnavailable.value = true
    else throw error
  })
</script>

<template>
  <main>
    <p v-if="backendUnavailable">The backend is not reachable. Try again later.</p>
    <template v-else-if="notFound">
      <p>Recipe not found.</p>
      <RouterLink to="/">Back to all recipes</RouterLink>
    </template>
    <template v-else-if="recipe">
      <h1>{{ recipe.nr }} {{ recipe.name }}</h1>
      <p v-if="recipe.effort !== null">Effort {{ recipe.effort }}/3</p>
      <p v-if="recipe.time_minutes !== null">{{ recipe.time_minutes }} min</p>
      <p v-if="recipe.servings !== null">{{ recipe.servings }} servings</p>
      <p v-if="recipe.kid_friendly !== null">
        Kid-friendly: {{ kidFriendlyLabel(recipe.kid_friendly) }}
      </p>
      <p v-if="recipe.tags.length > 0">Tags: {{ recipe.tags.join(', ') }}</p>
      <section v-if="ingredients.length > 0">
        <h2>Ingredients</h2>
        <ul>
          <li v-for="(line, index) in ingredients" :key="index">{{ line }}</li>
        </ul>
      </section>
      <section v-if="steps.length > 0">
        <h2>Steps</h2>
        <ol>
          <li v-for="(line, index) in steps" :key="index">{{ line }}</li>
        </ol>
      </section>
    </template>
  </main>
</template>
