<template>
  <component :is="layout">
    <router-view />
  </component>
</template>

<script lang="ts" setup>
import { computed, getCurrentInstance } from 'vue'
import DefaultLayout from '@/layouts/DefaultLayout.vue'
import LoginLayout from '@/layouts/LoginLayout.vue'
import router from '@/router'
import store from '@/store'

const layout = computed(() => {
  return router.currentRoute.value.meta.layout === 'default'
    ? DefaultLayout
    : LoginLayout
})

store.dispatch('set_instance', getCurrentInstance())
</script>

<style>
body {
  height: 100vh;
}

#app {
  height: 100%;
}
</style>
