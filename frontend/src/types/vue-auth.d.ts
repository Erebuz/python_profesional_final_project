import auth from '@/plugins/auth'

declare module '@vue/runtime-core' {
  export interface ComponentCustomProperties {
    $auth: typeof auth
  }
}
