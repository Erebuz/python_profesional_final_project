import http from '@/plugins/http-common'
import { AxiosInstance, AxiosRequestConfig } from 'axios'
abstract class AbstractApiService {
  protected path = ''
  protected http: AxiosInstance

  protected constructor(path: string) {
    this.path = path
    this.http = http
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  get(id: string, params: any = null) {
    const uri = id ? this.path + '/' + id : this.path
    return http.get(uri, params)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  create(data: any) {
    return http.post(this.path, data)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  set(id: string, data?: any, config?: AxiosRequestConfig) {
    const uri = id ? this.path + '/' + id : this.path
    return http.post(uri, data, config)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  update(id: string, data: any = null, config?: AxiosRequestConfig) {
    const uri = id ? this.path + '/' + id : this.path
    return http.put(uri, data, config)
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  delete(id: string, params?: AxiosRequestConfig) {
    const uri = id ? this.path + '/' + id : this.path
    return http.delete(uri, params)
  }

  deleteAll() {
    return http.delete(this.path)
  }
}

export default AbstractApiService
