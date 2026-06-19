<template>
  <div class="live-video">
    <video-player
      :options="videoOptions"
      @mounted="set_video"
      @timeupdate="time_watch"
    />

    <div class="live-video__mask" @click="reload">
      <div
        v-if="isDev()"
        style="background: white; width: max-content; margin: 2px"
      >
        <div>L: {{ latency.toFixed(2) }}</div>
        <div>ML: {{ min_delay.toFixed(2) }}</div>
        <div>TL: {{ delay.toFixed(2) }}</div>
        <div>P: {{ pckg_count }}\{{ delay_max_count }}</div>
        <div>GP\BP: {{ pckg_good_count }}\{{ pckg_bad_count }}</div>
        <div>PR: {{ video_player?.playbackRate() }}</div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { VideoJsPlayer, VideoJsPlayerOptions } from 'video.js'
import { VideoPlayer, VideoPlayerState } from '@videojs-player/vue'
import 'video.js/dist/video-js.css'
import { onMounted, onUnmounted, reactive, ref } from 'vue'
import Hls, { HlsConfig } from 'hls.js'
import { isDev } from '@/utils/func'

const props = withDefaults(
  defineProps<{
    path: string
    controls?: boolean
    autoDelay?: boolean
    autoplay?: boolean
    muted?: boolean
    reloadButton?: boolean
  }>(),
  {
    controls: false,
    autoDelay: false,
    autoplay: false,
    muted: false,
    reloadButton: false,
  }
)

defineExpose({
  set_volume: set_volume,
  play: play,
  stop: stop,
  get_played: get_played,
})

const videoOptions: VideoJsPlayerOptions = reactive({
  fluid: false,
  autoplay: props.autoplay,
  controls: props.controls,
  noUITitleAttributes: true,
  muted: props.muted,
})

let hls: Hls

const hls_options: Partial<HlsConfig> = {
  lowLatencyMode: true,
}

function create_hls() {
  hls = new Hls(hls_options)
  hls.loadSource(props.path)
  hls.attachMedia(video_html.value as HTMLMediaElement)

  hls.on(Hls.Events.ERROR, (err: string) => onError(err))
  hls.on(Hls.Events.FRAG_LOADING, () => onPlay())
  console.debug('HLS player created')
}

function destroy_hls() {
  if (hls) {
    hls.stopLoad()
    hls.destroy()
    console.debug('HLS player destroyed')
  }
}

const video_player = ref<VideoJsPlayer | null>(null)
const video_html = ref<HTMLVideoElement | null>(null)
const video_state = ref<VideoPlayerState | null>(null)

function set_video(ev: {
  video: HTMLVideoElement
  player: VideoJsPlayer
  state: VideoPlayerState
}) {
  video_player.value = ev.player
  video_html.value = ev.video
  video_state.value = ev.state
}

function rewind() {
  if (document.hidden || !props.autoDelay) return

  console.debug('Rewind stream')
  if (video_state.value?.duration) {
    video_player.value?.currentTime(video_state.value.duration - min_delay)
  } else {
    video_player.value?.currentTime(0)
  }
}

function play() {
  destroy_hls()

  create_hls()

  const vol = localStorage.getItem('volume') ?? '1'

  set_volume(Number.parseFloat(vol))

  // if (!hls.media.playing) {
  //   hls.media.play()
  //   video_player.value?.volume(vol ?? 0)
  // }
}

function stop() {
  if (hls?.media) {
    hls.media.pause()
    destroy_hls()
  }
}

function delay_rewind() {
  if (!props.autoDelay) return

  if (process.env.NODE_ENV !== 'production') {
    console.debug('Auto max delay:', delay.value)
  }

  pckg_count.value = 0
  pckg_bad_count.value = 0
  pckg_good_count.value = 0

  video_player.value?.playbackRate(1.05)
}

const delay_max_count = 30
const delay = ref(1)
const min_delay = 0.7
const pckg_count = ref(0)
const pckg_bad_count = ref(0)
const pckg_good_count = ref(0)

const latency = ref(0)

function time_watch() {
  if (!props.autoDelay) return

  latency.value = hls.latency

  pckg_count.value += 1

  if (latency.value > delay.value) {
    pckg_bad_count.value += 1
  } else {
    pckg_good_count.value += 1
  }

  if (pckg_count.value < delay_max_count) return

  if (pckg_bad_count.value > delay_max_count * 0.35) {
    delay.value += 0.1
    delay_rewind()
    return
  }

  if (pckg_good_count.value > delay_max_count && delay.value > min_delay) {
    delay.value -= 0.1
    delay_rewind()
    return
  }

  if (pckg_count.value > delay_max_count) {
    delay_rewind()
  }
}

// From 0.0 to 1.0
function set_volume(val: number) {
  video_player.value?.volume(val)
}

function get_played() {
  if (!hls || !hls.media) return false

  return !hls.media.paused
}

function reload() {
  if (props.reloadButton) {
    play()
  }
}

let error_timeout: undefined | number = undefined
let current_time_interval: undefined | number = undefined

function onPlay() {
  clearTimeout(error_timeout)
  error_timeout = undefined
}

function onError(err) {
  console.error(err)

  if (!error_timeout) {
    error_timeout = setTimeout(() => {
      console.debug('RESTART')

      play()
    }, 3000)
  }
}

function currentTimeObserve() {
  if (!hls || !video_player.value) return

  if (hls.latency < delay.value * 0.95) {
    video_player.value.playbackRate(1)
  }
}

onMounted(() => {
  if (props.autoplay) {
    create_hls()

    const vol = localStorage.getItem('volume') ?? '1'
    set_volume(Number.parseFloat(vol))

    setTimeout(() => {
      video_html.value?.play().catch((err) => console.error(err))
    }, 1000)

    current_time_interval = setInterval(currentTimeObserve, 200)
  }

  if (props.autoDelay) {
    window.addEventListener('visibilitychange', rewind)
  }
})

onUnmounted(() => {
  console.debug('HLS player unmounted')
  destroy_hls()

  clearTimeout(error_timeout)

  if (props.autoDelay) {
    window.removeEventListener('visibilitychange', rewind)
  }

  clearInterval(current_time_interval)
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
