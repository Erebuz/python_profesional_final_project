import AbstractApiService from '@/service/AbstractApiService'

export default class UserService extends AbstractApiService {
  constructor() {
    super('/api/users')
  }

  update_me(payload: { password?: string; username: string }) {
    return this.update('', payload)
  }
}
