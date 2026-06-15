<template>
  <v-container>
    <charts-component />

    <v-btn @click="router.push({ name: 'general' })">Назад</v-btn>
  </v-container>
</template>

<script lang="ts" setup>
import ChartsComponent from '@/components/сhartsComponent.vue'
import router from '@/router'
import store from '@/store'

store.dispatch('api_get_activity_log')
</script>

<style scoped></style>
