<template>
  <div class="chart-container">
    <div v-if="loading" class="loading">正在由 AI 评估实时数据...</div>
    <div v-else ref="chartRef" style="width: 100%; height: 500px;"></div>
  </div>
</template>

<script setup>
import { onMounted, ref, defineProps } from 'vue';
import * as echarts from 'echarts';
import axios from 'axios';

// frontend/src/components/ValuationChart.vue
const fetchData = async () => {
  try {
    // 1. 确保加上了 http://127.0.0.1:8000
    const res = await axios.get(`http://127.0.0.1:8000/api/valuation-analytics/?game=${props.game}`);
    if (res.data && res.data.length > 0) {
      renderChart(res.data); // 将数据传给绘图函数
    }
  } catch (err) {
    console.error("数据请求失败，请检查后端是否开启", err);
  }
};
const props = defineProps({
  game: String // 接收父组件传来的游戏类型
})

const chartRef = ref(null);
const loading = ref(true);

onMounted(async () => {
  try {
    // 动态请求对应游戏的数据
    const res = await axios.get(`http://127.0.0.1:8000/api/valuation-analytics/?game=${props.game}`);
    const rawData = res.data;
    loading.value = false;

    if(rawData.error) {
       console.error(rawData.error); return;
    }

    setTimeout(() => {
      const myChart = echarts.init(chartRef.value);
      const titleText = props.game === 'genshin' ? '原神实时捡漏雷达' : '三角洲行动资产估值图';
      const colorNormal = props.game === 'genshin' ? '#91cc75' : '#fac858';

      myChart.setOption({
        title: { text: titleText, left: 'center' },
        tooltip: { trigger: 'item', formatter: (p) => `${p.data[2]}<br/>实际标价: ￥${p.data[0]}<br/>AI评估价: ￥${p.data[1]}` },
        xAxis: { name: '实际挂牌价(元)', splitLine: { show: false } },
        yAxis: { name: 'AI预测价(元)' },
        series: [{
          type: 'scatter',
          symbolSize: 12,
          data: rawData.map(d => [d.actual, d.predict, d.name]),
          itemStyle: {
            // 如果 AI 估价大于实际标价 20%，标为红色高亮（代表极品捡漏号）
            color: (p) => (p.data[1] > p.data[0] * 1.2 ? '#ee6666' : colorNormal) 
          },
          markLine: {
            data: [{ type: 'average', name: '平均线' }],
            lineStyle: { type: 'dashed', color: '#999' }
          }
        }]
      });
    }, 100);
  } catch (err) {
    console.error("加载图表失败", err);
    loading.value = false;
  }
});
</script>

<style scoped>
.loading { text-align: center; color: #999; line-height: 500px; font-size: 18px; }
</style>