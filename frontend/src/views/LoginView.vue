<template>
  <v-container class="h-100">
    <v-row class="justify-center align-center h-100">
      <v-col cols="3">
        <v-form validate-on="submit" @submit.prevent="log_in">
          <v-text-field
            v-model="username"
            placeholder="Введите логин"
            label="Логин"
            :rules="[requirement, max60]"
            density="compact"
            variant="outlined"
          />
          <v-text-field
            v-model="password"
            placeholder="Введите пароль"
            label="Пароль"
            :rules="[requirement, max60]"
            density="compact"
            variant="outlined"
            class="my-2"
            :type="show_password ? 'text' : 'password'"
            :append-inner-icon="show_password ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="show_password = !show_password"
          />
          <v-btn type="submit" block variant="outlined">Вход</v-btn>
        </v-form>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import store from '@/store'
import { max60, requirement } from '@/utils/rules'

const username = ref('')
const password = ref('')
const show_password = ref(false)

function log_in() {
  store.getters.getAuth.login({
    data: { username: username.value, password: password.value },
  })
}
</script>

<style></style>
