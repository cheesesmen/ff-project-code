<template>
  <div class="market-container">
    <h2>💎 游戏账号交易中心</h2>
    <div class="grid">
      <div v-for="item in accounts" :key="item.id" class="card">
        <div class="price">￥{{ item.price }}</div>
        <div class="info">
          <p class="title">{{ item.show_title }}</p>
          <span class="tag">等级: {{ item.level || '精选' }}</span>
        </div>
        <button class="detail-btn">查看详情</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const accounts = ref([])

onMounted(async () => {
  try {
    // 连通你的 Django 接口
    const res = await axios.get('http://127.0.0.1:8000/api/delta/')
    accounts.value = res.data
  } catch (e) {
    console.error("数据加载失败，请检查 Django 是否运行", e)
  }
})
</script>

<style scoped>
.market-container { padding: 20px; background: #f5f7fa; min-height: 100vh; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; }
.card { background: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); transition: 0.3s; }
.card:hover { transform: translateY(-5px); }
.price { color: #f56c6c; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
.title { font-size: 14px; color: #303133; height: 40px; overflow: hidden; margin: 10px 0; }
.tag { background: #ecf5ff; color: #409eff; padding: 2px 8px; border-radius: 4px; font-size: 12px; }
.detail-btn { width: 100%; margin-top: 15px; border: none; background: #409eff; color: white; padding: 10px; border-radius: 6px; cursor: pointer; }
</style>