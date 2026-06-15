<template>
  <div class="live-video">
    <video-player
      :options="videoOptions"
      @mounted="set_video"
      @timeupdate="time_watch"
      @click="play"
    />
  </div>
</template>

<script lang="ts" setup>
import { VideoJsPlayer, VideoJsPlayerOptions } from 'video.js'
import { VideoPlayer, VideoPlayerState } from '@videojs-player/vue'
import 'video.js/dist/video-js.css'
import { onMounted, onUnmounted, reactive, Ref, ref } from 'vue'
import Hls, { HlsConfig } from 'hls.js'
import { STREAM_BASE } from '@/plugins/http-common'

const videoOptions: VideoJsPlayerOptions = reactive({
  fluid: true,
  autoplay: true,
  controls: false,
  noUITitleAttributes: true,
})

let hls

const hls_options: Partial<HlsConfig> = {}

function create_hls() {
  hls = new Hls(hls_options)
  hls.loadSource(STREAM_BASE + '/video/index.m3u8')
  hls.attachMedia(video.value)
}

function destroy_hls() {
  if (hls) {
    hls.destroy()
  }
}

const video_player = ref(null) as unknown as Ref<VideoJsPlayer>
const video = ref(null) as unknown as Ref<HTMLVideoElement>
const video_state = ref(null) as unknown as Ref<VideoPlayerState>

function set_video(ev: {
  video: HTMLVideoElement
  player: VideoJsPlayer
  state: VideoPlayerState
}) {
  video_player.value = ev.player
  video.value = ev.video
  video_state.value = ev.state
}

function play() {
  create_hls()

  if (!hls.media.playing) {
    hls.media.play()
    video_player.value.currentTime(video_state.value.duration - 1)
  }
}

function stop() {
  if (hls?.media) {
    hls.media.pause()
    destroy_hls()
  }
}

function rewind() {
  if (document.hidden) return

  if (process.env.NODE_ENV !== 'production') {
    console.debug('Reload video stream')
  }

  if (video_state.value.duration) {
    video_player.value.currentTime(video_state.value.duration - min_delay)
  } else {
    video_player.value.currentTime(0)
  }
}

function delay_rewind() {
  if (process.env.NODE_ENV !== 'production') {
    console.debug('Auto max delay:', delay)
  }

  rewind()

  delay_count = 0
  delay_bad_count = 0
  delay_good_count = 0
}

const delay_max_count = 30
let delay = 0.5
const min_delay = 0.5
let delay_count = 0
let delay_bad_count = 0
let delay_good_count = 0

function time_watch() {
  const time_shift = video_state.value.duration - video_state.value.currentTime

  delay_count += 1

  if (time_shift > delay) {
    delay_bad_count += 1
  } else {
    delay_good_count += 1
  }

  if (delay_count < delay_max_count) return

  if (delay_bad_count > delay_max_count * 0.35) {
    delay += 0.25
    delay_rewind()
    return
  }

  if (delay_good_count > delay_max_count * 0.95 && delay > min_delay) {
    delay -= 0.25
    delay_rewind()
    return
  }

  if (delay_count > delay_max_count) {
    if (process.env.NODE_ENV !== 'production') {
      console.debug('Auto max delay:', delay)
    }

    delay_count = 0
    delay_bad_count = 0
    delay_good_count = 0
    return
  }
}

onMounted(() => {
  create_hls()

  window.addEventListener('visibilitychange', rewind)
})

onUnmounted(() => {
  destroy_hls()

  window.removeEventListener('visibilitychange', rewind)
})
</script>

<style>
.live-video {
  width: 100%;
  height: 100%;
  position: relative;

  & .video-js {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}
</style>
