import { createStore } from 'vuex'
import { ComponentInternalInstance } from 'vue'
import VideoService from '@/service/videoService'
import NnService from '@/service/nnService'
import UserService from '@/service/UserService'

const videoService = new VideoService()
const nnService = new NnService()
const userService = new UserService()

type fpsType = {
  current: number
  max: number
  target: number
}
export default createStore<{
  currentInstance: ComponentInternalInstance | null
  video: {
    fps: fpsType
  }
  nn: {
    enable: boolean
    classes: Record<string, string>
    skip: number
    activity_log: number[]
    activity_log_data: Date
  }
  active_classes: Record<string, number>
}>({
  state: {
    currentInstance: null,
    video: {
      fps: {
        current: 0,
        max: 0,
        target: 0,
      },
    },
    nn: {
      enable: false,
      skip: 0,
      classes: {},
      activity_log: [],
      activity_log_data: new Date(),
    },
    active_classes: {},
  },
  getters: {
    getAuth: (state) => state.currentInstance!.proxy!.$auth,
    getVideo: (state) => state.video,
    getNN: (state) => state.nn,
    active_classes: (state) => state.active_classes,
  },
  mutations: {
    SOCKET_ONOPEN: () => {
      return
    },
    SOCKET_ONCLOSE: () => {
      return
    },
    SOCKET_ONERROR: () => {
      return
    },
    SOCKET_ONMESSAGE: () => {
      return
    },
    SOCKET_RECONNECT: () => {
      return
    },
    SOCKET_RECONNECT_ERROR: () => {
      return
    },
  },
  actions: {
    set_instance(state, payload: ComponentInternalInstance) {
      this.state.currentInstance = payload
    },
    api_get_fps() {
      return videoService.get_fps().then((res) => {
        this.state.video.fps = res.data
      })
    },
    api_set_fps(state, fps: number) {
      return videoService.set_fps(fps)
    },
    api_get_skip() {
      return nnService.get_frame_skip().then((res) => {
        this.state.nn.skip = res.data
      })
    },
    api_set_skip(state, val: number) {
      return nnService.set_frame_skip(val).then(() => {
        this.dispatch('api_get_skip')
      })
    },
    api_get_enable_nn() {
      return nnService.get_nn_enable().then((res) => {
        if (!res.data) return
        this.state.nn.enable = res.data.show_osd
        this.state.nn.classes = res.data.classes
      })
    },
    api_set_enable_nn(state, val: boolean) {
      return nnService.set_nn_enable(val)
    },
    api_set_classes(state, val: Record<string, string>) {
      return nnService.set_nn_classes(val)
    },
    api_get_activity_log() {
      return nnService.get_activity_log().then((res) => {
        this.state.nn.activity_log = res.data
        this.state.nn.activity_log_data = new Date(
          new Date().getTime() - res.data.length * 0.2 * 1000
        )
      })
    },
    api_update_me(state, payload: { password?: string; username: string }) {
      return userService.update_me(payload)
    },
    update(
      state,
      wsEvent: { data: { fps: fpsType; classes: Record<string, number> } }
    ) {
      this.state.video.fps = wsEvent.data.fps
      this.state.active_classes = wsEvent.data.classes

      let result = 0

      for (const key in wsEvent.data.classes) {
        result += wsEvent.data.classes[key]
      }

      this.state.nn.activity_log.push(result)
      if (this.state.nn.activity_log.length > 1500) {
        this.state.nn.activity_log.shift()
        this.state.nn.activity_log_data = new Date(
          new Date().getTime() - 1500 * 0.2 * 1000
        )
      }
    },
  },
})
