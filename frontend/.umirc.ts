import { defineConfig } from 'umi';

export default defineConfig({
  npmClient: 'pnpm',
  history: {
    type: 'hash',  // 使用 hash 路由，支持动态路径配置
  },
  base: '/',
  publicPath: '/',
  routes: [
    { 
      path: '/login', 
      component: '@/pages/Login',
      layout: false,  // 登录页面不使用布局
    },
    {
      path: '/',
      component: '@/layouts/index',
      layout: false,  // 禁用 umi 内置 layout，使用自定义 layout
      routes: [
        { path: '/', redirect: '/dashboard' },
        { path: '/dashboard', component: '@/pages/Dashboard' },
        { path: '/keys', component: '@/pages/Keys' },
        { path: '/logs', component: '@/pages/Logs' },
        { path: '/configs', component: '@/pages/Configs' },
      ],
    },
  ],
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:6777/admin',
      changeOrigin: true,
    },
    '/auth': {
      target: 'http://127.0.0.1:6777',
      changeOrigin: true,
    },
  },
});