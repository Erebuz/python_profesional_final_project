<template>
  <v-container class="mt-8">
    <v-form @submit.prevent="save">
      <v-row class="flex-column">
        <v-col cols="4">
          <v-text-field
            v-model="username"
            label="Имя пользователя"
            density="compact"
            variant="outlined"
            :rules="[requirement, max60]"
          />
        </v-col>

        <v-col cols="4">
          <v-text-field
            v-model.number="password"
            label="Новый пароль"
            density="compact"
            variant="outlined"
            :rules="[max60, confirmRule]"
            :type="show_password ? 'text' : 'password'"
            :append-inner-icon="show_password ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="show_password = !show_password"
          />
        </v-col>

        <v-col cols="4">
          <v-text-field
            v-model.number="confirm"
            label="Подтверждение пароля"
            density="compact"
            variant="outlined"
            :rules="[max60, confirmRule]"
            :type="show_password ? 'text' : 'password'"
            :append-inner-icon="show_password ? 'mdi-eye' : 'mdi-eye-off'"
            @click:append-inner="show_password = !show_password"
          />
        </v-col>

        <v-col cols="4">
          <v-btn variant="outlined" type="submit">Сохранить</v-btn>
        </v-col>
      </v-row>
    </v-form>

    <v-row>
      <v-col cols="4">
        <router-link :to="{ name: 'general' }" class="btn">
          <v-btn variant="outlined">Назад</v-btn>
        </router-link>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import store from '@/store'
import { max60, requirement } from '@/utils/rules'

const username = ref(store.getters.getAuth.user().username)

const password = ref('')
const confirm = ref('')
const show_password = ref(false)

function save() {
  if (password.value !== confirm.value) return

  if (
    password.value === '' &&
    username.value === store.getters.getAuth.user().username
  )
    return

  store.dispatch('api_update_me', {
    password: password.value,
    username: username.value,
  })
}

const confirmRule = () =>
  password.value === confirm.value || 'Пароли не совпадают'
</script>

<style scoped>
.btn {
  text-decoration: none;
  color: black;
}
</style>
