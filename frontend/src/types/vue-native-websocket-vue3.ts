import VueNativeSock from 'vue-native-websocket-vue3'

declare module '@vue/runtime-core' {
  export interface ComponentCustomProperties {
    $socket: any
    $connect: (url?: string) => void
    $disconnect: () => void
  }
}
