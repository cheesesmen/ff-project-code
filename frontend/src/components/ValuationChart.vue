<template>
  <div class="chart-container">
    <div class="chart-header">
      <h3>📊 市场实价 vs AI 预测估值 (最近60条)</h3>
    </div>
    <div ref="chartRef" style="width: 100%; height: 500px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'

const props = defineProps(['game'])
const chartRef = ref(null)
let myChart = null

const initChart = async () => {
  if (!chartRef.value) return
  
  // 1. 初始化实例
  if (!myChart) {
    myChart = echarts.init(chartRef.value)
  }
  myChart.showLoading()

  try {
    // 2. 获取后端数据 (指向你的 Django API 地址)
    const res = await axios.get(`http://127.0.0.1:8000/api/valuation-analytics/?game=${props.game}`)
    const data = res.data

    // 3. 准备坐标轴数据
    const names = data.map(item => item.name)
    const actuals = data.map(item => item.actual)
    const predicts = data.map(item => item.predict)

    // 4. 配置项
    const option = {
      tooltip: { trigger: 'axis' },
      legend: { data: ['市场实际价格', 'AI 预测价格'] },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'category', data: names, axisLabel: { show: false } }, // 隐藏下方杂乱名称
      yAxis: { type: 'value', name: '价格 (元)' },
      series: [
        {
          name: '市场实际价格',
          type: 'line',
          data: actuals,
          itemStyle: { color: '#2c3e50' },
          smooth: true
        },
        {
          name: 'AI 预测价格',
          type: 'bar',
          data: predicts,
          itemStyle: { color: '#409eff', opacity: 0.7 },
          barWidth: '40%'
        }
      ]
    }

    myChart.hideLoading()
    myChart.setOption(option)
  } catch (err) {
    console.error("图表数据加载失败:", err)
    myChart.hideLoading()
  }
}

// 监听游戏切换，重新加载数据
watch(() => props.game, () => initChart())

onMounted(() => {
  initChart()
  window.addEventListener('resize', () => myChart && myChart.resize())
})

onUnmounted(() => {
  if (myChart) myChart.dispose()
})
</script>

<style scoped>
.chart-container { width: 100%; }
.chart-header { margin-bottom: 20px; text-align: left; border-left: 4px solid #409eff; padding-left: 15px; }
</style>