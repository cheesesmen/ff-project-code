import { createApp } from 'vue'
import './style.css' // 引入默认样式
import App from './App.vue'

console.log("🚀 系统正在启动...");

const app = createApp(App)
app.mount('#app')