<template>
  <!-- Используем PascalCase и проверяем наличие опций -->
  <Chart
    v-if="series[0].data && series[0].data.length > 0"
    ref="chartRef"
    :constructor-type="'stockChart'"
    :options="chartOptions"
  />
  <div v-else class="loading-placeholder">Ожидание данных...</div>
</template>

<script lang="ts" setup>
import { Chart } from 'highcharts-vue'
import Highcharts from 'highcharts'
import StockModule from 'highcharts/modules/stock'
import { computed, ref } from 'vue'
import store from '@/store'

if (typeof StockModule === 'function') {
  StockModule(Highcharts)
} else if (StockModule && (StockModule as any).default) {
  ;(StockModule as any).default(Highcharts)
}

const chartRef = ref(null)

const activityData = computed(() => store.getters.getNN.activity_log)

const series = computed<Highcharts.SeriesOptionsType[]>(() => {
  return [
    {
      type: 'area',
      name: 'Activity',
      data: [...activityData.value], // Копируем массив
      marker: {
        enabled: true,
        symbol: 'circle',
      },
      states: {
        hover: { enabled: false },
      },
      color: '#ffffff',
      fillColor: {
        linearGradient: { x1: 0, y1: 0, x2: 0, y2: 1 },
        stops: [
          [0, 'rgba(255, 255, 255, 0.5)'],
          [1, 'rgba(255, 255, 255, 0.1)'],
        ],
      },
    },
  ]
})

const chartOptions = computed<Highcharts.Options>(() => {
  return {
    time: { useUTC: false },
    legend: { enabled: false },
    chart: {
      height: 600,
      animation: false, // Отключаем анимацию для частых обновлений (FPS)
    },
    rangeSelector: { enabled: false },
    navigator: { enabled: false },
    scrollbar: { enabled: false },
    xAxis: {
      type: 'linear',
      ordinal: false,
      labels: {
        formatter: function () {
          // 'this' в Highcharts содержит контекст точки
          const logData = store.getters.getNN.activity_log_data
          if (!logData) return ''
          const startTime = logData.getTime()
          return new Date(
            startTime + (this.value as int) * 200
          ).toLocaleTimeString()
        },
      },
    },
    yAxis: {
      minTickInterval: 1,
      max: 10,
      opposite: false,
    },
    tooltip: {
      formatter: function () {
        const logData = store.getters.getNN.activity_log_data
        if (!logData) return ''
        const startTime = logData.getTime()
        const x = this.x as number
        const time = new Date(startTime + x * 200).toLocaleTimeString()
        return `<b>${time}</b><br/>Activity: ${this.y}`
      },
    },
    series: series.value,
    credits: { enabled: false },
    accessibility: { enabled: false },
  }
})

Highcharts.setOptions({
  lang: {
    decimalPoint: '.',
    thousandsSep: ' ',
  },
  time: {
    useUTC: false,
  },
})
</script>

<style scoped>
.loading-placeholder {
  height: 600px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9f9f9;
  border: 1px solid #ddd;
}
</style>
