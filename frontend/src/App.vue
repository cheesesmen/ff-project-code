<template>
  <div class="main-layout">
    <header class="header">
      <h1>🎮 AI 游戏账号资产估值系统</h1>
      <div class="game-tabs">
        <button :class="{ active: curGame === 'genshin' }" @click="curGame = 'genshin'">🍃 原神估值大厅</button>
        <button :class="{ active: curGame === 'delta' }" @click="curGame = 'delta'">🪖 三角洲估值大厅</button>
      </div>
    </header>

    <main class="content">
      <section class="chart-section">
        <ValuationChart :game="curGame" :key="curGame + 'chart'" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import ValuationChart from './components/ValuationChart.vue'

// 默认显示原神
const curGame = ref('genshin')
</script>

<style scoped>
.main-layout { font-family: 'PingFang SC', sans-serif; background: #f0f2f5; min-height: 100vh; }
.header { background: #2c3e50; color: white; padding: 20px 0; text-align: center; }
.game-tabs { margin-top: 15px; }
.game-tabs button { background: transparent; border: 1px solid white; color: white; padding: 8px 20px; margin: 0 10px; border-radius: 20px; cursor: pointer; transition: 0.3s; }
.game-tabs button.active { background: #409eff; border-color: #409eff; font-weight: bold; }
.content { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
.chart-section { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
</style>