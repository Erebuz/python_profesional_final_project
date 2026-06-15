<template>
  <v-container>
    <v-row>
      <v-col cols="8">
        <div>
          <live-stream-video-component />
        </div>
      </v-col>

      <v-col cols="4">
        <h3>Настройки FPS</h3>

        <v-row class="mt-2">
          <v-col cols="6" class="d-flex align-center">
            <div>
              Максимум FPS: <b>{{ video.fps.max }}</b>
            </div>
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <div>
              Целевой FPS: <b>{{ video.fps.target }}</b>
            </div>
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <div>
              Текущий FPS: <b>{{ video.fps.current }}</b>
            </div>
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <div>
              Пропускает кадров: <b>{{ store.getters.getNN.skip }}</b>
            </div>
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <v-text-field
              v-model.number="target_fps"
              type="number"
              :min="5"
              :max="1000"
              label="Целевой FPS"
              hide-details
              density="compact"
              variant="outlined"
            />
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <v-btn variant="outlined" @click="set_fps">Установить</v-btn>
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <v-text-field
              v-model.number="skip"
              type="number"
              :min="0"
              :max="10"
              l
              label="Пропуск кадров"
              hide-details
              density="compact"
              variant="outlined"
            />
          </v-col>

          <v-col cols="6" class="d-flex align-center">
            <v-btn variant="outlined" @click="set_skip">Установить</v-btn>
          </v-col>
        </v-row>

        <h3 class="mt-8 mb-2">Настройки нейросети</h3>

        <v-row>
          <v-col cols="12" class="d-flex align-center">
            <v-switch
              v-model="enable_nn"
              :label="enable_nn ? 'Нейросеть включена' : 'Нейросеть отключена'"
              hide-details
            />
          </v-col>
        </v-row>

        <template v-if="enable_nn">
          <h4 class="my-4">Различаемые объекты</h4>

          <v-row>
            <div
              v-for="class_name in Object.keys(store.getters.getNN.classes)"
              :key="class_name"
              style="width: 33%"
            >
              <v-checkbox
                v-model="store.getters.getNN.classes[class_name]"
                :label="class_name[0].toUpperCase() + class_name.slice(1)"
                density="compact"
                @change="set_classes"
              />
            </div>
          </v-row>

          <v-row>
            <v-btn block @click="router.push({ name: 'chart' })"
              >График активности</v-btn
            >
          </v-row>
        </template>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts" setup>
import LiveStreamVideoComponent from '@/components/liveStreamVideoComponent.vue'
import store from '@/store'
import { computed, onMounted, onUnmounted, ref } from 'vue'
import router from '@/router'

store.dispatch('api_get_enable_nn')

let timeout

const target_fps = ref(store.getters.getVideo.fps.current)

const video = computed(() => store.getters.getVideo)

const skip = ref(store.getters.getNN.skip)

const enable_nn = computed({
  get() {
    return store.getters.getNN.enable
  },
  set(val: boolean) {
    store.state.nn.enable = val
    store.dispatch('api_set_enable_nn', val)
  },
})

function get_fps() {
  return store.dispatch('api_get_fps')
}

function set_fps() {
  return store.dispatch('api_set_fps', target_fps.value)
}

function get_skip() {
  return store.dispatch('api_get_skip')
}
function set_skip() {
  return store.dispatch('api_set_skip', skip.value)
}

function set_classes() {
  console.log(store.getters.getNN.classes)
  store.dispatch('api_set_classes', store.getters.getNN.classes)
}

onMounted(() => {
  get_fps().then(() => {
    target_fps.value = store.getters.getVideo.fps.target
  })
  get_skip().then(() => {
    skip.value = store.getters.getNN.skip
  })
})

onUnmounted(() => {
  clearInterval(timeout)
})
</script>
