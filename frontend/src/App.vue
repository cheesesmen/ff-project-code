<template>
  <div id="app-container">
    <AccountList />
  </div>
</template>

<script setup>
import AccountList from './components/AccountList.vue'
</script>

<style>
/* 保证页面没有边距 */
body {
  margin: 0;
  padding: 0;
  background-color: #f5f7fa;
}
#app-container {
  font-family: Arial, sans-serif;
}
</style>