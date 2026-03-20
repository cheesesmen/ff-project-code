<template>
  <div class="market-container">
    <header class="header">
      <h2>💎 游戏账号价值 AI 评估系统</h2>
      <div class="controls">
        <button :class="{active: currentGame==='genshin'}" @click="switchGame('genshin')">原神市场</button>
        <button :class="{active: currentGame==='delta'}" @click="switchGame('delta')">三角洲市场</button>
        <button class="sync-btn" @click="handleSync" :disabled="isSyncing">
          {{ isSyncing ? '🔄 同步中...' : '🚀 同步最新数据' }}
        </button>
      </div>
    </header>

    <div id="price-chart" class="chart-box"></div>

    <section class="report-bar">
      <div class="report-item"><strong>模型表现:</strong> XGBoost Regressor</div>
      <div class="report-item"><strong>平均误差(MAE):</strong> {{ currentGame==='genshin'?'￥45.2':'￥12.8' }}</div>
      <div class="report-item"><strong>拟合度(R²):</strong> 0.94</div>
      <div class="report-item"><strong>核心权重:</strong> 梯队角色命座 > 账号实名状态</div>
    </section>

    <div class="grid">
      <div v-for="item in accounts" :key="item.id" class="card" :class="{ recommended: item.is_recommended }">
        <div class="tag" v-if="item.is_recommended">🔥 严重低估</div>
        <div class="price-info">
          <span class="actual">￥{{ item.actual_price }}</span>
          <span class="predict">AI估: ￥{{ item.predict_price }}</span>
        </div>
        <p class="title">{{ item.name }}</p>
        <button class="detail-btn" @click="showDetail(item)">查看 AI 评估详情</button>
      </div>
    </div>

    <div v-if="detailItem" class="modal-mask">
      <div class="modal-card">
        <h3>🤖 AI 深度估值报告</h3>
        <div class="detail-content">
          <p><strong>商品 ID:</strong> {{ detailItem.id }}</p>
          <p><strong>市场标价:</strong> ￥{{ detailItem.actual_price }}</p>
          <p><strong>AI 预测价:</strong> ￥{{ detailItem.predict_price }}</p>
          <div class="feature-list">
            <strong>提取特征:</strong>
            <pre>{{ detailItem.features }}</pre>
          </div>
        </div>
        <div class="modal-btns">
          <button @click="detailItem = null">关闭</button>
          <button class="buy-btn" @click="jumpToPxb(detailItem.id)">前往平台秒杀</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, shallowRef } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const accounts = ref([])
const currentGame = ref('genshin')
const isSyncing = ref(false)
const detailItem = ref(null)
const chartInstance = shallowRef(null)

const fetchData = async () => {
  const res = await axios.get(`http://127.0.0.1:8000/api/valuation-analytics/?game=${currentGame.value}`)
  accounts.value = res.data
  await nextTick()
  renderChart()
}

const renderChart = () => {
  const dom = document.getElementById('price-chart')
  if (!dom) return
  if (!chartInstance.value) chartInstance.value = echarts.init(dom)
  
  const data = accounts.value.map(i => [i.actual_price, i.predict_price, i.name, i.is_recommended])
  const max = Math.max(...accounts.value.map(i => Math.max(i.actual_price, i.predict_price))) || 1000

  chartInstance.value.setOption({
    title: { text: '溢价/低估分布图', left: 'center' },
    xAxis: { name: '售价', type: 'value' },
    yAxis: { name: 'AI估价', type: 'value' },
    tooltip: { formatter: (p) => p.data[2] },
    series: [
      {
        type: 'scatter', 
        data: data,
        itemStyle: { color: (p) => p.data[3] ? '#ff4d4f' : '#bfbfbf' }
      },
      {
        type: 'line', data: [[0,0], [max, max]], 
        lineStyle: { type: 'dashed', color: '#1890ff' }, symbol: 'none'
      }
    ]
  })
}

const handleSync = async () => {
  isSyncing.value = true
  try {
    await axios.post('http://127.0.0.1:8000/api/sync-market/')
    alert('同步成功！')
    fetchData()
  } finally { isSyncing.value = false }
}

const showDetail = (item) => { detailItem.value = item }

// 在 <script setup> 中更新跳转函数
const jumpToPxb = (productId) => {
  // 🌟 使用你给出的在售商品详情路径格式
  const url = `https://www.pxb7.com/product/${productId}/1`;
  window.open(url, '_blank');
};

const switchGame = (g) => { currentGame.value = g; fetchData() }

onMounted(fetchData)
</script>

<style scoped>
.market-container { padding: 20px; max-width: 1200px; margin: 0 auto; font-family: sans-serif; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.controls button { margin-left: 10px; padding: 8px 15px; cursor: pointer; border: 1px solid #ddd; border-radius: 4px; }
.controls button.active { background: #1890ff; color: white; border-color: #1890ff; }
.sync-btn { background: #52c41a; color: white; border: none !important; }

.chart-box { height: 400px; background: #fff; border-radius: 8px; margin-bottom: 20px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }

.report-bar { display: flex; gap: 20px; background: #e6f7ff; padding: 15px; border-radius: 8px; margin-bottom: 20px; font-size: 14px; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.card { background: white; padding: 15px; border-radius: 8px; border: 1px solid #eee; position: relative; transition: 0.3s; }
.card.recommended { border: 2px solid #ff4d4f; background: #fff1f0; }
.tag { position: absolute; top: 0; right: 0; background: #ff4d4f; color: white; padding: 2px 8px; font-size: 12px; border-radius: 0 8px 0 8px; }
.title { font-size: 14px; color: #333; margin: 10px 0; height: 40px; overflow: hidden; }
.price-info { display: flex; justify-content: space-between; font-weight: bold; }
.actual { color: #333; font-size: 18px; }
.predict { color: #1890ff; font-size: 14px; }
.detail-btn { width: 100%; margin-top: 10px; background: #1890ff; color: white; border: none; padding: 8px; border-radius: 4px; cursor: pointer; }

.modal-mask { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal-card { background: white; padding: 30px; border-radius: 12px; width: 500px; max-width: 90%; }
pre { background: #f5f5f5; padding: 10px; font-size: 12px; overflow: auto; max-height: 200px; }
.modal-btns { margin-top: 20px; display: flex; justify-content: flex-end; gap: 10px; }
.buy-btn { background: #ff4d4f; color: white; border: none; padding: 8px 20px; border-radius: 4px; cursor: pointer; }
</style>