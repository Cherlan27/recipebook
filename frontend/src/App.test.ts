import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import App from './App.vue'

describe('App', () => {
  it('mounts and renders content', () => {
    const wrapper = mount(App)

    expect(wrapper.html()).not.toBe('')
  })
})
