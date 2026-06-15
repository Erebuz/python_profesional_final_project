import AbstractApiService from '@/service/AbstractApiService'

export default class VideoService extends AbstractApiService {
  constructor() {
    super('/api/video')
  }

  get_fps() {
    return this.get('fps')
  }

  set_fps(val: number) {
    return this.update('fps', { target: val })
  }
}
