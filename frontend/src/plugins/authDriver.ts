import { RequestOptions, VueAuthCreateOptions } from '@websanova/vue-auth'
import { AxiosResponse } from 'axios'

const request = function (
  this: VueAuthCreateOptions,
  req: RequestOptions,
  token: string
) {
  if (req.url?.indexOf('refresh') !== -1) {
    this.drivers.http.setHeaders.call(this, req, {
      Authorization: 'Bearer ' + token,
    })
    const ref_token = localStorage.getItem('refresh_token')
    req.data = { refresh_token: ref_token }
  } else {
    this.drivers.http.setHeaders.call(this, req, {
      Authorization: 'Bearer ' + token,
    })
  }
}

const response = function (res: AxiosResponse) {
  if (res.data?.refresh_token) {
    localStorage.setItem('refresh_token', res.data.refresh_token)
  }
  return res.data?.access_token
}

export default {
  request,
  response,
}
