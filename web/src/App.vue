<!-- 根组件 -->
<!-- template - 结构 -->
<template>
  <!-- 通过:locale属性传入语言包对象，全局配置国际化文案 -->
  <a-config-provider :locale="zhCN">
    <!-- <router-view> 使得单页面应用能够在不刷新整个页面的情况下，动态显示不同的内容 -->
    <router-view></router-view>
  </a-config-provider>
</template>

<!-- script - 行为 -->
<!-- 引入 Ant Design Vue所需的中文语言包 -->
<script setup lang="ts">
  import zhCN from 'ant-design-vue/es/locale/zh_CN';
</script>

<!-- style - 样式 -->
<!-- font-family指定了一个字体栈，即当浏览器渲染文本时会尝试使用的几个字体序列 -->
<style>
  #app {
  font-family: 'Avenir', Helvetica, Arial, sans-serif;
  height: 100vh;
}
</style>
